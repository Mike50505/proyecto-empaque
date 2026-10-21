import {chromium,expect} from '@playwright/test';
import {readFileSync,existsSync} from 'node:fs';
const credentials=readFileSync('../private/primer_acceso.txt','utf8');
const executablePath=['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','C:/Program Files/Google/Chrome/Application/chrome.exe'].find(existsSync);
const browser=await chromium.launch({headless:true,executablePath});
try{
 const page=await browser.newPage();
 await page.goto('http://127.0.0.1:55173/');
 await page.getByLabel('Usuario',{exact:true}).fill(credentials.match(/Usuario: (.+)/)[1].trim());
 await page.getByLabel('Contraseña',{exact:true}).fill(credentials.match(/Contraseña(?: temporal)?: (.+)/)[1].trim());
 await page.getByRole('button',{name:'Iniciar sesión',exact:true}).click();
 await page.getByRole('button',{name:'Importaciones',exact:true}).click();
 const link=page.getByRole('link',{name:'Descargar plantilla',exact:true});
 console.log('Download link:',await link.getAttribute('href'));
 const downloadPromise=page.waitForEvent('download');await link.click();const download=await downloadPromise;
 await download.saveAs('../private/plantilla-descargada-verificacion.xlsx');
 console.log('Served filename:',download.suggestedFilename());
 const response=await page.request.get('http://127.0.0.1:55173/api/template/?mode=new');
 console.log('Template response:',response.status(),'cache:',response.headers()['cache-control']);
 console.log('Clients in catalog:',Object.keys(await (await page.request.get('http://127.0.0.1:55173/api/catalog/')).json()).includes('clients'));
}finally{await browser.close()}
