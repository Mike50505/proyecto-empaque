import React,{useEffect,useState,useDeferredValue} from 'react';
import {Boxes,RefreshCw} from 'lucide-react';
import {api,n} from './api';

export default function Surplus({tick,catalog}) {
  const [filters,setFilters]=useState({search:'',client:'',scope:'',year:'',week:''});
  const [data,setData]=useState(null),[error,setError]=useState(''),[loading,setLoading]=useState(true),[refresh,setRefresh]=useState(0),[page,setPage]=useState(0);
  const search=useDeferredValue(filters.search);
  const params=new URLSearchParams(Object.entries({...filters,search}).filter(([,value])=>value)).toString();
  useEffect(()=>{
    let current=true;setLoading(true);setError('');setPage(0);
    api('surplus/?'+params).then(result=>{if(current)setData(result)}).catch(error=>{if(current)setError(error.message)}).finally(()=>{if(current)setLoading(false)});
    return()=>{current=false};
  },[params,tick,refresh]);
  const change=(key,value)=>setFilters(current=>({...current,[key]:value}));
  const rows=data?.rows||[],size=40,maxPage=Math.max(0,Math.ceil(rows.length/size)-1),currentPage=Math.min(page,maxPage);
  const programs=catalog?.programs||[];
  return <section className="panel surplus-panel" aria-label="Excedentes disponibles">
    <div className="panel-head"><div><h2>Excedentes disponibles</h2><p>Piezas liberadas que sobraron después de cubrir su orden. Cada saldo conserva su origen.</p></div><button className="secondary" onClick={()=>setRefresh(value=>value+1)} disabled={loading}><RefreshCw size={16}/>Actualizar excedentes</button></div>
    <div className="metrics"><article className="metric"><div className="metric-title">Piezas excedentes<Boxes size={18}/></div><strong>{loading?'…':n(data?.total)}</strong><small>Saldo disponible en los filtros seleccionados</small></article><article className="metric"><div className="metric-title">Números de parte</div><strong>{loading?'…':n(new Set(rows.map(row=>row.part)).size)}</strong><small>Piezas con sobrante disponible</small></article></div>
    <div className="filters">
      <label className="field"><span>Número de parte o diámetro</span><input type="search" value={filters.search} onChange={event=>change('search',event.target.value)}/></label>
      <label className="field"><span>Cliente</span><select value={filters.client} onChange={event=>change('client',event.target.value)}><option value="">Todos</option>{(catalog?.clients||[]).map(client=><option key={client}>{client}</option>)}</select></label>
      <label className="field"><span>Destino</span><input value={filters.scope} onChange={event=>change('scope',event.target.value)}/></label>
      <label className="field"><span>Año de origen</span><select value={filters.year} onChange={event=>change('year',event.target.value)}><option value="">Todos</option>{[...new Set(programs.map(program=>program.year))].sort().map(year=><option key={year}>{year}</option>)}</select></label>
      <label className="field"><span>Semana de origen</span><select value={filters.week} onChange={event=>change('week',event.target.value)}><option value="">Todas</option>{[...new Set(programs.map(program=>program.week))].sort((a,b)=>a-b).map(week=><option key={week} value={week}>Semana {week}</option>)}</select></label>
      <button className="text-button" onClick={()=>setFilters({search:'',client:'',scope:'',year:'',week:''})}>Limpiar filtros</button>
    </div>
    {error?<div className="notice error" role="alert">{error}</div>:loading?<p role="status">Consultando excedentes…</p>:rows.length?<>
      <div className="table-scroll"><table><thead><tr><th>Número de parte</th><th>Cliente / destino</th><th>Orden / semana de origen</th><th>Fecha</th><th className="numeric">Excedente disponible</th><th>Folio de origen</th><th>Empacador / quien libera</th></tr></thead><tbody>{rows.slice(currentPage*size,(currentPage+1)*size).map(row=><tr key={row.id}><td><b>{row.part}</b><small className="part-detail">Ø {row.diameter||'Sin especificar'}</small></td><td>{row.client}<small className="part-detail">{row.scope||'Sin destino'}</small></td><td>{row.reference}<small className="part-detail">{row.year}/S{row.week}{row.archived?' · Orden retirada':''}</small></td><td>{row.date}</td><td className="numeric"><b>{n(row.quantity)}</b> pzas.</td><td>{row.kind} #{row.source}</td><td>{row.packer||'—'} / {row.inspector||'—'}</td></tr>)}</tbody></table></div>
      {rows.length>size&&<div className="pagination"><button className="secondary" disabled={!currentPage} onClick={()=>setPage(value=>value-1)}>Anterior</button><span>{currentPage+1} / {maxPage+1}</span><button className="secondary" disabled={currentPage>=maxPage} onClick={()=>setPage(value=>value+1)}>Siguiente</button></div>}
    </>:<div className="empty"><Boxes size={32}/><h3>No hay excedentes disponibles</h3><p>Cuando una captura supere el pendiente de su orden, el sobrante aparecerá aquí.</p></div>}
    <p className="bottom-note">Los excedentes permanecen disponibles; no se trasladan automáticamente a otra semana ni cuentan como producción nueva.</p>
  </section>;
}
