// Synthetic fixtures only; no requests change the operational database.
import {chromium,expect} from '@playwright/test';
import {existsSync} from 'node:fs';
const executablePath=['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync);
const browser=await chromium.launch({headless:true,executablePath});
try {
 for(const width of [1440,390]) {
  const page=await browser.newPage({viewport:{width,height:1000}});
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  const row={id:1,part:'EXCESS-01',reference:'TEST-1',client:'LENNOX 1',scope:'SLP',year:2026,week:43,quantity:100,original:100,packed:130,pending_release:0,applied:100,pending:0,packing_pending:0,credit:30,A:130,B:0,published:true,priority:2};
  await page.route('**/api/**',async route=>{
   const url=new URL(route.request().url());let data;
   if(route.request().method()!=='GET')throw new Error('This check must be read-only');
   if(url.pathname==='/api/session/')data={authenticated:true,username:'synthetic',roles:{consult:true,capture:true,plan:true,release:true},csrf:'test'};
   else if(url.pathname==='/api/catalog/')data={today:'2026-10-28',current_year:2026,groups:[],parts:[],employees:[],shifts:[],clients:['LENNOX 1'],programs:[{id:1,client:'LENNOX 1',scope:'SLP',year:2026,week:43,published:true}],work_weeks:[]};
   else if(url.pathname==='/api/balance/')data={rows:[row,{...row,id:2,part:'PENDING',reference:'TEST-2',applied:80,pending:20},{...row,id:3,part:'AWAITING-RELEASE',reference:'TEST-3',applied:0,pending:100,packed:100,pending_release:100}],totals:{quantity:300,applied:180,packed:330,pending_release:100,pending:120,credit:30},updated_at:new Date().toISOString()};
   else if(url.pathname==='/api/surplus/')data=url.searchParams.get('search')==='NONE'?{rows:[],total:0}:{rows:[{...row,id:'capture-1',source:1,kind:'Captura',date:'2026-10-28',quantity:30,packer:'00007',inspector:'00045'}],total:30};
   else data=[];
   await route.fulfill({json:data});
  });
  await page.goto(process.argv[2]||'http://127.0.0.1:58080/');
  await expect(page.getByRole('heading',{name:'Empaque, de principio a fin',exact:true})).toBeVisible();
  if(width<600)await page.getByRole('button',{name:'Abrir navegación'}).click();
  await page.getByRole('button',{name:'Órdenes',exact:true}).click();
  await expect(page.getByRole('button',{name:/a la siguiente semana/})).toHaveCount(0);
  await expect(page.locator('.unified-orders')).not.toContainText('trasladado');
  await expect(page.locator('.unified-orders .order-completed')).toHaveCount(1);
  await expect(page.locator('.unified-orders .completed-order-badge')).toHaveText('Terminada');
  const light=await page.locator('.order-completed td').first().evaluate(cell=>getComputedStyle(cell).backgroundColor);
  expect(light).toBe('rgb(237, 240, 243)');
  await page.evaluate(()=>document.documentElement.dataset.theme='dark');
  expect(await page.locator('.order-completed td').first().evaluate(cell=>getComputedStyle(cell).backgroundColor)).toBe('rgb(37, 44, 53)');
  await page.evaluate(()=>document.documentElement.dataset.theme='light');
  if(width<600)await page.getByRole('button',{name:'Abrir navegación'}).click();
  await page.getByRole('button',{name:'Excedentes',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Excedentes disponibles',exact:true})).toBeVisible();
  await expect(page.locator('.surplus-panel tbody')).toContainText('EXCESS-01');
  await expect(page.locator('.surplus-panel tbody')).toContainText('30');
  await expect(page.locator('.surplus-panel tbody')).toContainText('00045');
  await page.getByLabel('Número de parte o diámetro',{exact:true}).fill('NONE');
  await expect(page.getByRole('heading',{name:'No hay excedentes disponibles',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Limpiar filtros',exact:true}).click();
  await expect(page.locator('.surplus-panel tbody')).toContainText('EXCESS-01');
  expect(errors).toEqual([]);
  console.log(`PASS ${width}: surplus inventory, filters and empty state; next-week action removed.`);
  await page.close();
 }
} finally {await browser.close();}
