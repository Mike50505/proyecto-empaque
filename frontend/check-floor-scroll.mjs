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
  let lastBalanceQuery;
  await page.route('**/api/**',route=>{
   const url=new URL(route.request().url()),path=url.pathname;
   if(path==='/api/balance/')lastBalanceQuery=url.searchParams;
   const query=url.searchParams.get('search')?.toLowerCase()||'';
   const filtered=rows.filter(row=>row.part.toLowerCase().includes(query));
   const data=path==='/api/session/'?{authenticated:true,username:'synthetic',roles:{consult:true,capture:true,plan:true,release:true}}:path==='/api/catalog/'?{programs:[{year:2026,week:44,published:true,client:'LENNOX 1'}],parts:[...rows.map(row=>({id:row.id,number:row.part,universe_id:String(row.id),customer:'LENNOX 1',attributes:{active:true}})),{id:999,number:'INACTIVE',universe_id:'999',customer:'LENNOX 1',attributes:{active:false}}],groups:[],work_weeks:[]}:path==='/api/balance/'?{rows:filtered,totals:{quantity:filtered.length*100,pending:filtered.length*100,applied:0},updated_at:new Date().toISOString()}:[];
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
  await expect(page.locator('.floor-filter-row .floor-week-control')).toBeVisible();
  expect(await page.locator('.floor-filter-row').evaluate(row=>{const tabs=row.querySelector('.group-tabs').getBoundingClientRect(),week=row.querySelector('.floor-week-control').getBoundingClientRect();return week.right<=tabs.left&&Math.abs(week.top-tabs.top)<40})).toBe(true);
  await page.locator('.floor-week-control select').selectOption('44');
  const search=page.locator('.floor-search-control input');
  await expect(search).toBeVisible();
  await search.fill('INACTIVE');await expect(page.getByRole('listbox').getByRole('option')).toHaveCount(0);
  await search.fill('TEST-8');await expect(page.getByRole('option',{name:'TEST-80',exact:true})).toBeVisible();
  await page.getByRole('option',{name:'TEST-80',exact:true}).click();await expect(search).toHaveValue('TEST-80');
  await search.fill('TEST-80');await search.press('ArrowDown');await search.press('Enter');
  await expect(page.getByRole('listbox')).toHaveCount(0);
  await expect(table.locator('tbody tr')).toHaveCount(1);await expect(table).toContainText('TEST-80');
  expect(lastBalanceQuery.get('search')).toBe('TEST-80');expect(lastBalanceQuery.get('week')).toBe('44');
  await page.locator('.floor-search-clear').click();await expect(search).toHaveValue('');
  await expect(table.locator('tbody tr')).toHaveCount(80);await expect(page.locator('.app.tv')).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  console.log(`PASS ${width}: all 80 orders, manual wheel/keyboard scroll, no rotation or reset after refresh.`);
  await page.close();
 }
}finally{await browser.close();}
