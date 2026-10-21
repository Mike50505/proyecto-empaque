export let csrf='';
export async function api(path, options={}) {
  const form=options.body instanceof FormData;
  const res=await fetch('/api/'+path,{credentials:'same-origin',...options,headers:{...(!form?{'Content-Type':'application/json'}:{}),'X-CSRFToken':csrf,...options.headers},body:options.body?(form?options.body:JSON.stringify(options.body)):undefined});
  const data=await res.json().catch(()=>({detail:'Respuesta del servidor inválida.'}));
  if(!res.ok) throw new Error(typeof data.detail==='string'?data.detail:JSON.stringify(data));
  if(data.csrf) csrf=data.csrf;
  return data;
}
export const n=value=>new Intl.NumberFormat('es-MX').format(value??0);
export const when=value=>value?new Date(value).toLocaleString('es-MX'):'Sin sincronización';
