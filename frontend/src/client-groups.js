export const CLIENT_GROUPS=Object.freeze(['DAIKIN','LENNOX 1','MESA MTY','RHEEM']);
export const CLIENT_SUBCLIENTS=Object.freeze({
 'MESA MTY':[
  {label:'BRAZEWAY',value:'MESA MTY / BRAZEWAY'},
  {label:'CARRIER',value:'MESA MTY / CARRIER'},
  {label:'CARRIER A',value:'MESA MTY / CARRIER A'},
  {label:'CARRIER D',value:'MESA MTY / CARRIER D'},
  {label:'LENNOX 2',value:'MESA MTY / LENNOX 2'},
  {label:'TRANE',value:'MESA MTY / TRANE'}
 ],
 RHEEM:[
  {label:'CIP-3501',value:'RHEEM CIP-3501'},
  {label:'FALCON',value:'RHEEM FALCON'},
  {label:'NIPLES',value:'RHEEM NIPLES'},
  {label:'TRANSFERENCIA',value:'RHEEM TRANSFERENCIA'}
 ]
});
export function normalizeClientGroup(value){
 const key=String(value||'').trim().toLocaleLowerCase('es-MX');
 const groupMatch=CLIENT_GROUPS.find(group=>group.toLocaleLowerCase('es-MX')===key);
 if(groupMatch)return groupMatch;
 for(const [group,children] of Object.entries(CLIENT_SUBCLIENTS)){
  if(children.some(child=>child.value.toLocaleLowerCase('es-MX')===key))return group;
 }
 return value||'';
}
