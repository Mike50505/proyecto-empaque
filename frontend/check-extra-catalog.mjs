// Only mocked catalog and requests; no production captures are created.
import {chromium,expect} from '@playwright/test';
const browser=await chromium.launch({headless:true,channel:'chrome'});
try{
 const page=await browser.newPage({viewport:{width:1280,height:1000}}),sent=[];
 const parts=[{id:1,number:'VALID-001',customer:'LENNOX 1',scope:'SLP',universe_id:'official-1',provisional:false,attributes:{active:true}},
 {id:2,number:'VALID-002',customer:'RHEEM',scope:'FALCON',universe_id:'official-2',provisional:false,attributes:{active:true}},
 {id:3,number:'INACTIVE-001',customer:'LENNOX 1',universe_id:'official-3',provisional:false,attributes:{active:false}},
 {id:4,number:'PROVISIONAL-001',customer:'LENNOX 1',provisional:true},
 {id:5,number:'DUPLICATE',customer:'LENNOX 1',scope:'SLP',universe_id:'official-5',provisional:false},
 {id:6,number:'DUPLICATE',customer:'RHEEM',scope:'FALCON',universe_id:'official-6',provisional:false}];
 await page.route('**/api/**',route=>{
  const path=new URL(route.request().url()).pathname;
  if(path==='/api/extras/'&&route.request().method()==='POST'){sent.push(route.request().postDataJSON());return route.fulfill({status:201,json:{id:'EX-TEST'}})}
  return route.fulfill({json:path==='/api/session/'?{authenticated:true,username:'synthetic',roles:{consult:true,capture:true,plan:true}}:path==='/api/catalog/'?{parts,programs:[],groups:[],work_weeks:[]}:path==='/api/balance/'?{rows:[],totals:{},updated_at:new Date().toISOString()}:[]});
 });
 await page.goto((process.argv[2]||'http://127.0.0.1:55175/')+'#'+encodeURIComponent('Órdenes'));
 await page.getByRole('button',{name:'Añadir extra',exact:true}).click();
 const dialog=page.getByRole('dialog'),input=dialog.getByRole('combobox',{name:'Número de parte',exact:true});
 const review=dialog.getByRole('button',{name:'Revisar extra',exact:true});
 for(const value of ['NO-SUCH-PART','INACTIVE','PROVISIONAL']){await input.fill(value);await expect(review).toBeDisabled();await expect(dialog.getByRole('option')).toHaveCount(0)}
 await input.fill('VALID');await expect(dialog.getByRole('option')).toHaveCount(2);
 await dialog.getByRole('option',{name:/VALID-001/}).click();await expect(input).toHaveValue('VALID-001');await expect(review).toBeEnabled();
 await input.fill('DUPLICATE');await expect(review).toBeDisabled();await expect(dialog.getByRole('option')).toHaveCount(2);
 await input.press('ArrowDown');await input.press('ArrowDown');await input.press('Enter');await expect(review).toBeEnabled();
 await dialog.getByLabel('Cantidad (piezas)',{exact:true}).fill('5');
 await dialog.getByLabel('Nómina del empacador',{exact:true}).fill('TEST-P');
 await dialog.getByLabel('Nómina de quien libera',{exact:true}).fill('TEST-I');
 await review.click();await dialog.getByRole('button',{name:'Confirmar extra',exact:true}).click();
 await expect(dialog).not.toBeVisible();expect(sent).toHaveLength(1);expect(sent[0].part_number).toBe('DUPLICATE');expect(sent[0].part_id).toBe(6);
 console.log('PASS: invalid parts blocked, active suggestions, mouse/keyboard selection, duplicate identity and confirmed payload.');
}finally{await browser.close()}
