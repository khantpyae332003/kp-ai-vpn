import subprocess,sys,tempfile,unittest
from pathlib import Path
from adb_transport import execute

PROGRAM="""import pathlib,sys,time
p=pathlib.Path(sys.argv[1]);n=int(p.read_text())+1 if p.exists() else 1;p.write_text(str(n))
if n<3:time.sleep(2)
print('fresh complete response')
"""
class TransportTests(unittest.TestCase):
 def test_transient_read_timeouts_eventually_return_one_complete_fresh_response(self):
  with tempfile.TemporaryDirectory() as d:
   counter=Path(d)/'calls';notices=[]
   try:r=execute([sys.executable,'-c',PROGRAM,str(counter)],timeout=.75,read_only=True,on_retry=notices.append)
   except subprocess.TimeoutExpired:self.fail('Read-only observation stopped at its first transient timeout')
   self.assertEqual(r.stdout,b'fresh complete response\n')
   self.assertEqual(counter.read_text(),'3');self.assertEqual(len(notices),2)
 def test_mutating_commands_are_never_automatically_repeated_after_timeout(self):
  with tempfile.TemporaryDirectory() as d:
   counter=Path(d)/'calls'
   with self.assertRaises(subprocess.TimeoutExpired):execute([sys.executable,'-c',PROGRAM,str(counter)],timeout=.75)
   self.assertEqual(counter.read_text(),'1')
if __name__=='__main__':unittest.main()
