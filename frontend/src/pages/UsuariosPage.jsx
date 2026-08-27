import { useState, useEffect } from 'react'
import { getUsuarios, crearUsuario, actualizarUsuario } from '../api/auth'
import { getColaboradores } from '../api/colaboradores'
import { UserCog, Plus, Edit, Check, Users, Shield, User } from 'lucide-react'
import toast from 'react-hot-toast'

const emptyForm = { nombres: '', apellidos: '', correo: '', password: '', rol: 'vendedor', activo: true }

export default function UsuariosPage() {
  const [usuarios, setUsuarios] = useState([])
  const [colaboradores, setColaboradores] = useState([])
  const [loading, setLoading] = useState(true)
  const [modo, setModo] = useState('lista')
  const [form, setForm] = useState(emptyForm)
  const [editId, setEditId] = useState(null)
  const [saving, setSaving] = useState(false)
  const [colSel, setColSel] = useState('')

  const cargar = () => {
    setLoading(true)
    Promise.all([getUsuarios(), getColaboradores()])
      .then(([u, c]) => { setUsuarios(u); setColaboradores(c) })
      .finally(() => setLoading(false))
  }
  useEffect(() => { cargar() }, [])

  const abrirNuevo = () => { setForm(emptyForm); setEditId(null); setColSel(''); setModo('nuevo') }
  const abrirEditar = (u) => { setForm({ nombres: u.nombres, apellidos: u.apellidos, correo: u.correo, password: '', rol: u.rol, activo: u.activo }); setEditId(u.id); setColSel(''); setModo('editar') }

  const handleSelCol = (e) => {
    const id = e.target.value; setColSel(id)
    if (!id) { setForm(f => ({ ...f, nombres: '', apellidos: '', correo: '' })); return }
    const col = colaboradores.find(c => String(c.id) === id)
    if (col) setForm(f => ({ ...f, nombres: col.nombres||'', apellidos: col.apellidos||'', correo: col.correo||'' }))
  }

  const handleGuardar = async (e) => {
    e.preventDefault(); setSaving(true)
    try {
      if (modo === 'nuevo') { await crearUsuario(form); toast.success('Usuario creado') }
      else { const d = { ...form }; if (!d.password) delete d.password; await actualizarUsuario(editId, d); toast.success('Usuario actualizado') }
      setModo('lista'); cargar()
    } catch (err) { toast.error(err.response?.data?.detail || 'Error') }
    finally { setSaving(false) }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #ec4899, #be185d)' }}>
            <UserCog size={20} className="text-white" />
          </div>
          <div>
            <h1 className="page-title">Usuarios</h1>
            <p className="page-subtitle">Gestión de accesos al sistema</p>
          </div>
        </div>
        <div className="flex gap-2">
          {modo !== 'lista' && <button onClick={() => setModo('lista')} className="btn-secondary text-sm">Ver lista</button>}
          <button onClick={abrirNuevo} className="btn-primary text-sm"><Plus size={15} /> Nuevo usuario</button>
        </div>
      </div>

      {(modo === 'nuevo' || modo === 'editar') && (
        <div className="card animate-fadeIn">
          <h2 className="text-base font-bold mb-4 ct-accent">{modo === 'nuevo' ? 'Crear nuevo usuario' : 'Editar usuario'}</h2>

          {/* Selector de colaborador */}
          {modo === 'nuevo' && colaboradores.length > 0 && (
            <div className="mb-5 p-4 rounded-2xl" style={{ background: 'linear-gradient(135deg, #fdf2f8, #fce7f3)', border: '1px solid #fbcfe8' }}>
              <label className="flex items-center gap-2 mb-2">
                <Users size={15} className="ct-pink" />
                <span className="text-xs font-bold uppercase tracking-wider ct-accent">Importar datos de colaborador</span>
              </label>
              <select className="input-field" value={colSel} onChange={handleSelCol}>
                <option value="">— Seleccionar colaborador (opcional) —</option>
                {colaboradores.map(c => <option key={c.id} value={c.id}>{c.nombres} {c.apellidos}{c.correo ? ` — ${c.correo}` : ''}</option>)}
              </select>
              <p className="text-[11px] mt-1.5 ct-muted">Al seleccionar, sus datos se autocompletan en el formulario.</p>
            </div>
          )}

          <form onSubmit={handleGuardar} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div><label className="label">Nombres *</label><input className="input-field" value={form.nombres} onChange={e => setForm(f => ({...f, nombres: e.target.value}))} required /></div>
            <div><label className="label">Apellidos *</label><input className="input-field" value={form.apellidos} onChange={e => setForm(f => ({...f, apellidos: e.target.value}))} required /></div>
            <div><label className="label">Correo *</label><input type="email" className="input-field" value={form.correo} onChange={e => setForm(f => ({...f, correo: e.target.value}))} required /></div>
            <div>
              <label className="label">{modo === 'editar' ? 'Nueva contraseña (vacío = sin cambio)' : 'Contraseña *'}</label>
              <input type="password" className="input-field" value={form.password} onChange={e => setForm(f => ({...f, password: e.target.value}))} required={modo === 'nuevo'} placeholder={modo === 'editar' ? 'Sin cambios' : ''} />
            </div>
            <div>
              <label className="label">Rol *</label>
              <select className="input-field" value={form.rol} onChange={e => setForm(f => ({...f, rol: e.target.value}))}>
                <option value="admin">Admin</option>
                <option value="vendedor">Vendedor</option>
              </select>
            </div>
            <div>
              <label className="label">Estado</label>
              <select className="input-field" value={form.activo ? 'true' : 'false'} onChange={e => setForm(f => ({...f, activo: e.target.value === 'true'}))}>
                <option value="true">Activo</option>
                <option value="false">Inactivo</option>
              </select>
            </div>
            <div className="sm:col-span-2 flex gap-3 justify-end">
              <button type="button" onClick={() => setModo('lista')} className="btn-secondary">Cancelar</button>
              <button type="submit" disabled={saving} className="btn-primary"><Check size={15} /> {saving ? 'Guardando...' : 'Guardar usuario'}</button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        {loading ? (
          <div className="flex justify-center py-12"><div className="spinner" /></div>
        ) : (
          <div className="divide-y" style={{ borderColor: '#fdf2f8' }}>
            {usuarios.map(u => (
              <div key={u.id} className={`flex items-center justify-between py-3.5 px-2 rounded-xl table-row-hover ${!u.activo ? 'opacity-50' : ''}`}>
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center text-sm font-bold text-white flex-shrink-0"
                       style={{ background: u.rol === 'admin' ? 'linear-gradient(135deg, #7c3aed, #4f46e5)' : 'linear-gradient(135deg, #f9a8d4, #ec4899)' }}>
                    {u.rol === 'admin' ? <Shield size={15} /> : <User size={15} />}
                  </div>
                  <div>
                    <p className="font-semibold text-sm ct-primary">{u.nombres} {u.apellidos}</p>
                    <p className="text-xs ct-muted">{u.correo}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={u.rol === 'admin' ? 'badge badge-purple' : 'badge badge-pink'}>{u.rol}</span>
                  <span className={u.activo ? 'badge badge-green' : 'badge badge-red'}>{u.activo ? 'Activo' : 'Inactivo'}</span>
                  <button onClick={() => abrirEditar(u)} className="w-8 h-8 rounded-xl flex items-center justify-center text-primary-500 hover:bg-primary-50 transition-colors"><Edit size={14} /></button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
