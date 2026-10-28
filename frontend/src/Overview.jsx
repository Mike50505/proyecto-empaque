import React from 'react';
import {Upload,CalendarDays,ClipboardList,PackageCheck,ArrowUpRight,ArrowRight,History,Boxes,LayoutDashboard} from 'lucide-react';
import {n} from './api';

export default function Overview({rows,catalog,session,onNavigate,onReset,filtered,loading}) {
  const published=rows.filter(r=>r.published);
  const sum=key=>published.reduce((total,r)=>total+Number(r[key]||0),0);
  const quantity=sum('quantity'),applied=sum('applied'),pending=sum('pending');
  const urgent=published.filter(r=>r.pending>0).sort((a,b)=>a.priority-b.priority||a.year-b.year||a.week-b.week).slice(0,5);
  const steps=[
    {page:'Importaciones',icon:Upload,title:'Cargar programa',text:'Sube el Excel y revisa las órdenes antes de guardarlas.',allowed:session.roles.plan},
    {page:'Programas',icon:CalendarDays,title:'Publicar semanas',text:'Prepara la demanda y habilita el trabajo para piso.',allowed:session.roles.plan},
    {page:'Órdenes',icon:PackageCheck,title:'Registrar empaque',text:'Elige la orden y agrega las piezas que se terminaron.',allowed:session.roles.capture},
    {page:'Historial',icon:History,title:'Consultar resultados',text:'Revisa folios, responsables y liberaciones.',allowed:true}
  ];
  return <div className="overview">
    <div className="overview-caption"><span><span className="small-dot"/>Resumen de programas publicados · {filtered?'Filtros personales activos':'Todos los clientes y semanas'}</span>{filtered&&<button className="text-button" onClick={onReset}>Ver toda la operación</button>}</div>
    <div className="metrics"><Summary label="Piezas programadas" value={loading?'—':n(quantity)} detail="Demanda publicada"/><Summary label="Empaque aplicado" value={loading?'—':n(applied)} detail="Piezas liberadas al programa"/><Summary label="Pendiente por cumplir" value={loading?'—':n(pending)} detail="Conserva su semana de origen"/><Summary label="Cumplimiento" value={loading?'—':quantity?Math.round(applied/quantity*100)+'%':'Sin programa'} detail="Ponderado por cantidad"/></div>
    <section className="workflow-section"><div className="section-title"><div><h2>Tu recorrido de trabajo</h2><p>Del programa a la captura, con seguimiento en cada paso.</p></div><span className="suite-kicker">OPERACIÓN DE EMPAQUE</span></div><div className="workflow-grid">{steps.filter(s=>s.allowed).map((s,i)=><button className="workflow-card" key={s.page} onClick={()=>onNavigate(s.page)}><div className="workflow-top"><span className="module-icon"><s.icon size={23}/></span><span className="step-number">0{i+1}</span></div><h3>{s.title}</h3><p>{s.text}</p><span className="module-link">Abrir módulo <ArrowUpRight size={17}/></span></button>)}</div></section>
    <div className="overview-bottom"><section className="panel"><div className="panel-head"><div><h2>Órdenes por atender</h2><p>Primero la prioridad; después, la semana de compromiso.</p></div><button className="text-button" onClick={()=>onNavigate('Órdenes')}>Ver órdenes <ArrowRight size={16}/></button></div>{urgent.length?<div className="table-scroll"><table><thead><tr><th>Pieza / cliente</th><th>Compromiso</th><th>Prioridad</th><th className="numeric">Pendiente</th></tr></thead><tbody>{urgent.map(r=><tr key={r.id}><td><b className="part-number">{r.part}</b><small className="part-detail">{r.client} · {r.scope}</small></td><td>{r.year} / S{r.week}</td><td><span className={'priority p'+r.priority}>{r.priority===1?'Alta':r.priority===3?'Baja':'Normal'}</span></td><td className="numeric"><b>{n(r.pending)}</b></td></tr>)}</tbody></table></div>:<div className="empty"><Boxes size={30}/><h3>{loading?'Cargando operación…':'Sin pendientes en este alcance'}</h3><p>{catalog?.programs.length?'Consulta otros filtros o revisa las órdenes.':'Carga y publica el primer programa para comenzar.'}</p></div>}</section>{session.roles.plan&&<section className="panel overview-follow"><span className="module-icon"><LayoutDashboard size={25}/></span><h2>El avance, a la vista</h2><p>Compara programa y cumplimiento por pieza, cliente y semana. Consulta el empaque físico por fecha y turno.</p><button className="primary" onClick={()=>onNavigate('Dashboard')}>Ver dashboard <ArrowRight size={17}/></button><a href="https://universo.mesaramos.com/" target="_blank" rel="noreferrer">Consultar Universo Ramos <ArrowUpRight size={15}/></a></section>}</div>
  </div>;
}
function Summary({label,value,detail}) {return <article className="metric"><div className="metric-title">{label}</div><strong>{value}</strong><small>{detail}</small></article>}
