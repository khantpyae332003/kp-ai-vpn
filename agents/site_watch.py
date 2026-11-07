"""Read-only public website checks; never executes downloaded config material."""
import argparse,json,re
from datetime import timedelta
from zoneinfo import ZoneInfo
from urllib.request import Request,urlopen
from html.parser import HTMLParser
from .core import date,now_utc

BASE='https://khantpyae332003.github.io/kp-ai-vpn/'
def fetch(path):
 with urlopen(Request(BASE+path,headers={'User-Agent':'KP-VPN-Monitor/0.2','Cache-Control':'no-cache'}),timeout=30) as r:
  body=r.read(1024*1024+1)
  if r.status!=200 or len(body)>1024*1024:raise ValueError('HTTP or size check failed')
  return body.decode('utf-8')
class Page(HTMLParser):
 def __init__(self):super().__init__();self.csp=False;self.scripts=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='meta' and a.get('http-equiv','').lower()=='content-security-policy':self.csp="default-src 'none'" in a.get('content','') and "script-src 'self'" in a.get('content','')
  if tag=='script':self.scripts.append(a.get('src',''))
def check(kind):
 html=fetch('');catalog=json.loads(fetch('catalog/index.json'));rows=catalog['files']
 if kind=='health':
  age=now_utc()-date(catalog['updated_at'])
  if age>timedelta(hours=6):raise ValueError('Catalog has not refreshed within six hours')
  print('PASS: public website and catalog available; catalog age minutes='+str(round(age.total_seconds()/60)))
 elif kind=='security':
  p=Page();p.feed(html)
  if not p.csp or any(not re.fullmatch(r'assets/[a-z0-9-]+\.js(?:\?v=[a-zA-Z0-9.-]+)?',s) for s in p.scripts):raise ValueError('Script/CSP policy mismatch')
  if re.search(r'PrivateKey\s*=|PresharedKey\s*=|\[Interface\]',json.dumps(catalog),re.I):raise ValueError('Config material found in public metadata')
  for row in rows:
   if row.get('download_kind')!='source_archive' or not re.fullmatch(r'https://raw\.githubusercontent\.com/[^/]+/[^/]+/[a-f0-9]{40}/[^?#]+\.zip',row['download']):raise ValueError('Unpinned public download')
  print('PASS: public CSP, script paths and metadata expose no config keys')
 elif kind=='integrity':
  if not isinstance(rows,list) or len(rows)>100:raise ValueError('Catalog shape')
  for row in rows:
   if row.get('server_status')!='handshake_https_pass' or not re.fullmatch('[a-f0-9]{64}',row['id']):raise ValueError('Unverified file displayed')
  report=json.loads(fetch('catalog/agents.json'))
  if {r['id'] for r in report['roles']}!={'finder','verifier','classifier','publisher','daily','health','security','integrity'}:raise ValueError('Missing pipeline roles')
  daily=json.loads(fetch('catalog/daily.json'))
  if not daily.get('title') or not daily.get('body'):raise ValueError('Daily learning is missing')
  local=now_utc().astimezone(ZoneInfo('Asia/Bangkok'));today=local.date().isoformat()
  if daily.get('date','')>today or (daily.get('date')!=today and local.hour>=2):raise ValueError('Daily learning is stale or the lesson bank needs replenishment')
  if daily.get('date')!=today:print('WARNING: Bangkok day changed; daily publication is pending')
  print('PASS: public catalog, eight role records and daily learning are consistent')
 else:raise ValueError('Unknown check')
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',choices=['health','security','integrity'],required=True);a=p.parse_args();check(a.check)
if __name__=='__main__':main()
