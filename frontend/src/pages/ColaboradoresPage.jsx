import { useState, useEffect } from 'react'
import { getColaboradores, crearColaborador, actualizarColaborador, eliminarColaborador } from '../api/colaboradores'
import { getUsuarios } from '../api/auth'
import { UserCog, Plus, Search, X, Edit, Eye, Phone, Mail, Briefcase } from 'lucide-react'
import toast from 'react-hot-toast'

const emptyForm = { nombres: '', apellidos: '', direccion: '', correo: '', telefono: '', whatsapp: '', edad_aproximada: '', rol_descripcion: '', usuario_sistema_id: '' }

function ModalColaborador({ colaborador, onClose }) {
  return (
    <div className="modal-overlay">
      <div className="modal-card max-w-md animate-fadeIn">
        <div className="flex justify-between items-start mb-5">
          <div>
            <h3 className="text-lg font-bold ct-primary">{colaborador.nombres} {colaborador.apellidos}</h3>
            {colaborador.rol_descripcion && <p className="text-sm mt-0.5 ct-muted">{colaborador.rol_descripcion}</p>}
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-xl flex items-center justify-center hover:bg-primary-50 text-rose-300"><X size={18} /></button>
        </div>
        <div className="space-y-2">
          {colaborador.correo && (
            <div className="flex items-center gap-3 p-3 rounded-xl bg-rose-soft">
              <Mail size={14} className="ct-pink" />
              <span className="text-sm ct-primary">{colaborador.correo}</span>
            </div>
          )}
          {colaborador.telefono && (
            <div className="flex items-center gap-3 p-3 rounded-xl bg-rose-soft">
              <Phone size={14} className="ct-pink" />
              <span className="text-sm ct-primary">{colaborador.telefono}</span>
            </div>
          )}
          {colaborador.rol_descripcion && (
            <div className="flex items-center gap-3 p-3 rounded-xl bg-rose-soft">
              <Briefcase size={14} className="ct-pink" />
              <span className="text-sm ct-primary">{colaborador.rol_descripcion}</span>
            </div>
          )}
          {colaborador.edad_aproximada && <p className="text-xs px-3 ct-muted">Edad: {colaborador.edad_aproximada} años</p>}
        </div>
        <button onClick={onClose} className="btn-secondary w-full mt-5">Cerrar</button>
      </div>
    </div>
  )
}

export default function ColaboradoresPage() {
  const [colaboradores, setColaboradores] = useState([])
  const [usuarios, setUsuarios] = useState([])
  const [loading, setLoading] = useState(true)
  const [busqueda, setBusqueda] = useState('')
  const [modo, setModo] = useState('lista')
  const [form, setForm] = useState(emptyForm)
  const [editId, setEditId] = useState(null)
  const [verCol, setVerCol] = useState(null)
  const [saving, setSaving] = useState(false)

  const cargar = () => {
    setLoading(true)
    Promise.all([getColaboradores(), getUsuarios()])
      .then(([c, u]) => { setColaboradores(c); setUsuarios(u) })
      .finally(() => setLoading(false))
  }
  useEffect(() => { cargar() }, [])

  const filtrados = colaboradores.filter(c => `${c.nombres} ${c.apellidos}`.toLowerCase().includes(busqueda.toLowerCase()))
  const abrirNuevo = () => { setForm(emptyForm); setEditId(null); setModo('nuevo') }
  const abrirEditar = (c) => { setForm({ nombres: c.nombres, apellidos: c.apellidos, direccion: c.direccion||'', correo: c.correo||'', telefono: c.telefono||'', whatsapp: c.whatsapp||'', edad_aproximada: c.edad_aproximada||'', rol_descripcion: c.rol_descripcion||'', usuario_sistema_id: c.usuario_sistema_id||'' }); setEditId(c.id); setModo('editar') }

  const handleGuardar = async (e) => {
    e.preventDefault(); setSaving(true)
    try {
      const data = { ...form, edad_aproximada: form.edad_aproximada ? parseInt(form.edad_aproximada) : null, usuario_sistema_id: form.usuario_sistema_id ? parseInt(form.usuario_sistema_id) : null }
      if (modo === 'nuevo') { await crearColaborador(data); toast.success('Colaborador registrado') }
      else { await actualizarColaborador(editId, data); toast.success('Colaborador actualizado') }
      setModo('lista'); cargar()
    } catch (err) { toast.error(err.response?.data?.detail || 'Error') }
    finally { setSaving(false) }
  }

  const handleEliminar = async (id) => {
    if (!confirm('¿Eliminar este colaborador?')) return
    try { await eliminarColaborador(id); toast.success('Eliminado'); cargar() }
    catch { toast.error('Error') }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {verCol && <ModalColaborador colaborador={verCol} onClose={() => setVerCol(null)} />}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #ec4899, #be185d)' }}>
            <UserCog size={20} className="text-white" />
          </div>
          <div>
            <h1 className="page-title">Colaboradores</h1>
            <p className="page-subtitle">{colaboradores.length} colaboradores registrados</p>
          </div>
        </div>
        <div className="flex gap-2">
          {modo !== 'lista' && <button onClick={() => setModo('lista')} className="btn-secondary text-sm">Ver lista</button>}
          <button onClick={abrirNuevo} className="btn-primary text-sm"><Plus size={15} /> Nuevo</button>
        </div>
      </div>

      {(modo === 'nuevo' || modo === 'editar') && (
        <div className="card animate-fadeIn">
          <h2 className="text-base font-bold mb-4 ct-accent">{modo === 'nuevo' ? 'Agregar colaborador' : 'Editar colaborador'}</h2>
          <form onSubmit={handleGuardar} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div><label className="label">Nombres *</label><input className="input-field" value={form.nombres} onChange={e => setForm(f => ({...f, nombres: e.target.value}))} required /></div>
            <div><label className="label">Apellidos *</label><input className="input-field" value={form.apellidos} onChange={e => setForm(f => ({...f, apellidos: e.target.value}))} required /></div>
            <div><label className="label">Correo</label><input type="email" className="input-field" value={form.correo} onChange={e => setForm(f => ({...f, correo: e.target.value}))} /></div>
            <div><label className="label">Teléfono</label><input className="input-field" value={form.telefono} onChange={e => setForm(f => ({...f, telefono: e.target.value}))} /></div>
            <div><label className="label">WhatsApp</label><input className="input-field" value={form.whatsapp} onChange={e => setForm(f => ({...f, whatsapp: e.target.value}))} /></div>
            <div><label className="label">Edad aproximada</label><input type="number" min="0" className="input-field" value={form.edad_aproximada} onChange={e => setForm(f => ({...f, edad_aproximada: e.target.value}))} /></div>
            <div className="sm:col-span-2"><label className="label">Dirección</label><input className="input-field" value={form.direccion} onChange={e => setForm(f => ({...f, direccion: e.target.value}))} /></div>
            <div className="sm:col-span-2"><label className="label">Rol / Descripción</label><textarea className="input-field" rows={2} value={form.rol_descripcion} onChange={e => setForm(f => ({...f, rol_descripcion: e.target.value}))} placeholder="Ej: Pastelera principal..." /></div>
            <div className="sm:col-span-2">
              <label className="label">Usuario del sistema (opcional)</label>
              <select className="input-field" value={form.usuario_sistema_id} onChange={e => setForm(f => ({...f, usuario_sistema_id: e.target.value}))}>
                <option value="">— Sin vincular —</option>
                {usuarios.map(u => <option key={u.id} value={u.id}>{u.nombres} {u.apellidos} ({u.correo})</option>)}
              </select>
            </div>
            <div className="sm:col-span-2 flex gap-3 justify-end">
              <button type="button" onClick={() => setModo('lista')} className="btn-secondary">Cancelar</button>
              <button type="submit" disabled={saving} className="btn-primary">{saving ? 'Guardando...' : 'Guardar'}</button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        <div className="search-box mb-4">
          <Search size={15} className="ct-pink-lt" />
          <input placeholder="Buscar colaborador..." value={busqueda} onChange={e => setBusqueda(e.target.value)} />
        </div>
        {loading ? (
          <div className="flex justify-center py-12"><div className="spinner" /></div>
        ) : filtrados.length === 0 ? (
          <div className="text-center py-12">
            <UserCog size={40} className="mx-auto mb-3 ct-pink-lt" />
            <p className="text-sm ct-muted">No hay colaboradores</p>
          </div>
        ) : (
          <div className="divide-y" style={{ borderColor: '#fdf2f8' }}>
            {filtrados.map(c => (
              <div key={c.id} className="flex items-center justify-between py-3.5 px-2 rounded-xl table-row-hover">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center text-sm font-bold text-white flex-shrink-0"
                       style={{ background: 'linear-gradient(135deg, #f9a8d4, #be185d)' }}>
                    {c.nombres.charAt(0)}
                  </div>
                  <div>
                    <p className="font-semibold text-sm ct-primary">{c.nombres} {c.apellidos}</p>
                    <p className="text-xs ct-muted">{c.rol_descripcion || c.correo || 'Sin rol asignado'}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => setVerCol(c)} className="btn-secondary text-xs py-1.5 flex items-center gap-1"><Eye size={12} /> Ver</button>
                  <button onClick={() => abrirEditar(c)} className="btn-secondary text-xs py-1.5 flex items-center gap-1"><Edit size={12} /> Editar</button>
                  <button onClick={() => handleEliminar(c.id)} className="w-8 h-8 rounded-xl flex items-center justify-center text-red-400 hover:bg-red-50 transition-colors"><X size={14} /></button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
