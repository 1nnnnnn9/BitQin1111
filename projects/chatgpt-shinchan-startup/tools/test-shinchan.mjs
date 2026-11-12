import {createRequire} from 'node:module';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {resolve,extname,sep} from 'node:path';
import {createServer} from 'node:http';
import assert from 'node:assert/strict';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.PLAYWRIGHT_PACKAGE||'playwright');
const output=resolve(process.argv[2]||'.build/visual-qa');await mkdir(output,{recursive:true});
const root=resolve('.');
const server=createServer(async(req,res)=>{try{const name=decodeURIComponent(new URL(req.url,'http://local/').pathname);const file=resolve(root,'.'+name);if(!file.startsWith(root+sep)){res.writeHead(403);res.end();return;}const mime={'.html':'text/html','.js':'application/javascript','.css':'text/css','.png':'image/png','.jpg':'image/jpeg'};res.setHeader('Content-Type',mime[extname(file)]||'application/octet-stream');res.end(await readFile(file));}catch{res.writeHead(404);res.end();}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
try{
 const page=await browser.newPage({viewport:{width:960,height:540},reducedMotion:'no-preference'});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.addInitScript(()=>{window.AEMEATH_PREWARM=true;window.__messages=[];window.chrome.webview={postMessage:message=>window.__messages.push(message)};});
 await page.goto(`http://127.0.0.1:${server.address().port}/index.html`);
 await page.waitForFunction(()=>window.__messages.includes('ready'),{timeout:20000});
 for(const [time,stage]of [[2.5,'identity'],[4.5,'dispersing'],[6.3,'drawing'],[8.5,'portrait']]){
  await page.locator('#timeline').evaluate((el,t)=>{el.value=String(t);el.dispatchEvent(new Event('input',{bubbles:true}));},time);
  const actual=await page.locator('.window').getAttribute('data-stage');assert.equal(actual,stage);
  await page.screenshot({path:resolve(output,`${stage}.png`)});
 }
 const movement=await page.evaluate(()=>{
  const c=document.querySelector('.shinchan-motion'),el=document.querySelector('#timeline');
  el.value='8.6';el.dispatchEvent(new Event('input'));const a=c.toDataURL();
  el.value='9.1';el.dispatchEvent(new Event('input'));return {changes:a!==c.toDataURL(),opacity:c.style.opacity};
 });assert(movement.changes);assert(Number(movement.opacity)>.9);
 const start=Date.now();await page.evaluate(()=>{window.__messages=[];window.launcherUI.beginLaunch(false);});
 await page.waitForFunction(()=>window.__messages.includes('complete'),{timeout:20000});
 const messages=await page.evaluate(()=>window.__messages);
 assert.equal(messages.filter(x=>x==='typing-sound').length,1,'Greeting must fire once during typing');
 const metrics=messages.filter(x=>typeof x==='string'&&x.startsWith('{')).map(x=>JSON.parse(x));
 assert.equal(errors.length,0,errors.join('\n'));
 const result={ok:true,errors,elapsedMs:Date.now()-start,stages:4,characterMotion:movement,metrics};
 await writeFile(resolve(output,'visual-test.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 if(process.argv.includes('--frames')){
  const frames=resolve(output,'frames');await mkdir(frames,{recursive:true});
  for(let n=0;n<144;n++){
   await page.locator('#timeline').evaluate((el,t)=>{el.value=String(t);el.dispatchEvent(new Event('input',{bubbles:true}));},n/12);
   await page.screenshot({path:resolve(frames,String(n).padStart(4,'0')+'.png')});
  }
  console.log('Rendered 144 animation frames');
 }
}finally{await browser.close();await new Promise(r=>server.close(r));}
