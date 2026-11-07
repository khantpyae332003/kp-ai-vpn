const {chromium}=require('playwright');const fs=require('node:fs');
(async()=>{
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const page=await browser.newPage({viewport:{width:390,height:844}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('https://khantpyae332003.github.io/kp-ai-vpn/',{waitUntil:'networkidle'});
await page.locator('#kp-catalog').waitFor();if(!/KP VPN/.test(await page.title()))throw Error('Website title mismatch');
if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile horizontal overflow');
fs.mkdirSync('watch-qa',{recursive:true});await page.screenshot({path:'watch-qa/live-mobile.png',fullPage:true});
await page.setViewportSize({width:1280,height:900});await page.screenshot({path:'watch-qa/live-desktop.png',fullPage:true});
if(errors.length)throw Error('Public page JavaScript error');await browser.close();console.log('PASS: public mobile/desktop website rendered without JavaScript errors');
})().catch(e=>{console.error(e.message);process.exit(1);});
