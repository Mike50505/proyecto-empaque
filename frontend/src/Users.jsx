import React,{useEffect,useRef,useState} from 'react';
import {UserPlus,Users as UsersIcon,Pencil,X} from 'lucide-react';
import {api} from './api';
import './users.css';

const roleLabels={admin:'Admin',planer:'Planer',operador:'Operador'};

function UserEditor({user,session,onClose,onSave}) {
  const dialog=useRef(null);
  const [form,setForm]=useState(()=>({username:user?.username||'',first_name:user?.first_name||'',last_name:user?.last_name||'',email:user?.email||'',role:user?.role||'operador',is_active:user?.is_active??true,password:'',confirmation:''}));
  const [error,setError]=useState(''),[busy,setBusy]=useState(false);
  useEffect(()=>{const opener=document.activeElement;dialog.current.showModal();return()=>opener?.focus()},[]);
  const update=(field,value)=>setForm(current=>({...current,[field]:value}));
  return <dialog ref={dialog} className="user-editor" onCancel={event=>{event.preventDefault();if(!busy)onClose()}} aria-labelledby="user-editor-title">
    <div className="modal-head"><h2 id="user-editor-title">{user?'Editar usuario':'Crear usuario'}</h2><button type="button" className="icon-btn" aria-label="Cerrar" onClick={onClose} disabled={busy}><X/></button></div>
    <form onSubmit={async event=>{event.preventDefault();setError('');if(form.password!==form.confirmation){setError('Las contraseñas no coinciden.');return}setBusy(true);try{const {confirmation,...payload}=form;await onSave(payload,user?.id);onClose()}catch(error){setError(error.message)}finally{setBusy(false)}}}>
      {error&&<div className="notice error" role="alert">{error}</div>}
      <label className="field"><span>Usuario</span><input autoFocus value={form.username} onChange={event=>update('username',event.target.value)} autoComplete="off" maxLength={150} required/></label>
      <div className="form-grid"><label className="field"><span>Nombre</span><input value={form.first_name} onChange={event=>update('first_name',event.target.value)} maxLength={150}/></label><label className="field"><span>Apellidos</span><input value={form.last_name} onChange={event=>update('last_name',event.target.value)} maxLength={150}/></label></div>
      <label className="field"><span>Correo (opcional)</span><input type="email" value={form.email} onChange={event=>update('email',event.target.value)} maxLength={254}/></label>
      <label className="field"><span>Rol</span><select value={form.role} onChange={event=>update('role',event.target.value)} disabled={user?.is_self}>{session.roles.admin&&<option value="admin">Admin</option>}<option value="planer">Planer</option><option value="operador">Operador</option></select></label>
      <p className="user-role-description">{form.role==='admin'?'Acceso completo y administración de todas las cuentas.':form.role==='planer'?'Toda la operación: programas, importaciones, captura, liberación, correcciones y cuentas operativas.':'Consulta de órdenes e historial para capturar y liberar. Sin permisos de planeación ni gestión de usuarios.'}</p>
      <label className="checkbox"><input type="checkbox" checked={form.is_active} onChange={event=>update('is_active',event.target.checked)} disabled={user?.is_self}/>Cuenta activa</label>
      <label className="field"><span>{user?'Nueva contraseña (opcional)':'Contraseña inicial'}</span><input type="password" value={form.password} onChange={event=>update('password',event.target.value)} autoComplete="new-password" minLength={8} required={!user}/></label>
      <label className="field"><span>Confirmar contraseña</span><input type="password" value={form.confirmation} onChange={event=>update('confirmation',event.target.value)} autoComplete="new-password" required={!user||!!form.password}/></label>
      <p className="user-role-description">{user?'Deja la contraseña vacía para conservar la actual. ':''}Usa al menos ocho caracteres y evita contraseñas comunes o solo numéricas.</p>
      <div className="modal-actions"><button type="button" className="secondary" onClick={onClose} disabled={busy}>Cancelar</button><button className="primary" disabled={busy}>{busy?'Guardando…':user?'Guardar cambios':'Crear usuario'}</button></div>
    </form>
  </dialog>;
}

export default function Users({session,onSessionRefresh}) {
  const [users,setUsers]=useState([]),[loading,setLoading]=useState(true),[error,setError]=useState(''),[message,setMessage]=useState(''),[editor,setEditor]=useState(null),[search,setSearch]=useState(''),[refresh,setRefresh]=useState(0);
  useEffect(()=>{let current=true;setLoading(true);api('users/').then(data=>{if(current){setUsers(data);setError('')}}).catch(error=>{if(current)setError(error.message)}).finally(()=>{if(current)setLoading(false)});return()=>{current=false}},[refresh]);
  const shown=users.filter(user=>`${user.username} ${user.first_name} ${user.last_name} ${roleLabels[user.role]||''}`.toLocaleLowerCase('es').includes(search.toLocaleLowerCase('es')));
  return <section className="panel users-panel" aria-label="Administración de usuarios">
    <div className="panel-head"><div><h2>Usuarios de Empaques</h2><p>Cuentas, roles y acceso a la aplicación.</p></div><button className="primary" onClick={()=>{setMessage('');setEditor({user:null})}}><UserPlus size={17}/>Crear usuario</button></div>
    <div className="user-role-cards"><article><b>Admin</b><span>Acceso completo y control de cuentas Admin.</span></article><article><b>Planer</b><span>Toda la operación y gestión de cuentas operativas.</span></article><article><b>Operador</b><span>Captura y liberación de empaque.</span></article></div>
    <div className="filters"><label className="field"><span>Buscar usuario, nombre o rol</span><input type="search" value={search} onChange={event=>setSearch(event.target.value)}/></label></div>
    {message&&<div className="notice" role="status">{message}</div>}{error&&<div className="notice error" role="alert">{error}</div>}
    {loading?<p className="padded" role="status">Consultando usuarios…</p>:<div className="table-scroll"><table className="users-table"><thead><tr><th>Usuario</th><th>Nombre</th><th>Rol</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{shown.map(user=><tr key={user.id}><td><b>{user.username}</b>{user.is_self&&<small className="part-detail">Tu cuenta</small>}</td><td>{[user.first_name,user.last_name].filter(Boolean).join(' ')||'Sin nombre'}<small className="part-detail">{user.email}</small></td><td>{roleLabels[user.role]||'Sin rol asignado'}</td><td><span className={'status '+(user.is_active?'done':'')}>{user.is_active?'Activo':'Inactivo'}</span></td><td>{user.can_edit?<button className="secondary" aria-label={'Editar usuario '+user.username} onClick={()=>{setMessage('');setEditor({user})}}><Pencil size={15}/>Editar</button>:<span className="part-detail">Solo Admin</span>}</td></tr>)}</tbody></table>{!shown.length&&<div className="empty"><UsersIcon size={30}/><h3>No hay usuarios con esta búsqueda</h3></div>}</div>}
    <p className="padded user-role-description">Desactiva una cuenta para impedir su acceso conservando el historial de sus capturas. Los cambios quedan registrados en auditoría.</p>
    {editor&&<UserEditor key={editor.user?.id||'new'} user={editor.user} session={session} onClose={()=>setEditor(null)} onSave={async(payload,id)=>{await api(id?`users/${id}/`:'users/',{method:id?'PATCH':'POST',body:payload});setMessage(id?'Usuario actualizado.':'Usuario creado.');setRefresh(value=>value+1);if(id===session.user_id)await onSessionRefresh()}}/>}
  </section>;
}
