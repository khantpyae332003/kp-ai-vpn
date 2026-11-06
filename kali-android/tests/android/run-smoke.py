#!/usr/bin/env python3
"""Destructive test ONLY for our dedicated kali-test Android emulator, never a phone.
Uses an explicitly labelled BIOS fixture, not Kali. Outputs screenshots and real UI assertions.
"""
from pathlib import Path
import subprocess,time,xml.etree.ElementTree as ET,re,struct,hashlib,os
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'.tools/android-smoke';OUT.mkdir(exist_ok=True)
ADB=str(ROOT/'.tools/android-sdk/platform-tools/adb');SERIAL='emulator-5554';APK=ROOT/'engine/kali-app/build/outputs/apk/debug/kali-app-debug.apk'
def adb(*args,timeout=60,check=True):
 p=subprocess.run([ADB,'-s',SERIAL,*args],capture_output=True,timeout=timeout)
 if check and p.returncode:raise RuntimeError(p.stderr.decode(errors='replace')+p.stdout.decode(errors='replace'))
 return p.stdout

def stage(text):print(text,flush=True)
def launch():
 adb('shell','am','start','-n','com.kp.kali/.BootstrapActivity');time.sleep(3)
 tap('Advanced · manual disk & diagnostics')
def ui():
 for attempt in range(6):
  adb('shell','sh','-c',': > /sdcard/kali-smoke.xml')
  result=adb('shell','uiautomator','dump','/sdcard/kali-smoke.xml',timeout=45)
  raw=adb('exec-out','cat','/sdcard/kali-smoke.xml')
  if not raw.strip():raise RuntimeError('No fresh UI hierarchy produced: '+result.decode(errors='replace'))
  tree=ET.fromstring(raw)
  if any(x.attrib.get('text')=="System UI isn't responding" for x in tree.iter('node')):
   wait=next(x for x in tree.iter('node') if x.attrib.get('text')=='Close app');a=list(map(int,re.findall(r'\d+',wait.attrib['bounds'])))
   stage('Software emulator System UI ANR: restarting System UI and retrying (app ANRs are not ignored).')
   adb('shell','input','tap',str((a[0]+a[2])//2),str((a[1]+a[3])//2));time.sleep(3);continue
  return tree
 raise RuntimeError('Emulator System UI remains unresponsive')
def tap(text,scroll=True):
 for n in range(7 if scroll else 1):
  tree=ui();nodes=[x for x in tree.iter('node') if x.attrib.get('text','').casefold()==text.casefold()]
  if nodes:
   node=nodes[0];a=list(map(int,re.findall(r'\d+',node.attrib['bounds'])));adb('shell','input','tap',str((a[0]+a[2])//2),str((a[1]+a[3])//2));time.sleep(3);return node
  adb('shell','input','swipe','240','680','240','240','200')
 raise AssertionError('Missing control: '+text)
def screenshot(name):
 data=adb('exec-out','screencap','-p',timeout=60);assert data.startswith(b'\x89PNG\r\n\x1a\n');(OUT/name).write_bytes(data)
def assert_text(text):
 for attempt in range(4):
  tree=ui()
  if any(x.attrib.get('text')==text for x in tree.iter('node')):return
  adb('shell','input','swipe','240','240','240','700','200');time.sleep(1)
 raise AssertionError(ET.tostring(tree).decode()[:2000])
def seed(image):
 # This function must only touch the dedicated test AVD. No user device or unrelated app.
 assert 'kali-test' in adb('emu','avd','name').decode()
 adb('shell','am','force-stop','com.kp.kali')
 fixture=OUT/'fixture.disk';fixture.write_bytes(image);adb('push',str(fixture),'/data/local/tmp/kali-smoke.disk')
 adb('shell','run-as','com.kp.kali','mkdir','-p','files')
 adb('shell','run-as','com.kp.kali','cp','/data/local/tmp/kali-smoke.disk','files/kali.disk')

stage('Waiting for Android boot (software emulation)…')
for n in range(90):
 try:
  if adb('shell','getprop','sys.boot_completed',timeout=10,check=False).strip()==b'1':break
 except subprocess.TimeoutExpired:pass
 if n%6==0:stage('Android still booting…')
 time.sleep(5)
else:raise RuntimeError('Android boot timed out')
assert 'kali-test' in adb('emu','avd','name').decode()
assert adb('shell','getprop','ro.kernel.qemu').strip()==b'1'
stage('Installing the final development APK on the dedicated emulator…')
if os.environ.get('KALI_SMOKE_SKIP_INSTALL')!='1':adb('install','-r',str(APK),timeout=180)
adb('shell','wm','size','480x800');adb('shell','wm','density','160')
for key in ['window_animation_scale','transition_animation_scale','animator_duration_scale']:adb('shell','settings','put','global',key,'0')
raw=(ROOT/'.tools/boot-proof.img').read_bytes();assert len(raw)==512 and raw[-2:]==b'\x55\xaa'
seed(raw);launch();screenshot('launcher.png');assert_text('STOPPED')
stage('Starting real QEMU with the labelled BIOS fixture…')
tap('Start Kali VM');time.sleep(12);screenshot('guest.png')
adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(3);assert_text('RUNNING')
tree=ui();start=next(x for x in tree.iter('node') if x.attrib.get('text')=='Start Kali VM');assert start.attrib['enabled']=='false'
stage('PASS: launcher reports QEMU RUNNING after Back; duplicate Start disabled.')
# Trigger activity recreation while retaining the service and process-owned session.
adb('shell','wm','size','500x820');time.sleep(3);assert_text('RUNNING');adb('shell','wm','size','480x800')
stage('PASS: actual Android activity recreation retained the running guest.')
tap('Shut down guest');time.sleep(3);assert_text('STOPPING')
stage('Waiting for graceful-shutdown timeout (BIOS fixture cannot handle ACPI)…');time.sleep(31)
tap('Force stop…');tap('Force stop',scroll=False);time.sleep(5);launch();assert_text('STOPPED')
assert adb('exec-out','run-as','com.kp.kali','cat','files/kali.disk')==raw
stage('PASS: shutdown timeout/confirmed force stop, disk retained, app can reopen.')
# Emulate a killed import and verify startup reclamation without touching the disk.
adb('shell','am','force-stop','com.kp.kali')
orphan=OUT/'orphan.partial';orphan.write_bytes(b'incomplete')
adb('push',str(orphan),'/data/local/tmp/kali-orphan.partial')
adb('shell','run-as','com.kp.kali','cp','/data/local/tmp/kali-orphan.partial','files/kali-import-orphan.partial')
launch();assert b'kali-import-orphan.partial' not in adb('shell','run-as','com.kp.kali','ls','files')
assert adb('exec-out','run-as','com.kp.kali','cat','files/kali.disk')==raw
stage('PASS: abandoned import recovered and existing disk retained.')
# Structurally plausible header but unsupported reference-count width: importer accepts basic
# header; native QEMU must reject it and leave a diagnostic after process death.
bad=bytearray(512);struct.pack_into('>IIQIIQIIQQIIQQQQII',bad,0,0x514649fb,3,0,0,16,1048576,0,1,65536,131072,1,0,0,0,0,0,100,104)
seed(bad);launch();tap('Start Kali VM');time.sleep(10);launch();tap('Startup diagnostics');time.sleep(3)
tree=ui();text='\n'.join(x.attrib.get('text','') for x in tree.iter('node'));(OUT/'invalid-disk-diagnostics.txt').write_text(text)
assert any(s in text.lower() for s in ['reference count entry width too large','refcount','l1 table','image is corrupt','could not open']),text[-3000:]
screenshot('invalid-disk-diagnostics.png');stage('PASS: native invalid-disk failure visible in diagnostics after reopening.')
# Leave a labelled running demonstration, not an invalid guest or a simulated Kali screen.
seed(raw);launch();tap('Start Kali VM');time.sleep(10);screenshot('guest-final.png')
stage('PASS: final APK launched with BIOS fixture; inspect guest-final.png for the boot marker. Kali OS/physical ARM64 phone not tested.')
(OUT/'result.txt').write_text('PASS: native BIOS guest; actual activity recreation; duplicate start controls; shutdown timeout and force stop; disk retention; killed-import recovery; native error diagnostics. No Kali OS or physical-phone verification.\n')
