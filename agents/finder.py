"""Agent 1: discover source metadata; collect from explicitly approved manifests."""
import argparse,json,os,time
from pathlib import Path
from urllib.parse import urlencode,urlsplit
from urllib.request import Request,urlopen
from .core import fetch_url,public_https,stamp,now_utc,CARRIERS,PLANS

QUERIES=['dtac nopro','true nopro','ais nopro','wireguard thailand','wireguard myanmar']

def discover():
 found={};errors=0
 for query in QUERIES:
  try:
   url='https://api.github.com/search/repositories?'+urlencode({'q':query,'per_page':5,'sort':'updated'})
   headers={'Accept':'application/vnd.github+json','User-Agent':'KP-VPN-Catalog/1.0','X-GitHub-Api-Version':'2022-11-28'}
   token=os.environ.get('GITHUB_TOKEN')
   if token:headers['Authorization']='Bearer '+token
   with urlopen(Request(url,headers=headers),timeout=15) as r:raw=r.read(1024*1024+1)
   if len(raw)>1024*1024:raise ValueError('Response limit')
   for item in json.loads(raw).get('items',[]):
    url=item.get('html_url','');public_https(url,{'github.com'})
    found[url]={'name':str(item.get('full_name',''))[:100],'url':url,'description':str(item.get('description') or '')[:200],'status':'source_not_approved','query':query,'updated_at':item.get('updated_at')}
  except Exception:errors+=1
  time.sleep(1)
 return {'updated_at':stamp(now_utc()),'sources':list(found.values())[:25],'search_errors':errors,'note':'Repository metadata only. These are not verified or approved VPN downloads.'}

def collect(sources):
 candidates=[];errors=0
 for s in sources[:20]:
  if s.get('enabled') is not True or s.get('redistribution_approved') is not True:continue
  try:
   hosts=set(s['allowed_hosts']);public_https(s['permission_url'],hosts)
   if s['carrier'] not in CARRIERS or s['plan'] not in PLANS:raise ValueError('Group')
   raw=fetch_url(s['manifest_url'],hosts,1024*1024)
   files=json.loads(raw)['files']
   for f in files[:40]:
    public_https(f['url'],hosts)
    candidates.append({'source_id':s['id'],'name':str(f.get('name','WireGuard'))[:100],'url':f['url'],'expires_at':f.get('expires_at'),'expected_sha256':f.get('sha256')})
    if len(candidates)>=40:return candidates,errors
  except Exception:errors+=1
 return candidates,errors

def main():
 p=argparse.ArgumentParser();p.add_argument('--discover',action='store_true');p.add_argument('--out',default='work');a=p.parse_args()
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 registry=json.loads(Path('data/sources.json').read_text());items,errors=collect(registry['sources'])
 (out/'candidates.json').write_text(json.dumps({'schema':1,'candidates':items,'source_errors':errors},ensure_ascii=False,indent=2)+'\n')
 discovery=discover() if a.discover else {'updated_at':stamp(now_utc()),'sources':[],'search_errors':0,'note':'Search skipped for local offline run'}
 (out/'discovery.json').write_text(json.dumps(discovery,ensure_ascii=False,indent=2)+'\n')
 print(f'Finder: {len(items)} eligible candidates; {len(discovery["sources"])} unapproved source leads; {errors} source errors')
if __name__=='__main__':main()
