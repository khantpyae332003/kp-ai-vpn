const test = require('node:test');
const assert = require('node:assert/strict');
let model;
try { model=require('../app/src/main/assets/model.js'); } catch { model={}; }
test('filter keeps only selected SIM and search matches Unicode names',()=>{
 assert.equal(typeof model.filterProfiles,'function');
 const rows=[{id:'a',name:'ရန်ကုန်',carrier:'MM',favorite:false},{id:'b',name:'Bangkok',carrier:'TH',favorite:true}];
 assert.deepEqual(model.filterProfiles(rows,'MM','ရန်',false).map(x=>x.id),['a']);
 assert.equal(model.filterProfiles(rows,'TH','ရန်',false).length,0);
});
test('favorites filter and sort never modify stored list',()=>{
 assert.equal(typeof model.filterProfiles,'function');
 const rows=[{id:'1',name:'Z',carrier:'TH',favorite:false},{id:'2',name:'A',carrier:'TH',favorite:true}];
 assert.deepEqual(model.filterProfiles(rows,'ALL','',true).map(x=>x.id),['2']);
 assert.equal(rows[0].id,'1');
});
test('a configured tunnel is not represented as verified internet',()=>{
 assert.equal(typeof model.statusLabel,'function');
 assert.equal(model.statusLabel('UP'),'Tunnel ဖွင့်ထားသည်');
 assert.equal(model.statusLabel('DOWN'),'မချိတ်ဆက်ထားပါ');
});
test('traffic display handles invalid inputs',()=>{
 assert.equal(typeof model.formatBytes,'function');
 assert.equal(model.formatBytes(1024),'1.0 KB');
 assert.equal(model.formatBytes(-1),'0 B');
 assert.equal(model.formatBytes(null),'0 B');
});
