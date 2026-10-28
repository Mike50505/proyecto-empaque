// Synthetic API fixtures: this check never writes operational data.
import {chromium,expect} from '@playwright/test';
import {existsSync} from 'node:fs';
const executablePath=['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync);
const browser=await chromium.launch({headless:true,executablePath});
try {
 for(const width of [1440,390]) {
  const page=await browser.newPage({viewport:{width,height:1000}});
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  let submitted;
  const row={id:1,part:'TEST-RELEASE',reference:'TEST-1',client:'LENNOX 1',scope:'SLP',year:2026,week:44,quantity:100,original:100,packed:0,pending_release:0,applied:0,pending:100,packing_pending:100,credit:0,A:0,B:0,published:true,priority:2};
  await page.route('**/api/**',async route=>{
   const url=new URL(route.request().url());let data;
   if(url.pathname==='/api/session/')data={authenticated:true,username:'synthetic',roles:{consult:true,capture:true,plan:false,release:false},csrf:'test',release_mode:'declared'};
   else if(url.pathname==='/api/catalog/')data={today:'2026-10-28',current_year:2026,groups:[],parts:[],employees:[],shifts:[],programs:[{id:1,client:'LENNOX 1',scope:'SLP',year:2026,week:44,published:true}],work_weeks:[]};
   else if(url.pathname==='/api/balance/')data={rows:[row],totals:{quantity:100,applied:0,packed:0,pending_release:0,pending:100},updated_at:new Date().toISOString()};
   else if(url.pathname==='/api/captures/'&&route.request().method()==='POST'){submitted=route.request().postDataJSON();data={id:1,...submitted,released:true};}
   else data=[];
   await route.fulfill({json:data});
  });
  await page.goto((process.argv[2]||'http://127.0.0.1:58080/')+'#Liberaciones');
  await expect(page.getByRole('heading',{name:'Empaque, de principio a fin',exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Liberaciones',exact:true})).toHaveCount(0);
  if(width<600)await page.getByRole('button',{name:'Abrir navegación'}).click();
  await page.getByRole('button',{name:'Órdenes',exact:true}).click();
  await page.getByRole('button',{name:'Capturar TEST-RELEASE orden TEST-1',exact:true}).click();
  await page.getByLabel('Cantidad adicional (piezas)').fill('20');
  await page.getByLabel('Nómina del empacador',{exact:true}).fill('00007');
  await page.getByRole('button',{name:'Revisar captura',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Registrar empaque',exact:true})).toBeVisible();
  await page.getByLabel('Número de nómina de quien libera',{exact:true}).fill('00045');
  await page.getByRole('button',{name:'Revisar captura',exact:true}).click();
  await expect(page.getByRole('dialog')).toContainText('00045');
  await expect(page.getByRole('dialog')).toContainText('se guardará liberada');
  await page.getByRole('button',{name:'Confirmar captura',exact:true}).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  expect(submitted.inspector).toBe('00045');expect(submitted.packer).toBe('00007');expect(submitted.quantity).toBe(20);
  expect(errors).toEqual([]);await page.close();console.log(`PASS ${width}: inline payroll, required validation, review and save; no release module.`);
 }
} finally {await browser.close();}
