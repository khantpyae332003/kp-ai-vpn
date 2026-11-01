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
  {...common,name:'public-archive.conf',carrier:'other',plan:'standard',download_kind:'source_archive',archive_member:'US/public-archive.conf',download:'https://raw.githubusercontent.com/owner/repo/'+('a'.repeat(40))+'/bundle.zip',permission_url:'https://github.com/owner/repo/blob/main/README.md'},
  {...common,name:'expired.conf',carrier:'mpt',plan:'nopro',expires_at:new Date(Date.now()-3600000).toISOString()},
  {...common,name:'failed.conf',carrier:'ais',plan:'nopro',server_status:'failed'}
 ];
 await page.route('**/catalog/index.json',route=>route.fulfill({json:{updated_at:checked,files:fixtures}}));
 await page.clock.install();await page.goto(url);await page.waitForSelector('.kp-file');
 if(await page.locator('.kp-file').count()!==4)throw Error('Expired or failed files were displayed');
 if(await page.evaluate(()=>window.bad))throw Error('HTML executed');
 if(await page.locator('.kp-file').filter({hasText:'<img src=x'}).locator('a').count())throw Error('Unsafe link rendered');
 const download=page.locator('.kp-file').filter({hasText:'dtac-standard.conf'}).getByRole('link',{name:'ဖိုင်ယူမယ်'});
 if(await download.getAttribute('href')!=='catalog/downloads/dtac/standard/dtac-standard-deadbeef.conf'||await download.getAttribute('download')!=='dtac-standard.conf')throw Error('Valid download link missing or incorrect');
 await page.locator('[data-carrier="ais"]').click();if(await page.locator('.kp-file').count())throw Error('Wrong carrier filter');
 await page.locator('[data-carrier="dtac"]').click();if(await page.locator('.kp-file').count()!==2)throw Error('Missing dtac rows');
 await page.locator('#kp-plan').selectOption('nopro');if(await page.locator('.kp-file').count()!==1||await page.locator('.kp-file').filter({hasText:'dtac-standard.conf'}).count())throw Error('nopro plan filter failed');
 await page.locator('#kp-plan').selectOption('standard');if(await page.locator('.kp-file').count()!==1||!await download.count())throw Error('standard plan filter failed');
 await page.locator('#kp-file-search').fill('not-present');if(await page.locator('.kp-file').count())throw Error('Search failed');
 await page.locator('#kp-reset').click();
 if(await page.locator('.kp-file').count()!==4||await page.locator('#kp-file-search').inputValue()!==''||await page.locator('#kp-plan').inputValue()!=='all')throw Error('Reset did not restore all files');
 await page.context().grantPermissions(['clipboard-read','clipboard-write']);
 await page.locator('.kp-file').filter({hasText:'public-archive.conf'}).getByRole('button',{name:'ဖိုင်နာမည် ကူးမယ်'}).click();
 if(await page.evaluate(()=>navigator.clipboard.readText())!=='US/public-archive.conf')throw Error('Archive name clipboard mismatch');
 await page.unroute('**/catalog/index.json');await page.route('**/catalog/index.json',route=>route.fulfill({json:{updated_at:new Date(Date.now()-3*3600000).toISOString(),files:fixtures}}));
 await page.locator('#kp-refresh').click();await page.locator('#kp-health.is-stale').waitFor();
 await page.unroute('**/catalog/index.json');let automaticReads=0;await page.route('**/catalog/index.json',route=>{automaticReads++;return route.fulfill({json:{updated_at:new Date().toISOString(),files:fixtures}});});
 await page.locator('.kp-file').filter({hasText:'public-archive.conf'}).getByRole('button').focus();
 await page.clock.fastForward(5*60000);await page.waitForFunction(()=>!document.querySelector('#kp-health').classList.contains('is-stale'));
 if(!automaticReads)throw Error('Automatic catalog refresh did not fetch');
 if(!await page.locator('.kp-file').filter({hasText:'public-archive.conf'}).getByRole('button').evaluate(el=>el===document.activeElement))throw Error('Unchanged background refresh lost action focus');
 await page.unroute('**/catalog/index.json');await page.route('**/catalog/index.json',route=>route.fulfill({json:{updated_at:checked,files:[]}}));await page.reload();await page.locator('#kp-empty').filter({hasText:'မရှိသေး'}).waitFor();
 await page.locator('#kp-catalog').scrollIntoViewIfNeeded();fs.mkdirSync('qa',{recursive:true});await page.screenshot({path:'qa/catalog-mobile.png',fullPage:true});
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Horizontal overflow');
 const guide=page.locator('.guide-card').first();
 if(await guide.getAttribute('open')!==null)throw Error('Guide should start collapsed');
 await guide.locator('summary').click();if(await guide.getAttribute('open')===null)throw Error('Guide did not open');
 await guide.locator('summary').click();
 await page.route('**/catalog/index.json',route=>route.fulfill({status:503,body:'unavailable'}));
 await page.locator('#kp-refresh').click();await page.getByRole('heading',{name:'ဖိုင်စာရင်း ဖတ်မရပါ'}).waitFor();
 await page.unroute('**/catalog/index.json');await page.route('**/catalog/index.json',route=>route.fulfill({json:{updated_at:checked,files:[]}}));await page.locator('#kp-refresh').click();await page.locator('#kp-empty-title').filter({hasText:'မရှိသေး'}).waitFor();
 await page.locator('a[href="#verification"]').click();if(await page.locator('#verification').getAttribute('open')===null)throw Error('Verification anchor did not expand guide');
 await page.locator('#verification summary').click();
 await page.locator('.site-header a[href="#make-config"]').click();
 if(await page.locator('#own-config-details').getAttribute('open')===null)throw Error('Builder navigation did not open');
 const requests=[];page.on('request',r=>requests.push(r.url()+' '+(r.postData()||'')));
 await page.locator('#kp-generate-keys').click();await page.waitForFunction(()=>document.getElementById('kp-client-public').value.length===44);
 await page.locator('#kp-builder-endpoint').fill('8.8.8.8:51820');
 await page.locator('#kp-builder-server-key').fill(Buffer.from(Array.from({length:32},(_,i)=>i+1)).toString('base64'));
 const got=page.waitForEvent('download');await page.locator('#kp-export-config').click();const file=await got;
 if(file.suggestedFilename()!=='dtac-personal.conf')throw Error('Wrong config filename');
 const body=fs.readFileSync(await file.path(),'utf8');if(!body.includes('[Interface]')||!body.includes('Endpoint = 8.8.8.8:51820'))throw Error('Bad exported config');
 const secret=/PrivateKey = ([^\n]+)/.exec(body)?.[1];if(!secret||requests.some(r=>r.includes(secret)))throw Error('Private key sent over network');
 await page.locator('#kp-clear-keys').click();if(await page.locator('#kp-client-public').inputValue()!==''||!await page.locator('#kp-export-config').isDisabled())throw Error('Key clear failed');
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Builder horizontal overflow');
 await page.screenshot({path:'qa/config-builder-mobile.png',fullPage:true});
 await page.unroute('**/catalog/index.json');await page.reload();await page.waitForFunction(()=>document.getElementById('kp-total').textContent!=='—');
 await page.screenshot({path:'qa/catalog-mobile.png',fullPage:true});
 await page.evaluate(()=>scrollTo(0,0));await page.setViewportSize({width:1280,height:900});await page.screenshot({path:'qa/catalog-desktop.png',fullPage:true});
 if(errors.length)throw Error(errors.join('\n'));
 console.log('PASS: carrier/plan filters, valid downloads, expired/failed suppression, search, inert untrusted data/URLs, mobile overflow, refresh recovery, collapsed guides, explanatory anchor, empty state');
 await browser.close();await new Promise(r=>server.close(r));
})().catch(e=>{console.error(e);process.exit(1);});
