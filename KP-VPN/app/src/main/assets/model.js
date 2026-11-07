(function(root){
 'use strict';
 const api={
  filterProfiles(rows,carrier,query,favorites){
   const q=String(query||'').trim().toLocaleLowerCase();
   return rows.filter(p=>(carrier==='ALL'||p.carrier===carrier)&&(!favorites||p.favorite)&&(!q||String(p.name).toLocaleLowerCase().includes(q))).slice().sort((a,b)=>Number(b.favorite)-Number(a.favorite)||a.name.localeCompare(b.name));
  },
  statusLabel(s){return s==='UP'?'Tunnel ဖွင့်ထားသည်':s==='STARTING'?'ချိတ်ဆက်နေသည်…':s==='STOPPING'?'ဖြုတ်နေသည်…':'မချိတ်ဆက်ထားပါ';},
  formatBytes(n){n=Number(n);if(!Number.isFinite(n)||n<=0)return '0 B'; const u=['B','KB','MB','GB'];let i=0;while(n>=1024&&i<3){n/=1024;i++;}return (i?n.toFixed(1):Math.round(n))+' '+u[i];}
 };
 if(typeof module!=='undefined')module.exports=api;else root.Model=api;
})(typeof window!=='undefined'?window:globalThis);
