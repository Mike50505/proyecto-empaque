import React,{useEffect,useState} from 'react';
import {api,n,when} from './api';

const modes={new:'Órdenes nuevas',revision:'Revisión de cantidades',opening:'Saldo inicial',reconcile:'Conciliación',history:'Histórico de consulta'};
export default function ImportOrders({mutate,onOpenCapture}){
 const [batch,setBatch]=useState(null),[history,setHistory]=useState([]),[mode,setMode]=useState('new'),[file,setFile]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [mapping,setMapping]=useState({reason:'Carga de órdenes de empaque',sheet:''});
 const [advanced,setAdvanced]=useState('');
 const refresh=async()=>setHistory(await api('imports/'));
 useEffect(()=>{refresh().catch(e=>setError(e.message))},[]);
 const blocked=batch?.preview.issues.some(i=>i.severity==='blocking');
 const canPublish=batch&&['new','opening'].includes(batch.mode||mode)&&!batch.missing_programs?.length;
 const update=(key,value)=>{setMapping(m=>({...m,[key]:value}));setBatch(null)};
 async function analyze(e){e.preventDefault();setError('');setBusy(true);try{
   const data=new FormData();data.set('file',file);data.set('mode',mode);data.set('mapping',JSON.stringify({...mapping,...(advanced?JSON.parse(advanced):{})}));
   const result=await api('imports/',{method:'POST',body:data});setBatch(result);setMapping(m=>({...m,sheet:result.preview.mapping?.sheet||''}));await refresh();
 }catch(e){setError(e.message)}finally{setBusy(false)}}
 async function confirm(publish){setError('');setBusy(true);try{
   const result=await mutate(`imports/${batch.id}/`,{publish},publish?'Órdenes publicadas.':'Carga guardada.');setBatch(result);await refresh();
 }catch(e){setError(e.message)}finally{setBusy(false)}}
 return <div className="orders-import">
 <ol className="import-steps" aria-label="Proceso de carga"><li>1. Elegir Excel</li><li>2. Revisar órdenes</li><li>3. Publicar en Órdenes</li></ol>
 {error&&<div className="notice error" role="alert">{error}</div>}
 <section className="panel"><div className="panel-head"><h2>Cargar órdenes desde Excel</h2><a className="text-button" href={'/api/template/?mode='+mode}>Descargar plantilla</a></div>
 <form className="padded" onSubmit={analyze}>
 <div className="form-grid"><label className="field"><span>Archivo Excel</span><input type="file" accept=".xlsx" required onChange={e=>{setFile(e.target.files[0]||null);setBatch(null);setMapping(m=>({...m,sheet:''}))}}/></label>
 <label className="field"><span>Tipo de carga</span><select value={mode} onChange={e=>{setMode(e.target.value);setBatch(null)}}>{Object.entries(modes).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label></div>
 <p>{mode==='revision'?'Para revisar cantidades conserva el folio que el sistema ya asignó a cada orden.':'Completa cliente, destino, semana, pieza y cantidad. El año actual y el folio de cada orden se asignan automáticamente.'} Cada pieza debe pertenecer al cliente indicado en Universo Ramos. Revisar el Excel todavía no guarda órdenes.</p>
 <details className="import-options"><summary>Ajustes para balances anteriores o archivos con varias hojas</summary><div className="form-grid">
 <label className="field"><span>Hoja del archivo</span>{batch?.preview.sheets?.length?<select value={mapping.sheet} onChange={e=>update('sheet',e.target.value)}><option value="">Detectar plantilla automáticamente</option>{batch.preview.sheets.map(s=><option key={s}>{s}</option>)}</select>:<input value={mapping.sheet} placeholder="Detección automática para plantilla" onChange={e=>update('sheet',e.target.value)}/>}</label>
 {['week','balance_column','cutoff'].map((key,i)=><label className="field" key={key}><span>{['Semana','Columna de saldo','Fecha/hora de corte con zona'][i]}</span><input value={mapping[key]||''} onChange={e=>update(key,e.target.value)}/></label>)}
 <label className="field"><span>Columnas de demanda, separadas por coma</span><input value={(mapping.quantity_columns||[]).join(',')} onChange={e=>update('quantity_columns',e.target.value.toUpperCase().split(',').map(s=>s.trim()).filter(Boolean))}/></label></div>
 {[['resolve_week','Confirmo la semana efectiva'],['resolve_version','Confirmo la versión de la hoja']].map(([key,text])=><label className="checkbox" key={key}><input type="checkbox" checked={!!mapping[key]} onChange={e=>update(key,e.target.checked)}/>{text}</label>)}
 <label className="field"><span>Vinculación adicional (JSON)</span><textarea value={advanced} onChange={e=>{setAdvanced(e.target.value);setBatch(null)}} placeholder={'{"program_id":1,"line_resolutions":{"11":4}}'}/></label></details>
 <label className="field"><span>Descripción de la carga</span><input value={mapping.reason} onChange={e=>update('reason',e.target.value)} required/></label>
 <button className="primary" disabled={!file||busy}>{busy?'Procesando…':'Revisar Excel'}</button>
 </form></section>
 {batch&&<section className="panel import-review"><div className="panel-head"><div><h2>{batch.missing_programs?.length?'Carga con programas eliminados':batch.applied?canPublish?batch.visible_in_capture?'Órdenes publicadas':'Guardado como borrador':'Carga confirmada':'Revisión antes de guardar'}</h2><p>Hoja {batch.preview.mapping?.sheet||'sin seleccionar'} · {batch.preview.rows.length} órdenes · {n(batch.preview.totals?.quantity)} piezas</p></div></div>
 <div className="padded">{batch.missing_programs?.length>0&&<div className="notice warning">Se eliminaron programas de esta carga. El archivo se conserva como evidencia y no vuelve a crear las órdenes eliminadas. Para una nueva carga, revisa y vuelve a importar el archivo con una nueva descripción.</div>}{batch.preview.issues.map((issue,i)=><div className={'notice '+(issue.severity==='blocking'?'error':'warning')} key={i} role={issue.severity==='blocking'?'alert':'status'}>{issue.sheet} {issue.cell}: {issue.message}</div>)}
 {batch.applied&&!batch.visible_in_capture&&canPublish&&<div className="notice warning">Las órdenes están guardadas, pero aún no aparecen al operador. Pulsa «Publicar órdenes».</div>}
 <div className="table-scroll"><table><thead><tr><th>Orden</th><th>Número de parte</th><th>Cliente / destino</th><th>Semana</th><th className="numeric">Cantidad</th></tr></thead><tbody>{batch.preview.rows.map(r=><tr key={r.row}><td>{batch.mode==='new'&&!batch.applied?'Se asigna al importar':r.reference}</td><td>{r.part}</td><td>{r.client}<small className="part-detail">{r.scope}</small></td><td>{r.year} / {r.week}</td><td className="numeric">{n(r.quantity)}</td></tr>)}</tbody></table></div>
 <div className="import-actions">{batch.visible_in_capture?<button className="primary" onClick={()=>onOpenCapture(batch.programs)}>Ver órdenes</button>:<>
 {canPublish&&<button className="primary" disabled={blocked&&!batch.applied||busy||!batch.preview.rows.length} onClick={()=>confirm(true)}>{batch.applied?'Publicar órdenes':'Importar y publicar órdenes'}</button>}
 {!batch.applied&&<button className="secondary" disabled={blocked||busy||!batch.preview.rows.length} onClick={()=>confirm(false)}>{canPublish?'Guardar como borrador':'Confirmar carga'}</button>}
 </>}</div>
 {batch.applied&&batch.visible_in_capture&&<p className="import-success" role="status">{batch.preview.rows.length} órdenes publicadas. Usa «Ver órdenes» para abrirlas sin filtros anteriores.</p>}
 <details><summary>Ver evidencia y filas omitidas</summary><pre>{JSON.stringify({omitted:batch.preview.omitted,controls:batch.preview.controls,reconciliation:batch.preview.reconciliation},null,2)}</pre></details>
 </div></section>}
 <section className="panel"><div className="panel-head"><h2>Cargas anteriores</h2></div>{history.map(b=><button className="history-batch" key={b.id} onClick={async()=>{try{setError('');setBatch(await api(`imports/${b.id}/`))}catch(e){setError(e.message)}}}><b>#{b.id} · {b.mapping.sheet||'Sin hoja'}</b><span>{modes[b.mode]}</span><span>{when(b.created_at)}</span><span>{b.applied?'Guardado · abrir para ver publicación':'Pendiente de revisión'}</span></button>)}</section>
 </div>
}
