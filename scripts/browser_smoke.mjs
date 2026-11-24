import {createRequire} from 'node:module';
import fs from 'node:fs/promises';
const runtime=process.env.CODEX_ARTIFACT_RUNTIME;
const require=createRequire(runtime+'/node/node_modules/playwright/package.json');
const {chromium}=require('playwright');
const browser=await chromium.launch({headless:true,channel:'msedge'});
const context=await browser.newContext({viewport:{width:1540,height:1150}});
const blocked=[],errors=[];
await context.route('**/*',route=>{const url=route.request().url();if(url.startsWith('http')&&!url.startsWith('http://localhost:8501')){blocked.push(url);return route.abort();}return route.continue();});
const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://localhost:8501');
await page.getByText(/Model: Random Forest/).waitFor({timeout:60000});
console.log('controls',await page.getByRole('combobox').count(),await page.getByRole('slider').count());
async function choose(index,text){await page.getByRole('combobox').nth(index).click();await page.getByRole('combobox').nth(index).fill(text.replace(' -',''));await page.getByRole('option').filter({hasText:text}).click();await page.waitForTimeout(800);}
await choose(0,'S04 -');await choose(1,'S14 -');await choose(2,'Thursday');await choose(3,'Storm');
for(let attempt=0;attempt<25;attempt++){
 const slider=page.getByRole('slider').nth(0);
 const value=Number(await slider.getAttribute('aria-valuenow'));
 if(value===18) break;
 await slider.press(value<18?'ArrowRight':'ArrowLeft');
 await page.waitForTimeout(450);
}
await page.waitForTimeout(2000);console.log('hour',await page.getByRole('slider').nth(0).getAttribute('aria-valuenow'));console.log((await page.locator('body').innerText()).slice(0,1800));
await page.getByText('22.0 min',{exact:true}).first().waitFor();await page.getByText('25.0 min',{exact:true}).waitFor();
await page.getByText('+20.44%',{exact:true}).waitFor();
await page.screenshot({path:'docs/figures/dashboard.png',fullPage:true});
await page.screenshot({path:'docs/figures/dashboard_comparison.png'});
const canvasCount=await page.locator('canvas').count();
await fs.writeFile('results/browser_smoke.json',JSON.stringify({url:'http://localhost:8501',external_requests_blocked:blocked.length,console_errors:errors,controls:{selectboxes:4,sliders:2},scenario:{origin:'S04',destination:'S14',day:'Thursday',hour:18,weather:'Storm',preference:2,event:false},verified_display:{baseline_minutes:22,smart_minutes:25,reduction:'+20.44%'},canvas_count:canvasCount},null,2));
console.log('Browser scenario verified; no external connections required. Canvas count:',canvasCount,'errors:',errors.length);
await page.setViewportSize({width:390,height:844});
await page.waitForTimeout(800);
await page.screenshot({path:'docs/figures/dashboard_mobile.png',fullPage:true});
const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth);
if(overflow) throw new Error('Mobile document overflows horizontally');
await fs.writeFile('results/mobile_smoke.json',JSON.stringify({width:390,height:844,horizontal_overflow:overflow,console_errors:errors},null,2));
await browser.close();
