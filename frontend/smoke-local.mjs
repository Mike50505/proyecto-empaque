// Read-only check of local operation. No orders or captures are created.
import {chromium,expect} from '@playwright/test';
import {readFileSync,existsSync} from 'node:fs';
const credentials=readFileSync('../private/primer_acceso.txt','utf8');
const username=credentials.match(/Usuario: (.+)/)[1].trim();
const password=credentials.match(/Contraseña(?: temporal)?: (.+)/)[1].trim();
const executablePath=['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','C:/Program Files/Google/Chrome/Application/chrome.exe'].find(existsSync);
const browser=await chromium.launch({headless:true,executablePath});
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:55173/');
 await page.getByLabel('Usuario',{exact:true}).fill(username);
 await page.getByLabel('Contraseña',{exact:true}).fill(password);
 await page.getByRole('button',{name:'Iniciar sesión',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Empaque, de principio a fin',exact:true})).toBeVisible();
 await page.screenshot({path:'../private/inicio-macros-desktop.png',fullPage:true});
 for(const [name,heading] of [['Órdenes','Órdenes de empaque'],['Dashboard','Dashboard de empaque'],['Historial','Historial de movimientos'],['Programas','Programas de trabajo'],['Importaciones','Importaciones y conciliación'],['Administración','Administración y auditoría']]){
   await page.getByRole('button',{name,exact:true}).click();
   await expect(page.getByRole('heading',{name:heading,exact:true})).toBeVisible();
 }
 await page.getByRole('button',{name:'Órdenes',exact:true}).click();
 await expect(page.locator('.orders-table tbody tr').first()).toBeVisible();
 await page.screenshot({path:'../private/captura-macros-desktop.png',fullPage:true});
 await page.getByRole('button',{name:'Activar tema oscuro',exact:true}).click();
 await page.screenshot({path:'../private/captura-macros-oscuro.png',fullPage:true});
 await page.reload();
 await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
 await expect(page.getByRole('heading',{name:'Órdenes de empaque',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Activar tema claro',exact:true}).click();
 for(const width of [375,768,1024,1440]){
   await page.setViewportSize({width,height:900});
   if(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth))throw new Error('Horizontal overflow at '+width);
   if(width===375){
     await page.getByRole('button',{name:'Abrir navegación'}).click();
     await page.getByRole('button',{name:'Inicio',exact:true}).click();
     await page.screenshot({path:'../private/inicio-macros-mobile.png',fullPage:true});
     await page.getByRole('button',{name:'Abrir navegación'}).click();
     await page.getByRole('button',{name:'Órdenes',exact:true}).click();
     await page.screenshot({path:'../private/captura-macros-mobile.png',fullPage:true});
   }
 }
 if(errors.length)throw new Error(errors.join('\n'));
 console.log('PASS: all modules, local data, theme persistence, navigation persistence and responsive 375/768/1024/1440. No data modified.');
}finally{await browser.close()}
