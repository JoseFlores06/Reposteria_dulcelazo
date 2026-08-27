import { useState, useEffect } from 'react'
import {
  getClientes, getClientesRecurrentes, crearCliente, actualizarCliente, eliminarCliente,
  getDirecciones, crearDireccion, actualizarDireccion, eliminarDireccion,
} from '../api/clientes'
import { Users, Plus, Search, X, Edit, Eye, Star, Phone, Mail, MapPin, Home, Trash2, Check } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'

const emptyForm = { nombres: '', apellidos: '', direccion: '', correo: '', telefono: '', whatsapp: '', edad_aproximada: '' }
const emptyDir  = { etiqueta: 'casa', direccion: '', distrito: '', referencia: '', principal: false }

const ETIQUETAS = ['casa', 'trabajo', 'familiar', 'otro']

// Modal de direcciones
function ModalDirecciones({ cliente, onClose }) {
  const [dirs, setDirs] = useState(cliente.direcciones || [])
  const [form, setForm] = useState(emptyDir)
  const [editId, setEditId] = useState(null)
  const [saving, setSaving] = useState(false)

  const cargar = async () => {
    try { const res = await getDirecciones(cliente.id); setDirs(res) } catch {}
  }

  const handleGuardar = async (e) => {
    e.preventDefault()
    if (!form.direccion.trim()) { toast.error('La dirección es requerida'); return }
    setSaving(true)
    try {
      if (editId) {
        await actualizarDireccion(cliente.id, editId, form)
        toast.success('Dirección actualizada')
      } else {
        await crearDireccion(cliente.id, form)
        toast.success('Dirección agregada')
      }
      setForm(emptyDir); setEditId(null); cargar()
    } catch { toast.error('Error al guardar') }
    finally { setSaving(false) }
  }

  const handleEditar = (d) => {
    setEditId(d.id)
    setForm({ etiqueta: d.etiqueta, direccion: d.direccion, distrito: d.distrito || '', referencia: d.referencia || '', principal: d.principal })
  }

  const handleEliminar = async (id) => {
    if (!confirm('¿Eliminar esta dirección?')) return
    try { await eliminarDireccion(cliente.id, id); toast.success('Eliminada'); cargar() }
    catch { toast.error('Error al eliminar') }
  }

  const etqColor = (e) => ({ casa: 'badge-blue', trabajo: 'badge-green', familiar: 'badge-pink', otro: 'badge-yellow' }[e] || 'badge-pink')

  return (
    <div className="modal-overlay">
      <div className="modal-card max-w-lg animate-fadeIn max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-base font-bold ct-primary flex items-center gap-2">
              <MapPin size={16} className="text-primary-400"/> Direcciones — {cliente.nombres} {cliente.apellidos}
            </h3>
            <p className="text-xs ct-muted">{dirs.length} dirección{dirs.length !== 1 ? 'es' : ''} registrada{dirs.length !== 1 ? 's' : ''}</p>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-xl flex items-center justify-center hover:bg-primary-50 ct-pink-lt"><X size={18}/></button>
        </div>

        {/* Lista de direcciones */}
        {dirs.length > 0 && (
          <div className="space-y-2 mb-4">
            {dirs.map(d => (
              <div key={d.id} className={`flex items-start gap-3 p-3 rounded-xl ${d.principal ? 'bg-primary-50 dark:bg-primary-950/30 border border-primary-200 dark:border-primary-800' : 'bg-rose-softer'}`}>
                <Home size={16} className={`mt-0.5 shrink-0 ${d.principal ? 'text-primary-500' : 'ct-muted'}`}/>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                    <span className={`badge ${etqColor(d.etiqueta)} text-[10px]`}>{d.etiqueta}</span>
                    {d.principal && <span className="badge badge-green text-[10px]">Principal</span>}
                  </div>
                  <p className="text-sm font-medium ct-primary">{d.direccion}</p>
                  {d.distrito && <p className="text-xs ct-muted">{d.distrito}</p>}
                  {d.referencia && <p className="text-xs ct-muted italic">{d.referencia}</p>}
                </div>
                <div className="flex gap-1 shrink-0">
                  <button onClick={() => handleEditar(d)} className="w-7 h-7 rounded-lg flex items-center justify-center hover:bg-primary-100 dark:hover:bg-primary-900/30 ct-muted hover:text-primary-600 transition-colors">
                    <Edit size={13}/>
                  </button>
                  <button onClick={() => handleEliminar(d.id)} className="w-7 h-7 rounded-lg flex items-center justify-center hover:bg-red-100 dark:hover:bg-red-950/30 ct-muted hover:text-red-500 transition-colors">
                    <Trash2 size={13}/>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Formulario */}
        <div className="border-t border-pink-100 dark:border-pink-900/20 pt-4">
          <p className="text-xs font-bold ct-accent mb-3">{editId ? 'Editar dirección' : 'Agregar nueva dirección'}</p>
          <form onSubmit={handleGuardar} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Etiqueta</label>
                <select className="input-field" value={form.etiqueta} onChange={e => setForm(f => ({...f, etiqueta: e.target.value}))}>
                  {ETIQUETAS.map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Distrito / Ciudad</label>
                <input className="input-field" placeholder="Miraflores, Lima" value={form.distrito} onChange={e => setForm(f => ({...f, distrito: e.target.value}))}/>
              </div>
            </div>
            <div>
              <label className="label">Dirección *</label>
              <input className="input-field" placeholder="Av. Ejemplo 123, Urb. Las Flores" value={form.direccion} onChange={e => setForm(f => ({...f, direccion: e.target.value}))} required/>
            </div>
            <div>
              <label className="label">Referencia</label>
              <input className="input-field" placeholder="Frente al parque, casa amarilla..." value={form.referencia} onChange={e => setForm(f => ({...f, referencia: e.target.value}))}/>
            </div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" className="w-4 h-4 rounded accent-pink-500" checked={form.principal} onChange={e => setForm(f => ({...f, principal: e.target.checked}))}/>
              <span className="text-sm ct-secondary">Marcar como dirección principal</span>
            </label>
            <div className="flex gap-2">
              <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
                <Check size={14}/> {saving ? 'Guardando...' : (editId ? 'Actualizar' : 'Agregar')}
              </button>
              {editId && (
                <button type="button" onClick={() => { setEditId(null); setForm(emptyDir) }} className="btn-secondary">Cancelar</button>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

// Modal ver cliente
function ModalCliente({ cliente, onClose, onVerDirecciones }) {
  const etqColor = (e) => ({ casa: 'badge-blue', trabajo: 'badge-green', familiar: 'badge-pink', otro: 'badge-yellow' }[e] || 'badge-pink')
  return (
    <div className="modal-overlay">
      <div className="modal-card max-w-md animate-fadeIn">
        <div className="flex justify-between items-start mb-5">
          <div>
            <h3 className="text-lg font-bold ct-primary">{cliente.nombres} {cliente.apellidos}</h3>
            {cliente.num_compras > 0 && (
              <span className="badge badge-pink mt-1">{cliente.num_compras} compra{cliente.num_compras !== 1 ? 's' : ''}</span>
            )}
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-xl flex items-center justify-center hover:bg-primary-50 ct-pink-lt"><X size={18}/></button>
        </div>
        <div className="space-y-2">
          {cliente.correo && (
            <div className="flex items-center gap-3 p-3 rounded-xl bg-rose-soft">
              <Mail size={15} className="text-primary-400 shrink-0"/>
              <span className="text-sm ct-primary">{cliente.correo}</span>
            </div>
          )}
          {cliente.telefono && (
            <div className="flex items-center gap-3 p-3 rounded-xl bg-rose-soft">
              <Phone size={15} className="text-primary-400 shrink-0"/>
              <span className="text-sm ct-primary">{cliente.telefono}</span>
            </div>
          )}
          {cliente.edad_aproximada && (
            <p className="text-sm px-3 ct-secondary">Edad aproximada: <strong>{cliente.edad_aproximada} años</strong></p>
          )}

          {/* Direcciones */}
          <div className="p-3 rounded-xl bg-rose-soft">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <MapPin size={15} className="text-primary-400"/>
                <span className="text-sm font-semibold ct-primary">
                  Direcciones ({cliente.num_direcciones || 0})
                </span>
              </div>
              <button onClick={onVerDirecciones} className="text-xs text-primary-600 font-medium hover:underline">
                Gestionar →
              </button>
            </div>
            {(cliente.direcciones || []).length === 0 ? (
              <p className="text-xs ct-muted">Sin direcciones registradas</p>
            ) : (
              <div className="space-y-1.5">
                {(cliente.direcciones || []).slice(0, 3).map(d => (
                  <div key={d.id} className="flex items-start gap-2">
                    <span className={`badge ${etqColor(d.etiqueta)} text-[10px] shrink-0`}>{d.etiqueta}</span>
                    <p className="text-xs ct-secondary">{d.direccion}{d.distrito ? `, ${d.distrito}` : ''}</p>
                    {d.principal && <span className="badge badge-green text-[10px] shrink-0">⭐</span>}
                  </div>
                ))}
                {(cliente.direcciones || []).length > 3 && (
                  <p className="text-xs ct-muted">+{cliente.direcciones.length - 3} más...</p>
                )}
              </div>
            )}
          </div>

          <p className="text-xs px-3 ct-muted">
            Registrado: {cliente.creado_en ? new Date(cliente.creado_en).toLocaleDateString('es-PE') : '—'}
          </p>
        </div>
        <div className="flex gap-2 mt-5">
          <button onClick={onVerDirecciones} className="btn-secondary flex-1 flex items-center justify-center gap-2">
            <MapPin size={14}/> Direcciones
          </button>
          <button onClick={onClose} className="btn-secondary flex-1">Cerrar</button>
        </div>
      </div>
    </div>
  )
}

// Página principal
export default function ClientesPage() {
  const { isAdmin } = useAuth()
  const [clientes, setClientes] = useState([])
  const [loading, setLoading] = useState(true)
  const [busqueda, setBusqueda] = useState('')
  const [modo, setModo] = useState('lista')
  const [form, setForm] = useState(emptyForm)
  const [editId, setEditId] = useState(null)
  const [verCliente, setVerCliente] = useState(null)
  const [verDirecciones, setVerDirecciones] = useState(null)
  const [saving, setSaving] = useState(false)

  const cargar = (tipo = 'lista') => {
    setLoading(true)
    const fn = tipo === 'recurrentes' ? getClientesRecurrentes : getClientes
    fn().then(setClientes).catch(() => toast.error('Error al cargar')).finally(() => setLoading(false))
  }
  useEffect(() => { cargar() }, [])

  const filtrados = clientes.filter(c => `${c.nombres} ${c.apellidos}`.toLowerCase().includes(busqueda.toLowerCase()))

  const abrirNuevo = () => { setForm(emptyForm); setEditId(null); setModo('nuevo') }
  const abrirEditar = (c) => {
    setForm({ nombres: c.nombres, apellidos: c.apellidos, direccion: c.direccion||'', correo: c.correo||'', telefono: c.telefono||'', whatsapp: c.whatsapp||'', edad_aproximada: c.edad_aproximada||'' })
    setEditId(c.id); setModo('editar')
  }

  const handleGuardar = async (e) => {
    e.preventDefault(); setSaving(true)
    try {
      const data = { ...form, edad_aproximada: form.edad_aproximada ? parseInt(form.edad_aproximada) : null }
      if (modo === 'nuevo') { await crearCliente(data); toast.success('Cliente registrado') }
      else { await actualizarCliente(editId, data); toast.success('Cliente actualizado') }
      setModo('lista'); cargar()
    } catch (err) { toast.error(err.response?.data?.detail || 'Error') }
    finally { setSaving(false) }
  }

  const irRecurrentes = () => { setModo('recurrentes'); cargar('recurrentes') }
  const irLista = () => { setModo('lista'); cargar('lista') }

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {verCliente && (
        <ModalCliente
          cliente={verCliente}
          onClose={() => setVerCliente(null)}
          onVerDirecciones={() => { setVerDirecciones(verCliente); setVerCliente(null) }}
        />
      )}
      {verDirecciones && (
        <ModalDirecciones
          cliente={verDirecciones}
          onClose={() => { setVerDirecciones(null); cargar() }}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #ec4899, #be185d)' }}>
            <Users size={20} className="text-white"/>
          </div>
          <div>
            <h1 className="page-title">Clientes</h1>
            <p className="page-subtitle">{clientes.length} clientes registrados</p>
          </div>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button onClick={irLista} className={`btn-secondary text-sm ${modo === 'lista' ? 'border-primary-400' : ''}`}>Lista</button>
          <button onClick={irRecurrentes} className={`btn-secondary text-sm flex items-center gap-1.5 ${modo === 'recurrentes' ? 'border-amber-400 bg-amber-50 text-amber-700' : ''}`}>
            <Star size={13} className="text-amber-500"/> Recurrentes
          </button>
          <button onClick={abrirNuevo} className="btn-primary text-sm flex items-center gap-1.5"><Plus size={15}/> Nuevo cliente</button>
        </div>
      </div>

      {/* Form */}
      {(modo === 'nuevo' || modo === 'editar') && (
        <div className="card animate-fadeIn">
          <h2 className="text-base font-bold mb-4 ct-accent">
            {modo === 'nuevo' ? 'Registrar nuevo cliente' : 'Editar cliente'}
          </h2>
          <form onSubmit={handleGuardar} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div><label className="label">Nombres *</label><input className="input-field" value={form.nombres} onChange={e => setForm(f => ({...f, nombres: e.target.value}))} required/></div>
            <div><label className="label">Apellidos *</label><input className="input-field" value={form.apellidos} onChange={e => setForm(f => ({...f, apellidos: e.target.value}))} required/></div>
            <div><label className="label">Correo</label><input type="email" className="input-field" value={form.correo} onChange={e => setForm(f => ({...f, correo: e.target.value}))}/></div>
            <div><label className="label">Teléfono</label><input className="input-field" value={form.telefono} onChange={e => setForm(f => ({...f, telefono: e.target.value}))}/></div>
            <div><label className="label">WhatsApp</label><input className="input-field" value={form.whatsapp} onChange={e => setForm(f => ({...f, whatsapp: e.target.value}))}/></div>
            <div><label className="label">Edad aproximada</label><input type="number" min="0" className="input-field" value={form.edad_aproximada} onChange={e => setForm(f => ({...f, edad_aproximada: e.target.value}))}/></div>
            <div className="sm:col-span-2">
              <label className="label">Dirección general (opcional)</label>
              <input className="input-field" placeholder="Se pueden agregar múltiples direcciones después de guardar" value={form.direccion} onChange={e => setForm(f => ({...f, direccion: e.target.value}))}/>
            </div>
            <div className="sm:col-span-2 flex gap-3 justify-end">
              <button type="button" onClick={irLista} className="btn-secondary">Cancelar</button>
              <button type="submit" disabled={saving} className="btn-primary">{saving ? 'Guardando...' : 'Guardar cliente'}</button>
            </div>
          </form>
        </div>
      )}

      {/* Lista */}
      <div className="card">
        {modo === 'recurrentes' && (
          <div className="flex items-center gap-2 mb-4 p-3 rounded-2xl" style={{ background: '#fffbeb', border: '1px solid #fde68a' }}>
            <Star size={15} className="text-amber-500"/>
            <p className="text-sm text-amber-700 font-medium">Clientes con más de una compra, ordenados por frecuencia</p>
          </div>
        )}
        <div className="search-box mb-4">
          <Search size={15} className="ct-pink-lt"/>
          <input placeholder="Buscar cliente..." value={busqueda} onChange={e => setBusqueda(e.target.value)}/>
        </div>
        {loading ? (
          <div className="flex justify-center py-12"><div className="spinner"/></div>
        ) : filtrados.length === 0 ? (
          <div className="text-center py-12">
            <Users size={40} className="mx-auto mb-3 ct-pink-lt"/>
            <p className="text-sm ct-muted">No hay clientes</p>
          </div>
        ) : (
          <div className="divide-y" style={{ borderColor: '#fdf2f8' }}>
            {filtrados.map(c => (
              <div key={c.id} className="flex items-center justify-between py-3.5 px-2 rounded-xl table-row-hover">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center text-sm font-bold text-white flex-shrink-0"
                       style={{ background: 'linear-gradient(135deg, #f9a8d4, #ec4899)' }}>
                    {c.nombres.charAt(0)}
                  </div>
                  <div>
                    <p className="font-semibold text-sm ct-primary">{c.nombres} {c.apellidos}</p>
                    <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                      <p className="text-xs ct-muted">{c.telefono || c.correo || 'Sin contacto'}</p>
                      {c.num_direcciones > 0 && (
                        <span className="flex items-center gap-0.5 text-[10px] text-primary-500 font-medium">
                          <MapPin size={9}/> {c.num_direcciones} dir.
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex gap-2 items-center flex-wrap">
                  {modo === 'recurrentes' && <span className="badge badge-yellow">{c.num_compras} compras</span>}
                  <button onClick={() => setVerDirecciones(c)} className="btn-secondary text-xs py-1.5 flex items-center gap-1">
                    <MapPin size={11}/> Dirs.
                  </button>
                  <button onClick={() => setVerCliente(c)} className="btn-secondary text-xs py-1.5 flex items-center gap-1">
                    <Eye size={12}/> Ver
                  </button>
                  <button onClick={() => abrirEditar(c)} className="btn-secondary text-xs py-1.5 flex items-center gap-1">
                    <Edit size={12}/> Editar
  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
