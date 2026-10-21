import React,{useId,useRef,useState} from 'react';
import {Layers,ChevronDown} from 'lucide-react';
import {CLIENT_GROUPS,CLIENT_SUBCLIENTS} from './client-groups';

function SubclientDropdown({group,children,value,onChange}){
 const id=useId(),menu=useRef(null),trigger=useRef(null);
 const [open,setOpen]=useState(false);
 const options=[{label:'Todos',value:''},...children];
 const show=()=>{
  const panel=menu.current;
  if(panel.matches(':popover-open')){panel.hidePopover();return;}
  const rect=trigger.current.getBoundingClientRect(),width=Math.min(240,window.innerWidth-16);
  const below=window.innerHeight-rect.bottom-8,above=rect.top-8;
  const upwards=below<240&&above>below;
  Object.assign(panel.style,{width:`${width}px`,left:`${Math.max(8,Math.min(rect.right-width,window.innerWidth-width-8))}px`,top:upwards?'auto':`${rect.bottom+6}px`,bottom:upwards?`${window.innerHeight-rect.top+6}px`:'auto',maxHeight:`${Math.max(80,(upwards?above:below)-6)}px`});
  panel.showPopover();
  panel.querySelector('[aria-checked="true"]')?.focus({preventScroll:true});
 };
 const navigate=event=>{
  const buttons=[...menu.current.querySelectorAll('[role="menuitemradio"]')];
  const index=buttons.indexOf(document.activeElement);
  let next;
  if(event.key==='ArrowDown')next=(index+1)%buttons.length;
  if(event.key==='ArrowUp')next=(index-1+buttons.length)%buttons.length;
  if(event.key==='Home')next=0;
  if(event.key==='End')next=buttons.length-1;
  if(next!==undefined){event.preventDefault();buttons[next].focus();}
  if(event.key==='Escape'){event.preventDefault();menu.current.hidePopover();trigger.current.focus();}
  if(event.key==='Tab')menu.current.hidePopover();
 };
 return <>
  <button ref={trigger} type="button" className="client-subfilter-toggle" aria-label={'Subclientes de '+group} aria-haspopup="menu" aria-controls={id} aria-expanded={open} onClick={show}>
   <ChevronDown size={14} aria-hidden="true"/>
  </button>
  <div ref={menu} id={id} popover="auto" role="menu" aria-label={'Subclientes de '+group} className="client-submenu" onToggle={event=>setOpen(event.newState==='open')} onKeyDown={navigate}>
   {options.map(option=><button key={option.value} type="button" role="menuitemradio" aria-checked={value===option.value} onClick={()=>{onChange(option.value);menu.current.hidePopover();trigger.current.focus();}}>{option.label}</button>)}
  </div>
 </>;
}

export default function ClientPicker({client='',subclient='',onChange,floor=false}){
 const choose=(group,child='')=>onChange(group,child);
 return <div className={'client-picker '+(floor?'client-picker-floor group-tabs':'client-picker-orders sheet-clients')} aria-label="Filtrar por cliente">
  <button type="button" className={'client-picker-all '+(!client?'selected':'')} onClick={()=>choose('','')}>
   {floor&&<Layers size={16}/>}<span>Todos los clientes</span>{floor&&<small>{CLIENT_GROUPS.length}</small>}
  </button>
  {CLIENT_GROUPS.map(group=>{
   const children=CLIENT_SUBCLIENTS[group]||[];
   const active=client===group;
   return <div className={'client-picker-item '+(children.length?'has-subclients ':'')+(active?'is-active':'')} key={group}>
    <button type="button" className={'client-picker-main '+(active?'selected':'')} aria-pressed={active} onClick={()=>choose(group,'')}>{group}{active&&subclient&&<small className="client-picker-current">· {children.find(child=>child.value===subclient)?.label||'Subcliente'}</small>}</button>
    {children.length>0&&<SubclientDropdown group={group} children={children} value={active?subclient:''} onChange={child=>choose(group,child)}/>}
   </div>;
  })}
 </div>;
}
