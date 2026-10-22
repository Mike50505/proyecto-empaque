import React,{useEffect,useMemo,useState} from 'react';
import {Download,RefreshCw} from 'lucide-react';
import {api,n} from './api';

const keyOf=date=>`${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
const parseDate=value=>{const [year,month,day]=value.split('-').map(Number);return new Date(year,month-1,day)};
const formatDate=value=>parseDate(value).toLocaleDateString('es-MX',{day:'2-digit',month:'2-digit',year:'2-digit'});
const initialRange=()=>{const end=new Date(),start=new Date();start.setDate(end.getDate()-4);return {from:keyOf(start),to:keyOf(end)}};

export default function DailyProduction({tick}){
 const [events,setEvents]=useState([]),[error,setError]=useState(''),[range,setRange]=useState(initialRange),[loading,setLoading]=useState(true),[refresh,setRefresh]=useState(0);
 useEffect(()=>{let current=true;setLoading(true);api('captures/').then(result=>{if(current){setEvents(result);setError('')}}).catch(e=>{if(current)setError(e.message)}).finally(()=>{if(current)setLoading(false)});return()=>{current=false}},[tick,refresh]);
 const days=useMemo(()=>{const start=parseDate(range.from),end=parseDate(range.to);if(Number.isNaN(start.getTime())||Number.isNaN(end.getTime())||start>end)return[];const result=[];for(const d=new Date(start);d<=end;d.setDate(d.getDate()+1))result.push(keyOf(d));return result},[range]);
 const {rows,totals}=useMemo(()=>{
  const grouped=new Map(),totals={};
  for(const day of days)totals[day]={A:0,B:0,all:0};
  for(const event of events){if(event.voided||!days.includes(event.operational_date))continue;
   const id=event.demand??`${event.part}|${event.client}|${event.year}|${event.week}|${event.scope}`;
   let row=grouped.get(id);if(!row){row={id,part:event.part,client:event.client,scope:event.scope,year:event.year,week:event.week,days:{},all:0};grouped.set(id,row)}
   const shift=event.shift==='A'?'A':'B',day=event.operational_date,quantity=Number(event.quantity)||0;
   row.days[day]??={A:0,B:0,all:0};row.days[day][shift]+=quantity;row.days[day].all+=quantity;row.all+=quantity;
   totals[day][shift]+=quantity;totals[day].all+=quantity;
  }
  return {rows:[...grouped.values()].sort((a,b)=>a.part.localeCompare(b.part,'es',{numeric:true})||a.year-b.year||a.week-b.week),totals};
 },[events,days]);
 const grandTotal=rows.reduce((sum,row)=>sum+row.all,0);
 return <section className="panel daily-production">
  <div className="panel-head"><div><h2>Registro por día <span className="count">{rows.length} piezas</span></h2><p>Empaque capturado por fecha operativa y turno. Las capturas anuladas quedan excluidas.</p></div><div className="panel-tools"><a className="text-button" href="/api/production-export/"><Download size={16}/>Exportar registros</a><button className="icon-btn" aria-label="Actualizar producción diaria" onClick={()=>setRefresh(value=>value+1)}><RefreshCw size={17}/></button></div></div>
  <div className="filters daily-filters"><label className="field"><span>Desde</span><input type="date" value={range.from} onChange={e=>setRange(value=>({...value,from:e.target.value}))}/></label><label className="field"><span>Hasta</span><input type="date" value={range.to} min={range.from} onChange={e=>setRange(value=>({...value,to:e.target.value}))}/></label><span className="daily-total">Total del periodo <b>{n(grandTotal)} pzas.</b></span></div>
  {error&&<div className="notice error" role="alert">{error}</div>}
  {!loading&&!error&&!rows.length?<div className="empty"><h3>Sin capturas en este periodo</h3><p>Elige otras fechas para consultar los registros de empaque.</p></div>:<div className="table-scroll daily-table-scroll"><table className="daily-table"><thead><tr><th rowSpan="2">Número de parte / semana</th>{days.map(day=><th key={day} colSpan="2" className="daily-date-head">{formatDate(day)}</th>)}<th rowSpan="2" className="numeric daily-ayb">AYB</th></tr><tr>{days.flatMap(day=>[<th key={day+'-A'} className="numeric">A</th>,<th key={day+'-B'} className="numeric">B</th>])}</tr></thead><tbody>{rows.map(row=><tr key={row.id}><td><b>{row.part}</b><small className="part-detail">{row.client} · S{row.week}/{row.year}{row.scope?` · ${row.scope}`:''}</small></td>{days.flatMap(day=>[<td className="numeric" key={row.id+day+'A'}>{row.days[day]?.A?n(row.days[day].A):'—'}</td>,<td className="numeric" key={row.id+day+'B'}>{row.days[day]?.B?n(row.days[day].B):'—'}</td>])}<td className="numeric daily-ayb"><b>{n(row.all)}</b></td></tr>)}</tbody><tfoot><tr><th>Total por turno</th>{days.flatMap(day=>[<td className="numeric" key={day+'totalA'}>{n(totals[day]?.A||0)}</td>,<td className="numeric" key={day+'totalB'}>{n(totals[day]?.B||0)}</td>])}<td className="numeric daily-ayb"><b>{n(grandTotal)}</b></td></tr></tfoot></table></div>}
  <div className="table-footer"><span>{loading?'Consultando capturas…':`${rows.length} renglones · ${days.length} días`}</span><span>Solo se excluyen registros anulados</span></div>
 </section>
}
