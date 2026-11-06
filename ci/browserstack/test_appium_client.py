import unittest,json,threading
from http.server import BaseHTTPRequestHandler,HTTPServer
from appium_client import Client,RemoteFailure,decode_value,has_guest_proof

class ProtocolTests(unittest.TestCase):
 def test_success_value_is_returned(self):
  self.assertEqual(decode_value({'value':{'sessionId':'test-session'}}),{'sessionId':'test-session'})
 def test_w3c_error_cannot_be_treated_as_a_success_or_leak_response_message(self):
  with self.assertRaises(RemoteFailure) as found:
   decode_value({'value':{'error':'session not created','message':'DO_NOT_LOG_ACCOUNT_SECRET'}})
  self.assertNotIn('DO_NOT_LOG_ACCOUNT_SECRET',str(found.exception))
 def test_malformed_response_is_rejected(self):
  with self.assertRaises(RemoteFailure):decode_value({'unexpected':'response'})
 def test_guest_proof_requires_all_exact_separate_lines_and_correct_manifest(self):
  digest='sha256:'+'a'*64
  xml='<hierarchy><node text="KP:ROOT_UID:0&#10;KP:SUDO_UID:0&#10;KP:DESKTOP_READY:'+digest+'"/></hierarchy>'
  self.assertTrue(has_guest_proof(xml,digest))
  self.assertTrue(has_guest_proof(xml.replace('<node ', '<android.widget.TextView '),digest))
  self.assertFalse(has_guest_proof(xml,'sha256:'+'b'*64))
  self.assertFalse(has_guest_proof(xml.replace('KP:SUDO_UID:0','prefixed KP:SUDO_UID:0'),digest))
  self.assertFalse(has_guest_proof(xml.replace('KP:ROOT_UID:0','KP:ROOT_UID:1000'),digest))
 def test_redirects_are_rejected_before_credentials_can_be_forwarded(self):
  paths=[]
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_GET(self):
    paths.append(self.path)
    if self.path=='/start':
     self.send_response(302);self.send_header('Location','/must-not-be-requested');self.end_headers()
    else:
     body=b'{"value":"unexpected redirected response"}';self.send_response(200);self.end_headers();self.wfile.write(body)
  server=HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   with self.assertRaises(RemoteFailure):Client('fixture-user','NOT_A_REAL_KEY').request('GET','http://127.0.0.1:'+str(server.server_port)+'/start')
   self.assertEqual(paths,['/start'])
  finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':unittest.main()
