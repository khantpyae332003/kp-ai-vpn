"""Bounded WireGuard parsing and public-catalog policy. Never logs config bytes."""
import base64,hashlib,ipaddress,json,re,shutil,socket,http.client,ssl
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import urlsplit
from urllib.request import build_opener,HTTPRedirectHandler,Request
from urllib.error import HTTPError

CARRIERS={'dtac':'TH','true':'TH','ais':'TH','mpt':'MM','atom':'MM','mytel':'MM','mm-other':'MM','other':'OTHER'}
PLANS={'nopro','standard','unknown'}
MAX_CONFIG=128*1024

def now_utc():return datetime.now(timezone.utc)
def stamp(t):return t.isoformat(timespec='seconds')
def date(s):
 t=datetime.fromisoformat(s.replace('Z','+00:00'))
 if t.tzinfo is None:raise ValueError('timezone required')
 return t

def global_ip(s):
 ip=ipaddress.ip_address(s)
 return ip.is_global and not ip.is_multicast and not ip.is_reserved and not ip.is_unspecified

def public_https(url,allowed_hosts):
 p=urlsplit(url)
 if p.scheme!='https' or not p.hostname or p.hostname.lower() not in allowed_hosts or p.username or p.password or p.fragment or p.query or p.port not in (None,443):raise ValueError('URL policy')
 try:
  if not global_ip(p.hostname):raise ValueError('Non-public address')
 except ValueError:
  # A literal private IP must not fall through to hostname handling.
  try:ipaddress.ip_address(p.hostname)
  except ValueError:pass
  else:raise ValueError('Non-public address')
  if p.hostname in ('localhost',) or '.' not in p.hostname:raise ValueError('Non-public hostname')
 return url

class PinnedHTTPSConnection(http.client.HTTPSConnection):
 def __init__(self,hostname,validated_ip,timeout=15):
  if not global_ip(validated_ip):raise ValueError('Non-public transport target')
  super().__init__(hostname,port=443,timeout=timeout,context=ssl.create_default_context())
  # HTTPSConnection keeps the original hostname for Host/SNI/certificate checks.
  # Only the TCP destination is pinned, preventing a second DNS lookup/rebinding.
  self._create_connection=lambda address,timeout=15,source_address=None:socket.create_connection((validated_ip,443),timeout,source_address)

def fetch_url(url,allowed_hosts,limit=MAX_CONFIG):
 for _ in range(4):
  public_https(url,allowed_hosts)
  parts=urlsplit(url);host=parts.hostname
  answers=socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
  if not answers or any(not global_ip(x[4][0]) for x in answers):raise ValueError('Non-public DNS')
  connection=PinnedHTTPSConnection(host,answers[0][4][0],timeout=15)
  try:
   connection.request('GET',parts.path or '/',headers={'User-Agent':'KP-VPN-Catalog/1.0','Host':parts.netloc})
   response=connection.getresponse()
   if response.status in (301,302,303,307,308):
    from urllib.parse import urljoin
    location=response.getheader('Location')
    if not location:raise ValueError('Missing redirect')
    url=urljoin(url,location);continue
   if response.status!=200:raise ValueError('Source HTTP status')
   data=response.read(limit+1)
   if len(data)>limit:raise ValueError('Response limit')
   return data
  finally:connection.close()
 raise ValueError('Redirect limit')

def _key(value):
 try:b=base64.b64decode(value,validate=True)
 except Exception:raise ValueError('Invalid key') from None
 if len(b)!=32 or not any(b):raise ValueError('Invalid key')
 return value

def parse_config(text):
 if len(text.encode())>MAX_CONFIG:raise ValueError('Config limit')
 sections={};current=None
 allowed={'Interface':{'PrivateKey','Address','DNS','MTU'},'Peer':{'PublicKey','PresharedKey','AllowedIPs','Endpoint','PersistentKeepalive'}}
 for raw in text.lstrip('\ufeff').splitlines():
  line=raw.split('#',1)[0].strip()
  if not line:continue
  if line.startswith('['):
   current=line[1:-1]
   if line not in ('[Interface]','[Peer]') or current in sections:raise ValueError('One interface and one peer required')
   sections[current]={};continue
  if current is None or '=' not in line:raise ValueError('Invalid config')
  k,v=map(str.strip,line.split('=',1))
  if k not in allowed[current] or k in sections[current] or not v:raise ValueError('Unsupported or duplicate field')
  sections[current][k]=v
 try:
  a,b=sections['Interface'],sections['Peer'];_key(a['PrivateKey']);_key(b['PublicKey'])
  if 'PresharedKey' in b:_key(b['PresharedKey'])
  addresses=[str(ipaddress.ip_interface(x.strip())) for x in a['Address'].split(',')]
  routes=[str(ipaddress.ip_network(x.strip(),strict=False)) for x in b['AllowedIPs'].split(',')]
  if not addresses or '0.0.0.0/0' not in routes:raise ValueError('IPv4 full-tunnel route required')
  for item in a.get('DNS','').split(','):
   if item.strip():ipaddress.ip_address(item.strip())
  if 'MTU' in a and not 1280<=int(a['MTU'])<=9000:raise ValueError('MTU range')
  if 'PersistentKeepalive' in b and not 0<=int(b['PersistentKeepalive'])<=65535:raise ValueError('Keepalive range')
  match=re.fullmatch(r'(?:\[([a-fA-F0-9:]+)\]|([A-Za-z0-9.-]+)):(\d{1,5})',b['Endpoint'])
  if not match:raise ValueError('Endpoint')
  host=match.group(1) or match.group(2);port=int(match.group(3))
  if not 1<=port<=65535:raise ValueError('Endpoint port')
  try:
   ipaddress.ip_address(host)
   if not global_ip(host):raise ValueError('Non-public endpoint')
  except ValueError:
   try:ipaddress.ip_address(host)
   except ValueError:
    if '.' not in host or host.endswith(('.local','.internal','.localhost')):raise ValueError('Endpoint hostname')
   else:raise ValueError('Non-public endpoint')
 except (KeyError,TypeError):raise ValueError('Required field missing') from None
 a['Address']=', '.join(addresses);b['AllowedIPs']=', '.join(routes)
 def section(name,values):return '['+name+']\n'+''.join(k+' = '+values[k]+'\n' for k in sorted(values))
 canonical=section('Interface',a)+'\n'+section('Peer',b)
 setconf=section('Interface',{'PrivateKey':a['PrivateKey']})+'\n'+section('Peer',b)
 return {'config':canonical,'sha256':hashlib.sha256(canonical.encode()).hexdigest(),'endpoint':(host,port),'addresses':addresses,'wg_setconf':setconf}

def sim_status(sha,carrier,plan,reports,now):
 for r in reports:
  try:
   age=now-date(r['tested_at'])
   if r['sha256']==sha and r['carrier']==carrier and r['plan']==plan and r['network']=='cellular' and r['result']=='pass' and timedelta(0)<=age<=timedelta(hours=24):
    u=r['evidence_url'];public_https(u,{'github.com'})
    return {'status':'user_reported_pass','tested_at':r['tested_at'],'evidence_url':u}
  except (ValueError,KeyError,TypeError):continue
 return {'status':'not_tested'}

def build_catalog(candidates,reports,out,fetch,probe):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 # This directory is generated output only, never a user-controlled path.
 downloads=out/'downloads'
 if downloads.exists():shutil.rmtree(downloads)
 downloads.mkdir()
 result={'schema':1,'updated_at':stamp(now_utc()),'files':[],'stats':{'candidates':len(candidates),'approved':0,'rejected':0,'duplicate':0},'verification_scope':'Cloud WireGuard handshake + IPv4 HTTPS; actual SIM not automatically tested'}
 seen=set()
 for c in candidates[:40]:
  if c.get('approved') is not True:continue
  result['stats']['approved']+=1
  try:
   carrier=c['carrier'];plan=c.get('plan','unknown')
   if carrier not in CARRIERS or plan not in PLANS or not c.get('permission_url'):raise ValueError('Missing policy')
   if c.get('expires_at') and date(c['expires_at'])<=now_utc():raise ValueError('Expired')
   body=fetch(c);p=parse_config(body.decode('utf-8-sig'))
   if c.get('expected_sha256') and hashlib.sha256(body).hexdigest()!=c['expected_sha256']:raise ValueError('Source checksum mismatch')
   identity=(p['sha256'],carrier,plan)
   if identity in seen:result['stats']['duplicate']+=1;continue
   if not probe(p):raise ValueError('Network check failed')
   tested=now_utc();expires=tested+timedelta(hours=24)
   if c.get('expires_at'):expires=min(expires,date(c['expires_at']))
   filename=f"{carrier}/{plan}/{carrier}-{plan}-{p['sha256'][:12]}.conf"
   target=downloads/filename;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(p['config'])
   seen.add(identity)
   result['files'].append({'id':p['sha256'],'name':target.name,'source_name':str(c.get('name',''))[:100],'carrier':carrier,'country':CARRIERS[carrier],'plan':plan,'protocol':'wireguard','format':'.conf','source_url':c['url'],'permission_url':c['permission_url'],'download':'catalog/downloads/'+filename,'checked_at':stamp(tested),'expires_at':stamp(expires),'server_status':'handshake_https_pass','sim':sim_status(p['sha256'],carrier,plan,reports,tested)})
  except Exception:result['stats']['rejected']+=1
 (out/'index.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 for carrier in CARRIERS:
  rows=[p for p in result['files'] if p['carrier']==carrier]
  (out/(carrier+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 return result
