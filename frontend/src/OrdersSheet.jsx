import React,{useState,useEffect} from 'react';
import {Plus,ArrowUpRight,Download,Printer,Settings,Trash2} from 'lucide-react';
import {n} from './api';
import ClientPicker from './ClientPicker';
import {isOrderComplete} from './order-status';

export default function OrdersSheet({rows,catalog,filters,onFilter,onClear,onCapture,updatedAt,loading,canCapture,canPlan,onImport,onRevise,onDeleteDemand,params,totals={}}){
  const [page,setPage]=useState(0);
  const size=30,maxPage=Math.max(0,Math.ceil(rows.length/size)-1),current=Math.min(page,maxPage);
  useEffect(()=>setPage(0),[params]);
  const programs=catalog?.programs||[];
  const workWeeks=catalog?.work_weeks||[];
  const years=[...new Set([...programs,...workWeeks].map(p=>p.year))].sort();
  const empty=loading?'Cargando órdenes…':programs.length?'No hay órdenes con estos filtros.':'Todavía no hay programas.';
  return <div className="orders-workspace">
    <div className="metrics">
      <Summary label="Programado" value={totals.quantity} detail="Demanda de las órdenes visibles" loading={loading}/>
      <Summary label="Empacado" value={totals.packed} detail="Piezas físicas registradas" loading={loading}/>
      <Summary label="Por liberar" value={totals.pending_release} detail="Empacado pendiente de liberación" loading={loading}/>
      <Summary label="Pendiente por cumplir" value={totals.pending} detail="Programa menos piezas aplicadas" loading={loading}/>
    </div>
    {rows.some(r=>r.catalog_error)&&<div className="notice error" role="alert">{rows.filter(r=>r.catalog_error).length} órdenes tienen una relación pieza–cliente inválida en Universo. Sus capturas están bloqueadas; Planeación debe revisarlas.</div>}
    <section className="capture-sheet" aria-label="Órdenes de empaque">
      <div className="panel-head"><div><h2>Programa y avance <span className="count">{rows.length} órdenes</span></h2><p>Cada orden conserva su semana. Los sobrantes se consultan en Excedentes.</p></div><div className="panel-tools"><a className="text-button" href={'/api/export/?'+params}><Download size={16}/>Exportar Excel</a><button className="icon-btn" aria-label="Imprimir órdenes" onClick={()=>window.print()}><Printer size={18}/></button>{canPlan&&<button className="text-button" onClick={onImport}>Cargar órdenes <ArrowUpRight size={16}/></button>}</div></div>
      <ClientPicker client={filters.client} subclient={filters.subclient} onChange={(client,subclient)=>{onFilter('client',client);onFilter('subclient',subclient)}}/>
      <div className="sheet-controls">
        <label>Número de parte o diámetro<input type="search" placeholder="Buscar pieza o diámetro" value={filters.search} onChange={e=>onFilter('search',e.target.value)}/></label>
        {years.length>1&&<label>Año<select value={filters.year} onChange={e=>onFilter('year',e.target.value)}><option value="">Todos</option>{years.map(y=><option key={y}>{y}</option>)}</select></label>}
        <label>Semana<select value={filters.week} onChange={e=>onFilter('week',e.target.value)}><option value="">Todas</option>{[...new Set([...programs,...workWeeks].map(p=>p.week))].sort((a,b)=>a-b).map(w=><option key={w} value={w}>Semana {w}</option>)}</select></label>
        <label>Alcance<select value={filters.view} onChange={e=>{onFilter('view',e.target.value);if(e.target.value==='operational'&&!filters.year)onFilter('year',String(catalog?.current_year||new Date().getFullYear()))}}><option value="week">Por semana de compromiso</option><option value="operational">Con semanas anteriores</option></select></label>
        <label>Destino<select value={filters.scope} onChange={e=>onFilter('scope',e.target.value)}><option value="">Todos los destinos</option>{[...new Set(programs.map(p=>p.scope))].filter(Boolean).sort().map(scope=><option key={scope}>{scope}</option>)}</select></label>
        <label>Estado<select aria-label="Estado de las órdenes" value={filters.status} onChange={e=>onFilter('status',e.target.value)}><option value="all">Todas las órdenes</option><option value="packing">Por empacar</option><option value="release">Por liberar</option><option value="pending">Pendientes de cumplir</option><option value="complete">Completadas</option><option value="credit">Con excedente</option></select></label>
        {canPlan&&<label>Publicación<select value={filters.publication} onChange={e=>onFilter('publication',e.target.value)}><option value="published">Publicadas</option><option value="draft">Borradores</option><option value="all">Todas</option></select></label>}
        <label className="sheet-check"><input type="checkbox" checked={filters.priority==='1'} onChange={e=>onFilter('priority',e.target.checked?'1':'')}/>Solo prioridad alta</label>
        <button className="sheet-reset" onClick={onClear}>Limpiar filtros</button>
      </div>
      <div className="sheet-scroll"><table className="orders-table unified-orders"><thead><tr><th scope="col">Cliente / destino</th><th scope="col">Número de parte</th><th scope="col">Diámetro</th><th scope="col">Semana</th><th scope="col" className="numeric">Programado</th><th scope="col" className="numeric">Empacado</th><th scope="col" className="numeric">Por liberar</th><th scope="col" className="numeric">Pendiente</th><th scope="col">Cumplimiento</th>{(canCapture||canPlan)&&<th scope="col" className="order-actions">Acciones</th>}</tr></thead><tbody>
        {rows.slice(current*size,(current+1)*size).map(r=><tr key={r.id} className={isOrderComplete(r)?'order-completed':undefined}>
          <td><strong>{r.client}</strong><span className="order-context">{r.scope||'Sin destino'}</span></td>
          <td><strong>{r.part}</strong>{isOrderComplete(r)&&<span className="completed-order-badge">Terminada</span>}<span className="order-context">{r.reference}</span><span className={'priority p'+r.priority}>{r.priority===1?'Alta':r.priority===3?'Baja':'Normal'}</span>{r.catalog_error&&<span className="order-catalog-error">{r.catalog_error}</span>}{!r.published&&<span className="order-context">Borrador · sin captura</span>}</td>
          <td className="diameter-value">{r.diameter||'Sin especificar'}</td>
          <td><span className="week-tag">S{r.week}</span><span className="order-context">{r.year}</span></td>
          <td className="numeric required-count">{n(r.quantity)}</td>
          <td className="numeric packed-count"><strong>{n(r.packed)}</strong><span className="order-context">{n(r.packing_pending)} por empacar</span></td>
          <td className="numeric release-count"><strong>{n(r.pending_release)}</strong><span className="order-context">{r.pending_release?'Sin liberar':'Al día'}</span></td>
          <td className="numeric pending-number"><strong>{n(r.pending)}</strong><span className="order-context">{isOrderComplete(r)?'Terminada':'Por cumplir'}</span></td>
          <td><div className="row-progress"><span>{r.quantity?Math.round(100*r.applied/r.quantity)+'%':'Sin demanda'}</span><div className="progress"><span style={{width:(r.quantity?Math.min(100,100*r.applied/r.quantity):0)+'%'}}/></div></div><span className="order-context">{n(r.applied)} aplicadas</span></td>
          {(canCapture||canPlan)&&<td className="order-actions"><div className="row-actions">{canCapture&&r.published&&r.quantity>0&&!r.catalog_error&&<button className="sheet-capture" aria-label={'Capturar '+r.part+' orden '+r.reference} onClick={()=>onCapture(r)}><Plus size={15}/>Capturar</button>}{canPlan&&<button className="icon-btn" aria-label={'Revisar demanda '+r.part}   onClick={()=>onRevise(r)}><Settings size={16}/></button>}{canPlan&&<button className="icon-btn delete-demand-button" aria-label={'Borrar número '+r.part} title="Borrar número de este programa" disabled={loading} onClick={()=>onDeleteDemand(r)}><Trash2 size={16}/></button>}</div></td>}
        </tr>)}
      </tbody></table></div>
      {!rows.length&&<div className="sheet-empty" role="status"><b>{empty}</b><p>{loading?'':programs.length?'Cambia el estado, la semana o el cliente para consultar otras órdenes.':'Planeación puede cargar un Excel o crear un programa.'}</p>{!loading&&programs.length>0&&<button className="secondary" onClick={onClear}>Mostrar órdenes publicadas</button>}</div>}
      {rows.length>size&&<div className="pagination"><button className="secondary" disabled={current===0} onClick={()=>setPage(current-1)}>Anterior</button><span>Página {current+1} de {maxPage+1}</span><button className="secondary" disabled={current===maxPage} onClick={()=>setPage(current+1)}>Siguiente</button></div>}
      <div className="sheet-foot"><span>{rows.length} órdenes · cantidades en piezas</span><span>{updatedAt?'Actualizado '+new Date(updatedAt).toLocaleTimeString('es-MX'):'Esperando datos'} · Consulta cada 20 s</span></div>
    </section>
  </div>
}
function Summary({label,value,detail,loading}){return <article className="metric"><div className="metric-title">{label}</div><strong>{loading?'—':n(value)}</strong><small>{detail}</small></article>}
