"""Agent 2 independently enforces registry policy before fetching/testing files."""
import argparse,json,shutil
from pathlib import Path
from .core import build_catalog,fetch_url,public_https
from .probe import probe

def authorize(candidates,registry):
 sources={s['id']:s for s in registry if s.get('enabled') is True and s.get('redistribution_approved') is True}
 approved=[]
 for c in candidates[:40]:
  try:
   s=sources[c['source_id']];hosts=set(s['allowed_hosts'])
   public_https(c['url'],hosts);public_https(s['permission_url'],hosts)
   approved.append({**c,'approved':True,'carrier':s['carrier'],'plan':s['plan'],'permission_url':s['permission_url'],'allowed_hosts':sorted(hosts)})
  except (KeyError,TypeError,ValueError):continue
 return approved

def main():
 p=argparse.ArgumentParser();p.add_argument('--input',default='work');p.add_argument('--out',default='catalog');p.add_argument('--offline',action='store_true');a=p.parse_args()
 source=Path(a.input);out=Path(a.out)
 raw=json.loads((source/'candidates.json').read_text())
 registry=json.loads(Path('data/sources.json').read_text())['sources']
 candidates=authorize(raw['candidates'],registry)
 reports=json.loads(Path('data/carrier-tests.json').read_text())['reports']
 result=build_catalog(candidates,reports,out,fetch=lambda c:fetch_url(c['url'],set(c['allowed_hosts'])),probe=(lambda _:False) if a.offline else probe)
 # Discovery contains public repository metadata only; not trusted file contents.
 shutil.copyfile(source/'discovery.json',out/'discovery.json')
 print(f'Verifier: {len(result["files"])} server-verified files published; {result["stats"]["rejected"]} rejected; actual SIM test is separate')
if __name__=='__main__':main()
