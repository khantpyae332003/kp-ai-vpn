#!/usr/bin/env python3
"""Real managed cold-setup verification, destructive ONLY to kali-auto-test AVD.
No alternative image, NBD root disk, fake readiness, or resource-check bypass.
Prepare the API29 6GiB/48GiB test AVD and its session-proxy CA separately.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,time,xml.etree.ElementTree as ET,re,shutil,signal,datetime,os
from run_evidence import RunEvidence
from adb_transport import execute
ROOT=Path(__file__).resolve().parents[2]
ADB=ROOT/'.tools/android-sdk/platform-tools/adb';OUT_BASE=ROOT/'.tools/managed-smoke'
parser=argparse.ArgumentParser();parser.add_argument('--watch-only',action='store_true');parser.add_argument('--apk',default='artifacts/KP-Kali-VM-0.2.2-debug.apk');parser.add_argument('--minutes',type=int,default=90);parser.add_argument('--status-file');args=parser.parse_args()
latest_phase='Not yet observed'
def publish_status(evidence=None,phase='Not yet observed'):
 if not args.status_file:return
 target=(ROOT/args.status_file).resolve()
 if not target.is_relative_to((ROOT/'artifacts').resolve()):raise ValueError('Status report must be inside generated artifacts')
 data=json.loads((evidence.directory/'status.json').read_text()) if evidence else {'status':'RUNNING','mode':'observation' if args.watch_only else 'cold'}
 data.update(checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),guest_phase=phase,evidence_directory=str(evidence.directory.relative_to(ROOT)) if evidence else None,observer_pid=os.getpid(),physical_phone_tested=False,display_visually_verified=False)
 stage=target.with_suffix('.tmp');stage.write_text(json.dumps(data,indent=2)+'\n');stage.replace(target)
publish_status()
apk=ROOT/args.apk
try:expected_hash=hashlib.sha256(apk.read_bytes()).hexdigest()
except OSError as exc:
 failed=RunEvidence(OUT_BASE,'0'*64,args.watch_only);failed.fail('Selected APK cannot be read');publish_status(failed);raise
record=RunEvidence(OUT_BASE,expected_hash,args.watch_only);OUT=record.directory;publish_status(record)
def adb(*a,timeout=30,check=True,read_only=False):
 p=execute([str(ADB),'-s','emulator-5554',*a],timeout=timeout,read_only=read_only,on_retry=lambda n:stage('Read-only ADB timeout; retry '+str(n)+' of 2'))
 if check and p.returncode:raise RuntimeError(p.stderr.decode(errors='replace')+p.stdout.decode(errors='replace'))
 return p.stdout

def stage(s):print(time.strftime('%H:%M:%S'),s,flush=True)
def screenshot(name):
 b=adb('exec-out','screencap','-p',timeout=60);assert b.startswith(b'\x89PNG\r\n\x1a\n');(OUT/name).write_bytes(b)
def private(*a,check=False,timeout=60):return adb('exec-out','run-as','com.kp.kali',*a,check=check,timeout=timeout,read_only=bool(a and a[0] in {'cat','ls','pwd','sha256sum','du'}))
def hierarchy():
 adb('shell',': > /sdcard/kali-auto-ui.xml')
 adb('shell','uiautomator','dump','/sdcard/kali-auto-ui.xml',timeout=45)
 raw=adb('exec-out','cat','/sdcard/kali-auto-ui.xml');assert raw.strip(),'Fresh UI hierarchy absent'
 return ET.fromstring(raw)
def check_dialogs():
 try:tree=hierarchy()
 except (RuntimeError,subprocess.TimeoutExpired,AssertionError,ET.ParseError):
  stage('Fresh UI hierarchy unavailable; no stale snapshot or blind dialog tap used')
  return
 texts=[n.attrib.get('text','') for n in tree.iter('node')]
 if "System UI isn't responding" in texts:
  screenshot('system-ui-anr.png')
  node=next(n for n in tree.iter('node') if n.attrib.get('text')=='Close app')
  q=list(map(int,re.findall(r'\d+',node.attrib['bounds'])));adb('shell','input','tap',str((q[0]+q[2])//2),str((q[1]+q[3])//2))
  stage('Dismissed only the observed emulator System UI ANR; app ANRs are never ignored')
 elif any("isn't responding" in text or 'is not responding' in text for text in texts):
  screenshot('blocking-anr.png');raise RuntimeError('Observed a non-System-UI ANR; no app success claimed')
def click(text):
 tree=hierarchy()
 for n in tree.iter('node'):
  if n.attrib.get('text','').casefold()==text.casefold():
   q=list(map(int,re.findall(r'\d+',n.attrib['bounds'])));adb('shell','input','tap',str((q[0]+q[2])//2),str((q[1]+q[3])//2));return
 raise AssertionError('Missing actual UI control: '+text)
def package_path(package):
 lines=adb('shell','pm','path',package).decode().splitlines()
 paths=[line[8:] for line in lines if line.startswith('package:')]
 assert len(paths)==1 and re.fullmatch(r'/data/app/[A-Za-z0-9._~+/=-]+/base\.apk',paths[0]), 'Unexpected installed APK layout'
 return paths[0]
def installed_hash():
 value=private('sha256sum',package_path('com.kp.kali'),check=True,timeout=180).decode().split()[0]
 assert re.fullmatch('[0-9a-f]{64}',value),'No installed APK checksum'
 return value
def main_pid():
 pids=adb('shell','pidof','com.kp.kali',check=False).decode().split()
 assert len(pids)==1,'Expected one live target app process'
 return pids[0]
def live_guest():
 data=private('pwd',check=True).decode().strip()
 output=private('env','CLASSPATH='+package_path('com.kp.kali.test'),'/system/bin/app_process','/system/bin','--nice-name=kp-verify-qmp','com.kp.kali.QmpStatusProbe',data,check=True,timeout=90).decode()
 (OUT/'live-qmp.txt').write_text(output)
 rows=[line[len('KP_TEST_QMP='):] for line in output.splitlines() if line.startswith('KP_TEST_QMP=')]
 assert len(rows)==1,'No live QMP test response'
 status=json.loads(rows[0]);assert status['running'] is True and status['status']=='running' and status['uid']>=10000,'No ordinary-app-UID live guest'
 frame=private('cat','cache/verification.ppm',check=True);assert frame.startswith((b'P6',b'P3')),'No actual guest framebuffer'
 (OUT/'guest-framebuffer.ppm').write_bytes(frame)
 return True
def main():
 global latest_phase
 assert adb('shell','getprop','ro.kernel.qemu').strip()==b'1'
 assert adb('emu','avd','name').splitlines()[0].strip()==b'kali-auto-test', 'Refusing any phone or other AVD'
 assert adb('shell','id','-u').strip()==b'2000','Return adbd to unrooted shell before app test'
 profile=json.loads((ROOT/'engine/kali-app/src/main/assets/managed/profile.json').read_text())
 (OUT/('environment-watch.txt' if args.watch_only else 'environment.txt')).write_text('AVD=kali-auto-test; API29 x86_64; software emulation; stock app resources/network paths\nAPK SHA256='+hashlib.sha256(apk.read_bytes()).hexdigest()+'\n'+adb('shell','cat','/proc/meminfo').decode().splitlines()[0]+'\n'+adb('shell','df','-h','/data').decode())
 if not args.watch_only:
  stage('Installing exact published APK, clearing only disposable test app data')
  adb('install','-r',str(apk),timeout=420)
  assert adb('shell','pm','clear','com.kp.kali').strip()==b'Success'
  adb('shell','am','start','-n','com.kp.kali/.BootstrapActivity')
  stage('Cold automatic launch; normal registry downloads and private root volume')
 assert installed_hash()==expected_hash,'Installed APK differs from the selected artifact'
 stage('Installed APK byte hash matches selected artifact; mode='+('observation' if args.watch_only else 'controlled cold setup'))
 start=time.monotonic();last='';seen=[];foregrounded=False;lastCapture=0;boot_pid=None;boot_requested=None;last_serial=None;serial_progress=None
 while time.monotonic()-start<args.minutes*60:
  if shutil.disk_usage(ROOT).free<512*1024*1024:
   adb('shell','am','force-stop','com.kp.kali')
   raise SystemExit('Stopped disposable app before cloud host disk exhaustion; no success claimed')
  serial=private('cat','cache/managed-serial.log').decode(errors='replace')
  receipt=private('cat','files/managed/volume.properties').decode(errors='replace')
  blobs=private('ls','-l','files/managed/blobs').decode(errors='replace').strip()
  # Returning to the real launcher after background transfer exercises its normal automatic boot.
  entries={}
  for row in blobs.splitlines():
   cols=row.split()
   if len(cols)>=8:
    try:entries[cols[-1]]=int(cols[4])
    except ValueError:pass
  complete=all(entries.get(layer['digest'][7:])==layer['size']+(512-layer['size']%512)%512 for layer in profile['layers'])
  if complete and not foregrounded:
   adb('shell','am','start','-n','com.kp.kali/.BootstrapActivity')
   stage('All pinned blobs published by production verifier; returned to ordinary launcher for automatic boot')
   foregrounded=True;boot_requested=time.monotonic()
  if serial and serial!=last_serial:
   last_serial=serial;serial_progress=time.monotonic()
  phases=[s.strip() for s in serial.splitlines() if s.startswith('KP:')]
  if phases:latest_phase=phases[-1]
  elif serial:latest_phase='Linux kernel boot output observed'
  publish_status(record,latest_phase)
  if boot_requested and not phases and time.monotonic()-(serial_progress or boot_requested)>1200:
   screenshot('no-kernel-progress.png');raise RuntimeError('No new guest serial output for20minutes after complete-cache launch; inspect native firmware/boot diagnostics')
  if phases and not boot_pid:boot_pid=main_pid()
  if boot_pid and not args.watch_only:assert main_pid()==boot_pid,'Guest process changed; no continuous cold-run proof'
  if phases and phases[-1]!=last:stage(phases[-1]);last=phases[-1]
  if any(s.startswith('KP:ERROR:') for s in phases):
   screenshot('guest-error.png');(OUT/'guest-serial.log').write_text(serial);raise SystemExit('Guest emitted actual setup error')
  if 'ready=true' in receipt:
   required=['KP:ROOT_UID:0','KP:SUDO_UID:0','KP:DESKTOP_READY:'+profile['manifestDigest']]
   assert all(s in phases for s in required), 'Receipt without complete observed guest proof'
   (OUT/'guest-serial.log').write_text(serial);(OUT/'volume.properties').write_text(receipt)
   actual_hash=installed_hash()
   live=live_guest()
   if not args.watch_only:assert boot_pid==main_pid(),'Guest process changed during final verification'
   screenshot('app-screenshot.png')
   record.complete(actual_hash,live)
   stage(record.status+': live guest and stored root/sudo/desktop proof captured; inspect app/framebuffer images. Physical phone untested.')
   break
  if not phases:
   summary=' | '.join(blobs.splitlines()[-5:])
   if summary!=last:stage('Image cache: '+(summary or 'not yet available'));last=summary
  if not private('cat','/proc/self/status').strip():stage('App private state temporarily unavailable')
  if time.monotonic()-lastCapture>=120:
   screenshot('latest.png');check_dialogs();lastCapture=time.monotonic()
  time.sleep(15)
 else:
  screenshot('timeout.png');(OUT/'guest-serial.log').write_text(serial)
  raise SystemExit('Timed out; no desktop success claimed. Inspect actual UI/serial/cache evidence.')

def interrupted(signum,frame):raise KeyboardInterrupt()
signal.signal(signal.SIGTERM,interrupted)
try:main()
except KeyboardInterrupt:
 record.interrupt();raise SystemExit(130)
except BaseException as exc:
 record.fail(str(exc));raise
finally:publish_status(record,latest_phase)
