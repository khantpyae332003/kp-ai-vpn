const test=require('node:test');const assert=require('node:assert/strict');const crypto=require('node:crypto');
let B={};try{B=require('../assets/config-builder-core.js');}catch{}
const serverKey=Buffer.from(Array.from({length:32},(_,i)=>i+1)).toString('base64');
function data(keys){return {carrier:'dtac',endpoint:'8.8.8.8:51820',address:'10.8.0.2/32',dns:'1.1.1.1',serverPublicKey:serverKey,...keys};}
test('generated WireGuard keys match an independent X25519 public-key derivation',async()=>{
 assert.equal(typeof B.generateKeys,'function');const keys=await B.generateKeys(crypto.webcrypto);
 assert.equal(Buffer.from(keys.privateKey,'base64').length,32);assert.equal(Buffer.from(keys.publicKey,'base64').length,32);
 const privateDer=Buffer.concat([Buffer.from('302e020100300506032b656e04220420','hex'),Buffer.from(keys.privateKey,'base64')]);
 const pub=crypto.createPublicKey(crypto.createPrivateKey({key:privateDer,format:'der',type:'pkcs8'})).export({type:'spki',format:'der'}).subarray(-32);
 assert.equal(keys.publicKey,pub.toString('base64'));assert.notEqual((await B.generateKeys(crypto.webcrypto)).privateKey,keys.privateKey);
});
test('export builds real WireGuard fields and a carrier label without a nopro claim',async()=>{
 assert.equal(typeof B.buildConfig,'function');const keys=await B.generateKeys(crypto.webcrypto);const result=B.buildConfig(data(keys));
 assert.equal(result.filename,'dtac-personal.conf');assert.match(result.text,/\[Interface\]/);assert.ok(result.text.includes('PrivateKey = '+keys.privateKey));assert.ok(result.text.includes('PublicKey = '+serverKey));assert.match(result.text,/AllowedIPs = 0.0.0.0\/0, ::\/0/);assert.doesNotMatch(result.text,/nopro/);
});
test('invalid keys, fake example endpoints and injected directives never produce a file',async()=>{
 assert.equal(typeof B.buildConfig,'function');const keys=await B.generateKeys(crypto.webcrypto);
 for(const patch of [{serverPublicKey:'bad'},{endpoint:'vpn.example.com:51820'},{endpoint:'192.0.2.1:51820'},{endpoint:'8.8.8.8:51820\nPostUp = bad'},{address:'10.8.0.2/99'},{dns:'1.1.1.1\nPostUp=bad'},{carrier:'../../bad'}])assert.throws(()=>B.buildConfig({...data(keys),...patch}));
});
