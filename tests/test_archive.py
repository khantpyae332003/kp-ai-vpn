import io,zipfile,unittest,sys,tempfile
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_catalog import CONF,KEY
try:
 from agents.archive import inspect_archive,read_member
except ImportError:
 inspect_archive=read_member=None
class ArchiveTests(unittest.TestCase):
 def archive(self,items):
  out=io.BytesIO()
  with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
   for name,text in items:z.writestr(name,text)
  return out.getvalue()
 def test_lists_only_safe_conf_names_without_keys(self):
  self.assertTrue(callable(inspect_archive),'archive adapter missing')
  raw=self.archive([('JP/client.conf',CONF),('../bad.conf',CONF),('readme.txt','hi')]);items=inspect_archive(raw,limit=20,slot=0)
  self.assertEqual([x['member'] for x in items],['JP/client.conf']);self.assertNotIn(KEY,str(items))
 def test_read_member_checks_archive_and_member_checksum(self):
  self.assertTrue(callable(inspect_archive),'archive adapter missing')
  raw=self.archive([('client.conf',CONF)]);item=inspect_archive(raw,limit=20,slot=0)[0]
  self.assertEqual(read_member(raw,item).decode(),CONF)
  item['member_sha256']='0'*64
  with self.assertRaises(ValueError):read_member(raw,item)
 def test_rotation_and_previously_working_names_are_bounded(self):
  self.assertTrue(callable(inspect_archive),'archive adapter missing')
  raw=self.archive([(f'{i:02}.conf',CONF) for i in range(30)])
  a=inspect_archive(raw,limit=10,slot=0,preferred=['29.conf']);b=inspect_archive(raw,limit=10,slot=1,preferred=['29.conf'])
  self.assertEqual(len(a),10);self.assertEqual(a[0]['member'],'29.conf');self.assertNotEqual([x['member'] for x in a],[x['member'] for x in b])
 def test_link_only_does_not_republish_shared_keys(self):
  from agents.core import build_catalog
  with tempfile.TemporaryDirectory() as d:
   c={'name':'client.conf','carrier':'other','plan':'standard','url':'https://raw.githubusercontent.com/owner/repo/'+'a'*40+'/bundle.zip','approved':True,'permission_url':'https://github.com/owner/repo','link_only':True,'member':'client.conf','source_id':'public-test'}
   r=build_catalog([c],[],Path(d),fetch=lambda _:CONF.encode(),probe=lambda _:True)
   self.assertEqual(len(r['files']),1);self.assertEqual(r['files'][0].get('download_kind'),'source_archive')
   self.assertEqual(list((Path(d)/'downloads').rglob('*.conf')),[]);self.assertNotIn(KEY,str(r))
 def test_zip_authorization_is_pinned_to_registry_repository_and_path(self):
  from agents.verifier import authorize
  source={'id':'zip','kind':'github_zip','enabled':True,'public_link_approved':True,'github_repository':'owner/repo','archive_path':'bundle.zip','allowed_hosts':['github.com','raw.githubusercontent.com'],'permission_url':'https://github.com/owner/repo','carrier':'other','plan':'standard'}
  candidate={'source_id':'zip','url':'https://raw.githubusercontent.com/owner/repo/'+('a'*40)+'/bundle.zip','commit_sha':'a'*40,'member':'US/a.conf','archive_sha256':'b'*64,'member_sha256':'c'*64,'carrier':'dtac','plan':'nopro','link_only':False}
  out=authorize([candidate],[source]);self.assertEqual(len(out),1);self.assertTrue(out[0]['link_only']);self.assertEqual(out[0]['carrier'],'other')
  self.assertEqual(authorize([{**candidate,'url':candidate['url'].replace('owner/repo','evil/repo')}],[source]),[])
  self.assertEqual(authorize([{**candidate,'member':'../a.conf'}],[source]),[])
  self.assertEqual(authorize([candidate],[{**source,'public_link_approved':False}]),[])
 def test_manifest_candidate_must_belong_to_independently_fetched_manifest(self):
  from agents.verifier import authorize
  from unittest.mock import patch
  import json
  s={'id':'manifest','enabled':True,'redistribution_approved':True,'manifest_url':'https://example.com/feed.json','permission_url':'https://example.com/license','allowed_hosts':['example.com'],'carrier':'other','plan':'standard'}
  c={'source_id':'manifest','url':'https://example.com/unlisted-private.conf'}
  with patch('agents.verifier.fetch_url',return_value=json.dumps({'files':[{'url':'https://example.com/public.conf'}]}).encode()):
   self.assertEqual(authorize([c],[s]),[])
if __name__=='__main__':unittest.main()
