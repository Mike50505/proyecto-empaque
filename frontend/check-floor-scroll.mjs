// Synthetic orders only; no operational data is modified.
import {chromium,expect} from '@playwright/test';
import {existsSync} from 'node:fs';
const executablePath=['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync);
const browser=await chromium.launch({headless:true,executablePath});
try {
 for(const width of [1440,768]) {
  const page=await browser.newPage({viewport:{width,height:900}});
  await page.clock.install();
  const rows=Array.from({length:80},(_,index)=>({id:index+1,part:`TEST-${index+1}`,reference:`ORDER-${index+1}`,client:'LENNOX 1',scope:'SLP',year:2026,week:44,quantity:100,packed:0,applied:0,pending:100,packing_pending:100,pending_release:0,credit:0,published:true,priority:2}));
  await page.route('**/api/**',route=>{
   const path=new URL(route.request().url()).pathname;
   const data=path==='/api/session/'?{authenticated:true,username:'synthetic',roles:{consult:true,capture:true,plan:true,release:true}}:path==='/api/catalog/'?{programs:[{year:2026,week:44,published:true,client:'LENNOX 1'}],parts:[],groups:[],work_weeks:[]}:path==='/api/balance/'?{rows,totals:{quantity:8000,pending:8000,applied:0},updated_at:new Date().toISOString()}:[];
   return route.fulfill({json:data});
  });
  await page.goto((process.argv[2]||'http://127.0.0.1:58080/')+'?tv=1');
  const table=page.getByRole('region',{name:'Órdenes de empaque, desplazamiento manual',exact:true});
  await expect(table.locator('tbody tr')).toHaveCount(80);
  expect(await table.evaluate(element=>element.scrollHeight>element.clientHeight)).toBe(true);
  await page.clock.fastForward(16000);
  await expect(table.locator('tbody tr').first()).toContainText('TEST-1');
  await expect(table.locator('tbody tr')).toHaveCount(80);
  await table.hover();await page.mouse.wheel(0,600);
  await expect.poll(()=>table.evaluate(element=>element.scrollTop)).toBeGreaterThan(0);
  const position=await table.evaluate(element=>element.scrollTop);
  await page.clock.fastForward(21000);
  await expect(table.locator('tbody tr')).toHaveCount(80);
  expect(await table.evaluate(element=>element.scrollTop)).toBe(position);
  await table.focus();await page.keyboard.press('End');
  await expect.poll(()=>table.evaluate(element=>element.scrollTop+element.clientHeight>=element.scrollHeight-2)).toBe(true);
  console.log(`PASS ${width}: all 80 orders, manual wheel/keyboard scroll, no rotation or reset after refresh.`);
  await page.close();
 }
}finally{await browser.close();}
