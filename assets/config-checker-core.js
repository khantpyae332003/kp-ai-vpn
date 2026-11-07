(function(root){'use strict';
function ip(value){
 if(value.includes(':')){try{return new URL('http://['+value+']/').hostname.startsWith('[');}catch{return false;}}
 const parts=value.split('.');return parts.length===4&&parts.every(p=>/^\d{1,3}$/.test(p)&&String(Number(p))===p&&Number(p)<=255);
}
function cidr(value){const parts=value.split('/');return parts.length===2&&ip(parts[0])&&/^\d{1,3}$/.test(parts[1])&&Number(parts[1])<=(parts[0].includes(':')?128:32);}
function key(value){try{return /^[A-Za-z0-9+/]{43}=$/.test(value)&&btoa(atob(value))===value&&atob(value).length===32&&[...atob(value)].some(c=>c.charCodeAt(0)!==0);}catch{return false;}}
function host(value){return ip(value)||/^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/i.test(value)&&!/^\d+(?:\.\d+)*$/.test(value);}
function endpoint(value){const m=/^(?:\[([^\]]+)\]|([^:\s]+)):(\d{1,5})$/.exec(value);return !!m&&Number(m[3])>0&&Number(m[3])<=65535&&(m[1]?m[1].includes(':')&&ip(m[1]):host(m[2]));}
function inspect(text){
 const errors=[],warnings=[];const error=s=>{if(!errors.includes(s))errors.push(s);};const warn=s=>{if(!warnings.includes(s))warnings.push(s);};
 if(typeof text!=='string'||new TextEncoder().encode(text).length>128*1024)return {ok:false,errors:['ဖိုင်တစ်ဖိုင်ကို 128 KB အထိသာ စစ်နိုင်သည်။'],warnings};
 let section=null,interfaces=0;const peers=[];let iface={};
 const lists=new Set(['Address','DNS','AllowedIPs']);
 const allowed={Interface:new Set(['PrivateKey','Address','DNS','MTU','ListenPort','IncludedApplications','ExcludedApplications']),Peer:new Set(['PublicKey','PresharedKey','Endpoint','AllowedIPs','PersistentKeepalive'])};
 for(const raw of text.replace(/^\uFEFF/,'').split(/\r?\n/)){
  const line=raw.split('#',1)[0].trim();if(!line)continue;
  if(line==='[Interface]'){interfaces++;section={kind:'Interface',values:iface};continue;}
  if(line==='[Peer]'){const values={};peers.push(values);section={kind:'Peer',values};continue;}
  const m=/^([A-Za-z][A-Za-z0-9]*)\s*=\s*(.+)$/.exec(line);
  if(!m||!section){error('Section သို့မဟုတ် key = value ဖိုင်ပုံစံ မမှန်ပါ။');continue;}
  const field=m[1],value=m[2].trim();
  if(/^(PreUp|PostUp|PreDown|PostDown|SaveConfig|Table)$/i.test(field)){error('Server / wg-quick ဆိုင်ရာ directive ပါနေသည်။ Android client ဖိုင်ကို ပြန်ယူပါ။');continue;}
  if(!allowed[section.kind].has(field)){if(allowed.Interface.has(field)||allowed.Peer.has(field)){error('Key သတ်မှတ်ချက်သည် section နေရာမှားနေသည်။');continue;}warn('မသိသော directive ပါသည်။ Provider ရဲ့ Android WireGuard ဖိုင်နဲ့ ပြန်တိုက်စစ်ပါ။');continue;}
  if(Object.hasOwn(section.values,field)&&!lists.has(field)){error('ထပ်နေသော key သတ်မှတ်ချက် ရှိသည်။');continue;}
  section.values[field]=Object.hasOwn(section.values,field)?section.values[field]+', '+value:value;
 }
 if(interfaces!==1)error('[Interface] တစ်ခုတိတိ ပါရမည်။');
 if(!key(iface.PrivateKey||''))error('Client PrivateKey မပါ သို့မဟုတ် key ပုံစံမမှန်ပါ။');
 const values=s=>String(s||'').split(',').map(x=>x.trim());
 if(!iface.Address||values(iface.Address).some(x=>!cidr(x)))error('Client Address / CIDR မပါ သို့မဟုတ် မမှန်ပါ။');
 if(iface.DNS&&values(iface.DNS).some(x=>!host(x)))error('DNS လိပ်စာ ပုံစံမမှန်ပါ။');
 for(const field of ['MTU','ListenPort'])if(iface[field]&&(!/^\d+$/.test(iface[field])||Number(iface[field])>65535||(field==='MTU'&&Number(iface[field])<1)))error('MTU / ListenPort ကိန်းဂဏန်း မမှန်ပါ။');
 if(iface.IncludedApplications&&iface.ExcludedApplications)error('IncludedApplications နဲ့ ExcludedApplications ကို တစ်ပြိုင်နက် မသုံးနိုင်ပါ။');
 if(!peers.length)error('[Peer] အနည်းဆုံးတစ်ခု ပါရမည်။');
 for(const p of peers){
  if(!key(p.PublicKey||''))error('Peer PublicKey မပါ သို့မဟုတ် key ပုံစံမမှန်ပါ။');
  if(p.PresharedKey&&!key(p.PresharedKey))error('PresharedKey ပုံစံမမှန်ပါ။');
  if(!endpoint(p.Endpoint||''))error('Peer Endpoint ကို host:port ပုံစံ မှန်မှန်ဖြည့်ရမည်။');
  if(!p.AllowedIPs||values(p.AllowedIPs).some(x=>!cidr(x)))error('AllowedIPs / CIDR မပါ သို့မဟုတ် မမှန်ပါ။');
  if(p.PersistentKeepalive&&(!/^\d+$/.test(p.PersistentKeepalive)||Number(p.PersistentKeepalive)>65535))error('PersistentKeepalive ကိန်းဂဏန်း မမှန်ပါ။');
 }
 if(peers.length&&!peers.some(p=>values(p.AllowedIPs).includes('0.0.0.0/0')))warn('IPv4 traffic အားလုံးကို VPN ထဲ ပို့ထားခြင်း မဟုတ်ပါ။ Split tunnel ဖြစ်နိုင်သည်။');
 return {ok:errors.length===0,errors,warnings};
}
const api={inspect};if(typeof module!=='undefined')module.exports=api;else root.KpConfigCheck=api;
})(typeof window!=='undefined'?window:globalThis);
