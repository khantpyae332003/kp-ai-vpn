'use strict';
(function(){
const input=document.getElementById('kp-check-file');if(!input)return;
const output=document.getElementById('kp-check-result');let revision=0;
const reveal=()=>{document.querySelector('#check-config details').open=true;};
document.querySelectorAll('a[href="#check-config"]').forEach(a=>a.addEventListener('click',reveal));
if(location.hash==='#check-config')reveal();
function show(title,items=[]){output.replaceChildren();const p=document.createElement('p');p.textContent=title;output.append(p);if(items.length){const ul=document.createElement('ul');for(const text of items){const li=document.createElement('li');li.textContent=text;ul.append(li);}output.append(ul);}}
input.addEventListener('change',async()=>{
 const current=++revision,file=input.files?.[0];show('');if(!file)return;
 if(!/\.conf$/i.test(file.name)){show('WireGuard .conf တစ်ဖိုင်ကို ရွေးပါ။ ZIP ဖြစ်လျှင် အရင်ဖြည်ပါ။');return;}
 if(file.size>128*1024){show('ဖိုင်တစ်ဖိုင်ကို 128 KB အထိသာ စစ်နိုင်သည်။');return;}
 try{const text=await file.text();if(current!==revision)return;const result=KpConfigCheck.inspect(text);
  show(result.ok?(result.warnings.length?'အခြေခံစစ်ဆေးမှု အောင်သည်။ အောက်ကအချက်တွေကို ဆက်စစ်ပါ။':'အခြေခံ WireGuard ဖိုင်ပုံစံ စစ်ဆေးမှု အောင်သည်။'):'ဖိုင်ပြန်ပြင်ရန် လိုအပ်သည်။',[...result.errors,...result.warnings,'Server ချိတ်ဆက်မှု၊ key အစစ်နဲ့ SIM / nopro အလုပ်လုပ်မှုကို ဤစစ်ဆေးမှုက အတည်မပြုပါ။']);
 }catch{if(current===revision)show('ဖိုင်ကို ဖတ်မရပါ။ ဖုန်းထဲ ပြန်သိမ်းပြီး ပြန်ရွေးပါ။');}
});
document.getElementById('kp-check-clear').addEventListener('click',()=>{revision++;input.value='';show('ရွေးထားသောဖိုင်နဲ့ ရလဒ်ကို ရှင်းပြီးပြီ။ ဖုန်းထဲက မူရင်းဖိုင်ကို မဖျက်ပါ။');});
})();
