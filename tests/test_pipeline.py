import json,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
from agents.pipeline import classify,daily,audit,run

NOW=datetime(2026,11,7,18,0,tzinfo=timezone.utc)
ROOT=Path(__file__).resolve().parents[1]
class PipelineTests(unittest.TestCase):
 def test_classifier_uses_registry_not_claimed_country(self):
  registry=[{'id':'a','enabled':True,'carrier':'other','plan':'standard'}]
  row={'source_id':'a','id':'hash','carrier':'dtac','country':'TH','plan':'nopro'}
  result=classify([row],registry,[],NOW)[0]
  self.assertEqual((result['carrier'],result['country'],result['plan']),('other','GLOBAL','standard'))
  self.assertEqual(result['sim']['status'],'not_tested')
  self.assertEqual(classify([row],[],[],NOW),[])
 def test_reports_require_same_hash_and_cellular(self):
  registry=[{'id':'a','enabled':True,'carrier':'ais','plan':'standard'}]
  row={'source_id':'a','id':'exact'}
  report={'sha256':'wrong','carrier':'ais','plan':'standard','network':'cellular','result':'pass','tested_at':NOW.isoformat(),'evidence_url':'https://github.com/a/b/issues/1'}
  self.assertEqual(classify([row],registry,[report],NOW)[0]['sim']['status'],'not_tested')
  report['sha256']='exact';report['network']='wifi'
  self.assertEqual(classify([row],registry,[report],NOW)[0]['sim']['status'],'not_tested')
  report['network']='cellular'
  self.assertEqual(classify([row],registry,[report],NOW)[0]['sim']['status'],'user_reported_pass')
 def test_daily_bangkok_idempotent_and_exhaustion(self):
  bank=[{'id':'one','title':'One','body':['First lesson'],'source_url':'https://www.wireguard.com/quickstart/'}]
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)
   self.assertEqual(daily(out,bank,NOW)[0],'pass')
   first=json.loads((out/'daily.json').read_text());self.assertEqual(first['date'],'2026-11-08')
   daily(out,bank,NOW);self.assertEqual(len(json.loads((out/'daily-history.json').read_text())['posts']),1)
   self.assertEqual(daily(out,bank,NOW+timedelta(days=1))[0],'warning')
   self.assertEqual(json.loads((out/'daily.json').read_text()),first)
 def test_bank_has_at_least_thirty_distinct_lessons(self):
  bank=json.loads((ROOT/'data/daily-bank.json').read_text())
  self.assertGreaterEqual(len(bank),30)
  self.assertEqual(len({x['id'] for x in bank}),len(bank))
  self.assertEqual(len({tuple(x['body']) for x in bank}),len(bank))
 def test_security_withholds_bad_links_and_cleans_downloads(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);(out/'downloads').mkdir();(out/'downloads/secret.conf').write_text('credential')
   rows,issues=audit([{'source_id':'unknown','download':'https://evil.example/a'}],out,[],NOW)
   self.assertEqual(rows,[]);self.assertTrue(issues);self.assertEqual(list((out/'downloads').iterdir()),[])
 def test_integrity_rejects_stale_unpinned_and_duplicate_rows(self):
  registry=json.loads((ROOT/'data/sources.json').read_text())['sources'];source=registry[0];commit='a'*40
  url='https://raw.githubusercontent.com/'+source['github_repository']+'/'+commit+'/'+source['archive_path']
  row={'id':'b'*64,'source_id':source['id'],'source_commit':commit,'download_kind':'source_archive','download':url,'source_url':url,'permission_url':source['permission_url'],'server_status':'handshake_https_pass','checked_at':NOW.isoformat(),'expires_at':(NOW+timedelta(hours=1)).isoformat()}
  with tempfile.TemporaryDirectory() as d:
   valid,issues=audit([row,row],Path(d),registry,NOW)
   self.assertEqual(len(valid),1);self.assertTrue(issues)
   for bad in ({**row,'download':url.replace(commit,'main')},{**row,'expires_at':NOW.isoformat()},{**row,'private_config':'secret'}):
    self.assertEqual(audit([bad],Path(d),registry,NOW)[0],[])
 def test_eight_roles_are_honest_without_credentials(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);report=run(out,ROOT/'data',NOW)
   self.assertEqual({x['id'] for x in report['roles']},{'finder','verifier','classifier','publisher','daily','health','security','integrity'})
   self.assertEqual(report['ai'],{'configured':False,'mode':'deterministic'})
   self.assertEqual(next(x for x in report['roles'] if x['id']=='verifier')['status'],'warning')
if __name__=='__main__':unittest.main()
