const value=n=>Number(n)||0;
export function groupOrders(rows,by='client'){
 const groups=new Map();
 for(const row of rows){
  const key=by==='week'?`${row.year}-${row.week}`:row.client;
  if(!groups.has(key))groups.set(key,{key,label:by==='week'?`Semana ${row.week}`:row.client,year:row.year,week:row.week,client:row.client,quantity:0,applied:0,pending:0,count:0});
  const group=groups.get(key);group.quantity+=value(row.quantity);group.applied+=value(row.applied);group.pending+=value(row.pending);group.count++;
 }
 return [...groups.values()].sort((a,b)=>b.pending-a.pending||b.quantity-a.quantity||a.label.localeCompare(b.label));
}
export function activityDays(records,end,length=7){
 const anchor=new Date(end+'T12:00:00Z');
 if(!Number.isFinite(anchor.getTime()))return [];
 const days=Array.from({length},(_,i)=>{const date=new Date(anchor);date.setUTCDate(anchor.getUTCDate()-length+1+i);return {date:date.toISOString().slice(0,10),total:0,shifts:{}}});
 const indexed=new Map(days.map(day=>[day.date,day]));
 for(const record of records||[]){const day=indexed.get(record.operational_date);if(!day)continue;const shift=record.shift__code||'Sin turno';day.shifts[shift]=(day.shifts[shift]||0)+value(record.quantity);day.total+=value(record.quantity)}
 return days;
}
export function chartMaximum(amount){
 if(amount<=0)return 100;
 const power=10**Math.floor(Math.log10(amount));
 return [1,2,4,5,8,10].map(step=>step*power).find(step=>step>=amount)||10*power;
}
export function urgentOrders(rows){return rows.filter(row=>row.pending>0).slice().sort((a,b)=>a.priority-b.priority||a.year-b.year||a.week-b.week||b.pending-a.pending).slice(0,5)}
