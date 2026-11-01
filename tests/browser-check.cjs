const {chromium}=require('playwright');
const fs=require('node:fs');
const http=require('node:http');
const path=require('node:path');
(async()=>{
 const root=path.resolve('.');const server=http.createServer((req,res)=>{let p=path.join(root,new URL(req.url,'http://localhost').pathname);if(!p.startsWith(root+path.sep)&&p!==root){res.writeHead(403).end();return;}if(p===root+path.sep||p===root)p=path.join(root,'index.html');fs.readFile(p,(e,b)=>{if(e){res.writeHead(404).end();return;}res.setHeader('Content-Type',p.endsWith('.js')?'application/javascript':p.endsWith('.css')?'text/css':p.endsWith('.json')?'application/json':'text/html');res.end(b);});});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const url='http://127.0.0.1:'+server.address().port;
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const page=await browser.newPage({viewport:{width:390,height:844}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const checked=new Date().toISOString(),expires=new Date(Date.now()+3600000).toISOString();
 const common={server_status:'handshake_https_pass',checked_at:checked,expires_at:expires,sim:{status:'not_tested'}};
 const fixtures=[
  {...common,name:'<img src=x onerror=window.bad=1>',carrier:'dtac',plan:'nopro',source_url:'javascript:alert(1)',download:'javascript:alert(1)'},
  {...common,name:'dtac-standard.conf',carrier:'dtac',plan:'standard',source_url:'https://example.com/public.conf',download:'catalog/downloads/dtac/standard/dtac-standard-deadbeef.conf'},
  {...common,name:'true-nopro.conf',carrier:'true',plan:'nopro'},
  {...common,name:'expired.conf',carrier:'mpt',plan:'nopro',expires_at:new Date(Date.now()-3600000).toISOString()},
  {...common,name:'failed.conf',carrier:'ais',plan:'nopro',server_status:'failed'}
 ];
 await page.route('**/catalog/index.json',route=>route.fulfill({json:{updated_at:checked,files:fixtures}}));
 await page.goto(url);await page.waitForSelector('.kp-file');
 if(await page.locator('.kp-file').count()!==3)throw Error('Expired or failed files were displayed');
 if(await page.evaluate(()=>window.bad))throw Error('HTML executed');
 if(await page.locator('.kp-file').filter({hasText:'<img src=x'}).locator('a').count())throw Error('Unsafe link rendered');
 const download=page.locator('.kp-file').filter({hasText:'dtac-standard.conf'}).getByRole('link',{name:'ဖိုင်ယူမယ်'});
 if(await download.getAttribute('href')!=='catalog/downloads/dtac/standard/dtac-standard-deadbeef.conf'||await download.getAttribute('download')!=='dtac-standard.conf')throw Error('Valid download link missing or incorrect');
 await page.locator('[data-carrier="ais"]').click();if(await page.locator('.kp-file').count())throw Error('Wrong carrier filter');
 await page.locator('[data-carrier="dtac"]').click();if(await page.locator('.kp-file').count()!==2)throw Error('Missing dtac rows');
 await page.locator('#kp-plan').selectOption('nopro');if(await page.locator('.kp-file').count()!==1||await page.locator('.kp-file').filter({hasText:'dtac-standard.conf'}).count())throw Error('nopro plan filter failed');
 await page.locator('#kp-plan').selectOption('standard');if(await page.locator('.kp-file').count()!==1||!await download.count())throw Error('standard plan filter failed');
 await page.locator('#kp-file-search').fill('not-present');if(await page.locator('.kp-file').count())throw Error('Search failed');
 await page.unroute('**/catalog/index.json');await page.reload();await page.locator('#kp-empty').filter({hasText:'မရှိသေး'}).waitFor();
 await page.locator('#kp-catalog').scrollIntoViewIfNeeded();fs.mkdirSync('qa',{recursive:true});await page.screenshot({path:'qa/catalog-mobile.png',fullPage:true});
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Horizontal overflow');
 const guide=page.locator('.guide-card').first();
 if(await guide.getAttribute('open')!==null)throw Error('Guide should start collapsed');
 await guide.locator('summary').click();if(await guide.getAttribute('open')===null)throw Error('Guide did not open');
 await guide.locator('summary').click();
 await page.route('**/catalog/index.json',route=>route.fulfill({status:503,body:'unavailable'}));
 await page.locator('#kp-refresh').click();await page.getByRole('heading',{name:'ဖိုင်စာရင်း ဖတ်မရပါ'}).waitFor();
 await page.unroute('**/catalog/index.json');await page.locator('#kp-refresh').click();await page.locator('#kp-empty-title').filter({hasText:'မရှိသေး'}).waitFor();
 await page.locator('a[href="#verification"]').click();if(await page.locator('#verification').getAttribute('open')===null)throw Error('Verification anchor did not expand guide');
 await page.locator('#verification summary').click();
 await page.evaluate(()=>scrollTo(0,0));await page.setViewportSize({width:1280,height:900});await page.screenshot({path:'qa/catalog-desktop.png',fullPage:true});
 if(errors.length)throw Error(errors.join('\n'));
 console.log('PASS: carrier/plan filters, valid downloads, expired/failed suppression, search, inert untrusted data/URLs, mobile overflow, refresh recovery, collapsed guides, explanatory anchor, empty state');
 await browser.close();await new Promise(r=>server.close(r));
})().catch(e=>{console.error(e);process.exit(1);});
