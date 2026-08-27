import { useState, useEffect } from 'react'
import { getPromociones, crearPromocion, actualizarPromocion, togglePromocion, eliminarPromocion, sugerirIA } from '../api/promociones'
import { getProductos } from '../api/productos'
import { getPaquetes } from '../api/paquetes'
import { Tag, Plus, X, Edit, Zap, ToggleLeft, ToggleRight } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'

const BASE_URL = 'http://127.0.0.1:8000'

export default function PromocionesPage() {
  const { isAdmin } = useAuth()
  const [promociones, setPromociones] = useState([])
  const [productos, setProductos] = useState([])
  const [paquetes, setPaquetes] = useState([])
  const [loading, setLoading] = useState(true)
  const [modo, setModo] = useState('grid')
  const [promoEditar, setPromoEditar] = useState(null)
  const [sugerencias, setSugerencias] = useState([])
  const [cargandoIA, setCargandoIA] = useState(false)
  const [guardando, setGuardando] = useState(false)
  const [form, setForm] = useState({ nombre: '', descripcion: '', item_tipo: 'producto', item_id: '', porcentaje_descuento: '', activo: true, fecha_inicio: '', fecha_fin: '', foto: null })

  const cargar = () => {
    setLoading(true)
    Promise.all([getPromociones(), getProductos(true), getPaquetes(true)])
      .then(([promos, prods, paqs]) => { setPromociones(promos); setProductos(prods); setPaquetes(paqs) })
      .finally(() => setLoading(false))
  }
  useEffect(() => { cargar() }, [])

  const itemSel = form.item_tipo === 'producto' ? productos.find(p => p.id === parseInt(form.item_id)) : paquetes.find(p => p.id === parseInt(form.item_id))

  const handleSugerirIA = async () => {
    if (!form.item_id) { toast.error('Selecciona un producto o paquete'); return }
    setCargandoIA(true)
    try { const res = await sugerirIA(form.item_tipo, parseInt(form.item_id)); setSugerencias(res.sugerencias) }
    catch { toast.error('Error al obtener sugerencias') }
    finally { setCargandoIA(false) }
  }

  const aplicarSugerencia = (s) => { setForm(f => ({ ...f, porcentaje_descuento: s.porcentaje_descuento })); setSugerencias([]) }

  const handleGuardar = async (e) => {
    e.preventDefault(); setGuardando(true)
    try {
      const fd = new FormData()
      fd.append('nombre', form.nombre); fd.append('descripcion', form.descripcion||''); fd.append('item_tipo', form.item_tipo)
      fd.append('item_id', parseInt(form.item_id)); fd.append('porcentaje_descuento', parseFloat(form.porcentaje_descuento)); fd.append('activo', form.activo)
      if (form.fecha_inicio) fd.append('fecha_inicio', form.fecha_inicio)
      if (form.fecha_fin) fd.append('fecha_fin', form.fecha_fin)
      if (form.foto) fd.append('foto', form.foto)
      if (modo === 'nuevo') { await crearPromocion(fd); toast.success('Promoción creada') }
      else { await actualizarPromocion(promoEditar.id, fd); toast.success('Promoción actualizada') }
      setModo('grid'); cargar()
    } catch (err) { toast.error(err.response?.data?.detail || 'Error') }
    finally { setGuardando(false) }
  }

  const handleToggle = async (id) => {
    try { await togglePromocion(id); cargar() } catch { toast.error('Error') }
  }
  const handleEliminar = async (id) => {
    if (!confirm('¿Eliminar esta promoción?')) return
    try { await eliminarPromocion(id); toast.success('Eliminada'); cargar() } catch { toast.error('Error') }
  }

  const abrirNuevo = () => { setForm({ nombre: '', descripcion: '', item_tipo: 'producto', item_id: '', porcentaje_descuento: '', activo: true, fecha_inicio: '', fecha_fin: '', foto: null }); setPromoEditar(null); setSugerencias([]); setModo('nuevo') }
  const abrirEditar = (p) => {
    setPromoEditar(p)
    setForm({ nombre: p.nombre, descripcion: p.descripcion||'', item_tipo: p.item_tipo, item_id: p.item_id, porcentaje_descuento: p.porcentaje_descuento, activo: p.activo, fecha_inicio: p.fecha_inicio ? p.fecha_inicio.slice(0,16) : '', fecha_fin: p.fecha_fin ? p.fecha_fin.slice(0,16) : '', foto: null })
    setSugerencias([]); setModo('editar')
  }

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #ec4899, #be185d)' }}>
            <Tag size={20} className="text-white" />
          </div>
          <div>
            <h1 className="page-title">Promociones</h1>
            <p className="page-subtitle">{promociones.filter(p => p.activa_ahora).length} activas ahora</p>
          </div>
        </div>
        {isAdmin && (
          <div className="flex gap-2">
            {modo !== 'grid' && <button onClick={() => setModo('grid')} className="btn-secondary text-sm">Ver catálogo</button>}
            <button onClick={abrirNuevo} className="btn-primary text-sm"><Plus size={15} /> Nueva promoción</button>
          </div>
        )}
      </div>

      {/* Form */}
      {(modo === 'nuevo' || modo === 'editar') && (
        <div className="card animate-fadeIn">
          <h2 className="text-base font-bold mb-4 ct-accent">{modo === 'nuevo' ? 'Nueva promoción' : 'Editar promoción'}</h2>
          <form onSubmit={handleGuardar} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="label">Nombre de la promoción *</label>
                <input className="input-field" value={form.nombre} onChange={e => setForm(f => ({...f, nombre: e.target.value}))} required placeholder="Ej: Oferta de verano" />
              </div>
              <div>
                <label className="label">Foto</label>
                <input type="file" accept="image/*" className="input-field text-xs" onChange={e => setForm(f => ({...f, foto: e.target.files[0]}))} />
              </div>
              <div className="sm:col-span-2">
                <label className="label">Descripción</label>
                <textarea className="input-field" rows={2} value={form.descripcion} onChange={e => setForm(f => ({...f, descripcion: e.target.value}))} placeholder="Descripción breve..." />
              </div>
              <div>
                <label className="label">Tipo *</label>
                <select className="input-field" value={form.item_tipo} onChange={e => setForm(f => ({...f, item_tipo: e.target.value, item_id: ''}))}>
                  <option value="producto">Producto</option>
                  <option value="paquete">Paquete</option>
                </select>
              </div>
              <div>
                <label className="label">{form.item_tipo === 'producto' ? 'Producto' : 'Paquete'} *</label>
                <select className="input-field" value={form.item_id} onChange={e => { setForm(f => ({...f, item_id: e.target.value})); setSugerencias([]) }} required>
                  <option value="">— Seleccionar —</option>
                  {(form.item_tipo === 'producto' ? productos : paquetes).map(i => (
                    <option key={i.id} value={i.id}>{i.nombre} · S/ {parseFloat(i.precio_venta||0).toFixed(2)}</option>
                  ))}
                </select>
              </div>
            </div>

            {form.item_id && (
              <div>
                <button type="button" onClick={handleSugerirIA} disabled={cargandoIA} className="btn-secondary text-sm flex items-center gap-2">
                  <Zap size={14} className="text-amber-500" />
                  {cargandoIA ? 'Consultando IA...' : 'Sugerir descuento con IA'}
                </button>
                {sugerencias.length > 0 && (
                  <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {sugerencias.map(s => (
                      <button key={s.nivel} type="button" onClick={() => aplicarSugerencia(s)}
                        className="text-left p-3 rounded-2xl transition-all" style={{ background: '#fdf2f8', border: '2px solid #fce7f3' }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor = '#ec4899' }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor = '#fce7f3' }}>
                        <p className="font-bold text-sm ct-accent">{s.nivel}</p>
                        <p className="text-primary-600 font-bold text-lg">{s.porcentaje_descuento}% off</p>
                        <p className="text-xs ct-muted">Precio: S/ {s.precio_promocion?.toFixed(2)}</p>
                        <p className="text-xs ct-muted">Margen: {s.margen_restante}%</p>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
              <div>
                <label className="label">Descuento (%) *</label>
                <input type="number" min="0" max="99" step="0.1" className="input-field" value={form.porcentaje_descuento} onChange={e => setForm(f => ({...f, porcentaje_descuento: e.target.value}))} required placeholder="20" />
              </div>
              {itemSel && form.porcentaje_descuento && (
                <div className="p-3 rounded-2xl" style={{ background: '#fdf2f8', border: '1px solid #fce7f3' }}>
                  <p className="text-xs ct-muted">Original: S/ {parseFloat(itemSel.precio_venta||0).toFixed(2)}</p>
                  <p className="font-bold text-primary-600">Promo: S/ {(parseFloat(itemSel.precio_venta||0) * (1 - parseFloat(form.porcentaje_descuento||0)/100)).toFixed(2)}</p>
                </div>
              )}
              <div>
                <label className="label">Estado</label>
                <select className="input-field" value={form.activo ? 'true' : 'false'} onChange={e => setForm(f => ({...f, activo: e.target.value === 'true'}))}>
                  <option value="true">Activa</option>
                  <option value="false">Inactiva</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div><label className="label">Fecha inicio (opcional)</label><input type="datetime-local" className="input-field" value={form.fecha_inicio} onChange={e => setForm(f => ({...f, fecha_inicio: e.target.value}))} /></div>
              <div><label className="label">Fecha fin (opcional)</label><input type="datetime-local" className="input-field" value={form.fecha_fin} onChange={e => setForm(f => ({...f, fecha_fin: e.target.value}))} /></div>
            </div>

            <div className="flex gap-3 justify-end">
              <button type="button" onClick={() => setModo('grid')} className="btn-secondary">Cancelar</button>
              <button type="submit" disabled={guardando} className="btn-primary">{guardando ? 'Guardando...' : modo === 'nuevo' ? 'Crear promoción' : 'Guardar'}</button>
            </div>
          </form>
        </div>
      )}

      {/* Grid */}
      {modo === 'grid' && (
        loading ? (
          <div className="flex justify-center py-12"><div className="spinner" /></div>
        ) : promociones.length === 0 ? (
          <div className="text-center py-16">
            <Tag size={48} className="mx-auto mb-3 ct-pink-lt" />
            <p className="text-sm ct-muted">No hay promociones. ¡Crea la primera!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {promociones.map(p => (
              <div key={p.id} className={`card p-0 overflow-hidden hover:shadow-rose-md transition-all ${!p.activa_ahora ? 'opacity-60' : ''}`}>
                {p.foto
                  ? <img src={`${BASE_URL}${p.foto}`} alt={p.nombre} className="w-full h-40 object-cover rounded-t-[1.125rem]" />
                  : <div className="w-full h-40 flex items-center justify-center rounded-t-[1.125rem]" style={{ background: 'linear-gradient(135deg, #fdf2f8, #fbcfe8)' }}>
                      <Tag size={36} className="ct-pink-lt" />
                    </div>
                }
                <div className="p-4">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-bold text-sm ct-primary">{p.nombre}</h3>
                    <span className="badge badge-pink ml-2 shrink-0">-{parseFloat(p.porcentaje_descuento).toFixed(0)}%</span>
                  </div>
                  <div className="flex gap-2 items-center mb-1">
                    <span className="text-sm line-through ct-muted">S/ {parseFloat(p.precio_original).toFixed(2)}</span>
                    <span className="text-lg font-bold text-primary-600">S/ {parseFloat(p.precio_promocion).toFixed(2)}</span>
                  </div>
                  {(p.fecha_inicio || p.fecha_fin) && (
                    <p className="text-[11px] mb-2 ct-muted">
                      {p.fecha_inicio ? `Desde ${new Date(p.fecha_inicio).toLocaleDateString('es-PE')}` : ''}
                      {p.fecha_fin ? ` · Hasta ${new Date(p.fecha_fin).toLocaleDateString('es-PE')}` : ''}
                    </p>
                  )}
                  {isAdmin && (
                    <div className="flex gap-2 mt-3 pt-3 border-t border-pink-50">
                      <button onClick={() => handleToggle(p.id)} className={`flex-1 flex items-center gap-1.5 justify-center text-xs py-1.5 rounded-xl border transition-colors font-medium ${p.activo ? 'border-green-300 text-green-700 bg-green-50' : 'border-pink-200 text-rose-400'}`}>
                        {p.activo ? <ToggleRight size={13} /> : <ToggleLeft size={13} />}
                        {p.activo ? 'Activa' : 'Inactiva'}
                      </button>
                      <button onClick={() => abrirEditar(p)} className="w-8 h-8 rounded-xl flex items-center justify-center text-primary-500 hover:bg-primary-50 transition-colors"><Edit size={14} /></button>
                      <button onClick={() => handleEliminar(p.id)} className="w-8 h-8 rounded-xl flex items-center justify-center text-red-400 hover:bg-red-50 transition-colors"><X size={14} /></button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  )
}
