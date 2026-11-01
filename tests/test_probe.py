import unittest,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from agents import probe
class ProbeTargetTests(unittest.TestCase):
 def test_https_targets_use_current_public_dns_not_a_stale_fixed_ip(self):
  fn=getattr(probe,'https_targets',None);self.assertTrue(callable(fn),'DNS-based HTTPS targets missing')
  with patch('agents.probe.socket.getaddrinfo',return_value=[(2,1,6,'',('9.9.9.9',443))]):
   targets=fn()
  self.assertEqual(len(targets),2);self.assertTrue(all(x[1]=='9.9.9.9' for x in targets))
 def test_https_targets_cannot_resolve_to_private_networks(self):
  fn=getattr(probe,'https_targets',None);self.assertTrue(callable(fn),'DNS-based HTTPS targets missing')
  with patch('agents.probe.socket.getaddrinfo',return_value=[(2,1,6,'',('10.0.0.1',443))]):self.assertEqual(fn(),[])
if __name__=='__main__':unittest.main()
