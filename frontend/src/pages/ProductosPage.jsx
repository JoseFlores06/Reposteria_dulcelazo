import { useState, useEffect } from 'react'
import { getProductos, costearProducto, crearProducto, actualizarProducto, eliminarProducto } from '../api/productos'
import { getInsumos } from '../api/insumos'
import { Package, Plus, Search, X, Edit, Calculator, Clock, Copy } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'

const BASE_URL = 'http://127.0.0.1:8000'

function FotoProducto({ foto, nombre, size = 'md' }) {
  const sz = { sm: 'w-10 h-10', md: 'w-full h-44', lg: 'w-full h-52' }
  if (foto) return <img src={`${BASE_URL}${foto}`} alt={nombre} className={`${sz[size]} object-cover`} />
  return (
    <div className={`${sz[size]} flex items-center justify-center`} style={{ background: 'linear-gradient(135deg, #fdf2f8, #fce7f3)' }}>
      <Package size={size === 'sm' ? 18 : 36} className="ct-pink-lt" />
    </div>
  )
}

export default function ProductosPage() {
  const { isAdmin } = useAuth()
  const [productos, setProductos] = useState([])
  const [insumos, setInsumos] = useState([])
  const [loading, setLoading] = useState(true)
  const [modo, setModo] = useState('grid')
  const [busqueda, setBusqueda] = useState('')
  const [productoSel, setProductoSel] = useState(null)
  const [costeado, setCosteado] = useState(null)
  const [guardando, setGuardando] = useState(false)
  const [form, setForm] = useState({ nombre: '', tiempo_preparacion: '', unidad_tiempo: 'horas', porcentaje_ganancia: '', insumos_seleccionados: [], foto: null })
  const [busquedaInsumo, setBusquedaInsumo] = useState('')
  const [duplicando, setDuplicando] = useState(null)

  const cargar = () => {
    setLoading(true)
    Promise.all([getProductos(), getInsumos(true)])
      .then(([p, i]) => { setProductos(p); setInsumos(i) })
      .catch(() => toast.error('Error al cargar'))
      .finally(() => setLoading(false))
  }
  useEffect(() => { cargar() }, [])

  const filtrados = productos.filter(p => p.nombre.toLowerCase().includes(busqueda.toLowerCase()))
  const resetForm = () => { setForm({ nombre: '', tiempo_preparacion: '', unidad_tiempo: 'horas', porcentaje_ganancia: '', insumos_seleccionados: [], foto: null }); setCosteado(null); setBusquedaInsumo(''); setDuplicando(null) }

  const abrirNuevo = () => { resetForm(); setProductoSel(null); setModo('nuevo') }
  const abrirEditar = (p) => {
    setProductoSel(p); setDuplicando(null)
    setForm({ nombre: p.nombre, tiempo_preparacion: p.tiempo_preparacion || '', unidad_tiempo: p.unidad_tiempo || 'horas', porcentaje_ganancia: p.porcentaje_ganancia || '', foto: null, insumos_seleccionados: (p.insumos||[]).map(i => ({ insumo_id: i.insumo_id, cantidad_necesaria: i.cantidad_necesaria, nombre: i.nombre_insumo, unidad: i.unidad_insumo })) })
    setCosteado(p.precio_costo ? { precio_costo: p.precio_costo, precio_venta: p.precio_venta } : null)
    setModo('editar')
  }
  // Duplicar: pre-llena el form con los datos del producto (incluidos sus insumos)
  // pero como producto NUEVO (no edita el original). Ajusta nombre y cantidades y guarda.
  const abrirDuplicar = (p) => {
    setProductoSel(null); setDuplicando(p.nombre)
    setForm({ nombre: p.nombre, tiempo_preparacion: p.tiempo_preparacion || '', unidad_tiempo: p.unidad_tiempo || 'horas', porcentaje_ganancia: p.porcentaje_ganancia || '', foto: null, insumos_seleccionados: (p.insumos||[]).map(i => ({ insumo_id: i.insumo_id, cantidad_necesaria: i.cantidad_necesaria, nombre: i.nombre_insumo, unidad: i.unidad_insumo })) })
    setCosteado(p.precio_costo ? { precio_costo: p.precio_costo, precio_venta: p.precio_venta } : null)
    setBusquedaInsumo(''); setModo('nuevo')
  }

  const agregarInsumo = (ins) => {
    if (form.insumos_seleccionados.find(i => i.insumo_id === ins.id)) return
    setForm(f => ({ ...f, insumos_seleccionados: [...f.insumos_seleccionados, { insumo_id: ins.id, cantidad_necesaria: 1, nombre: ins.nombre, unidad: ins.unidad }] }))
    setBusquedaInsumo(''); setCosteado(null)
  }
  const quitarInsumo = (id) => { setForm(f => ({ ...f, insumos_seleccionados: f.insumos_seleccionados.filter(i => i.insumo_id !== id) })); setCosteado(null) }
  const setCantInsumo = (id, v) => { setForm(f => ({ ...f, insumos_seleccionados: f.insumos_seleccionados.map(i => i.insumo_id === id ? { ...i, cantidad_necesaria: v } : i) })); setCosteado(null) }

  const handleCostear = async () => {
    if (!form.porcentaje_ganancia || !form.insumos_seleccionados.length) { toast.error('Agrega insumos y porcentaje'); return }
    try {
      const res = await costearProducto({ porcentaje_ganancia: parseFloat(form.porcentaje_ganancia), insumos: form.insumos_seleccionados.map(i => ({ insumo_id: i.insumo_id, cantidad_necesaria: parseFloat(i.cantidad_necesaria) })) })
      setCosteado(res); toast.success('Costeo calculado')
    } catch (err) { toast.error(err.response?.data?.detail || 'Error') }
  }

  const handleGuardar = async () => {
    if (!costeado) { toast.error('Primero costea el producto'); return }
    setGuardando(true)
    try {
      const fd = new FormData()
      fd.append('nombre', form.nombre); fd.append('porcentaje_ganancia', parseFloat(form.porcentaje_ganancia))
      if (form.tiempo_preparacion) fd.append('tiempo_preparacion', parseFloat(form.tiempo_preparacion))
      if (form.unidad_tiempo) fd.append('unidad_tiempo', form.unidad_tiempo)
      fd.append('insumos_json', JSON.stringify(form.insumos_seleccionados.map(i => ({ insumo_id: i.insumo_id, cantidad_necesaria: parseFloat(i.cantidad_necesaria) }))))
      if (form.foto) fd.append('foto', form.foto)
      if (modo === 'nuevo') { await crearProducto(fd); toast.success('Producto creado') }
      else { await actualizarProducto(productoSel.id, fd); toast.success('Producto actualizado') }
      setModo('grid'); cargar()
    } catch (err) { toast.error(err.response?.data?.detail || 'Error') }
    finally { setGuardando(false) }
  }

  const handleEliminar = async (id) => {
    if (!confirm('¿Desactivar este producto?')) return
    try { await eliminarProducto(id); toast.success('Desactivado'); cargar() }
    catch { toast.error('Error') }
  }

  const insumosFiltrados = insumos.filter(i => i.nombre.toLowerCase().includes(busquedaInsumo.toLowerCase()) && !form.insumos_seleccionados.find(s => s.insumo_id === i.id)).slice(0, 6)

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #ec4899, #be185d)' }}>
            <Package size={20} className="text-white" />
          </div>
          <div>
            <h1 className="page-title">Productos</h1>
            <p className="page-subtitle">{productos.filter(p => p.activo).length} productos activos</p>
          </div>
        </div>
        {isAdmin && (
          <div className="flex gap-2">
            {modo !== 'grid' && <button onClick={() => setModo('grid')} className="btn-secondary text-sm">Ver catálogo</button>}
            <button onClick={abrirNuevo} className="btn-primary text-sm"><Plus size={15} /> Nuevo producto</button>
          </div>
        )}
      </div>

      {/* Form */}
      {(modo === 'nuevo' || modo === 'editar') && (
        <div className="card space-y-5 animate-fadeIn">
          <h2 className="text-base font-bold ct-accent">{modo === 'nuevo' ? (duplicando ? 'Duplicar producto' : 'Agregar nuevo producto') : 'Editar producto'}</h2>
          {duplicando && (
            <div className="flex items-start gap-2 -mt-2 p-3 rounded-xl bg-rose-softer border border-pink-100 dark:border-pink-900/30">
              <Copy size={15} className="text-primary-500 shrink-0 mt-0.5" />
              <p className="text-xs ct-secondary">Estás duplicando <strong className="text-primary-600">"{duplicando}"</strong>. Se creará un producto <strong>nuevo</strong> (el original no se modifica). Cambia el nombre, ajusta las cantidades de insumos, vuelve a costear y guarda.</p>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="sm:col-span-2">
              <label className="label">Nombre del producto *</label>
              <input className="input-field" value={form.nombre} onChange={e => setForm(f => ({...f, nombre: e.target.value}))} placeholder="Ej: Torta de chocolate" />
            </div>
            <div>
              <label className="label">Tiempo de preparación</label>
              <div className="flex gap-2">
                <input type="number" min="0" step="0.5" className="input-field" value={form.tiempo_preparacion} onChange={e => setForm(f => ({...f, tiempo_preparacion: e.target.value}))} placeholder="2" />
                <select className="input-field w-32" value={form.unidad_tiempo} onChange={e => setForm(f => ({...f, unidad_tiempo: e.target.value}))}>
                  <option value="horas">horas</option>
                  <option value="dias">días</option>
                  <option value="semanas">semanas</option>
                </select>
              </div>
            </div>
            <div>
              <label className="label">Foto</label>
              <input type="file" accept="image/*" className="input-field text-xs" onChange={e => setForm(f => ({...f, foto: e.target.files[0]}))} />
              <p className="text-[11px] mt-1 ct-muted">JPG/PNG, máx 2MB, recomendado 800×800px</p>
            </div>
          </div>

          {/* Insumos */}
          <div>
            <label className="label">Insumos necesarios</label>
            <div className="relative mb-3">
              <input className="input-field" placeholder="Buscar insumo para agregar..." value={busquedaInsumo} onChange={e => setBusquedaInsumo(e.target.value)} />
              {busquedaInsumo && insumosFiltrados.length > 0 && (
                <div className="dropdown-menu absolute top-full left-0 right-0 z-20 mt-1.5 animate-fadeIn">
                  {insumosFiltrados.map(ins => (
                    <div key={ins.id} className="dropdown-item" onMouseDown={() => agregarInsumo(ins)}>
                      <span className="font-medium">{ins.nombre}</span>
                      <span className="badge badge-pink text-[10px]">{ins.unidad} · S/{parseFloat(ins.precio_unitario).toFixed(4)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            {form.insumos_seleccionados.length > 0 && (
              <div className="space-y-2">
                {form.insumos_seleccionados.map(item => (
                  <div key={item.insumo_id} className="flex items-center gap-3 rounded-xl px-3 py-2.5" style={{ background: '#fdf2f8', border: '1px solid #fce7f3' }}>
                    <span className="flex-1 text-sm font-medium ct-primary">{item.nombre}</span>
                    <span className="badge badge-pink">{item.unidad}</span>
                    <input type="number" min="0" step="0.01" className="input-field w-24 text-sm py-1" value={item.cantidad_necesaria} onChange={e => setCantInsumo(item.insumo_id, e.target.value)} />
                    <button type="button" onClick={() => quitarInsumo(item.insumo_id)} className="w-6 h-6 rounded-lg flex items-center justify-center text-red-400 hover:bg-red-50"><X size={14} /></button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Ganancia + costear */}
          <div className="flex items-end gap-4">
            <div className="flex-1">
              <label className="label">Porcentaje de ganancia (%)</label>
              <input type="number" min="0" max="99" step="0.1" className="input-field" value={form.porcentaje_ganancia} onChange={e => { setForm(f => ({...f, porcentaje_ganancia: e.target.value})); setCosteado(null) }} placeholder="30" />
            </div>
            <button type="button" onClick={handleCostear} className="btn-secondary flex items-center gap-2">
              <Calculator size={15} /> Costear
            </button>
          </div>

          {costeado && (
            <div className="rounded-2xl p-4" style={{ background: 'linear-gradient(135deg, #fdf2f8, #fce7f3)', border: '1px solid #fbcfe8' }}>
              <div className="flex gap-8">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-rose-400 mb-1">Costo de producción</p>
                  <p className="text-2xl font-bold ct-secondary">S/ {parseFloat(costeado.precio_costo).toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-rose-400 mb-1">Precio de venta</p>
                  <p className="text-2xl font-bold text-primary-600">S/ {parseFloat(costeado.precio_venta).toFixed(2)}</p>
                </div>
              </div>
            </div>
          )}

          <div className="flex gap-3 justify-end">
            <button onClick={() => setModo('grid')} className="btn-secondary">Cancelar</button>
            <button onClick={handleGuardar} disabled={!costeado || guardando} className="btn-primary">
              <Package size={15} /> {guardando ? 'Guardando...' : modo === 'nuevo' ? 'Agregar producto' : 'Guardar cambios'}
            </button>
          </div>
        </div>
      )}

      {/* Grid */}
      {modo === 'grid' && (
        <>
          <div className="search-box max-w-sm">
            <Search size={15} className="ct-pink-lt" />
            <input placeholder="Buscar producto..." value={busqueda} onChange={e => setBusqueda(e.target.value)} />
          </div>
          {loading ? (
            <div className="flex justify-center py-12"><div className="spinner" /></div>
          ) : filtrados.length === 0 ? (
            <div className="text-center py-16">
              <Package size={48} className="mx-auto mb-3 ct-pink-lt" />
              <p className="text-sm ct-muted">No hay productos aún. ¡Agrega el primero!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {filtrados.map(p => (
                <div key={p.id} className={`card p-0 overflow-hidden transition-all hover:shadow-rose-md ${!p.activo ? 'opacity-60' : ''}`}>
                  <div className="relative overflow-hidden rounded-t-[1.125rem]">
                    <FotoProducto foto={p.foto} nombre={p.nombre} />
                    {!p.activo && (
                      <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                        <span className="badge badge-gray">Inactivo</span>
                      </div>
                    )}
                  </div>
                  <div className="p-4">
                    <h3 className="font-bold text-sm mb-1 ct-primary">{p.nombre}</h3>
                    {p.tiempo_preparacion && (
                      <p className="text-xs flex items-center gap-1 mb-2 ct-muted">
                        <Clock size={11} /> {p.tiempo_preparacion} {p.unidad_tiempo}
                      </p>
                    )}
                    <div className="flex items-end justify-between">
                      <div>
                        <p className="text-xl font-bold text-primary-600">S/ {parseFloat(p.precio_venta||0).toFixed(2)}</p>
                        <p className="text-[11px] ct-muted">Costo: S/ {parseFloat(p.precio_costo||0).toFixed(2)}</p>
                      </div>
                      {p.insumos && <span className="badge badge-pink">{p.insumos.length} insumos</span>}
                    </div>
                    {isAdmin && (
                      <div className="flex gap-2 mt-3 pt-3 border-t border-pink-50">
                        <button onClick={() => abrirEditar(p)} className="btn-secondary text-xs py-1.5 flex-1 flex items-center justify-center gap-1"><Edit size={12} /> Editar</button>
                        <button onClick={() => abrirDuplicar(p)} title="Duplicar producto" className="w-8 h-8 rounded-xl flex items-center justify-center text-primary-500 hover:bg-primary-50 transition-colors"><Copy size={14} /></button>
                        {p.activo && (
                          <button onClick={() => handleEliminar(p.id)} className="w-8 h-8 rounded-xl flex items-center justify-center text-red-400 hover:bg-red-50 transition-colors"><X size={14} /></button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
