import importlib.util,json,os,subprocess,tempfile,unittest
from pathlib import Path

class PublicationTests(unittest.TestCase):
 def test_rejected_progress_push_preserves_observation_and_can_recover(self):
  os.environ.setdefault('GITHUB_RUN_ID','12345')
  spec=importlib.util.spec_from_file_location('observer',Path(__file__).with_name('observe_phone.py'))
  observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);remote=root/'remote.git';work=root/'work'
   def run(*args,cwd=None):return subprocess.run(['git',*args],cwd=cwd,check=True,capture_output=True,text=True)
   run('init','--bare',str(remote));run('clone',str(remote),str(work))
   run('config','user.name','Fixture',cwd=work);run('config','user.email','fixture@example.invalid',cwd=work)
   run('checkout','-b',observer.BRANCH,cwd=work)
   (work/'README').write_text('fixture');run('add','README',cwd=work);run('commit','-m','fixture',cwd=work)
   run('push','origin','HEAD',cwd=work)
   hook=remote/'hooks/pre-receive';hook.write_text('#!/bin/sh\nexit 1\n');hook.chmod(0o755)
   observer.ROOT=work;observer.OUT=work/'.ci/observation';observer.OUT.mkdir(parents=True)
   observer.STATE={'status':'OBSERVING_FIRST_SETUP','apk_release':'WITHHELD'}
   old=os.environ.get('PUBLISH_PHONE_PROGRESS');os.environ['PUBLISH_PHONE_PROGRESS']='1'
   try:
    try:observer.publish()
    except Exception as error:self.fail('Progress transport aborted observation: '+type(error).__name__)
    saved=json.loads((observer.OUT/'status.json').read_text())
    self.assertEqual(saved['status'],'OBSERVING_FIRST_SETUP')
    self.assertIn('progress_publication_error',saved)
    self.assertEqual(saved['apk_release'],'WITHHELD')
    hook.unlink();observer.publish()
    pushed=json.loads(run('--git-dir='+str(remote),'show',observer.BRANCH+':.ci/observation/status.json').stdout)
    self.assertEqual(pushed['status'],'OBSERVING_FIRST_SETUP')
    self.assertNotIn('progress_publication_error',pushed)
   finally:
    if old is None:os.environ.pop('PUBLISH_PHONE_PROGRESS',None)
    else:os.environ['PUBLISH_PHONE_PROGRESS']=old
