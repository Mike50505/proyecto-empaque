import React,{useId,useState} from 'react';
import {Search,X} from 'lucide-react';
import {validExtraParts} from './ExtraPartPicker';

export default function FloorPartSearch({parts,value,onChange}){
 const id=useId(),[open,setOpen]=useState(false),[active,setActive]=useState(-1);
 const query=value.trim().toLocaleLowerCase();
 const numbers=[...new Set(validExtraParts(parts).map(part=>part.number))];
 const matches=query?numbers.filter(number=>number.toLocaleLowerCase().includes(query)).sort((a,b)=>Number(b.toLocaleLowerCase()===query)-Number(a.toLocaleLowerCase()===query)||a.localeCompare(b)).slice(0,12):[];
 const expanded=open&&!!query;
 const choose=number=>{onChange(number);setOpen(false);setActive(-1)};
 return <div className="floor-search-control" role="search" aria-label="Buscar por número de parte"><Search size={17} aria-hidden="true"/><input type="search" role="combobox" aria-label="Buscar número de parte en pantalla completa" placeholder="Buscar número de parte..." autoComplete="off" aria-autocomplete="list" aria-expanded={expanded} aria-controls={id} aria-activedescendant={expanded&&active>=0?id+'-'+active:undefined} value={value} onFocus={()=>setOpen(true)} onBlur={()=>setOpen(false)} onChange={event=>{onChange(event.target.value);setOpen(true);setActive(-1)}} onKeyDown={event=>{
  if(event.key==='ArrowDown'||event.key==='ArrowUp'){event.preventDefault();setOpen(true);setActive(index=>matches.length?(event.key==='ArrowDown'?(index+1)%matches.length:index<0?matches.length-1:(index-1+matches.length)%matches.length):-1)}
  if(event.key==='Enter'&&expanded&&active>=0&&matches[active]){event.preventDefault();choose(matches[active])}
  if(event.key==='Escape'&&expanded){event.preventDefault();event.stopPropagation();setOpen(false)}
 }}/>{value&&<button type="button" className="floor-search-clear" aria-label="Limpiar búsqueda de número de parte" onClick={()=>{onChange('');setOpen(false);setActive(-1)}}><X size={15}/></button>}{expanded&&<div id={id} role="listbox" aria-label="Números de parte existentes" className="floor-part-options">{matches.length?matches.map((number,index)=><button type="button" role="option" id={id+'-'+index} aria-selected={active===index} className={active===index?'active':''} key={number} onMouseDown={event=>event.preventDefault()} onClick={()=>choose(number)}>{number}</button>):<p>No hay piezas del catálogo con ese número.</p>}</div>}</div>;
}
