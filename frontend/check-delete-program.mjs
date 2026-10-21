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
 await page.getByRole('button',{name:'Programas',exact:true}).click();
 const cards=page.locator('.program-card');await expect(cards.first()).toBeVisible();const before=await cards.count();
 const card=cards.filter({hasText:'RHEEM TRANSFERENCIA'}).first();
 await card.getByRole('button',{name:'Eliminar programa',exact:true}).click();
 await expect(page.getByRole('dialog').getByRole('heading',{name:'Eliminar programa',exact:true})).toBeVisible();
 await expect(page.getByLabel('Motivo de eliminación',{exact:true})).toBeVisible();
 await expect(page.getByRole('button',{name:'Eliminar definitivamente',exact:true})).toBeDisabled();
 await page.screenshot({path:'../private/programa-eliminar-confirmacion.png',fullPage:true});
 await page.getByRole('dialog').getByRole('button',{name:'Cancelar',exact:true}).click();
 await expect(cards).toHaveCount(before);
 console.log('PASS: delete button, program/order review, mandatory reason and cancellation. No real programs deleted.');
}finally{await browser.close()}
