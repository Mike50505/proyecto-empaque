import {chromium,expect} from '@playwright/test';
import {readFileSync,existsSync} from 'node:fs';
const credentials=readFileSync('../private/primer_acceso.txt','utf8');
const executablePath=['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','C:/Program Files/Google/Chrome/Application/chrome.exe'].find(existsSync);
const browser=await chromium.launch({headless:true,executablePath});
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 await page.goto('http://127.0.0.1:55173/');
 await page.getByLabel('Usuario',{exact:true}).fill(credentials.match(/Usuario: (.+)/)[1].trim());
 await page.getByLabel('Contraseña',{exact:true}).fill(credentials.match(/Contraseña(?: temporal)?: (.+)/)[1].trim());
 await page.getByRole('button',{name:'Iniciar sesión',exact:true}).click();
 await page.getByRole('button',{name:'Órdenes',exact:true}).click();
 await page.getByRole('button',{name:'RHEEM TRANSFERENCIA',exact:true}).click();
 await expect(page.locator('.order-catalog-error')).toHaveCount(11);
 await expect(page.locator('.sheet-capture')).toHaveCount(0);
 await page.screenshot({path:'../private/ordenes-cliente-incompatible-bloqueadas.png',fullPage:true});
 await page.getByRole('button',{name:'Programas',exact:true}).click();
 await page.getByRole('button',{name:'Crear programa',exact:true}).click();
 const combo=page.getByRole('dialog').getByRole('combobox',{name:'Cliente',exact:true});
 if(await combo.evaluate(node=>node.tagName)==='SELECT')await combo.selectOption('RHEEM TRANSFERENCIA');else{await combo.click();await page.getByRole('option',{name:'RHEEM TRANSFERENCIA',exact:true}).click()}
 const options=await page.getByRole('dialog').locator('.line-form select').first().locator('option').evaluateAll(nodes=>nodes.map(node=>node.value).filter(Boolean));
 const catalog=await (await page.request.get('http://127.0.0.1:55173/api/catalog/')).json();
 if(!options.length)throw new Error('No valid RHEEM parts offered');
 if(options.some(id=>catalog.parts.find(part=>String(part.id)===id)?.customer!=='RHEEM TRANSFERENCIA'))throw new Error('Foreign customer part offered');
 console.log('PASS: 11 legacy mismatches visible and blocked; manual selector offers only Universo parts for RHEEM TRANSFERENCIA. No operational data changed.');
}finally{await browser.close()}
