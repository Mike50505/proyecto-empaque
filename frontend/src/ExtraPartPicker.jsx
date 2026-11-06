import React,{useId,useState} from 'react';
import {Search,CheckCircle2} from 'lucide-react';

export const validExtraParts=parts=>(parts||[]).filter(part=>part.universe_id&&!part.provisional&&part.attributes?.active!==false&&String(part.universe_customer||part.customer||'').trim());
const normalized=value=>String(value||'').trim().toLocaleLowerCase();
export function selectedExtraPart(parts,number,id){
  const matches=parts.filter(part=>normalized(part.number)===normalized(number));
  return (id?matches.find(part=>String(part.id)===String(id)):matches.length===1?matches[0]:null)||null;
}

export default function ExtraPartPicker({parts,value,selected,onChange,onSelect,ready}){
  const id=useId(),[open,setOpen]=useState(false),[active,setActive]=useState(-1);
  const query=normalized(value);
  const matches=query?parts.filter(part=>normalized(part.number).includes(query)).sort((a,b)=>Number(normalized(b.number)===query)-Number(normalized(a.number)===query)||a.number.localeCompare(b.number)).slice(0,12):[];
  const choose=part=>{onSelect(part);setOpen(false);setActive(-1)};
  return <div className="extra-part-picker"><label htmlFor={id}>Número de parte</label><div className="extra-part-input"><Search size={17} aria-hidden="true"/><input id={id} type="search" role="combobox" aria-autocomplete="list" aria-controls={id+'-options'} aria-expanded={open&&!!query} aria-activedescendant={open&&active>=0?id+'-option-'+active:undefined} aria-describedby={id+'-hint'} autoComplete="off" required maxLength={120} autoFocus value={value} onFocus={()=>setOpen(true)} onBlur={()=>setOpen(false)} onChange={event=>{onChange(event.target.value);setOpen(true);setActive(-1)}} onKeyDown={event=>{
    if(event.key==='ArrowDown'||event.key==='ArrowUp'){event.preventDefault();setOpen(true);setActive(index=>matches.length?(event.key==='ArrowDown'?(index+1)%matches.length:index<0?matches.length-1:(index-1+matches.length)%matches.length):-1)}
    if(event.key==='Enter'&&open&&active>=0&&matches[active]){event.preventDefault();choose(matches[active])}
    if(event.key==='Escape'&&open){event.preventDefault();event.stopPropagation();setOpen(false)}
  }}/></div>{open&&query&&<div id={id+'-options'} role="listbox" className="extra-part-options" aria-label="Piezas existentes">{matches.length?matches.map((part,index)=><button type="button" role="option" id={id+'-option-'+index} aria-selected={selected?.id===part.id} className={active===index?'active':''} key={part.id} onMouseDown={event=>event.preventDefault()} onClick={()=>choose(part)}><strong>{part.number}</strong><small>{part.universe_customer||part.customer}{part.scope?' · '+part.scope:''}{part.diameter?' · Ø '+part.diameter:''}</small></button>):<p>No hay piezas válidas con ese número.</p>}</div>}<small id={id+'-hint'} className={selected?'extra-part-valid':'extra-part-hint'}>{!ready?'El catálogo todavía no está disponible.':selected?<><CheckCircle2 size={14}/>Pieza validada · {selected.universe_customer||selected.customer}{selected.scope?' · '+selected.scope:''}</>:query?'Selecciona una pieza existente o escribe su número completo. No se permiten piezas nuevas o inactivas.':'Escribe para buscar en el catálogo validado de Universo Ramos.'}</small></div>;
}
