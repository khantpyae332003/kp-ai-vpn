'use strict';
(function(){
const form=document.getElementById('kp-builder-form');if(!form)return;
const $=id=>document.getElementById(id);let keys=null;
function status(text){$('kp-builder-status').textContent=text;}
$('kp-generate-keys').addEventListener('click',async()=>{
 const button=$('kp-generate-keys');button.disabled=true;
 try{keys=await KpConfig.generateKeys();$('kp-client-public').value=keys.publicKey;$('kp-copy-public').disabled=false;$('kp-export-config').disabled=false;$('kp-key-status').textContent='Client PublicKey ကို server မှာ မှတ်ပုံတင်ပါ။ PrivateKey က ဒီ browser memory ထဲမှာပဲ ရှိသည်။';status('Server အချက်အလက် ဖြည့်ပြီး .conf ဖိုင်ကို ဖုန်းထဲသိမ်းပါ။');}
 catch{keys=null;$('kp-client-public').value='';$('kp-copy-public').disabled=true;$('kp-export-config').disabled=true;$('kp-key-status').textContent='ဒီ browser က X25519 key မထုတ်နိုင်ပါ။ HTTPS နဲ့ browser အသစ်ကိုသုံးပါ၊ သို့မဟုတ် provider မှ ဖိုင်ယူပါ။';}
 finally{button.disabled=false;}
});
$('kp-copy-public').addEventListener('click',async()=>{try{await navigator.clipboard.writeText($('kp-client-public').value);$('kp-key-status').textContent='PublicKey ကူးပြီးပြီ။ Server ရဲ့ [Peer] PublicKey မှာ ထည့်ပါ။';}catch{$('kp-client-public').focus();$('kp-client-public').select();$('kp-key-status').textContent='PublicKey ကို ဖိထားပြီး ကိုယ်တိုင် ကူးပါ။';}});
$('kp-clear-keys').addEventListener('click',()=>{keys=null;$('kp-client-public').value='';$('kp-copy-public').disabled=true;$('kp-export-config').disabled=true;form.reset();$('kp-key-status').textContent='ဒီစာမျက်နှာထဲက key ရှင်းပြီးပြီ။ သိမ်းထားသော .conf ဖိုင်ကို မဖျက်ပါ။';status('Key အသစ်ထုတ်ပြီး ပြန်စနိုင်သည်။');});
form.addEventListener('submit',e=>{
 e.preventDefault();if(!keys){status('Client key ကို အရင်ထုတ်ပါ။');return;}
 try{
  const result=KpConfig.buildConfig({...keys,carrier:$('kp-builder-carrier').value,address:$('kp-builder-address').value.trim(),endpoint:$('kp-builder-endpoint').value.trim(),dns:$('kp-builder-dns').value.trim(),serverPublicKey:$('kp-builder-server-key').value.trim(),presharedKey:$('kp-builder-psk').value.trim()});
  const blob=new Blob([result.text],{type:'application/octet-stream'});const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=result.filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  status('ဖိုင်သိမ်းပြီးလျှင် KP VPN ထဲ import လုပ်ပါ။ Server မှာ client PublicKey မှတ်ပုံတင်ထားပြီးမှ ချိတ်ဆက်စမ်းပါ။');
 }catch(error){status(error.message);}
});
document.querySelectorAll('a[href="#make-config"]').forEach(a=>a.addEventListener('click',()=>{$('own-config-details').open=true;}));
})();
