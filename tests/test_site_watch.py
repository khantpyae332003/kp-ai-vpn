import json,unittest
from datetime import datetime,timezone
from unittest.mock import patch
from agents.site_watch import check

class PublicMonitorTests(unittest.TestCase):
 def run_integrity(self,post_date):
  data={'':'<title>KP VPN</title>','catalog/index.json':json.dumps({'files':[]}),
        'catalog/agents.json':json.dumps({'roles':[{'id':i} for i in ['finder','verifier','classifier','publisher','daily','health','security','integrity']]}),
        'catalog/daily.json':json.dumps({'date':post_date,'title':'A lesson','body':['Explanation']})}
  with patch('agents.site_watch.fetch',side_effect=lambda p:data[p]),patch('agents.site_watch.now_utc',return_value=datetime(2026,11,7,12,tzinfo=timezone.utc)):
   check('integrity')
 def test_stale_daily_post_is_reported(self):
  with self.assertRaisesRegex(ValueError,'stale'):self.run_integrity('2026-11-06')
 def test_current_bangkok_daily_post_is_accepted(self):self.run_integrity('2026-11-07')
if __name__=='__main__':unittest.main()
