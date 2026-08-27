import { useState, useEffect } from 'react'
import { getPaquetes, crearPaquete, actualizarPaquete, eliminarPaquete } from '../api/paquetes'
import { getProductos } from '../api/productos'
import { Package, Plus, Search, X, Edit, Eye, Calculator } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'

const BASE_URL = 'http://127.0.0.1:8000'

function FotoPaquete({ foto, nombre }) {
  if (foto) return <img src={`${BASE_URL}${foto}`} alt={nombre} className="w-full h-44 object-cover" />
  return (
    <div className="w-full h-44 flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #fdf2f8, #fce7f3)' }}>
      <Package size={36} className="ct-pink-lt" />
    </div>
  )
}

export default function PaquetesPage() {
  const { isAdmin } = useAuth()
  const [paquetes, setPaquetes] = useState([])
  const [productos, setProductos] = useState([])
  const [loading, setLoading] = useState(true)
  const [modo, setModo] = useState('grid')
  const [busqueda, setBusqueda] = useState('')
  const [paqueteEditar, setPaqueteEditar] = useState(null)
  const [modalVer, setModalVer] = useState(null)
  const [costeado, setCosteado] = useState(null)
  const [guardando, setGuardando] = useState(false)
  const [busquedaProducto, setBusquedaProducto] = useState('')
  const [form, setForm] = useState({ nombre: '', porcentaje_ganancia: '', productos_seleccionados: [], foto: null })

  const cargar = () => {
    setLoading(true)
    Promise.all([getPaquetes(), getProductos(true)])
      .then(([paq, prods]) => { setPaquetes(paq); setProductos(prods) })
      .catch(() => toast.error('Error al cargar')).finally(() => setLoading(false))
  }
  useEffect(() => { cargar() }, [])

  const filtrados = paquetes.filter(p => p.nombre.toLowerCase().includes(busqueda.toLowerCase()))
  const resetForm = () => { setForm({ nombre: '', porcentaje_ganancia: '', productos_seleccionados: [], foto: null }); setCosteado(null); setBusquedaProducto('') }

  const abrirNuevo = () => { resetForm(); setPaqueteEditar(null); setModo('nuevo') }
  const abrirEditar = (p) => {
    setPaqueteEditar(p)
    setForm({ nombre: p.nombre, porcentaje_ganancia: p.porcentaje_ganancia||'', foto: null, productos_seleccionados: (p.productos||[]).map(pp => ({ producto_id: pp.producto_id, cantidad: pp.cantidad, nombre: pp.nombre_producto, precio_venta: pp.precio_venta, precio_costo: pp.precio_costo })) })
    setCosteado(p.precio_costo_real ? { precio_costo_real: p.precio_costo_real, precio_referencia_suma: p.precio_referencia_suma, precio_venta: p.precio_venta } : null)
    setModo('editar')
  }

  const agregarProducto = (prod) => {
    if (form.productos_seleccionados.find(p => p.producto_id === prod.id)) return
    setForm(f => ({ ...f, productos_seleccionados: [...f.productos_seleccionados, { producto_id: prod.id, cantidad: 1, nombre: prod.nombre, precio_venta: prod.precio_venta, precio_costo: prod.precio_costo }] }))
    setBusquedaProducto('')
  }
  const quitarProducto = (id) => setForm(f => ({ ...f, productos_seleccionados: f.productos_seleccionados.filter(p => p.producto_id !== id) }))
  const setCantidad = (id, v) => setForm(f => ({ ...f, productos_seleccionados: f.productos_seleccionados.map(p => p.producto_id === id ? { ...p, cantidad: v } : p) }))

  const calcularLocal = () => {
    const suma = form.productos_seleccionados.reduce((a, p) => a + parseFloat(p.precio_venta||0)*parseInt(p.cantidad||1), 0)
    const costo = form.productos_seleccionados.reduce((a, p) => a + parseFloat(p.precio_costo||0)*parseInt(p.cantidad||1), 0)
    const pg = parseFloat(form.porcentaje_ganancia) / 100
    const venta = pg < 1 ? costo / (1 - pg) : 0
    setCosteado({ precio_costo_real: costo.toFixed(2), precio_referencia_suma: suma.toFixed(2), precio_venta: venta.toFixed(2) })
    toast.success('Costeo calculado')
  }

  const handleGuardar = async () => {
    if (!costeado) { toast.error('Primero costea el paquete'); return }
    setGuardando(true)
    try {
      const fd = new FormData()
      fd.append('nombre', form.nombre); fd.append('porcentaje_ganancia', parseFloat(form.porcentaje_ganancia))
      fd.append('productos_json', JSON.stringify(form.productos_seleccionados.map(p => ({ producto_id: p.producto_id, cantidad: parseInt(p.cantidad) }))))
      if (form.foto) fd.append('foto', form.foto)
      if (modo === 'nuevo') { await crearPaquete(fd); toast.success('Paquete creado') }
      else { await actualizarPaquete(paqueteEditar.id, fd); toast.success('Paquete actualizado') }
      setModo('grid'); cargar()
    } catch (err) { toast.error(err.response?.data?.detail || 'Error') }
    finally { setGuardando(false) }
  }

  const handleEliminar = async (id) => {
    if (!confirm('¿Desactivar este paquete?')) return
    try { await eliminarPaquete(id); toast.success('Paquete desactivado'); cargar() }
    catch { toast.error('Error') }
  }

  const prodsFiltrados = productos.filter(p => p.nombre.toLowerCase().includes(busquedaProducto.toLowerCase()) && !form.productos_seleccionados.find(s => s.producto_id === p.id)).slice(0, 6)

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      {/* Modal ver paquete */}
      {modalVer && (
        <div className="modal-overlay">
          <div className="modal-card max-w-lg max-h-[80vh] overflow-y-auto animate-fadeIn">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-base font-bold ct-primary">{modalVer.nombre}</h3>
              <button onClick={() => setModalVer(null)} className="w-8 h-8 rounded-xl flex items-center justify-center hover:bg-primary-50 text-rose-300"><X size={18} /></button>
            </div>
            {modalVer.foto && <img src={`${BASE_URL}${modalVer.foto}`} alt={modalVer.nombre} className="w-full h-44 object-cover rounded-2xl mb-4" />}
            <p className="text-xs font-semibold uppercase tracking-wide mb-3 ct-muted">Productos incluidos:</p>
            <div className="space-y-2 mb-4">
              {(modalVer.productos||[]).map(pp => (
                <div key={pp.producto_id} className="flex items-center gap-3 p-3 rounded-xl" style={{ background: '#fdf5f9', border: '1px solid #fce7f3' }}>
                  {pp.foto_producto && <img src={`${BASE_URL}${pp.foto_producto}`} alt="" className="w-10 h-10 object-cover rounded-lg" />}
                  <div className="flex-1">
                    <p className="text-sm font-semibold ct-primary">{pp.nombre_producto}</p>
                    <p className="text-xs ct-muted">Cantidad: {pp.cantidad}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex justify-between items-center pt-3 border-t border-pink-100">
              <span className="text-sm ct-secondary">Precio venta del paquete</span>
              <span className="text-xl font-bold text-primary-600">S/ {parseFloat(modalVer.precio_venta||0).toFixed(2)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #ec4899, #be185d)' }}>
            <Package size={20} className="text-white" />
          </div>
          <div>
            <h1 className="page-title">Paquetes</h1>
            <p className="page-subtitle">{paquetes.filter(p => p.activo).length} paquetes activos</p>
          </div>
        </div>
        {isAdmin && (
          <div className="flex gap-2">
            {modo !== 'grid' && <button onClick={() => setModo('grid')} className="btn-secondary text-sm">Ver catálogo</button>}
            <button onClick={abrirNuevo} className="btn-primary text-sm"><Plus size={15} /> Nuevo paquete</button>
          </div>
        )}
      </div>

      {/* Form */}
      {(modo === 'nuevo' || modo === 'editar') && (
        <div className="card space-y-5 animate-fadeIn">
          <h2 className="text-base font-bold ct-accent">{modo === 'nuevo' ? 'Crear nuevo paquete' : 'Editar paquete'}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label">Nombre del paquete *</label>
              <input className="input-field" value={form.nombre} onChange={e => setForm(f => ({...f, nombre: e.target.value}))} placeholder="Ej: Combo Cumpleaños" />
            </div>
            <div>
              <label className="label">Foto</label>
              <input type="file" accept="image/*" className="input-field text-xs" onChange={e => setForm(f => ({...f, foto: e.target.files[0]}))} />
            </div>
          </div>

          <div>
            <label className="label">Productos del paquete</label>
            <div className="relative mb-3">
              <input className="input-field" placeholder="Buscar producto..." value={busquedaProducto} onChange={e => setBusquedaProducto(e.target.value)} />
              {busquedaProducto && prodsFiltrados.length > 0 && (
                <div className="dropdown-menu absolute top-full left-0 right-0 z-20 mt-1.5 animate-fadeIn">
                  {prodsFiltrados.map(p => (
                    <div key={p.id} className="dropdown-item" onMouseDown={() => agregarProducto(p)}>
                      <span className="font-medium">{p.nombre}</span>
                      <span className="text-primary-600 font-semibold text-sm">S/ {parseFloat(p.precio_venta||0).toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="space-y-2">
              {form.productos_seleccionados.map(item => (
                <div key={item.producto_id} className="flex items-center gap-3 p-3 rounded-xl" style={{ background: '#fdf2f8', border: '1px solid #fce7f3' }}>
                  <span className="flex-1 text-sm font-medium ct-primary">{item.nombre}</span>
                  <span className="text-xs ct-muted">S/ {parseFloat(item.precio_venta||0).toFixed(2)}</span>
                  <input type="number" min="1" className="input-field w-20 text-sm py-1" value={item.cantidad} onChange={e => setCantidad(item.producto_id, e.target.value)} />
                  <button type="button" onClick={() => quitarProducto(item.producto_id)} className="w-6 h-6 rounded-lg flex items-center justify-center text-red-400 hover:bg-red-50"><X size={14} /></button>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-end gap-4">
            <div className="flex-1">
              <label className="label">Porcentaje de ganancia (%)</label>
              <input type="number" min="0" max="99" step="0.1" className="input-field" value={form.porcentaje_ganancia} onChange={e => { setForm(f => ({...f, porcentaje_ganancia: e.target.value})); setCosteado(null) }} />
            </div>
            <button type="button" onClick={calcularLocal} className="btn-secondary"><Calculator size={15} /> Costear</button>
          </div>

          {costeado && (
            <div className="grid grid-cols-3 gap-4 p-4 rounded-2xl" style={{ background: 'linear-gradient(135deg, #fdf2f8, #fce7f3)', border: '1px solid #fbcfe8' }}>
              {[['Precio referencia', costeado.precio_referencia_suma, '#78536b'], ['Costo real', costeado.precio_costo_real, '#1a0a14'], ['Precio venta', costeado.precio_venta, '#ec4899']].map(([label, val, color]) => (
                <div key={label}>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-rose-400 mb-1">{label}</p>
                  <p className="text-lg font-bold" style={{ color }}>S/ {parseFloat(val).toFixed(2)}</p>
                </div>
              ))}
            </div>
          )}

          <div className="flex gap-3 justify-end">
            <button onClick={() => setModo('grid')} className="btn-secondary">Cancelar</button>
            <button onClick={handleGuardar} disabled={!costeado || guardando} className="btn-primary">
              <Package size={15} /> {guardando ? 'Guardando...' : modo === 'nuevo' ? 'Crear paquete' : 'Guardar cambios'}
            </button>
          </div>
        </div>
      )}

      {/* Grid */}
      {modo === 'grid' && (
        <>
          <div className="search-box max-w-sm">
            <Search size={15} className="ct-pink-lt" />
            <input placeholder="Buscar paquete..." value={busqueda} onChange={e => setBusqueda(e.target.value)} />
          </div>
          {loading ? (
            <div className="flex justify-center py-12"><div className="spinner" /></div>
          ) : filtrados.length === 0 ? (
            <div className="text-center py-16">
              <Package size={48} className="mx-auto mb-3 ct-pink-lt" />
              <p className="text-sm ct-muted">No hay paquetes. ¡Crea el primero!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {filtrados.map(p => (
                <div key={p.id} className={`card p-0 overflow-hidden hover:shadow-rose-md transition-all ${!p.activo ? 'opacity-60' : ''}`}>
                  <div className="rounded-t-[1.125rem] overflow-hidden"><FotoPaquete foto={p.foto} nombre={p.nombre} /></div>
                  <div className="p-4">
                    <h3 className="font-bold text-sm mb-2 ct-primary">{p.nombre}</h3>
                    <div className="flex items-end justify-between mb-3">
                      <div>
                        <p className="text-xl font-bold text-primary-600">S/ {parseFloat(p.precio_venta||0).toFixed(2)}</p>
                        <p className="text-[11px] ct-muted">Ref: S/ {parseFloat(p.precio_referencia_suma||0).toFixed(2)}</p>
                      </div>
                      {p.productos && <span className="badge badge-pink">{p.productos.length} productos</span>}
                    </div>
                    <div className="flex gap-2 pt-3 border-t border-pink-50">
                      <button onClick={() => setModalVer(p)} className="btn-secondary text-xs py-1.5 flex-1 flex items-center justify-center gap-1"><Eye size={12} /> Ver</button>
                      {isAdmin && <button onClick={() => abrirEditar(p)} className="btn-secondary text-xs py-1.5 flex-1 flex items-center justify-center gap-1"><Edit size={12} /> Editar</button>}
                      {isAdmin && p.activo && <button onClick={() => handleEliminar(p.id)} className="w-8 h-8 rounded-xl flex items-center justify-center text-red-400 hover:bg-red-50 transition-colors"><X size={14} /></button>}
                    </div>
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
