'use strict';
(function(){
const root=document.getElementById('kp-catalog');if(!root)return;
const $=s=>root.querySelector(s);
let files=[],carrier='all',plan='all',lastUpdated=null,loadError=false,loading=false;
const names={dtac:'dtac',true:'True',ais:'AIS',mpt:'MPT',atom:'ATOM',mytel:'Mytel','mm-other':'မြန်မာ အခြား',other:'အခြား'};
function safeLink(url){try{const u=new URL(url,location.href);if(u.protocol!=='https:'||u.username||u.password)return null;return u.href;}catch{return null;}}
function time(value){const date=new Date(value);return Number.isNaN(date.getTime())?'—':date.toLocaleString('en-GB',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit',timeZone:'Asia/Bangkok'});}
function currentFiles(){return files.filter(f=>f&&typeof f.name==='string'&&typeof f.carrier==='string'&&f.server_status==='handshake_https_pass'&&Date.parse(f.expires_at)>Date.now());}
function render(){
 const valid=currentFiles(),q=$('#kp-file-search').value.toLowerCase().trim(),container=$('#kp-file-list');container.replaceChildren();
 const rows=valid.filter(f=>(carrier==='all'||f.carrier===carrier)&&(plan==='all'||f.plan===plan)&&(!q||f.name.toLowerCase().includes(q)));
 $('#kp-count').textContent=String(rows.length);$('#kp-total').textContent=loadError?'—':String(valid.length);
 for(const f of rows.slice(0,100)){
  const row=document.createElement('article');row.className='kp-file';
  const title=document.createElement('h4');title.textContent=f.name;
  const detail=document.createElement('p');detail.textContent=(names[f.carrier]||f.carrier)+' · '+f.plan+' · WireGuard .conf';
  const status=document.createElement('p');status.className='kp-verify';status.textContent='Server handshake + HTTPS စစ်ပြီး';
  const sim=document.createElement('p');sim.textContent=f.sim?.status==='user_reported_pass'?'SIM စမ်းသုံးသူ အောင်ကြောင်းတင်ပြထားသည်':'SIM / nopro လက်တွေ့ မစစ်ရသေးပါ';
  const checked=document.createElement('p');checked.className='kp-muted';checked.textContent='စစ်ချိန် '+time(f.checked_at)+' · သက်တမ်း '+time(f.expires_at)+' (TH)';
  row.append(title,detail,status,sim,checked);
  const actions=document.createElement('div');actions.className='file-actions';
  if(/^catalog\/downloads\/(dtac|true|ais|mpt|atom|mytel|mm-other|other)\/(nopro|standard|unknown)\/[a-z0-9-]+\.conf$/.test(f.download)){
   const a=document.createElement('a');a.href=f.download;a.download=f.name;a.className='button-primary';a.textContent='ဖိုင်ယူမယ်';actions.append(a);
  }
  const source=safeLink(f.source_url);if(source){const a=document.createElement('a');a.href=source;a.rel='noopener noreferrer';a.target='_blank';a.textContent='မူရင်းရင်းမြစ် ↗';a.className='source-link';actions.append(a);}
  row.append(actions);container.append(row);
 }
 $('#kp-empty').hidden=rows.length>0;
 if(loadError){$('#kp-empty-title').textContent='ဖိုင်စာရင်း ဖတ်မရပါ';$('#kp-empty-description').textContent='အင်တာနက်ချိတ်ဆက်မှု စစ်ပြီး “ပြန်စစ်မယ်” ကိုနှိပ်ပါ။';}
 else if(valid.length){$('#kp-empty-title').textContent='ကိုက်ညီတဲ့ဖိုင် မရှိပါ';$('#kp-empty-description').textContent='တခြား SIM၊ ဖိုင်အမျိုးအစား သို့မဟုတ် ရှာဖွေစာသားကို ပြောင်းကြည့်ပါ။';}
 else{$('#kp-empty-title').textContent='စစ်ပြီးသားဖိုင် မရှိသေးပါ';$('#kp-empty-description').textContent='ချိတ်ဆက်စစ်ဆေးမှု အောင်တဲ့ဖိုင်တွေကို ဒီနေရာမှာ ပြပေးမယ်။ အခုတော့ ဖိုင်ထည့်သုံးနည်းကို အရင်ကြည့်နိုင်တယ်။';}
 if(!loadError&&lastUpdated)$('#kp-updated').textContent='နောက်ဆုံးစစ်ချိန် '+time(lastUpdated)+' · ထိုင်းစံတော်ချိန်';
}
root.querySelectorAll('[data-carrier]').forEach(b=>b.addEventListener('click',()=>{carrier=b.dataset.carrier;root.querySelectorAll('[data-carrier]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));render();}));
$('#kp-plan').addEventListener('change',e=>{plan=e.target.value;render();});$('#kp-file-search').addEventListener('input',render);
async function loadCatalog(){
 if(loading)return;loading=true;$('#kp-refresh').disabled=true;$('#kp-refresh').textContent='စစ်နေသည်…';
 try{const r=await fetch('catalog/index.json',{cache:'no-store'});if(!r.ok)throw Error();const j=await r.json();if(!Array.isArray(j.files)||!Number.isFinite(Date.parse(j.updated_at)))throw Error();files=j.files;lastUpdated=j.updated_at;loadError=false;}
 catch{files=[];loadError=true;$('#kp-updated').textContent='စာရင်းကို လောလောဆယ် ဖတ်မရပါ။';}
 finally{loading=false;$('#kp-refresh').disabled=false;$('#kp-refresh').textContent='ပြန်စစ်မယ်';render();}
}
async function loadSources(){
 try{const r=await fetch('catalog/discovery.json',{cache:'no-store'});if(!r.ok)throw Error();const j=await r.json();const list=$('#kp-discovery');list.replaceChildren();let count=0;
  for(const item of (Array.isArray(j.sources)?j.sources:[]).slice(0,25)){if(!item||typeof item.url!=='string')continue;const url=safeLink(item.url);if(!url||new URL(url).hostname!=='github.com')continue;const li=document.createElement('li'),a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener noreferrer';a.textContent=item.name;li.append(a);list.append(li);count++;}
  $('#kp-source-count').textContent=String(count);
  if(!count){const li=document.createElement('li');li.textContent='ရင်းမြစ်အသစ် ရှာဖွေနေဆဲ ဖြစ်သည်။';list.append(li);}
 }catch{$('#kp-source-count').textContent='—';$('#kp-discovery').textContent='ရင်းမြစ်စာရင်း ဖတ်မရပါ။ နောက်မှ ပြန်စမ်းပါ။';}
}
$('#kp-refresh').addEventListener('click',()=>{loadCatalog();loadSources();});
// Anchor links to a collapsed guide should reveal the requested explanation.
root.querySelectorAll('a[href="#verification"]').forEach(a=>a.addEventListener('click',()=>{$('#verification').open=true;}));
loadCatalog();loadSources();setInterval(render,60000);
})();
