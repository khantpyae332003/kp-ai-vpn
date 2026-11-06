"""Honest, isolated terminal evidence for Android verification runs."""
from pathlib import Path
import datetime,json,re,uuid
class RunEvidence:
 def __init__(self,root,expected_hash,observation_only):
  if not re.fullmatch('[0-9a-f]{64}',expected_hash):raise ValueError('Invalid expected APK digest')
  self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.expected=expected_hash;self.observation_only=observation_only
  stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
  legacy=[self.root/name for name in ['result.txt','actual-android-kali-desktop.png'] if (self.root/name).exists()]
  if legacy:
   archive=self.root/('legacy-'+stamp);archive.mkdir()
   for p in legacy:p.rename(archive/p.name)
  self.directory=self.root/('run-'+stamp);self.directory.mkdir();self.status='RUNNING';self._write('RUNNING')
  stage=self.root/('current-'+uuid.uuid4().hex+'.tmp');stage.write_text(json.dumps({'directory':self.directory.name})+'\n');stage.replace(self.root/'CURRENT.json')
 def _write(self,status,**extra):
  self.status=status
  data={'status':status,'mode':'observation' if self.observation_only else 'cold','expected_apk_sha256':self.expected,**extra}
  p=self.directory/'status.json';stage=p.with_suffix('.tmp');stage.write_text(json.dumps(data,indent=2)+'\n');stage.replace(p)
 def fail(self,reason):
  (self.directory/'result.txt').write_text('FAIL: '+str(reason)+'\n');self._write('FAIL',reason=str(reason))
 def interrupt(self):
  (self.directory/'result.txt').write_text('INTERRUPTED: observer stopped; no success claim.\n');self._write('INTERRUPTED')
 def complete(self,actual_hash,live):
  if actual_hash!=self.expected or live is not True:
   reason='Installed APK differs from selected artifact' if actual_hash!=self.expected else 'No live guest confirmed'
   self.fail(reason);raise ValueError(reason)
  if self.observation_only:
   text='OBSERVED_READY: installed APK matches, live QMP is running and stored guest readiness was observed; this does not establish a cold setup.\n';status='OBSERVED_READY'
  else:
   text='PASS: controlled cold setup reached guest-confirmed desktop with root/sudo proof and a live QMP guest. Physical ARM64 phones remain untested.\n';status='PASS'
  (self.directory/'result.txt').write_text(text);self._write(status,installed_apk_sha256=actual_hash,live_qmp=True)
