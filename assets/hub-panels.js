'use strict';
(function(){
const $=id=>document.getElementById(id);
function text(tag,value,className){const el=document.createElement(tag);el.textContent=String(value);if(className)el.className=className;return el;}
async function json(path){const response=await fetch(path,{cache:'no-store'});if(!response.ok)throw Error('unavailable');return response.json();}
function https(value){try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password?u:null;}catch{return null;}}
function bangkokTime(value){return new Date(value).toLocaleString('en-GB',{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',hour12:false,timeZone:'Asia/Bangkok'})+' (TH)';}
async function release(){const link=$('kp-apk-download'),status=$('kp-release-status');try{
 const r=await json('assets/app-release.json');const url=https(r.apk_url);
 if(r.version!=='0.2.0'||r.version_code!==2||!url||url.hostname!=='github.com'||url.pathname!=='/khantpyae332003/kp-ai-vpn/releases/download/v0.2.0/KP-VPN-0.2.0.apk'||url.search||url.hash||!/^[a-f0-9]{64}$/i.test(r.sha256)||!Number.isSafeInteger(r.size_bytes)||r.size_bytes<=0||r.size_bytes>100*1024*1024||!Number.isFinite(Date.parse(r.published_at)))throw Error('pending');
 link.href=url.href;link.removeAttribute('aria-disabled');link.textContent=r.signing_mode==='debug_preview'?'KP VPN 0.2.0 စမ်းသပ် APK ↓':'KP VPN 0.2.0 APK ယူမယ် ↓';link.setAttribute('download','KP-VPN-0.2.0.apk');
 status.textContent='v'+r.version+' · '+(r.size_bytes/1048576).toFixed(1)+' MB · '+(r.signing_mode==='debug_preview'?'စမ်းသပ် APK · ရှိပြီးသား app ကို update လုပ်နိုင်မည်ဟု မသတ်မှတ်ပါ။':'Android APK');
 const meta=$('kp-release-meta');for(const [label,value] of [['Version',r.version],['Published',bangkokTime(r.published_at)],['SHA-256',r.sha256]])meta.append(text('dt',label),text('dd',value));
 }catch{link.removeAttribute('href');link.setAttribute('aria-disabled','true');link.textContent='APK release ပြင်ဆင်နေဆဲ';status.textContent='စစ်ဆေးနိုင်သော release အချက်အလက် မရသေးပါ။ ခဏနေ ပြန်လာကြည့်ပါ။';}}
async function daily(){const box=$('kp-daily');try{const d=await json('catalog/daily.json');if(typeof d.title!=='string'||!Array.isArray(d.body)||!d.body.length||!d.body.every(x=>typeof x==='string')||!/^\d{4}-\d{2}-\d{2}$/.test(d.date)||!['curated','ai_reviewed'].includes(d.mode))throw Error();$('kp-daily-title').textContent=d.title;$('kp-daily-date').textContent=d.date+' · '+(d.mode==='curated'?'ရွေးချယ်ထားသော သင်ခန်းစာ':'AI အကူအညီဖြင့် ပြန်လည်စစ်ဆေးထား');box.replaceChildren(...d.body.slice(0,6).map(p=>text('p',p)));const url=https(d.source_url);if(url){const a=text('a','မူရင်း လမ်းညွှန် ↗','source-link');a.href=url.href;a.target='_blank';a.rel='noopener noreferrer';box.append(a);}}catch{box.replaceChildren(text('p','နေ့စဉ်စာစုကို လောလောဆယ် ဖတ်မရပါ။ အောက်က သုံးနည်းလမ်းညွှန်တွေကို ကြည့်နိုင်ပါတယ်။'));}}
const roleNames={finder:'Finder',verifier:'Verifier',classifier:'Classifier',publisher:'Publisher',daily:'Daily learning',health:'Health',security:'Security',integrity:'Integrity'};
const statusNames={pass:'အောင်မြင်',warning:'စစ်ရန်ရှိ',blocked:'ရပ်ထား',not_configured:'မသတ်မှတ်ရသေး'};
async function agents(){const box=$('kp-agents');let data;try{data=await json('catalog/agents.json');if(!Array.isArray(data.roles))throw Error();}catch{data={roles:[],ai:{configured:false}};}
 $('kp-ai-status').textContent=data.ai?.configured===true?'AI ချိတ်ဆက်မှု သတ်မှတ်ထားသည် · '+String(data.ai.mode||''):'AI မချိတ်ဆက်ရသေးပါ · သတ်မှတ်ထားသော စည်းမျဉ်းများအတိုင်း အလုပ်လုပ်သည်။';
 $('kp-agents-updated').textContent=Number.isFinite(Date.parse(data.updated_at))?'Update · '+bangkokTime(data.updated_at):'အလုပ်စဉ် အချက်အလက် မရသေးပါ။';
 let passed=0;for(const [id,name] of Object.entries(roleNames)){const role=data.roles.find(r=>r&&r.id===id);const status=role&&Object.hasOwn(statusNames,role.status)?role.status:'not_configured';if(status==='pass')passed++;const card=text('article','','agent-card');card.append(text('h3',name),text('span',statusNames[status],'agent-status status-'+status),text('p',typeof role?.detail==='string'?role.detail:'အခြေအနေ အချက်အလက် မရသေးပါ။'));box.append(card);}
 $('kp-agent-summary').textContent=passed+'/8 အောင်မြင်';
}
release();daily();agents();
})();
