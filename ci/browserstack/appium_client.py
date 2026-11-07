"""Small W3C Appium client. Provider errors never expose credential-bearing bodies."""
import base64,json,re,urllib.error,urllib.request,uuid,xml.etree.ElementTree as ET
from pathlib import Path

class RemoteFailure(Exception):pass

class RejectRedirects(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):raise RemoteFailure('unexpected_remote_redirect')

def decode_value(payload):
 if not isinstance(payload,dict) or 'value' not in payload:raise RemoteFailure('malformed_remote_response')
 value=payload['value']
 if isinstance(value,dict) and value.get('error'):
  known={'session not created','invalid session id','no such element','unknown error','invalid argument','unsupported operation','timeout'}
  code=value['error'] if isinstance(value['error'],str) and value['error'] in known else 'remote_error'
  raise RemoteFailure(code)
 return value

def has_guest_proof(xml,digest):
 tree=ET.fromstring(xml);lines=set()
 for node in tree.iter():lines.update(line.strip() for line in node.attrib.get('text','').splitlines())
 return all(line in lines for line in ['KP:ROOT_UID:0','KP:SUDO_UID:0','KP:DESKTOP_READY:'+digest])

class Client:
 def __init__(self,username,key):
  self.authorization='Basic '+base64.b64encode((username+':'+key).encode()).decode();self.session=None
  self.opener=urllib.request.build_opener(RejectRedirects())
 def request(self,method,url,body=None,raw=None,content_type=None):
  data=raw if raw is not None else json.dumps(body).encode() if body is not None else None
  headers={'Authorization':self.authorization,'Accept':'application/json'}
  if data is not None:headers['Content-Type']=content_type or 'application/json'
  request=urllib.request.Request(url,data=data,headers=headers,method=method)
  try:
   with self.opener.open(request,timeout=60) as response:
    raw_response=response.read()
   return json.loads(raw_response) if raw_response else {'value':None}
  except urllib.error.HTTPError as error:
   body=error.read(65536).decode(errors='replace')
   codes=sorted(set(re.findall(r'BROWSERSTACK_[A-Z0-9_]{3,80}',body))-{'BROWSERSTACK_USERNAME','BROWSERSTACK_ACCESS_KEY'})
   raise RemoteFailure('HTTP_'+str(error.code)+(' '+','.join(codes) if codes else '')) from None
  except (urllib.error.URLError,TimeoutError,OSError):raise RemoteFailure('network_request_failed') from None
  except ValueError:raise RemoteFailure('invalid_json_response') from None
 def api(self,path):return self.request('GET','https://api-cloud.browserstack.com'+path)
 def upload(self,apk):
  boundary='kp-kali-'+uuid.uuid4().hex
  head=('--'+boundary+'\r\nContent-Disposition: form-data; name="file"; filename="kali-candidate.apk"\r\nContent-Type: application/vnd.android.package-archive\r\n\r\n').encode()
  data=head+Path(apk).read_bytes()+('\r\n--'+boundary+'--\r\n').encode()
  result=self.request('POST','https://api-cloud.browserstack.com/app-automate/upload',raw=data,content_type='multipart/form-data; boundary='+boundary)
  url=result.get('app_url') if isinstance(result,dict) else None
  if not isinstance(url,str) or not url.startswith('bs://'):raise RemoteFailure('app_upload_not_confirmed')
  return url
 def start(self,app_url,run,device="Samsung Galaxy S23 Ultra",os_version="13.0"):
  caps={'platformName':'Android','appium:automationName':'UiAutomator2','appium:deviceName':device,
        'appium:platformVersion':os_version,'appium:app':app_url,'appium:appPackage':'com.kp.kali',
        'appium:appActivity':'com.kp.kali.BootstrapActivity','appium:autoGrantPermissions':True,'appium:noReset':False,'appium:fullReset':True,
        'bstack:options':{'projectName':'KP Kali Rootless VM','buildName':'GitHub '+run,'sessionName':'Real first setup and readiness',
                         'idleTimeout':120,'networkLogs':False,'video':True}}
  result=decode_value(self.request('POST','https://hub-cloud.browserstack.com/wd/hub/session',{'capabilities':{'alwaysMatch':caps}}))
  if not isinstance(result,dict) or not result.get('sessionId'):raise RemoteFailure('session_creation_not_confirmed')
  self.session=result['sessionId']
  capabilities=result.get('capabilities',{})
  if not isinstance(capabilities,dict):raise RemoteFailure('invalid_capabilities_response')
  return capabilities
 def command(self,method,path,body=None):
  if not self.session:raise RemoteFailure('no_session')
  return decode_value(self.request(method,'https://hub-cloud.browserstack.com/wd/hub/session/'+self.session+path,body))
 def source(self):
  value=self.command('GET','/source')
  if not isinstance(value,str):raise RemoteFailure('invalid_source_response')
  ET.fromstring(value);return value
 def screenshot(self):
  encoded=self.command('GET','/screenshot')
  if not isinstance(encoded,str):raise RemoteFailure('invalid_screenshot_value')
  if encoded.startswith('data:image/png;base64,'):encoded=encoded[len('data:image/png;base64,'):]
  encoded=''.join(encoded.split())
  try:data=base64.b64decode(encoded,validate=True)
  except ValueError:raise RemoteFailure('invalid_screenshot_encoding') from None
  if not data.startswith(b'\x89PNG\r\n\x1a\n'):raise RemoteFailure('invalid_screenshot_response')
  return data
 def click_text(self,text,scroll=False):
  selector='new UiSelector().text('+json.dumps(text,ensure_ascii=False)+')'
  if scroll:selector='new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView('+selector+')'
  element=self.command('POST','/element',{'using':'-android uiautomator','value':selector})
  identifier=element.get('element-6066-11e4-a52e-4f735466cecf') or element.get('ELEMENT')
  if not identifier:raise RemoteFailure('invalid_element_response')
  self.command('POST','/element/'+identifier+'/click',{})
 def type_text(self,text):
  element=self.command('POST','/element',{'using':'class name','value':'android.widget.EditText'})
  identifier=element.get('element-6066-11e4-a52e-4f735466cecf') or element.get('ELEMENT')
  if not identifier:raise RemoteFailure('invalid_element_response')
  self.command('POST','/element/'+identifier+'/clear',{})
  self.command('POST','/element/'+identifier+'/value',{'text':text,'value':list(text)})
 def tap(self,x,y,double=False):
  rect=self.command('GET','/window/rect')
  if not (0<=x<rect['width'] and 0<=y<rect['height']):raise RemoteFailure('tap_outside_window')
  events=[{'type':'pointerMove','duration':0,'x':x,'y':y},{'type':'pointerDown','button':0},{'type':'pause','duration':100},{'type':'pointerUp','button':0}]
  if double:events+=[{'type':'pause','duration':120},*events]
  self.command('POST','/actions',{'actions':[{'type':'pointer','id':'touch','parameters':{'pointerType':'touch'},'actions':events}]})
 def close(self):
  if self.session:
   try:self.command('DELETE','')
   finally:self.session=None
