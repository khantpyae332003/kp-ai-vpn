'use strict';
const $=id=>document.getElementById(id);
let state={profiles:[],state:'DOWN',activeId:'',ready:true,rx:0,tx:0,error:''},selected='',country='ALL',favorites=false,limit=30,messageTimer;
function action(name,payload={}){if(window.Native){Native.action(name,JSON.stringify(payload));}else{showMessage('ဒီမျက်နှာပြင်သည် preview ဖြစ်သည်။ VPN သုံးရန် Android APK လိုအပ်သည်။');}}
window.showMessage=function(text){$('message').textContent=text;$('message').hidden=false;clearTimeout(messageTimer);messageTimer=setTimeout(()=>$('message').hidden=true,6500);};
window.receive=function(next){state=next;if(next.activeId)selected=next.activeId;if(!next.profiles.some(p=>p.id===selected))selected=next.profiles[0]?.id||'';render();};
function tags(){const [carrier,operator]=$('group').value.split('|');return {carrier,operator};}
function render(){
 const busy=(state.state==='STARTING'||state.state==='STOPPING'),up=state.state==='UP';
 $('status').textContent=Model.statusLabel(state.state);
 $('dot').style.background=up?'#4de0b5':busy?'#efc46f':'#8998ac';
 $('power').classList.toggle('connected',up);$('power').disabled=busy||(!up&&!selected)||!state.ready;
 $('power').setAttribute('aria-label',up?'VPN ဖြုတ်မယ်':'VPN ချိတ်ဆက်မယ်');
 $('selectedName').textContent=state.profiles.find(p=>p.id===selected)?.name||'Config တစ်ခု ရွေးပါ';
 $('connectionHint').textContent=state.error||(up?'Tunnel ဖွင့်ထားခြင်းသည် server အလုပ်လုပ်မှု အာမခံချက်မဟုတ်ပါ။':'အလုပ်လုပ်တဲ့ WireGuard server config လိုအပ်သည်။');
 $('rx').textContent=Model.formatBytes(state.rx);$('tx').textContent=Model.formatBytes(state.tx);$('count').textContent=state.profiles.length;
 $('add').disabled=!state.ready;
 const rows=Model.filterProfiles(state.profiles,country,$('search').value,favorites);
 $('profiles').replaceChildren();
 rows.slice(0,limit).forEach(p=>{
  const row=document.createElement('div');row.className='profile'+(p.id===selected?' selected':'');
  const choose=document.createElement('button');choose.className='choose';choose.disabled=busy||up;
  const name=document.createElement('span');name.className='name';name.textContent=p.name;
  const tag=document.createElement('span');tag.className='tag';tag.textContent=(p.carrier==='TH'?'🇹🇭 ထိုင်း':p.carrier==='MM'?'🇲🇲 မြန်မာ':'အခြား')+(p.operator?' · '+p.operator:'')+' · WireGuard';choose.append(name,tag);choose.addEventListener('click',()=>{selected=p.id;render();});
  const star=document.createElement('button');star.className='star';star.textContent=p.favorite?'★':'☆';star.setAttribute('aria-label',p.favorite?'အကြိုက်ဆုံးမှ ဖယ်ရန်':'အကြိုက်ဆုံး ထည့်ရန်');star.addEventListener('click',()=>action('favorite',{id:p.id}));
  const del=document.createElement('button');del.className='delete';del.textContent='×';del.setAttribute('aria-label',p.name+' ဖျက်ရန်');del.disabled=up||busy;del.addEventListener('click',()=>action('delete',{id:p.id}));row.append(choose,star,del);$('profiles').append(row);
 });
 $('empty').hidden=rows.length>0;$('more').hidden=rows.length<=limit;
 if(!rows.length){$('empty').querySelector('h3').textContent=state.profiles.length?'ကိုက်ညီသော config မရှိပါ':'သင့် config ကို ထည့်ပါ';}
}
$('power').addEventListener('click',()=>action(state.state==='UP'?'disconnect':'connect',{id:selected}));
$('add').addEventListener('click',()=>$('importDialog').showModal());$('closeDialog').addEventListener('click',()=>$('importDialog').close());
$('scan').addEventListener('click',()=>{action('scan',tags());$('importDialog').close();});
$('files').addEventListener('click',()=>{action('files',tags());$('importDialog').close();});
$('save').addEventListener('click',()=>{
 const text=$('configText').value.trim();if(!text){showMessage('Config စာသားကို အရင်ထည့်ပါ။');return;}
 action('importText',{...tags(),name:$('profileName').value.trim()||'WireGuard',text});$('configText').value='';$('importDialog').close();
});
document.querySelectorAll('[data-country]').forEach(b=>b.addEventListener('click',()=>{country=b.dataset.country;limit=30;document.querySelectorAll('[data-country]').forEach(x=>x.classList.toggle('chosen',x===b));render();}));
$('favorites').addEventListener('click',()=>{favorites=!favorites;limit=30;$('favorites').setAttribute('aria-pressed',String(favorites));$('favorites').textContent=favorites?'★':'☆';render();});
$('search').addEventListener('input',()=>{limit=30;render();});$('more').addEventListener('click',()=>{limit+=30;render();});
render();
