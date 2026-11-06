import json,subprocess,sys,tempfile,unittest
from pathlib import Path

SHA='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
class RestoreTests(unittest.TestCase):
 def fixture(self,root):
  asset=root/'engine/kali-app/src/main/assets/managed';asset.mkdir(parents=True)
  (asset/'profile.json').write_text(json.dumps({'initrdSha256':SHA}))
  parts=root/'ci-payload';parts.mkdir();(parts/'part-000').write_bytes(b'a');(parts/'part-001').write_bytes(b'bc')
  (parts/'manifest.json').write_text(json.dumps({'parts':['part-000','part-001'],'size':3,'sha256':SHA}))
  return asset/'initrd.bin'
 def run_restore(self,root):
  return subprocess.run([sys.executable,str(Path(__file__).with_name('restore_payload.py')),str(root)],capture_output=True)
 def test_valid_parts_restore_the_exact_boot_payload(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);out=self.fixture(root);r=self.run_restore(root)
   self.assertEqual(r.returncode,0,r.stderr.decode());self.assertEqual(out.read_bytes(),b'abc')
 def test_corruption_is_rejected_without_replacing_a_previous_payload(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);out=self.fixture(root);out.write_bytes(b'previous verified payload')
   (root/'ci-payload/part-001').write_bytes(b'bd');r=self.run_restore(root)
   self.assertNotEqual(r.returncode,0);self.assertEqual(out.read_bytes(),b'previous verified payload')
 def test_missing_parts_are_rejected_without_replacing_a_previous_payload(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);out=self.fixture(root);out.write_bytes(b'previous verified payload')
   (root/'ci-payload/part-001').unlink();r=self.run_restore(root)
   self.assertNotEqual(r.returncode,0);self.assertEqual(out.read_bytes(),b'previous verified payload')
if __name__=='__main__':unittest.main()
