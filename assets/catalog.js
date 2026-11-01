'use strict';
(function(){
const root=document.getElementById('kp-catalog');if(!root)return;
const $=s=>root.querySelector(s);let files=[],carrier='all',plan='all';
const names={dtac:'dtac',true:'True',ais:'AIS',mpt:'MPT',atom:'ATOM',mytel:'Mytel','mm-other':'မြန်မာ အခြား',other:'အခြား'};
function safeLink(url){try{const u=new URL(url,location.href);if(u.protocol!=='https:'||u.username||u.password)return null;return u.href;}catch{return null;}}
function render(){
 const q=$('#kp-file-search').value.toLowerCase().trim(),container=$('#kp-file-list');container.replaceChildren();
 const rows=files.filter(f=>(carrier==='all'||f.carrier===carrier)&&(plan==='all'||f.plan===plan)&&(!q||f.name.toLowerCase().includes(q))&&Date.parse(f.expires_at)>Date.now());
 $('#kp-count').textContent=String(rows.length);
 Object.keys(names).forEach(c=>{const el=root.querySelector('[data-count="'+c+'"]');if(el)el.textContent=String(files.filter(f=>f.carrier===c&&f.plan==='nopro'&&Date.parse(f.expires_at)>Date.now()).length);});
 for(const f of rows.slice(0,100)){
  const row=document.createElement('article');row.className='kp-file';
  const title=document.createElement('h4');title.textContent=f.name;
  const detail=document.createElement('p');detail.textContent=(names[f.carrier]||f.carrier)+' · '+f.plan+' (source label) · WireGuard .conf';
  const status=document.createElement('p');status.className='kp-verify';status.textContent='✓ Server handshake + HTTPS စစ်ပြီး';
  const sim=document.createElement('p');sim.textContent=f.sim?.status==='user_reported_pass'?'SIM စမ်းသုံးသူ အောင်ကြောင်းတင်ပြထားသည် — '+f.sim.tested_at:'SIM / nopro လက်တွေ့ မစစ်ရသေးပါ';
  const checked=document.createElement('p');checked.className='kp-muted';checked.textContent='စစ်ချိန်: '+new Date(f.checked_at).toLocaleString()+' · သက်တမ်း: '+new Date(f.expires_at).toLocaleString();
  row.append(title,detail,status,sim,checked);
  // Only generated relative paths in the catalog can become download links.
  if(/^catalog\/downloads\/(dtac|true|ais|mpt|atom|mytel|mm-other|other)\/(nopro|standard|unknown)\/[a-z0-9-]+\.conf$/.test(f.download)){
   const a=document.createElement('a');a.href=f.download;a.download=f.name;a.className='btn small';a.textContent='ဖိုင်ယူမယ်';row.append(a);
  }
  const source=safeLink(f.source_url);if(source){const a=document.createElement('a');a.href=source;a.rel='noopener noreferrer';a.target='_blank';a.textContent=' မူရင်း';row.append(a);}
  container.append(row);
 }
 $('#kp-empty').hidden=rows.length>0;
 $('#kp-empty').textContent=files.length?'ဒီ filter နဲ့ ကိုက်ညီတဲ့ သက်တမ်းရှိဖိုင် မရှိပါ။':'လက်ရှိ စစ်ပြီးသား download ဖိုင် မရှိသေးပါ။ မျှဝေခွင့်ရှိသော config feed ထည့်ပြီး server စစ်ဆေးမှု အောင်မှ ဒီမှာပေါ်မည်။';
}
root.querySelectorAll('[data-carrier]').forEach(b=>b.addEventListener('click',()=>{carrier=b.dataset.carrier;root.querySelectorAll('[data-carrier]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));render();}));
$('#kp-plan').addEventListener('change',e=>{plan=e.target.value;render();});$('#kp-file-search').addEventListener('input',render);
root.querySelectorAll('[data-category]').forEach(b=>b.addEventListener('click',()=>{carrier=b.dataset.category;plan='nopro';$('#kp-plan').value=plan;root.querySelectorAll('[data-carrier]').forEach(x=>x.setAttribute('aria-pressed',String(x.dataset.carrier===carrier)));render();$('#kp-file-list').scrollIntoView({behavior:'smooth',block:'start'});}));
async function load(){
 try{const r=await fetch('catalog/index.json',{cache:'no-store'});if(!r.ok)throw Error();const j=await r.json();files=Array.isArray(j.files)?j.files:[];$('#kp-updated').textContent='နောက်ဆုံးစစ်ဆေးချိန် — '+new Date(j.updated_at).toLocaleString();render();}
 catch{$('#kp-updated').textContent='ဖိုင်စာရင်းကို လောလောဆယ် ဖတ်မရပါ။ နောက်မှ ပြန်စမ်းပါ။';}
 try{const r=await fetch('catalog/discovery.json',{cache:'no-store'});if(!r.ok)throw Error();const j=await r.json();const list=$('#kp-discovery');list.replaceChildren();
  for(const item of (j.sources||[]).slice(0,25)){const url=safeLink(item.url);if(!url||new URL(url).hostname!=='github.com')continue;const li=document.createElement('li'),a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener noreferrer';a.textContent=item.name;li.append(a,document.createTextNode(' — ရင်းမြစ်စစ်ဆေးရန် ကျန်သေးသည်'));list.append(li);}
  if(!list.children.length){const li=document.createElement('li');li.textContent='ရှာဖွေမှုရလဒ် မရှိသေးပါ။ နောက် workflow run မှာ ပြန်စစ်မည်။';list.append(li);}
 }catch{$('#kp-discovery').textContent='ရင်းမြစ်ရှာဖွေမှုရလဒ်ကို ဖတ်မရပါ။';}
}
load();setInterval(render,60000);
})();
