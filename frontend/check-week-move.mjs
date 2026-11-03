// Synthetic API fixtures; operational orders are never modified.
import {chromium,expect} from '@playwright/test';
import {existsSync} from 'node:fs';
const executablePath=['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync);
const browser=await chromium.launch({headless:true,executablePath});
try {
 for(const width of [1440,390]) {
  const page=await browser.newPage({viewport:{width,height:1000}});
  let moved=false,posts=0;
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  const row={id:1,part:'MOVE-01',reference:'TEST-1',client:'LENNOX 1',scope:'SLP',year:2026,week:43,next_year:2026,next_week:44,quantity:100,original:100,packed:130,pending_release:0,applied:100,pending:0,packing_pending:0,credit:30,published:true,priority:2};
  await page.route('**/api/**',async route=>{
   const url=new URL(route.request().url());let data;
   if(url.pathname==='/api/session/')data={authenticated:true,username:'synthetic',roles:{consult:true,capture:true,plan:true,release:true,manage_users:true,admin:true},csrf:'test'};
   else if(url.pathname==='/api/catalog/')data={today:'2026-10-28',current_year:2026,groups:[],parts:[],employees:[],shifts:[],clients:['LENNOX 1'],programs:[{id:1,client:'LENNOX 1',scope:'SLP',year:2026,week:43,published:true}],work_weeks:moved?[{year:2026,week:44}]:[]};
   else if(url.pathname==='/api/balance/')data={rows:[moved?{...row,id:2,reference:'TARGET-1',week:44,next_week:45,quantity:200,applied:30,pending:170,credit:0}:row],totals:{quantity:100,applied:20,packed:20,pending:80},updated_at:new Date().toISOString()};
   else if(url.pathname==='/api/demands/1/next-week/'){
    const payload=route.request().postDataJSON();expect(payload.year).toBe(2026);expect(payload.week).toBe(43);expect(payload.key).toMatch(/^[0-9a-f-]{36}$/);posts++;moved=true;
    data={year:2026,week:44,pending:0,applied_credit:30,remaining_credit:0};
   }else data=[];
   await route.fulfill({json:data});
  });
  await page.goto((process.argv[2]||'http://127.0.0.1:58080/')+'#'+encodeURIComponent('Órdenes'));
  const move=page.getByRole('button',{name:'Pasar excedente de MOVE-01 a la siguiente semana',exact:true});
  await move.click();
  await expect(page.getByRole('dialog')).toContainText('30 piezas');
  await expect(page.getByRole('dialog')).toContainText('Excedentes');
  await page.getByRole('button',{name:'Cancelar',exact:true}).click();expect(posts).toBe(0);
  await move.click();await page.getByRole('button',{name:'Confirmar excedente',exact:true}).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);expect(posts).toBe(1);
  await expect(page.locator('.unified-orders .week-tag')).toHaveText('S44');
  await expect(page.locator('.unified-orders')).toContainText('170');
  expect(errors).toEqual([]);console.log(`PASS ${width}: review, cancel, confirm surplus only and show next-week pending.`);await page.close();
 }
}finally{await browser.close();}
