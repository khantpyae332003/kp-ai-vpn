import json,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
from agents.ai_review import IDS,AIError,context,validate,run,request_ai

def answer():return {'reviews':[{'id':i,'summary':'စစ်ဆေးမှုအထောက်အထားကို ပြန်ကြည့်ပါ။'} for i in IDS], 'lesson':{'title':'Key ကို ကာကွယ်ပါ','body':['ကိုယ်ပိုင်ဖိုင်ကို လုံခြုံစွာ သိမ်းပါ။']}}
class AIReviewTests(unittest.TestCase):
 def setup_dir(self,path):
  (path/'agents.json').write_text(json.dumps({'roles':[{'id':i,'status':'pass','private':'NEVER_SEND'} for i in IDS]}))
  (path/'daily.json').write_text(json.dumps({'date':'2026-11-08','title':'A lesson','body':['Fact'],'source_url':'https://www.wireguard.com/','mode':'curated'}))
 def test_metadata_allowlist_excludes_arbitrary_fields(self):
  value=context({'roles':[{'id':'finder','status':'pass','private':'NEVER_SEND'}]}, {'title':'Lesson','body':['Fact'],'private':'NEVER_SEND'})
  self.assertNotIn('NEVER_SEND',json.dumps(value))
 def test_invalid_model_output_cannot_publish_secrets_html_or_change_roles(self):
  for field in ['PrivateKey = secret','<script>bad</script>','https://evil.invalid/']:
   value=answer();value['lesson']['body']=[field]
   with self.assertRaises(AIError):validate(value)
  value=answer();value['reviews'][0]['id']='not-a-role'
  with self.assertRaises(AIError):validate(value)
 def test_success_is_cached_and_does_not_change_verification_status(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self.setup_dir(p);calls=[]
   def invoke(payload,key,model):calls.append(payload);return answer()
   now=datetime(2026,11,8,3,tzinfo=timezone.utc)
   self.assertTrue(run(p,key='test',now=now,call=invoke)['configured'])
   self.assertTrue(run(p,key='test',now=now,call=invoke)['configured'])
   self.assertEqual(len(calls),1)
   report=json.loads((p/'agents.json').read_text());self.assertTrue(all(r['status']=='pass' for r in report['roles']))
   daily=json.loads((p/'daily.json').read_text());self.assertEqual(daily['source_url'],'https://www.wireguard.com/')
 def test_missing_secret_does_not_call_api(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self.setup_dir(p)
   self.assertEqual(run(p,key='',call=lambda *a:self.fail('API called'))['status'],'missing_secret')
 def test_same_day_lesson_correction_invalidates_cached_rewrite(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self.setup_dir(p);calls=[];now=datetime(2026,11,8,3,tzinfo=timezone.utc)
   def invoke(*a):calls.append(1);return answer()
   run(p,key='test',now=now,call=invoke)
   lesson=json.loads((p/'daily.json').read_text());lesson.update(title='Corrected lesson',body=['New facts'],source_url='https://protonvpn.com/')
   (p/'daily.json').write_text(json.dumps(lesson));run(p,key='test',now=now,call=invoke)
   self.assertEqual(len(calls),2)
 def test_invalid_api_content_does_not_enable_ai_or_overwrite_the_daily_post(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self.setup_dir(p);original=(p/'daily.json').read_text()
   value=answer();value['lesson']['body']=['PrivateKey = secret']
   self.assertFalse(run(p,key='test',call=lambda *a:value)['configured'])
   self.assertEqual((p/'daily.json').read_text(),original)
 def test_secret_is_authorization_only_and_destination_is_fixed(self):
  import io
  class Response(io.BytesIO):
   def __enter__(self):return self
   def __exit__(self,*args):self.close()
  def fake(req,timeout):
   self.assertEqual(req.full_url,'https://api.openai.com/v1/responses')
   self.assertEqual(req.get_header('Authorization'),'Bearer PRIVATE_TEST_KEY')
   self.assertNotIn('PRIVATE_TEST_KEY',req.data.decode())
   body=json.loads(req.data);self.assertFalse(body['store']);self.assertEqual(body['max_output_tokens'],2400)
   return Response(json.dumps({'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(answer())}]}]}).encode())
  with patch('agents.ai_review.urlopen',side_effect=fake):request_ai({'roles':[]},'PRIVATE_TEST_KEY','gpt-4.1-mini')
 def test_errors_never_publish_exception_details_and_have_cooldown(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self.setup_dir(p);now=datetime(2026,11,8,3,tzinfo=timezone.utc);calls=[]
   def fail(*a):calls.append(1);raise AIError('authentication_failed')
   self.assertFalse(run(p,key='test',now=now,call=fail)['configured']);run(p,key='test',now=now,call=fail)
   self.assertEqual(len(calls),1);self.assertNotIn('test', (p/'ai-review.json').read_text())
if __name__=='__main__':unittest.main()
