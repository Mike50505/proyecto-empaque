// Synthetic API fixtures: accounts are never created in the operational database.
import {chromium,expect} from '@playwright/test';
import {existsSync} from 'node:fs';
const executablePath=['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync);
const browser=await chromium.launch({headless:true,executablePath});
try {
 for(const width of [1440,390]) {
  const page=await browser.newPage({viewport:{width,height:1000}});
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  const users=[{id:1,username:'admin',first_name:'Admin',last_name:'Test',role:'admin',is_active:true,can_edit:true,is_self:true,email:''}];
  await page.route('**/api/**',async route=>{
   const url=new URL(route.request().url());let data;
   if(url.pathname==='/api/session/')data={authenticated:true,username:'admin',user_id:1,role:'admin',roles:{consult:true,capture:true,plan:true,release:true,manage_users:true,admin:true},csrf:'test'};
   else if(url.pathname==='/api/catalog/')data={today:'2026-10-28',groups:[],parts:[],employees:[],shifts:[],programs:[],clients:[],integration:{local_parts:0},work_weeks:[]};
   else if(url.pathname==='/api/balance/')data={rows:[],totals:{},updated_at:new Date().toISOString()};
   else if(url.pathname==='/api/users/'){
    if(route.request().method()==='POST'){data={id:2,...route.request().postDataJSON(),can_edit:true,is_self:false};delete data.password;users.push(data);}else data=users;
   } else if(url.pathname==='/api/users/2/'){
    const payload=route.request().postDataJSON();expect(payload.is_active).toBe(false);expect(payload.role).toBe('planer');Object.assign(users[1],payload);delete users[1].password;data=users[1];
   }else data=[];
   await route.fulfill({json:data});
  });
  await page.goto((process.argv[2]||'http://127.0.0.1:58080/')+'#Usuarios');
  await expect(page.getByRole('heading',{name:'Usuarios de Empaques',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Crear usuario',exact:true}).click();
  await page.getByLabel('Usuario',{exact:true}).fill('new-operator');
  await page.getByLabel('Nombre',{exact:true}).fill('Synthetic');
  await page.getByLabel('Contraseña inicial',{exact:true}).fill('Synthetic-Password-713!');
  await page.getByLabel('Confirmar contraseña',{exact:true}).fill('Synthetic-Password-713!');
  await page.getByRole('dialog').getByRole('button',{name:'Crear usuario',exact:true}).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.locator('.users-table')).toContainText('new-operator');
  await page.getByRole('button',{name:'Editar usuario new-operator',exact:true}).click();
  const role=page.getByRole('combobox',{name:'Rol',exact:true});
  if(await role.evaluate(element=>element.tagName)==='SELECT')await role.selectOption('planer');
  else{await role.click();await page.getByRole('option',{name:'Planer',exact:true}).click()}
  await page.getByLabel('Cuenta activa',{exact:true}).uncheck();
  await page.getByRole('button',{name:'Guardar cambios',exact:true}).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.locator('.users-table')).toContainText('Inactivo');
  await expect(page.locator('.users-table')).toContainText('Planer');
  expect(errors).toEqual([]);console.log(`PASS ${width}: create, edit role and deactivate through Users.`);await page.close();
 }
 const page=await browser.newPage();
 await page.route('**/api/**',route=>{const url=new URL(route.request().url());const data=url.pathname==='/api/session/'?{authenticated:true,username:'operator',role:'operador',roles:{consult:true,capture:true,release:true,plan:false,manage_users:false,admin:false}}:url.pathname==='/api/catalog/'?{programs:[],parts:[],groups:[],shifts:[],employees:[]}:url.pathname==='/api/balance/'?{rows:[],totals:{},updated_at:new Date().toISOString()}:[];return route.fulfill({json:data})});
 await page.goto((process.argv[2]||'http://127.0.0.1:58080/')+'#Usuarios');
 await expect(page.getByRole('heading',{name:'Empaque, de principio a fin',exact:true})).toBeVisible();
 await expect(page.getByRole('button',{name:'Usuarios',exact:true})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Programas',exact:true})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Administración',exact:true})).toHaveCount(0);
 console.log('PASS operator: user and planning management are hidden, including direct hash navigation.');
} finally {await browser.close();}
