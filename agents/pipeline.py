"""Eight bounded metadata roles. No AI credentials or config bytes are consumed here."""
import argparse,json,re
from pathlib import Path
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from .core import CARRIERS,PLANS,date,now_utc,stamp,sim_status,public_https

def read(path,default):
 try:return json.loads(Path(path).read_text())
 except (OSError,ValueError):return default

def write(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def classify(rows,registry,reports,now):
 """Registry owns SIM grouping; cellular evidence must match canonical config hash."""
 trusted={s['id']:s for s in registry if s.get('enabled') is True}
 result=[]
 for raw in rows:
  s=trusted.get(raw.get('source_id'))
  if not s or s.get('carrier') not in CARRIERS or s.get('plan') not in PLANS:continue
  row=dict(raw);carrier=s['carrier'];plan=s['plan']
  row.update(carrier=carrier,country=CARRIERS[carrier],plan=plan,sim=sim_status(row['id'],carrier,plan,reports,now))
  result.append(row)
 return result

def daily(out,bank,now):
 today=now.astimezone(ZoneInfo('Asia/Bangkok')).date().isoformat()
 history=read(out/'daily-history.json',{'posts':[]})
 for post in history['posts']:
  if post['date']==today:
   write(out/'daily.json',post);return 'pass','Today’s curated educational post is ready.'
 used={p.get('content_id') for p in history['posts']}
 for item in bank:
  if item['id'] in used:continue
  public_https(item['source_url'],{'www.wireguard.com','protonvpn.com','docs.github.com','developer.android.com','support.google.com'})
  post={'date':today,'title':item['title'],'body':item['body'],'source_url':item['source_url'],'mode':'curated','content_id':item['id']}
  history['posts'].append(post);write(out/'daily-history.json',history);write(out/'daily.json',post)
  return 'pass','New curated educational post published for Asia/Bangkok.'
 return 'warning','needs_content: curated bank exhausted; previous post retained without repetition.'

def audit(rows,out,registry,now):
 issues=[];valid=[];seen=set();known={s['id']:s for s in registry if s.get('enabled') is True}
 for row in rows:
  try:
   s=known[row['source_id']]
   if s.get('public_link_approved') is not True or row.get('download_kind')!='source_archive':raise ValueError('Source permission')
   commit=row['source_commit']
   if not re.fullmatch('[a-f0-9]{40}',commit):raise ValueError('Commit')
   expected='https://raw.githubusercontent.com/'+s['github_repository']+'/'+commit+'/'+s['archive_path']
   if row['download']!=expected or row['source_url']!=expected:raise ValueError('Pinned source')
   public_https(row['download'],set(s['allowed_hosts']))
   if row['permission_url']!=s['permission_url']:raise ValueError('Permission URL')
   if row['server_status']!='handshake_https_pass' or not re.fullmatch('[a-f0-9]{64}',row['id']):raise ValueError('Verification')
   if date(row['expires_at'])<=now or date(row['checked_at'])>now or now-date(row['checked_at'])>timedelta(hours=24):raise ValueError('Freshness')
   if re.search(r'PrivateKey\s*=|PresharedKey\s*=|\[Interface\]',json.dumps(row),re.I):raise ValueError('Key material')
   identity=(row['id'],s.get('carrier'),s.get('plan'))
   if identity in seen:raise ValueError('Duplicate identity')
   seen.add(identity)
   allowed={'id','name','source_name','carrier','country','plan','protocol','format','source_url','permission_url','download','download_kind','archive_member','source_id','source_commit','checked_at','expires_at','server_status','sim'}
   if set(row)-allowed:raise ValueError('Unexpected metadata field')
   valid.append(row)
  except (KeyError,ValueError,TypeError):issues.append('Unsafe, stale or inconsistent catalog entry withheld.')
 # Generated downloads must never contain configs, regardless of catalog references.
 exposed=[p for p in (out/'downloads').rglob('*') if p.is_file()] if (out/'downloads').exists() else []
 for p in exposed:p.unlink()
 if exposed:issues.append('Unexpected generated download artifacts removed.')
 return valid,issues

def run(out=Path('catalog'),data=Path('data'),now=None):
 out=Path(out);data=Path(data);now=now or now_utc()
 catalog=read(out/'index.json',{'schema':1,'files':[],'stats':{}})
 registry=read(data/'sources.json',{'sources':[]})['sources']
 reports=read(data/'carrier-tests.json',{'reports':[]})['reports']
 rows,issues=audit(catalog.get('files',[]),out,registry,now)
 rows=classify(rows,registry,reports,now);catalog['files']=rows
 write(out/'index.json',catalog)
 for carrier in CARRIERS:write(out/(carrier+'.json'),[r for r in rows if r['carrier']==carrier])
 write(out/'summary.json',{'updated_at':stamp(now),'total':len(rows),'country_meaning':'SIM country, not server location','countries':{c:sum(r['country']==c for r in rows) for c in ('TH','MM','GLOBAL')},'sim_verified':sum(r['sim']['status']=='user_reported_pass' for r in rows),'scope':'Cloud handshake + HTTPS does not prove SIM service or free data.'})
 ds,dd=daily(out,read(data/'daily-bank.json',[]),now)
 stats=catalog.get('stats',{});discovery=read(out/'discovery.json',{})
 roles=[]
 def role(id,name,status,detail):roles.append(dict(id=id,name=name,status=status,detail=detail))
 role('finder','Config finder','warning' if stats.get('source_errors') or discovery.get('search_errors') else 'pass',f"{stats.get('candidates',0)} candidates; only approved registry sources eligible. Unapproved leads require review.")
 role('verifier','Connection tester','pass' if rows else 'warning',f'{len(rows)} current handshake + HTTPS results. Actual SIM service is separate.')
 role('classifier','SIM classifier','pass',f'{len(rows)} records grouped by trusted SIM country and carrier; cellular reports require matching hash.')
 role('publisher','Catalog publisher','pass' if rows else 'warning',f'{len(rows)} safe source links published; no shared keys redistributed.')
 role('daily','Daily educational writer',ds,dd)
 role('health','Website health and freshness monitor','pass' if rows else 'warning',f'{len(rows)} fresh catalog records; stale entries withheld. Deployment availability is checked separately.')
 role('security','Website security monitor','warning' if issues else 'pass',' '.join(issues) if issues else 'Catalog URLs are approved and commit pinned; no generated config downloads exposed.')
 role('integrity','Website catalog integrity monitor','warning' if issues else 'pass',f'{len(rows)} consistent catalog links and carrier indexes; checks are local, not remote availability probes.')
 report={'updated_at':stamp(now),'ai':{'configured':False,'mode':'deterministic'},'roles':roles}
 write(out/'agents.json',report);return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',default='catalog');p.add_argument('--data',default='data');a=p.parse_args();report=run(Path(a.out),Path(a.data));print('Pipeline: '+', '.join(r['id']+'='+r['status'] for r in report['roles']))
if __name__=='__main__':main()
