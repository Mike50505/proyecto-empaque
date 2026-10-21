import {chromium,expect} from '@playwright/test';
import {readFileSync,existsSync} from 'node:fs';
const credentials=readFileSync('../private/primer_acceso.txt','utf8');
const executablePath=['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','C:/Program Files/Google/Chrome/Application/chrome.exe'].find(existsSync);
const browser=await chromium.launch({headless:true,executablePath});
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}});page.setDefaultTimeout(10000);
 const errors=[];page.on('pageerror',error=>errors.push(error.message));
 await page.goto('http://127.0.0.1:55173/');
 await page.getByLabel('Usuario',{exact:true}).fill(credentials.match(/Usuario: (.+)/)[1].trim());
 await page.getByLabel('Contraseña',{exact:true}).fill(credentials.match(/Contraseña(?: temporal)?: (.+)/)[1].trim());
 await page.getByRole('button',{name:'Iniciar sesión',exact:true}).click();
 await page.getByRole('button',{name:'Dashboard',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Ritmo de empaque',exact:true})).toBeVisible();
 await expect(page.getByText('Consultando producción',{exact:true})).toHaveCount(0);
 await page.evaluate(()=>scrollTo(0,0));
 await page.screenshot({path:'../private/dashboard-renovado-desktop.png',fullPage:true});
 if(await page.locator('.dash-day').count()){
   await page.getByRole('button',{name:'14 días',exact:true}).click();
   await expect(page.locator('.dash-day')).toHaveCount(14);
   await page.getByRole('button',{name:'7 días',exact:true}).click();
 }
 await page.getByRole('button',{name:'Semana',exact:true}).click();
 await page.getByRole('button',{name:'Cliente',exact:true}).click();
 await page.getByRole('button',{name:'Explorar órdenes',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Órdenes de empaque',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Dashboard',exact:true}).click();
 for(const width of [375,768,1024,1440]){
  await page.setViewportSize({width,height:1000});
  if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw new Error('Page overflow at '+width);
  if(width===375)await page.evaluate(()=>scrollTo(0,0));
  if(width===375)await page.screenshot({path:'../private/dashboard-renovado-mobile.png',fullPage:true});
 }
 await page.getByRole('button',{name:'Elegir colores',exact:true}).click();
 const palette=page.getByRole('combobox',{name:'Paleta de colores',exact:true});
 if(await palette.evaluate(node=>node.tagName)==='SELECT')await palette.selectOption('night');else{await palette.click();await page.getByRole('option',{name:'Oscuro · negro',exact:true}).click()}
 await page.keyboard.press('Escape');
 await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
 await page.evaluate(()=>scrollTo(0,0));
 await page.screenshot({path:'../private/dashboard-renovado-oscuro.png',fullPage:true});
 if(errors.length)throw new Error(errors.join('\n'));
 console.log('PASS: dashboard, production periods, grouping, orders drill-through, dark mode and responsive 375/768/1024/1440. No operational data changed.');
}finally{await browser.close()}
