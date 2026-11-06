import json,tempfile,unittest,subprocess,sys,shutil
from pathlib import Path
from run_evidence import RunEvidence
H='a'*64
class EvidenceTests(unittest.TestCase):
 def test_previous_success_is_not_current_after_a_failed_new_run(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);old=RunEvidence(root,H,False);old.complete(H,True)
   new=RunEvidence(root,H,False);new.fail('fixture failed')
   pointer=json.loads((root/'CURRENT.json').read_text())
   self.assertEqual(pointer['directory'],new.directory.name)
   self.assertEqual(json.loads((new.directory/'status.json').read_text())['status'],'FAIL')
   self.assertNotEqual(old.directory,new.directory)
 def test_observer_never_claims_a_cold_setup_pass(self):
  with tempfile.TemporaryDirectory() as d:
   r=RunEvidence(Path(d),H,True);r.complete(H,True)
   self.assertEqual(json.loads((r.directory/'status.json').read_text())['status'],'OBSERVED_READY')
   self.assertIn('does not establish a cold setup',(r.directory/'result.txt').read_text())
 def test_different_installed_apk_cannot_publish_success(self):
  with tempfile.TemporaryDirectory() as d:
   r=RunEvidence(Path(d),H,False)
   with self.assertRaises(ValueError):r.complete('b'*64,True)
   self.assertEqual(json.loads((r.directory/'status.json').read_text())['status'],'FAIL')
 def test_stopped_guest_cannot_publish_success(self):
  with tempfile.TemporaryDirectory() as d:
   r=RunEvidence(Path(d),H,False)
   with self.assertRaises(ValueError):r.complete(H,False)
   self.assertFalse((r.directory/'result.txt').read_text().startswith('PASS'))
 def test_legacy_success_is_archived_not_reused(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'result.txt').write_text('PASS old run');(root/'actual-android-kali-desktop.png').write_bytes(b'old')
   r=RunEvidence(root,H,False)
   self.assertFalse((root/'result.txt').exists())
   self.assertFalse((r.directory/'actual-android-kali-desktop.png').exists())
   self.assertEqual(json.loads((r.directory/'status.json').read_text())['status'],'RUNNING')
 def test_missing_apk_replaces_a_published_old_success_with_failure(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);scripts=root/'tests/android';scripts.mkdir(parents=True)
   for name in ['run-managed-setup.py','run_evidence.py','adb_transport.py']:
    shutil.copyfile(Path(__file__).with_name(name),scripts/name)
   reports=root/'artifacts';reports.mkdir();report=reports/'status.json'
   report.write_text(json.dumps({'status':'OBSERVED_READY','expected_apk_sha256':H}))
   result=subprocess.run([sys.executable,str(scripts/'run-managed-setup.py'),'--watch-only','--apk','missing.apk','--status-file','artifacts/status.json'],capture_output=True,timeout=10)
   self.assertNotEqual(result.returncode,0)
   self.assertEqual(json.loads(report.read_text())['status'],'FAIL')
if __name__=='__main__':unittest.main()
