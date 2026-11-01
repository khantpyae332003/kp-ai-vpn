"""Agent 2 independently authorizes, fetches, parses and probes candidate files."""
import argparse,json,shutil,re,hashlib
from pathlib import Path
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
from .core import build_catalog,fetch_url,public_https,parse_config,date,now_utc
from .archive import read_member,safe_member,MAX_ARCHIVE
from .probe import probe

def authorize(candidates,registry):
 sources={s['id']:s for s in registry if s.get('enabled') is True and (s.get('redistribution_approved') is True or (s.get('kind')=='github_zip' and s.get('public_link_approved') is True))}
 approved=[];manifests={}
 for c in candidates[:40]:
  try:
   s=sources[c['source_id']];hosts=set(s['allowed_hosts']);public_https(c['url'],hosts);public_https(s['permission_url'],hosts)
   if s.get('kind')=='github_zip':
    sha=c['commit_sha']
    if not re.fullmatch('[a-f0-9]{40}',sha) or not safe_member(c['member']):raise ValueError('Archive candidate')
    expected='https://raw.githubusercontent.com/'+s['github_repository']+'/'+sha+'/'+quote(s['archive_path'],safe='/')
    if c['url']!=expected or not all(re.fullmatch('[a-f0-9]{64}',c[k]) for k in ('archive_sha256','member_sha256')):raise ValueError('Archive provenance')
    approved.append({**c,'approved':True,'link_only':True,'carrier':s['carrier'],'plan':s['plan'],'permission_url':s['permission_url'],'allowed_hosts':sorted(hosts),'expected_sha256':c['member_sha256']})
   else:
    if s['id'] not in manifests:
     manifests[s['id']]=None
     public_https(s['manifest_url'],hosts)
     manifest=json.loads(fetch_url(s['manifest_url'],hosts,1024*1024))
     manifests[s['id']]={f['url']:f for f in manifest['files'][:40] if isinstance(f,dict) and isinstance(f.get('url'),str)}
    records=manifests[s['id']]
    if not records or c['url'] not in records:raise ValueError('Not in trusted manifest')
    entry=records[c['url']]
    approved.append({'source_id':s['id'],'url':entry['url'],'name':str(entry.get('name','WireGuard'))[:100],'expected_sha256':entry.get('sha256'),'expires_at':entry.get('expires_at'),'approved':True,'link_only':False,'carrier':s['carrier'],'plan':s['plan'],'permission_url':s['permission_url'],'allowed_hosts':sorted(hosts)})
  except (KeyError,TypeError,ValueError,OSError):continue
 return approved

def main():
 p=argparse.ArgumentParser();p.add_argument('--input',default='work');p.add_argument('--out',default='catalog');p.add_argument('--offline',action='store_true');a=p.parse_args()
 source=Path(a.input);out=Path(a.out);raw=json.loads((source/'candidates.json').read_text())
 registry=json.loads(Path('data/sources.json').read_text())['sources'];candidates=authorize(raw['candidates'],registry)
 reports=json.loads(Path('data/carrier-tests.json').read_text())['reports'];archives={};bodies={};parsed={}
 def fetch(c):
  key=(c['url'],c.get('member'))
  if key in bodies:return bodies[key]
  if a.offline:raise ValueError('Offline')
  if c.get('link_only'):
   if c['url'] not in archives:archives[c['url']]=fetch_url(c['url'],set(c['allowed_hosts']),MAX_ARCHIVE)
   body=read_member(archives[c['url']],c)
  else:body=fetch_url(c['url'],set(c['allowed_hosts']))
  bodies[key]=body;return body
 for c in candidates:
  try:
   if c.get('expires_at') and date(c['expires_at'])<=now_utc():continue
   body=fetch(c)
   if c.get('expected_sha256') and hashlib.sha256(body).hexdigest()!=c['expected_sha256']:continue
   config=parse_config(body.decode('utf-8-sig'));parsed[config['sha256']]=config
  except Exception:pass
 results={}
 if not a.offline:
  with ThreadPoolExecutor(max_workers=4) as pool:
   for sha,ok in zip(parsed,pool.map(probe,parsed.values())):results[sha]=ok
 result=build_catalog(candidates,reports,out,fetch=fetch,probe=lambda c:results.get(c['sha256'],False))
 result['stats']['source_errors']=raw.get('source_errors',0)
 (out/'index.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 shutil.copyfile(source/'discovery.json',out/'discovery.json')
 print(f'Verifier: {len(candidates)} candidates; {len(parsed)} parse-valid; {sum(bool(v) for v in results.values())} successful server probes; {len(result["files"])} files listed. Actual SIM test is separate.')
if __name__=='__main__':main()
