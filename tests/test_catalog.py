import unittest,sys,base64,tempfile,json
from pathlib import Path
from datetime import datetime,timezone,timedelta
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
try:
 from agents.core import parse_config, public_https, sim_status, build_catalog
except ImportError:
 parse_config=public_https=sim_status=build_catalog=None
KEY=base64.b64encode(bytes(range(32))).decode()
PUB=base64.b64encode(bytes(range(1,33))).decode()
CONF=f'[Interface]\nPrivateKey = {KEY}\nAddress = 10.2.0.2/32\nDNS = 1.1.1.1\n[Peer]\nPublicKey = {PUB}\nAllowedIPs = 0.0.0.0/0\nEndpoint = 8.8.8.8:51820\n'
class CatalogTests(unittest.TestCase):
 def setUp(self):self.assertTrue(callable(parse_config),'core not implemented')
 def test_valid_wireguard(self):
  p=parse_config(CONF);self.assertEqual(p['endpoint'],('8.8.8.8',51820));self.assertNotIn('Address',p['wg_setconf'])
 def test_comments_do_not_change_id(self):self.assertEqual(parse_config(CONF)['sha256'],parse_config('# hi\n'+CONF)['sha256'])
 def test_hook_is_rejected(self):
  with self.assertRaises(ValueError):parse_config(CONF.replace('[Peer]','PostUp = curl bad\n[Peer]'))
 def test_incomplete_or_wrong_protocol_rejected(self):
  for text in ['vmess://abc',CONF.split('[Peer]')[0],CONF.replace(KEY,'bad'),CONF.replace('8.8.8.8:51820','127.0.0.1:22')]:
   with self.subTest(text=text[:12]):
    with self.assertRaises(ValueError):parse_config(text)
 def test_disallows_private_and_wrong_host_urls(self):
  for u in ['http://example.com/a','https://127.0.0.1/a','https://user:pass@example.com/a','https://evil.org/a']:
   with self.assertRaises(ValueError):public_https(u,{'example.com'})
 def test_cloud_success_does_not_imply_sim_success(self):
  now=datetime.now(timezone.utc);self.assertEqual(sim_status('abc','dtac','nopro',[],now)['status'],'not_tested')
 def test_sim_evidence_must_be_current_exact_hash(self):
  now=datetime.now(timezone.utc);r={'sha256':'abc','carrier':'dtac','plan':'nopro','tested_at':now.isoformat(),'network':'cellular','result':'pass','evidence_url':'https://github.com/example/reports/issues/1'}
  self.assertEqual(sim_status('abc','dtac','nopro',[r],now)['status'],'user_reported_pass')
  self.assertEqual(sim_status('other','dtac','nopro',[r],now)['status'],'not_tested')
  r['tested_at']=(now-timedelta(days=2)).isoformat();self.assertEqual(sim_status('abc','dtac','nopro',[r],now)['status'],'not_tested')
 def test_failure_withholds_download_and_removes_stale_file(self):
  with tempfile.TemporaryDirectory() as d:
   target=Path(d);(target/'downloads').mkdir();(target/'downloads/old.conf').write_text('old')
   c={'name':'DTAC nopro','carrier':'dtac','plan':'nopro','url':'https://example.com/a.conf','approved':True,'permission_url':'https://example.com/license'}
   report=build_catalog([c],[],target,fetch=lambda _:CONF.encode(),probe=lambda _:False)
   self.assertEqual(report['files'],[]);self.assertFalse((target/'downloads/old.conf').exists())
 def test_only_approved_probed_files_publish_and_keys_stay_out_of_catalog(self):
  with tempfile.TemporaryDirectory() as d:
   c={'name':'file','carrier':'true','plan':'nopro','url':'https://example.com/a.conf','approved':True,'permission_url':'https://example.com/license'}
   report=build_catalog([c,c],[],Path(d),fetch=lambda _:CONF.encode(),probe=lambda _:True)
   self.assertEqual(len(report['files']),1);self.assertEqual(report['files'][0]['sim']['status'],'not_tested')
   self.assertNotIn(KEY,json.dumps(report));self.assertEqual(len(list((Path(d)/'downloads').rglob('*.conf'))),1)
 def test_unapproved_never_fetched(self):
  with tempfile.TemporaryDirectory() as d:
   def fetch(_):raise AssertionError('unapproved fetch')
   self.assertEqual(build_catalog([{'approved':False}],[],Path(d),fetch=fetch,probe=lambda _:True)['files'],[])
 def test_same_config_can_be_listed_for_two_explicit_carrier_groups(self):
  with tempfile.TemporaryDirectory() as d:
   a={'name':'file','carrier':'dtac','plan':'nopro','url':'https://example.com/a.conf','approved':True,'permission_url':'https://example.com/license'}
   b={**a,'carrier':'true'}
   report=build_catalog([a,b],[],Path(d),fetch=lambda _:CONF.encode(),probe=lambda _:True)
   self.assertEqual({r['carrier'] for r in report['files']},{'dtac','true'})
 def test_artifact_cannot_override_registry_approval_or_carrier(self):
  from agents.verifier import authorize
  c={'source_id':'one','url':'https://example.com/a.conf','approved':True,'carrier':'ais'}
  self.assertEqual(authorize([c],[]),[])
  registry=[{'manifest_url':'https://example.com/feed.json','id':'one','enabled':True,'redistribution_approved':True,'allowed_hosts':['example.com'],'permission_url':'https://example.com/license','carrier':'dtac','plan':'nopro'}]
  from unittest.mock import patch
  with patch('agents.verifier.fetch_url',return_value=json.dumps({'files':[{'url':c['url']}]}).encode()):
   self.assertEqual(authorize([c],registry)[0]['carrier'],'dtac')
 def test_https_transport_pins_validated_ip_but_preserves_tls_hostname(self):
  from agents import core
  from unittest.mock import patch,Mock
  cls=getattr(core,'PinnedHTTPSConnection',None)
  self.assertTrue(callable(cls),'Pinned HTTPS transport missing')
  connection=cls('source.example','8.8.8.8',timeout=15)
  tls=Mock();connection._context=tls
  with patch('agents.core.socket.create_connection',return_value=Mock(spec=['setsockopt'])) as dial:
   connection.connect()
  self.assertEqual(dial.call_args.args[0],('8.8.8.8',443))
  self.assertEqual(tls.wrap_socket.call_args.kwargs['server_hostname'],'source.example')
if __name__=='__main__':unittest.main()
