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
   write(out/'daily.json',post);return 'pass','ယနေ့အတွက် စိစစ်ရွေးချယ်ထားသော ပညာပေးစာတို အသင့်ဖြစ်ပါပြီ။'
 used={p.get('content_id') for p in history['posts']}
 for item in bank:
  if item['id'] in used:continue
  public_https(item['source_url'],{'www.wireguard.com','protonvpn.com','docs.github.com','developer.android.com','support.google.com'})
  post={'date':today,'title':item['title'],'body':item['body'],'source_url':item['source_url'],'mode':'curated','content_id':item['id']}
  history['posts'].append(post);write(out/'daily-history.json',history);write(out/'daily.json',post)
  return 'pass','ဘန်ကောက်စံတော်ချိန်အရ ယနေ့အတွက် ပညာပေးစာတိုအသစ် ထုတ်ဝေပြီးပါပြီ။'
 return 'warning','needs_content: မထပ်သော သင်ခန်းစာ ၃၂ ပုဒ်ကို အသုံးပြုပြီးပါပြီ။ အကြောင်းအရာအသစ် ထပ်ဖြည့်ရန်လိုပြီး ယခင်စာတိုကိုသာ ဆက်ပြထားပါသည်။'

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
  except (KeyError,ValueError,TypeError):issues.append('လုံခြုံမှုမရှိသော၊ သက်တမ်းကုန်သော သို့မဟုတ် အချက်အလက်မကိုက်ညီသော စာရင်းကို ထုတ်ဝေမှုမှ ဖယ်ထားပါသည်။')
 # Generated downloads must never contain configs, regardless of catalog references.
 exposed=[p for p in (out/'downloads').rglob('*') if p.is_file()] if (out/'downloads').exists() else []
 for p in exposed:p.unlink()
 if exposed:issues.append('ထုတ်ဝေရန်မသင့်သော ဒေါင်းလုဒ်ဖိုင်များကို ဖယ်ရှားပြီးပါပြီ။')
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
 write(out/'summary.json',{'updated_at':stamp(now),'total':len(rows),'country_meaning':'SIM အသုံးပြုရာနိုင်ငံကို ဖော်ပြသည်။ ဆာဗာတည်နေရာကို မဖော်ပြပါ။','countries':{c:sum(r['country']==c for r in rows) for c in ('TH','MM','GLOBAL')},'sim_verified':sum(r['sim']['status']=='user_reported_pass' for r in rows),'scope':'Cloud မှ handshake နှင့် HTTPS အောင်မြင်ခြင်းက SIM ဖြင့် အသုံးပြုနိုင်မှု သို့မဟုတ် ဒေတာအခမဲ့ရမှုကို အတည်မပြုပါ။'})
 ds,dd=daily(out,read(data/'daily-bank.json',[]),now)
 stats=catalog.get('stats',{});discovery=read(out/'discovery.json',{})
 roles=[]
 def role(id,name,status,detail):roles.append(dict(id=id,name=name,status=status,detail=detail))
 role('finder','Config ရှာဖွေသူ','warning' if stats.get('source_errors') or discovery.get('search_errors') else 'pass',f"စစ်ဆေးရန် config {stats.get('candidates',0)} ခု။ ခွင့်ပြုထားသော ရင်းမြစ်စာရင်းမှသာ ရယူသည်။ ရင်းမြစ်အသစ်များကို လူက စိစစ်ခွင့်ပြုရန် လိုပါသည်။")
 role('verifier','ချိတ်ဆက်မှု စမ်းသပ်သူ','pass' if rows else 'warning',f'Cloud မှ handshake နှင့် HTTPS အောင်မြင်ပြီး သက်တမ်းရှိသော ရလဒ် {len(rows)} ခု။ SIM ဖြင့် တကယ်အသုံးပြုနိုင်မှုကို သီးခြားစမ်းသပ်ရပါမည်။')
 role('classifier','SIM အမျိုးအစား ခွဲခြားသူ','pass',f'ယုံကြည်ထားသော ရင်းမြစ်စာရင်းအရ SIM နိုင်ငံနှင့် အော်ပရေတာကို ခွဲထားသော မှတ်တမ်း {len(rows)} ခု။ SIM စမ်းသပ်အစီရင်ခံစာတွင် config hash အတိအကျ ကိုက်ညီရပါမည်။')
 role('publisher','Config စာရင်း ထုတ်ဝေသူ','pass' if rows else 'warning',f'လုံခြုံသော မူရင်းလင့်ခ် {len(rows)} ခု ထုတ်ဝေထားပါသည်။ မျှဝေထားသော လျှို့ဝှက် key များကို ပြန်လည်ဖြန့်ဝေခြင်း မရှိပါ။')
 role('daily','နေ့စဉ် ပညာပေးစာတို ရေးသားသူ',ds,dd)
 role('health','ဝက်ဘ်ဆိုက်နှင့် စာရင်းသက်တမ်း စောင့်ကြည့်သူ','pass' if rows else 'warning',f'သက်တမ်းရှိသော စာရင်း {len(rows)} ခု။ သက်တမ်းကုန်စာရင်းများကို ဖယ်ထားပါသည်။ အွန်လိုင်းတင်ထားသော ဝက်ဘ်ဆိုက် ဖွင့်ရမရကို သီးခြားစစ်ဆေးပါသည်။')
 role('security','ဝက်ဘ်ဆိုက် လုံခြုံရေး စောင့်ကြည့်သူ','warning' if issues else 'pass',' '.join(issues) if issues else 'စာရင်းလင့်ခ်များသည် ခွင့်ပြုထားသောရင်းမြစ်နှင့် commit အတိအကျကို ညွှန်းပါသည်။ Config ဖိုင်အသစ်များကို ဒေါင်းလုဒ်ရအောင် ထုတ်ဝေမထားပါ။')
 role('integrity','ဝက်ဘ်ဆိုက် စာရင်းမှန်ကန်မှု စောင့်ကြည့်သူ','warning' if issues else 'pass',f'စာရင်းလင့်ခ်နှင့် အော်ပရေတာစာရင်း ကိုက်ညီသော မှတ်တမ်း {len(rows)} ခု။ ဤစစ်ဆေးမှုသည် ဖိုင်များကို စစ်ဆေးခြင်းဖြစ်ပြီး အဝေးဆာဗာ ဖွင့်ရမရ စမ်းသပ်မှု မဟုတ်ပါ။')
 report={'updated_at':stamp(now),'ai':{'configured':False,'mode':'deterministic'},'roles':roles}
 write(out/'agents.json',report);return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',default='catalog');p.add_argument('--data',default='data');a=p.parse_args();report=run(Path(a.out),Path(a.data));print('Pipeline: '+', '.join(r['id']+'='+r['status'] for r in report['roles']))
if __name__=='__main__':main()
