'use strict';
(function(){
const root=document.getElementById('kp-catalog');if(!root)return;
const $=s=>root.querySelector(s);
let lastAttempt=0;
let files=[],carrier='all',country='all',plan='all',lastUpdated=null,loadError=false,loading=false,renderedSignature='';
const names={dtac:'dtac',true:'True',ais:'AIS',mpt:'MPT',atom:'ATOM',mytel:'Mytel','mm-other':'မြန်မာ အခြား',other:'SIM မသတ်မှတ်ထား'};
function safeLink(url){try{const u=new URL(url,location.href);if(u.protocol!=='https:'||u.username||u.password)return null;return u.href;}catch{return null;}}
function time(value){const date=new Date(value);return Number.isNaN(date.getTime())?'—':date.toLocaleString('en-GB',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit',timeZone:'Asia/Bangkok'});}
const carrierCountries={dtac:'TH',true:'TH',ais:'TH',mpt:'MM',atom:'MM',mytel:'MM','mm-other':'MM',other:'GLOBAL'};
function simCountry(f){return ['TH','MM','GLOBAL'].includes(f.sim_country)?f.sim_country:['TH','MM','GLOBAL'].includes(f.country)?f.country:(carrierCountries[f.carrier]||'GLOBAL');}
function currentFiles(){return files.filter(f=>f&&typeof f.name==='string'&&typeof f.carrier==='string'&&f.server_status==='handshake_https_pass'&&Date.parse(f.expires_at)>Date.now());}
function renderHealth(){
 const age=Date.now()-Date.parse(lastUpdated),health=$('#kp-health');
 health.classList.toggle('is-stale',loadError||age>90*60000);
 health.textContent=loadError?'စာရင်းရယူမှု မအောင်မြင်ပါ။ ပြန်စမ်းနိုင်ပါတယ်။':!lastUpdated?'':age>90*60000?'စာရင်း update နောက်ကျနေသည်။ ယခုဖော်ပြထားသော စစ်ချိန်ကို ကြည့်ပါ။':'စာရင်း အချိန်မီ update ဖြစ်ထားသည်။';
}
function render(){
 const valid=currentFiles(),q=$('#kp-file-search').value.toLowerCase().trim(),container=$('#kp-file-list');container.replaceChildren();
 renderedSignature=JSON.stringify(valid.map(f=>[f.id,f.carrier,f.plan,f.name,f.expires_at]));
 const rows=valid.filter(f=>(country==='all'||simCountry(f)===country)&&(carrier==='all'||f.carrier===carrier)&&(plan==='all'||(f.plan||'unknown')===plan)&&(!q||f.name.toLowerCase().includes(q)));
 $('#kp-count').textContent=String(rows.length);$('#kp-total').textContent=loadError?'—':String(valid.length);
 for(const f of rows.slice(0,100)){
  const row=document.createElement('article');row.className='kp-file';
  const title=document.createElement('h4');title.textContent=f.name;
  const detail=document.createElement('p');detail.textContent=simCountry(f)+' · '+(names[f.carrier]||f.carrier)+' · '+(f.plan||'unknown')+' · WireGuard .conf';
  const status=document.createElement('p');status.className='kp-verify';status.textContent='Server handshake + HTTPS စစ်ပြီး';
  const sim=document.createElement('p');sim.textContent=f.sim?.status==='user_reported_pass'?'SIM စမ်းသုံးသူ အောင်ကြောင်းတင်ပြထားသည်':'SIM / nopro လက်တွေ့ မစစ်ရသေးပါ';
  const checked=document.createElement('p');checked.className='kp-muted';checked.textContent='စစ်ချိန် '+time(f.checked_at)+' · သက်တမ်း '+time(f.expires_at)+' (TH)';
  row.append(title,detail,status,sim,checked);
  const actions=document.createElement('div');actions.className='file-actions';
  if(/^catalog\/downloads\/(dtac|true|ais|mpt|atom|mytel|mm-other|other)\/(nopro|standard|unknown)\/[a-z0-9-]+\.conf$/.test(f.download)){
   const a=document.createElement('a');a.href=f.download;a.download=f.name;a.className='button-primary';a.textContent='ဖိုင်ယူမယ်';actions.append(a);
  }
  if(f.download_kind==='source_archive'){
   const url=safeLink(f.download);
   if(url&&/^https:\/\/raw\.githubusercontent\.com\/[^/]+\/[^/]+\/[a-f0-9]{40}\/[^?#]+\.zip$/.test(url)){
    const a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener noreferrer';a.className='source-archive';a.textContent='မူရင်း ZIP ယူမယ် ↗';actions.append(a);
    const copy=document.createElement('button');copy.type='button';copy.className='button-secondary';copy.textContent='ဖိုင်နာမည် ကူးမယ်';
    copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(String(f.archive_member||f.name));copy.textContent='ကူးပြီးပါပြီ';}catch{copy.textContent='အောက်က နာမည်ကို ဖိထားပြီး ကူးပါ';}});actions.append(copy);
    const note=document.createElement('p');note.className='archive-note';note.textContent='ZIP ထဲမှ '+f.archive_member+' ကို ရွေးသုံးပါ။ ZIP ထဲက ဖိုင်အားလုံး စစ်ပြီးပြီဟု မဆိုလိုပါ။';row.append(note);
   }
  }
  const source=safeLink(f.download_kind==='source_archive'?f.permission_url:f.source_url);if(source){const a=document.createElement('a');a.href=source;a.rel='noopener noreferrer';a.target='_blank';a.textContent='မူရင်းရင်းမြစ် ↗';a.className='source-link';actions.append(a);}
  row.append(actions);container.append(row);
 }
 $('#kp-empty').hidden=rows.length>0;
 $('#kp-reset').hidden=country==='all'&&carrier==='all'&&plan==='all'&&!q;renderHealth();
 if(loadError){$('#kp-empty-title').textContent='ဖိုင်စာရင်း ဖတ်မရပါ';$('#kp-empty-description').textContent='အင်တာနက်ချိတ်ဆက်မှု စစ်ပြီး “ပြန်စစ်မယ်” ကိုနှိပ်ပါ။';}
 else if(valid.length){$('#kp-empty-title').textContent='ကိုက်ညီတဲ့ဖိုင် မရှိပါ';$('#kp-empty-description').textContent='တခြား SIM၊ ဖိုင်အမျိုးအစား သို့မဟုတ် ရှာဖွေစာသားကို ပြောင်းကြည့်ပါ။';}
 else{$('#kp-empty-title').textContent='စစ်ပြီးသားဖိုင် မရှိသေးပါ';$('#kp-empty-description').textContent='ချိတ်ဆက်စစ်ဆေးမှု အောင်တဲ့ဖိုင်တွေကို ဒီနေရာမှာ ပြပေးမယ်။ အခုတော့ ဖိုင်ထည့်သုံးနည်းကို အရင်ကြည့်နိုင်တယ်။';}
 if(!loadError&&lastUpdated)$('#kp-updated').textContent='နောက်ဆုံးစစ်ချိန် '+time(lastUpdated)+' · ထိုင်းစံတော်ချိန်';
}
root.querySelectorAll('[data-carrier]').forEach(b=>b.addEventListener('click',()=>{carrier=b.dataset.carrier;root.querySelectorAll('[data-carrier]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));render();}));
$('#kp-country').addEventListener('change',e=>{country=e.target.value;render();});
$('#kp-plan').addEventListener('change',e=>{plan=e.target.value;render();});$('#kp-file-search').addEventListener('input',render);
async function loadCatalog(){
 if(loading)return;let unchanged=false;const wasError=loadError;lastAttempt=Date.now();loading=true;$('#kp-refresh').disabled=true;$('#kp-refresh').textContent='စစ်နေသည်…';
 try{const r=await fetch('catalog/index.json',{cache:'no-store'});if(!r.ok)throw Error();const j=await r.json();if(!Array.isArray(j.files)||!Number.isFinite(Date.parse(j.updated_at)))throw Error();unchanged=renderedSignature!==''&&!wasError&&JSON.stringify(files)===JSON.stringify(j.files);files=j.files;lastUpdated=j.updated_at;loadError=false;}
 catch{files=[];loadError=true;$('#kp-updated').textContent='စာရင်းကို လောလောဆယ် ဖတ်မရပါ။';}
 finally{loading=false;$('#kp-refresh').disabled=false;$('#kp-refresh').textContent='ပြန်စစ်မယ်';if(unchanged){renderHealth();$('#kp-updated').textContent='နောက်ဆုံးစစ်ချိန် '+time(lastUpdated)+' · ထိုင်းစံတော်ချိန်';}else render();}
}
async function loadSources(){
 try{const r=await fetch('catalog/discovery.json',{cache:'no-store'});if(!r.ok)throw Error();const j=await r.json();const list=$('#kp-discovery');list.replaceChildren();let count=0;
  for(const item of (Array.isArray(j.sources)?j.sources:[]).slice(0,25)){if(!item||typeof item.url!=='string')continue;const url=safeLink(item.url);if(!url||new URL(url).hostname!=='github.com')continue;const li=document.createElement('li'),a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener noreferrer';a.textContent=item.name;li.append(a);list.append(li);count++;}
  $('#kp-source-count').textContent=String(count);
  if(!count){const li=document.createElement('li');li.textContent='ရင်းမြစ်အသစ် ရှာဖွေနေဆဲ ဖြစ်သည်။';list.append(li);}
 }catch{$('#kp-source-count').textContent='—';$('#kp-discovery').textContent='ရင်းမြစ်စာရင်း ဖတ်မရပါ။ နောက်မှ ပြန်စမ်းပါ။';}
}
$('#kp-reset').addEventListener('click',()=>{country='all';$('#kp-country').value='all';carrier='all';plan='all';$('#kp-plan').value='all';$('#kp-file-search').value='';root.querySelectorAll('[data-carrier]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.carrier==='all')));render();$('#kp-file-search').focus();});
function refreshIfDue(){if(!document.hidden&&Date.now()-lastAttempt>=5*60000){loadCatalog();loadSources();}}
document.addEventListener('visibilitychange',refreshIfDue);
window.addEventListener('online',()=>{if(!document.hidden){loadCatalog();loadSources();}});
$('#kp-refresh').addEventListener('click',()=>{loadCatalog();loadSources();});
// Anchor links to a collapsed guide should reveal the requested explanation.
root.querySelectorAll('a[href="#verification"],a[href="#troubleshooting"]').forEach(a=>a.addEventListener('click',()=>{const guide=$(a.getAttribute('href'));if(guide)guide.open=true;}));
loadCatalog();loadSources();setInterval(()=>{
 const signature=JSON.stringify(currentFiles().map(f=>[f.id,f.carrier,f.plan,f.name,f.expires_at]));
 if(signature!==renderedSignature)render();else renderHealth();
 refreshIfDue();
},60000);
})();
