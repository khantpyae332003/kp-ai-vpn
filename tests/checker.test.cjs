const test=require('node:test');const assert=require('node:assert/strict');
const C=require('../assets/config-checker-core.js');
const key=Buffer.alloc(32,7).toString('base64');
const config=`[Interface]\nPrivateKey = ${key}\nAddress = 10.8.0.2/32\nDNS = 1.1.1.1\n[Peer]\nPublicKey = ${key}\nEndpoint = vpn.test.net:51820\nAllowedIPs = 0.0.0.0/0, ::/0\nPersistentKeepalive = 25\n`;
test('accepts common full tunnel and bracketed IPv6 endpoint without revealing credentials',()=>{
 for(const body of [config,config.replace('vpn.test.net:51820','[2001:db8::1]:51820')]){
  const result=C.inspect(body);assert.equal(result.ok,true);assert.doesNotMatch(JSON.stringify(result),new RegExp(key));
 }
});
test('missing keys, bad ports, bad addresses and malformed sections fail basic checks',()=>{
 for(const body of [config.replace('PrivateKey = '+key,''),config.replace('51820','99999'),config.replace('10.8.0.2/32','999.8.0.2/32'),config.replace('[Peer]','[Other]'),config.replace(key,'bad'),config+'PrivateKey = '+key])assert.equal(C.inspect(body).ok,false);
});
test('rejects shell hooks and oversized configs without reflecting their contents',()=>{
 const secret='PRIVATE_SECRET_DO_NOT_REFLECT';
 for(const body of [config+'PostUp = '+secret,'x'.repeat(128*1024+1)]){
  const result=C.inspect(body);assert.equal(result.ok,false);assert.ok(!JSON.stringify(result).includes(secret));
 }
});
test('unknown directives and split routes require review rather than claiming a full pass',()=>{
 for(const body of [config.replace('DNS = 1.1.1.1','Mystery = sensitive'),config.replace('0.0.0.0/0, ::/0','10.0.0.0/8')]){
  const result=C.inspect(body);assert.equal(result.ok,true);assert.ok(result.warnings.length>0);
 }
});
test('allows separate peers but validates each peer and rejects duplicate singleton fields',()=>{
 assert.equal(C.inspect(config+'\n[Peer]\nPublicKey = '+key+'\nEndpoint = 8.8.8.8:123\nAllowedIPs = 192.168.0.0/16').ok,true);
 assert.equal(C.inspect(config+'\n[Peer]\nAllowedIPs = 0.0.0.0/0').ok,false);
 assert.equal(C.inspect(config.replace('Address =','PrivateKey = '+key+'\nAddress =')).ok,false);
});
