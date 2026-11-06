export let csrf='';
export async function api(path, options={}) {
  const form=options.body instanceof FormData;
  const res=await fetch('/api/'+path,{credentials:'same-origin',...options,headers:{...(!form?{'Content-Type':'application/json'}:{}),'X-CSRFToken':csrf,...options.headers},body:options.body?(form?options.body:JSON.stringify(options.body)):undefined});
  const data=await res.json().catch(()=>{throw new Error(res.status===404?'La función solicitada no está disponible en el servidor (404).':res.status===403?'El servidor rechazó la solicitud. Recarga la página y vuelve a iniciar sesión.':res.status>=500?`El servidor no pudo completar la consulta (HTTP ${res.status}). Intenta actualizar en unos momentos.`:`El servidor devolvió una respuesta inesperada (HTTP ${res.status}). Recarga la página e inténtalo de nuevo.`)});
  if(!res.ok){const detail=data.detail??data;throw new Error(typeof detail==='string'?detail:Array.isArray(detail)?detail.join(' '):JSON.stringify(data));}
  if(data.csrf) csrf=data.csrf;
  return data;
}
export const n=value=>new Intl.NumberFormat('es-MX').format(value??0);
export const when=value=>value?new Date(value).toLocaleString('es-MX'):'Sin sincronización';
