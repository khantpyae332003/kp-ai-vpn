#!/usr/bin/env python3
"""One bounded free-plan physical session; captures evidence, never fabricates readiness."""
import datetime,hashlib,json,os,re,subprocess,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
from appium_client import Client,RemoteFailure,has_guest_proof

ROOT=Path(__file__).resolve().parents[2]
RUN=os.environ.get('GITHUB_RUN_ID','')
if not RUN.isdigit():raise SystemExit('A GitHub Actions run ID is required')
ATTEMPT=os.environ.get('GITHUB_RUN_ATTEMPT','1')
if not ATTEMPT.isdigit():raise SystemExit('Invalid run attempt')
OUT=ROOT/'.ci/phone-observation'/(RUN+'-'+ATTEMPT)
OUT.mkdir(parents=True,exist_ok=True)
STATE={'status':'PREPARING','run_id':RUN,'run_attempt':ATTEMPT,'apk_release':'WITHHELD','device':os.environ.get('DEVICE_NAME','Samsung Galaxy S23 Ultra'),'os_version':os.environ.get('DEVICE_OS_VERSION','13.0'),
       'root_sudo_manifest_observed':False,'visible_desktop_reviewed':False,'tools_verified':False,'shutdown_reopen_verified':False,
       'installed_apk_bytes_independently_verified':False,'session_started':False,'session_creation_attempted':False,'cleanup_confirmed':False,'cleanup_state':'not_required'}
BRANCH='codex/browserstack-connection'

def git(*args,check=True):
 return subprocess.run(['git',*args],cwd=ROOT,capture_output=True,text=True,timeout=90,check=check)
def save():
 STATE['checked_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 (OUT/'status.json').write_text(json.dumps(STATE,indent=2)+'\n')
def publish():
 # Local evidence is authoritative; remote progress transport must not stop a phone.
 STATE.pop('progress_publication_error',None)
 save()
 if os.environ.get('PUBLISH_PHONE_PROGRESS')!='1':return
 try:
  git('config','user.name','github-actions[bot]');git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
  git('add',str(OUT.relative_to(ROOT)))
  if git('diff','--cached','--quiet',check=False).returncode!=0:
   git('commit','-q','-m','Record phone observation '+RUN)
  # Retry unpushed commits even when no new evidence needs a commit.
  for attempt in range(3):
   git('fetch','origin',BRANCH);git('rebase','FETCH_HEAD')
   if git('push','origin','HEAD:'+BRANCH,check=False).returncode==0:return
  raise RuntimeError('progress_push_rejected')
 except (subprocess.SubprocessError,RuntimeError) as error:
  # Never retain raw git output: a remote error may include credential material.
  STATE['progress_publication_error']=type(error).__name__
  save()
  print('::warning::Remote progress unavailable; local evidence retained and phone observation continues.',flush=True)
def node_texts(xml):return [n.attrib.get('text','') for n in ET.fromstring(xml).iter() if n.attrib.get('displayed')!='false' and n.attrib.get('visible-to-user')!='false']
def in_app(xml):return any(n.attrib.get('package')=='com.kp.kali' for n in ET.fromstring(xml).iter())
def capture(client,label,xml=None):
 xml=xml if xml is not None else client.source()
 # Publish UI captures only when the observed hierarchy belongs to the test app.
 if not in_app(xml):return False
 (OUT/(label+'.xml')).write_text(xml)
 try:
  image=client.screenshot();(OUT/(label+'.png')).write_bytes(image)
  STATE.pop('screenshot_capture_error',None);STATE['last_screenshot_sha256']=hashlib.sha256(image).hexdigest();return True
 except (RemoteFailure,ValueError) as error:
  STATE['screenshot_capture_error']=str(error) if isinstance(error,RemoteFailure) else type(error).__name__
  return False

def collect_guest_proof(client,digest):
 client.command('POST','/back',{});time.sleep(2)
 xml=client.source()
 if 'Kali desktop ready' not in '\n'.join(node_texts(xml)):raise RemoteFailure('ready_overlay_without_current_runtime_readiness')
 client.click_text('Advanced · manual disk & diagnostics');time.sleep(2)
 client.click_text('Startup diagnostics',scroll=True)
 end=time.monotonic()+20
 while time.monotonic()<end:
  xml=client.source()
  if has_guest_proof(xml,digest):
   capture(client,'guest-proof',xml);STATE['root_sudo_manifest_observed']=True
   client.click_text('Close');client.click_text('Open desktop',scroll=True);time.sleep(2)
   capture(client,'observed-desktop');return
  time.sleep(2)
 raise RemoteFailure('missing_real_root_sudo_manifest_proof')

def apply_control(client,last_sequence):
 git('fetch','origin',BRANCH)
 result=git('show','FETCH_HEAD:.ci/phone-control.json',check=False)
 if result.returncode:return last_sequence,False
 control=json.loads(result.stdout)
 if str(control.get('run_id'))!=RUN or str(control.get('run_attempt','1'))!=ATTEMPT or int(control.get('sequence',0))<=last_sequence:return last_sequence,False
 sequence=int(control['sequence']);actions=control.get('actions',[])
 if not isinstance(actions,list) or len(actions)>30:raise ValueError('Invalid bounded UI action list')
 try:
  for action in actions:
   kind=action.get('type')
   if kind in {'tap','double_tap'}:client.tap(int(action['x']),int(action['y']),kind=='double_tap')
   elif kind=='back':client.command('POST','/back',{})
   elif kind=='click_text':client.click_text(str(action['text']),bool(action.get('scroll')))
   elif kind=='type_text':client.type_text(str(action['text']))
   elif kind=='keycode':client.command('POST','/appium/device/press_keycode',{'keycode':int(action['keycode']),'metastate':int(action.get('metastate',0))})
   elif kind=='w3c_keys':
    client.command('POST','/actions',{'actions':[{'type':'key','id':'keyboard','actions':action['actions']}]})
    client.command('DELETE','/actions')
   elif kind=='activate_app':client.command('POST','/appium/device/activate_app',{'appId':'com.kp.kali'})
   elif kind=='snapshot':pass
   elif kind=='stop_observation':return sequence,True
   else:raise ValueError('Unsupported UI action')
   time.sleep(1)
 except RemoteFailure as error:
  STATE['last_control_sequence']=sequence;STATE['last_control_error']=str(error)
  capture(client,'control-error-'+str(sequence));return sequence,False
 capture(client,'control-'+str(sequence));STATE['last_control_sequence']=sequence
 return sequence,False

def main():
 client=None;exit_code=1
 try:
  publish()
  username=os.environ.get('BROWSERSTACK_USERNAME');key=os.environ.get('BROWSERSTACK_ACCESS_KEY')
  if not username or not key:raise RuntimeError('Missing GitHub BrowserStack secrets')
  apks=list((ROOT/'candidate').rglob('*.apk'))
  if len(apks)!=1:raise RuntimeError('Expected exactly one candidate APK')
  sha=hashlib.sha256(apks[0].read_bytes()).hexdigest();expected=os.environ.get('EXPECTED_APK_SHA256','')
  if sha!=expected:raise RuntimeError('Candidate SHA256 mismatch')
  STATE['uploaded_apk_sha256']=sha
  profile=json.loads((ROOT/'kali-android/engine/kali-app/src/main/assets/managed/profile.json').read_text());digest=profile['manifestDigest']
  client=Client(username,key)
  plan=client.api('/app-automate/plan.json')
  if str(plan.get('automate_plan','')).lower() not in {'free','trial','free trial','freetrial'}:raise RuntimeError('Free/trial plan not confirmed; no paid session authorized')
  if int(plan.get('parallel_sessions_running',0))>=int(plan.get('parallel_sessions_max_allowed',0)):raise RuntimeError('No available free-plan parallel session')
  STATE['status']='UPLOADING_CANDIDATE';publish()
  app=client.upload(apks[0]);STATE['status']='REQUESTING_ONE_DEVICE';publish()
  STATE['session_creation_attempted']=True;STATE['cleanup_state']='unknown_until_session_reconciled';publish()
  caps=client.start(app,RUN+'-'+ATTEMPT,STATE['device'],STATE['os_version']);STATE['session_started']=True;STATE['cleanup_state']='active_known_session';STATE['status']='OBSERVING_FIRST_SETUP'
  STATE['reported_platform']=caps.get('platformName');publish()
  try:
   info=client.command('POST','/execute/sync',{'script':'mobile: deviceInfo','args':[]})
   if isinstance(info,dict):STATE['device_info']={k:info[k] for k in ['model','manufacturer','apiVersion','platformVersion','cpuAbi','realDisplaySize','displayDensity'] if k in info}
  except RemoteFailure:STATE['device_info']='not_available_through_provider'
  minutes=int(os.environ.get('SESSION_MINUTES','45'))
  if not 1<=minutes<=48:raise RuntimeError('Observation duration must be within1..48minutes')
  STATE['observation_minutes_limit']=minutes
  deadline=time.monotonic()+minutes*60;last_capture=0;last_sequence=0;seen_boot_overlay=False;seen_app=False;outside_app=0
  while time.monotonic()<deadline:
   xml=client.source();texts=node_texts(xml);joined='\n'.join(texts)
   STATE['visible_packages']=sorted({n.attrib.get('package') for n in ET.fromstring(xml).iter() if n.attrib.get('package')})[:8]
   if ('permissioncontroller' in xml and 'KP Kali VM' in joined and 'notifications' in joined.lower()
       and any(t.casefold()=='allow' for t in texts)):
    client.click_text('Allow');STATE['notification_permission_dialog_handled']=True;continue
   if in_app(xml):seen_app=True;outside_app=0
   elif seen_app and not STATE['root_sudo_manifest_observed']:
    outside_app+=1
    if outside_app>=3:raise RemoteFailure('app_left_foreground_during_first_setup')
   phases=[t for t in texts if t.startswith(('Downloading layer','Kali:','Booting Kali','Preparing Kali'))]
   if phases:STATE['last_app_phase']=phases[-1]
   if 'Preparing your Kali desktop' in texts:seen_boot_overlay=True
   fatal=['Free at least 18 GiB','needs a phone with at least 4 GiB','Cannot start Kali engine:',
          'Required PC boot firmware missing:','Open diagnostics from Advanced.','isn’t responding','is not responding']
   from collections import Counter
   duplicate_setup_error=('KP / KALI DESKTOP' in texts and 'Retry / resume' in texts and 'Cancel download' not in texts
                          and any(text and count>=2 for text,count in Counter(texts).items()))
   if duplicate_setup_error or any(message in joined for message in fatal):
    capture(client,'app-error',xml);raise RemoteFailure('actual_app_resource_startup_or_guest_error')
   if seen_boot_overlay and 'Preparing your Kali desktop' not in texts and 'Limbo Emulator' in joined and not STATE['root_sudo_manifest_observed']:
    capture(client,'first-desktop',xml);collect_guest_proof(client,digest)
    STATE['status']='OBSERVED_READY_REQUIRES_VISUAL_TOOLS_AND_REOPEN_CHECKS';publish()
   if time.monotonic()-last_capture>60:
    capture(client,'latest',xml);publish();last_capture=time.monotonic()
   last_sequence,stop=apply_control(client,last_sequence)
   if stop:
    STATE['status']='OBSERVATION_STOPPED_REVIEW_REQUIRED';exit_code=0 if STATE['root_sudo_manifest_observed'] else 1;break
   time.sleep(15)
  else:
   STATE['status']='TIME_LIMIT_INCOMPLETE' if not STATE['root_sudo_manifest_observed'] else 'OBSERVED_READY_REVIEW_PENDING'
   capture(client,'time-limit');exit_code=1
 except Exception as error:
  STATE['status']='FAILED_OR_INCOMPLETE';STATE['reason']=str(error) if isinstance(error,(RemoteFailure,RuntimeError)) else type(error).__name__
  # Exception bodies from provider requests are never placed in reports.
  try:capture(client,'failure') if client and client.session else None
  except Exception:pass
 finally:
  if client and client.session:
   try:client.close();STATE['cleanup_confirmed']=True;STATE['cleanup_state']='delete_confirmed'
   except Exception:STATE['cleanup_confirmed']=False;STATE['cleanup_state']='delete_not_confirmed'
  elif STATE['session_creation_attempted']:
   STATE['cleanup_confirmed']=False;STATE['cleanup_state']='unknown_creation_result'
  else:STATE['cleanup_state']='not_required'
  publish()
  summary='Physical observation status: '+STATE['status']+'\nAPK release remains WITHHELD.\n'
  print(summary)
  if os.environ.get('GITHUB_STEP_SUMMARY'):
   with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write(summary)
 return exit_code
if __name__=='__main__':sys.exit(main())
