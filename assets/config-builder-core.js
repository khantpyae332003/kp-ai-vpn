(function(root){'use strict';
const carriers=new Set(['dtac','true','ais','mpt','atom','mytel','other']);
function base64(bytes){return btoa(String.fromCharCode(...bytes));}
function decode(text){try{if(!/^[A-Za-z0-9+/]{43}=$/.test(text))throw Error();const bytes=Uint8Array.from(atob(text),c=>c.charCodeAt(0));if(bytes.length!==32||!bytes.some(x=>x))throw Error();return bytes;}catch{throw Error('Key သည် base64 32-byte WireGuard key ဖြစ်ရမည်။');}}
function ipv4(text){const a=text.split('.');return a.length===4&&a.every(x=>/^\d{1,3}$/.test(x)&&String(Number(x))===x&&Number(x)<=255);}
async function generateKeys(provider=root.crypto){
 if(!provider?.subtle)throw Error('HTTPS နဲ့ WebCrypto ပါသော browser လိုအပ်သည်။');
 const pair=await provider.subtle.generateKey({name:'X25519'},true,['deriveBits']);
 const jwk=await provider.subtle.exportKey('jwk',pair.privateKey);
 const encoded=jwk.d.replace(/-/g,'+').replace(/_/g,'/');const raw=Uint8Array.from(atob(encoded+'='.repeat((4-encoded.length%4)%4)),c=>c.charCodeAt(0));
 raw[0]&=248;raw[31]&=127;raw[31]|=64;
 const pub=new Uint8Array(await provider.subtle.exportKey('raw',pair.publicKey));
 return {privateKey:base64(raw),publicKey:base64(pub)};
}
function buildConfig(s){
 if(!carriers.has(s.carrier))throw Error('SIM အမျိုးအစား ရွေးပါ။');
 decode(s.privateKey||'');decode(s.publicKey||'');decode(s.serverPublicKey||'');
 if(s.publicKey===s.serverPublicKey)throw Error('Server နဲ့ client public key သီးခြားဖြစ်ရမည်။');
 if(s.presharedKey)decode(s.presharedKey);
 const endpoint=String(s.endpoint||'').trim();const match=/^([A-Za-z0-9.-]+):(\d{1,5})$/.exec(endpoint);
 if(!match||Number(match[2])<1||Number(match[2])>65535)throw Error('Endpoint ကို server-IP:port ပုံစံ ဖြည့်ပါ။');
 const host=match[1].toLowerCase();
 if(ipv4(host)){
  const a=host.split('.').map(Number);
  if(a[0]===0||a[0]===10||a[0]===127||a[0]>=224||(a[0]===169&&a[1]===254)||(a[0]===172&&a[1]>=16&&a[1]<=31)||(a[0]===192&&a[1]===168)||(a[0]===192&&a[1]===0&&a[2]===2)||(a[0]===198&&a[1]===51&&a[2]===100)||(a[0]===203&&a[1]===0&&a[2]===113))throw Error('ကိုယ့် server ရဲ့ public IPv4 အစစ်ကို ဖြည့်ပါ။');
 }else if(!/^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/.test(host)||host==='example.com'||host.endsWith('.example.com')||host==='example.net'||host==='example.org'||host.endsWith('.local')||host.endsWith('.invalid'))throw Error('ကိုယ့် server ရဲ့ DNS နာမည်အစစ်ကို ဖြည့်ပါ။');
 const address=String(s.address||'').trim();const a=/^([^/]+)\/(\d{1,2})$/.exec(address);
 if(!a||!ipv4(a[1])||Number(a[2])<1||Number(a[2])>32)throw Error('Client IPv4/CIDR မှန်မှန်ဖြည့်ပါ။ ဥပမာ 10.8.0.2/32');
 const dns=String(s.dns||'').trim().split(',').map(x=>x.trim());if(!dns.length||dns.length>4||dns.some(x=>!ipv4(x)))throw Error('DNS IPv4 မှန်မှန်ဖြည့်ပါ။');
 const text='# KP VPN personal configuration; server not verified\n# SIM label: '+s.carrier+' (organization only)\n[Interface]\nPrivateKey = '+s.privateKey+'\nAddress = '+address+'\nDNS = '+dns.join(', ')+'\n\n[Peer]\nPublicKey = '+s.serverPublicKey+'\n'+(s.presharedKey?'PresharedKey = '+s.presharedKey+'\n':'')+'Endpoint = '+endpoint+'\nAllowedIPs = 0.0.0.0/0, ::/0\nPersistentKeepalive = 25\n';
 return {filename:s.carrier+'-personal.conf',text};
}
const api={generateKeys,buildConfig};if(typeof module!=='undefined')module.exports=api;else root.KpConfig=api;
})(typeof window!=='undefined'?window:globalThis);
