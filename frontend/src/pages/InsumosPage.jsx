import { useState, useEffect } from 'react'
import { getInsumos, crearInsumo, actualizarInsumo, eliminarInsumo, reabastecerInsumo, registrarMerma, getMermas } from '../api/insumos'
import { Archive, Plus, Edit, X, Check, Search, ShoppingCart, Boxes, PackageMinus, History, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'

const UNIDADES = [
  { value: 'mg',     label: 'mg / gramos', emoji: '⚖️', ejemplo: 'Harina, azúcar, sal' },
  { value: 'ml',     label: 'ml (líquidos)', emoji: '💧', ejemplo: 'Leche, aceite, esencia' },
  { value: 'unidad', label: 'Unidades', emoji: '🥚', ejemplo: 'Huevos, bolsas de manjar' },
]

const emptyForm = { nombre: '', unidad: 'mg', cantidad_compra: '', precio_compra: '', comprado: false }
const emptyEditForm = { nombre: '', unidad: 'mg', precio_unitario: '', stock_actual: '', costo_total: '' }

const MOTIVOS_MERMA = [
  { value: 'vencido', label: 'Vencido' },
  { value: 'otro',    label: 'Otro (especificar)' },
]

function ModalMerma({ insumo, onClose, onGuardado }) {
  const [cantidad, setCantidad] = useState('')
  const [motivo, setMotivo] = useState('vencido')
  const [detalle, setDetalle] = useState('')
  const [saving, setSaving] = useState(false)

  const stock = parseFloat(insumo.stock_actual)

  const handleSubmit = async (e) => {
    e.preventDefault()
    const c = parseFloat(cantidad)
    if (!c || c <= 0) { toast.error('Indica cuánto vas a dar de baja'); return }
    if (c > stock) { toast.error(`Solo hay ${stock.toFixed(2)} ${insumo.unidad} en stock`); return }
    if (motivo === 'otro' && !detalle.trim()) { toast.error('Escribe el motivo'); return }
    setSaving(true)
    try {
      await registrarMerma(insumo.id, { cantidad: c, motivo, detalle: motivo === 'otro' ? detalle.trim() : null })
      toast.success('Baja registrada')
      onGuardado(); onClose()
    } catch (err) { toast.error(err.response?.data?.detail || 'Error') }
    finally { setSaving(false) }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-card max-w-md animate-fadeIn">
        <div className="flex justify-between items-start mb-5">
          <div>
            <h3 className="text-base font-bold ct-primary">Dar de baja stock</h3>
            <p className="text-sm font-semibold text-primary-600 mt-0.5">{insumo.nombre}</p>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-xl flex items-center justify-center hover:bg-primary-50 ct-pink-lt"><X size={18}/></button>
        </div>

        <div className="flex items-start gap-2 mb-5 p-3 rounded-xl bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/30">
          <AlertTriangle size={16} className="text-amber-500 shrink-0 mt-0.5"/>
          <p className="text-xs text-amber-700 dark:text-amber-300">Reduce el stock por pérdida (vencido, dañado…). <strong>No modifica el precio</strong> del insumo. Stock actual: <strong>{stock.toFixed(2)} {insumo.unidad}</strong></p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Cantidad a dar de baja ({insumo.unidad}) *</label>
            <input type="number" step="0.001" min="0.001" max={stock} className="input-field" value={cantidad}
              onChange={e => setCantidad(e.target.value)} required autoFocus
              placeholder={`Máximo ${stock.toFixed(2)} ${insumo.unidad}`}/>
          </div>
          <div>
            <label className="label">Motivo *</label>
            <select className="input-field" value={motivo} onChange={e => setMotivo(e.target.value)}>
              {MOTIVOS_MERMA.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
          </div>
          {motivo === 'otro' && (
            <div>
              <label className="label">Especifica el motivo *</label>
              <input className="input-field" value={detalle} onChange={e => setDetalle(e.target.value)}
                placeholder="Ej: se dañó por humedad, se cayó al piso..." autoFocus/>
            </div>
          )}
          {cantidad && parseFloat(cantidad) > 0 && parseFloat(cantidad) <= stock && (
            <div className="rounded-xl p-3 bg-rose-softer text-xs">
              <span className="ct-secondary">Stock después de la baja: </span>
              <span className="font-bold font-mono ct-accent">{(stock - parseFloat(cantidad)).toFixed(2)} {insumo.unidad}</span>
            </div>
          )}
          <div className="flex gap-3 justify-end pt-1">
            <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-danger">
              <PackageMinus size={15}/> {saving ? 'Registrando...' : 'Dar de baja'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function ModalReabastecer({ insumo, onClose, onGuardado }) {
  const [form, setForm] = useState({ cantidad_compra: '', precio_compra: '' })
  const [saving, setSaving] = useState(false)

  const precioNuevo = () => {
    const c = parseFloat(form.cantidad_compra), p = parseFloat(form.precio_compra)
    return (!c || !p || c <= 0) ? null : (p / c).toFixed(6)
  }
  const precioPromedio = () => {
    const c = parseFloat(form.cantidad_compra), p = parseFloat(form.precio_compra)
    if (!c || !p || c <= 0) return null
    const sa = parseFloat(insumo.stock_actual), pa = parseFloat(insumo.precio_unitario)
    const total = sa + c
    return total > 0 ? ((sa * pa + p) / total).toFixed(6) : null
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const c = parseFloat(form.cantidad_compra), p = parseFloat(form.precio_compra)
    if (!c || c <= 0) { toast.error('La cantidad debe ser mayor a 0'); return }
    if (!p || p < 0) { toast.error('El precio no puede ser negativo'); return }
    setSaving(true)
    try { await reabastecerInsumo(insumo.id, { cantidad_compra: c, precio_compra: p }); toast.success('Stock actualizado'); onGuardado(); onClose() }
    catch (err) { toast.error(err.response?.data?.detail || 'Error') }
    finally { setSaving(false) }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-card max-w-md animate-fadeIn">
        <div className="flex justify-between items-start mb-5">
          <div>
            <h3 className="text-base font-bold ct-primary">Reabastecer insumo</h3>
            <p className="text-sm font-semibold text-primary-600 mt-0.5">{insumo.nombre}</p>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-xl flex items-center justify-center hover:bg-primary-50 ct-pink-lt"><X size={18}/></button>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-5 p-3.5 rounded-2xl bg-rose-softer">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider ct-pink-lt mb-0.5">Stock actual</p>
            <p className="font-semibold text-sm ct-primary">{parseFloat(insumo.stock_actual).toFixed(2)} {insumo.unidad}</p>
          </div>
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider ct-pink-lt mb-0.5">Precio actual</p>
            <p className="font-mono font-semibold text-sm ct-primary">S/ {parseFloat(insumo.precio_unitario).toFixed(6)}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Cantidad comprada ({insumo.unidad}) *</label>
            <input type="number" step="0.001" min="0.001" className="input-field" value={form.cantidad_compra}
              onChange={e => setForm(f => ({...f, cantidad_compra: e.target.value}))} required
              placeholder={insumo.unidad === 'unidad' ? 'Ej: 30 unidades' : 'Ej: 1000'}/>
          </div>
          <div>
            <label className="label">Precio total pagado (S/) *</label>
            <input type="number" step="0.01" min="0" className="input-field" value={form.precio_compra}
              onChange={e => setForm(f => ({...f, precio_compra: e.target.value}))} required placeholder="Ej: 15.00"/>
          </div>

          {precioPromedio() && (
            <div className="rounded-2xl p-4 bg-rose-tint">
              <p className="text-xs font-bold text-primary-700 dark:text-primary-300 mb-2.5 uppercase tracking-wide">Resultado del reabastecimiento</p>
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between">
                  <span className="ct-secondary">Nuevo stock total:</span>
                  <span className="font-bold font-mono ct-accent">{(parseFloat(insumo.stock_actual) + parseFloat(form.cantidad_compra||0)).toFixed(2)} {insumo.unidad}</span>
                </div>
                <div className="flex justify-between">
                  <span className="ct-secondary">Precio esta compra:</span>
                  <span className="font-mono text-primary-600">S/ {precioNuevo()}/{insumo.unidad}</span>
                </div>
                <div className="flex justify-between pt-1.5 border-t border-pink-200 dark:border-pink-800/30 mt-1">
                  <span className="font-semibold ct-accent">Precio promedio:</span>
                  <span className="font-bold font-mono text-primary-600">S/ {precioPromedio()}/{insumo.unidad}</span>
                </div>
              </div>
            </div>
          )}

          <div className="flex gap-3 justify-end pt-1">
            <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-primary">
              <ShoppingCart size={15}/> {saving ? 'Guardando...' : 'Reabastecer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function InsumosPage() {
  const [insumos, setInsumos] = useState([])
  const [loading, setLoading] = useState(true)
  const [busqueda, setBusqueda] = useState('')
  const [modo, setModo] = useState('lista')
  const [form, setForm] = useState(emptyForm)
  const [editForm, setEditForm] = useState(emptyEditForm)
  const [editId, setEditId] = useState(null)
  const [saving, setSaving] = useState(false)
  const [restockInsumo, setRestockInsumo] = useState(null)
  const [mermaInsumo, setMermaInsumo] = useState(null)
  const [mermas, setMermas] = useState([])
  const [showMermas, setShowMermas] = useState(false)

  const cargarMermas = () => { getMermas({ limite: 30 }).then(setMermas).catch(() => {}) }

  const cargar = () => {
    setLoading(true)
    getInsumos().then(setInsumos).catch(() => toast.error('Error al cargar')).finally(() => setLoading(false))
    cargarMermas()
  }
  useEffect(() => { cargar() }, [])

  const filtrados = insumos.filter(i => i.nombre.toLowerCase().includes(busqueda.toLowerCase()))

  const abrirNuevo = () => { setForm(emptyForm); setEditId(null); setModo('nuevo') }
  const abrirEditar = (ins) => {
    const costoTotal = (parseFloat(ins.precio_unitario) * parseFloat(ins.stock_actual)) || 0
    setEditForm({ nombre: ins.nombre, unidad: ins.unidad, precio_unitario: ins.precio_unitario, stock_actual: ins.stock_actual, costo_total: costoTotal.toFixed(2) })
    setEditId(ins.id); setModo('editar')
  }

  // Mantiene sincronizados precio unitario, stock y costo total en el form de edición.
  // Fuente de verdad al guardar = costo total (igual que al crear un insumo).
  const editChange = (campo, valor) => setEditForm(f => {
    const next = { ...f, [campo]: valor }
    const stock = parseFloat(next.stock_actual) || 0
    if (campo === 'costo_total') {
      const ct = parseFloat(valor) || 0
      next.precio_unitario = stock > 0 ? (ct / stock).toFixed(6) : f.precio_unitario
    } else {
      // cambió precio_unitario o stock_actual → recalcular costo total
      const pu = parseFloat(next.precio_unitario) || 0
      next.costo_total = (pu * stock).toFixed(2)
    }
    return next
  })

  const precioCalc = () => {
    const c = parseFloat(form.cantidad_compra), p = parseFloat(form.precio_compra)
    return (!c || !p || c <= 0) ? null : (p / c).toFixed(6)
  }

  const handleGuardarNuevo = async (e) => {
    e.preventDefault()
    const c = parseFloat(form.cantidad_compra), p = parseFloat(form.precio_compra)
    if (!c || c <= 0) { toast.error('Cantidad debe ser mayor a 0'); return }
    if (!p || p < 0) { toast.error('Precio no puede ser negativo'); return }
    setSaving(true)
    try { await crearInsumo({ nombre: form.nombre, unidad: form.unidad, cantidad_compra: c, precio_compra: p, comprado: form.comprado }); toast.success('Insumo creado'); setModo('lista'); cargar() }
    catch (err) { toast.error(err.response?.data?.detail || 'Error') }
    finally { setSaving(false) }
  }

  const handleGuardarEdicion = async (e) => {
    e.preventDefault()
    const stock = parseFloat(editForm.stock_actual)
    const costoTotal = parseFloat(editForm.costo_total)
    if (isNaN(stock) || stock < 0) { toast.error('Stock inválido'); return }
    // Precio unitario derivado del costo total (fuente de verdad). Si stock = 0, conserva el precio unitario.
    const precioUnitario = (!isNaN(costoTotal) && stock > 0)
      ? costoTotal / stock
      : parseFloat(editForm.precio_unitario)
    if (isNaN(precioUnitario) || precioUnitario < 0) { toast.error('Costo total inválido'); return }
    setSaving(true)
    try {
      await actualizarInsumo(editId, { nombre: editForm.nombre, unidad: editForm.unidad, precio_unitario: precioUnitario, stock_actual: stock })
      toast.success('Insumo actualizado'); setModo('lista'); cargar()
    } catch (err) { toast.error(err.response?.data?.detail || 'Error') }
    finally { setSaving(false) }
  }

  const handleEliminar = async (id) => {
    if (!confirm('¿Desactivar este insumo?')) return
    try { await eliminarInsumo(id); toast.success('Insumo desactivado'); cargar() }
    catch { toast.error('Error') }
  }

  const u = UNIDADES.find(u => u.value === form.unidad)

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {restockInsumo && <ModalReabastecer insumo={restockInsumo} onClose={() => setRestockInsumo(null)} onGuardado={cargar}/>}
      {mermaInsumo && <ModalMerma insumo={mermaInsumo} onClose={() => setMermaInsumo(null)} onGuardado={cargar}/>}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{background:'linear-gradient(135deg,#ec4899,#be185d)'}}>
            <Archive size={20} className="text-white"/>
          </div>
          <div>
            <h1 className="page-title">Insumos</h1>
            <p className="page-subtitle">{insumos.filter(i => i.activo).length} activos · {insumos.length} en total</p>
          </div>
        </div>
        <div className="flex gap-2">
          {modo !== 'lista' && <button onClick={() => setModo('lista')} className="btn-secondary text-sm">Ver lista</button>}
          <button onClick={abrirNuevo} className="btn-primary text-sm"><Plus size={15}/> Nuevo insumo</button>
        </div>
      </div>

      {/* Form nuevo */}
      {modo === 'nuevo' && (
        <div className="card animate-fadeIn">
          <h2 className="text-base font-bold mb-1 ct-accent">Registrar insumo</h2>
          <p className="text-sm mb-5 ct-muted">Ingresa la cantidad y el precio total — el precio por unidad se calcula automáticamente. Marca si ya lo compraste o solo lo registras para armar productos.</p>
          <form onSubmit={handleGuardarNuevo} className="space-y-4">
            <div>
              <label className="label">Nombre del insumo *</label>
              <input className="input-field" value={form.nombre} onChange={e => setForm(f => ({...f, nombre: e.target.value}))} required placeholder="Ej: Harina de trigo, Leche fresca"/>
            </div>
            <div>
              <label className="label">Tipo de unidad *</label>
              <div className="grid grid-cols-3 gap-3">
                {UNIDADES.map(u => (
                  <label key={u.value} className={`relative flex flex-col items-center gap-1.5 p-4 rounded-2xl cursor-pointer border-2 transition-all ${
                    form.unidad === u.value
                      ? 'border-primary-400 bg-rose-softer shadow-rose'
                      : 'border-pink-100 dark:border-pink-900/30 hover:border-pink-300 bg-white dark:bg-gray-900/50'
                  }`}>
                    <input type="radio" name="unidad" value={u.value} checked={form.unidad === u.value} onChange={e => setForm(f => ({...f, unidad: e.target.value}))} className="hidden"/>
                    <span className="text-2xl">{u.emoji}</span>
                    <span className="text-sm font-semibold ct-accent">{u.label}</span>
                    <span className="text-[11px] text-center ct-muted">{u.ejemplo}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">{form.unidad === 'unidad' ? 'Cantidad (piezas)' : form.unidad === 'ml' ? 'Cantidad (ml)' : 'Cantidad (mg/g)'} *</label>
                <input type="number" step="0.001" min="0.001" className="input-field" value={form.cantidad_compra}
                  onChange={e => setForm(f => ({...f, cantidad_compra: e.target.value}))} required
                  placeholder={form.unidad === 'unidad' ? 'Ej: 30' : 'Ej: 1000'}/>
                {u && <p className="text-[11px] mt-1 ct-muted">{u.ejemplo}</p>}
              </div>
              <div>
                <label className="label">Precio total pagado (S/) *</label>
                <input type="number" step="0.01" min="0" className="input-field" value={form.precio_compra}
                  onChange={e => setForm(f => ({...f, precio_compra: e.target.value}))} required placeholder="Ej: 10.50"/>
              </div>
            </div>
            {/* Switch: ¿ya comprado? */}
            <div className={`flex items-start gap-3 p-4 rounded-2xl border-2 transition-colors ${form.comprado ? 'border-green-200 bg-green-50/60 dark:bg-green-950/20 dark:border-green-900/40' : 'border-pink-100 dark:border-pink-900/30 bg-rose-softer'}`}>
              <button type="button" role="switch" aria-checked={form.comprado}
                onClick={() => setForm(f => ({ ...f, comprado: !f.comprado }))}
                className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors mt-0.5 ${form.comprado ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`}>
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${form.comprado ? 'translate-x-6' : 'translate-x-1'}`}/>
              </button>
              <div className="flex-1">
                <p className="text-sm font-semibold ct-primary">
                  {form.comprado ? '✅ Ya lo compré' : '🕒 Aún no lo he comprado'}
                </p>
                <p className="text-xs ct-muted mt-0.5">
                  {form.comprado
                    ? 'Cuenta como gasto en Finanzas.'
                    : 'No aparece en Finanzas. Se marcará como comprado automáticamente al vender un producto que lo use o al reabastecerlo.'}
                </p>
              </div>
            </div>

            {precioCalc() && (
              <div className="rounded-2xl p-4 bg-rose-tint">
                <p className="text-xs font-semibold ct-pink-lt mb-1 uppercase tracking-wide">Precio calculado</p>
                <p className="text-lg font-bold text-primary-600">S/ {precioCalc()} <span className="text-sm font-normal ct-muted">/ {form.unidad === 'unidad' ? 'unidad' : form.unidad}</span></p>
                <p className="text-xs mt-0.5 ct-muted">{parseFloat(form.precio_compra||0).toFixed(2)} ÷ {parseFloat(form.cantidad_compra||0).toFixed(2)} · Stock inicial: {parseFloat(form.cantidad_compra||0).toFixed(2)} {form.unidad}</p>
              </div>
            )}
            <div className="flex gap-3 justify-end pt-2">
              <button type="button" onClick={() => setModo('lista')} className="btn-secondary">Cancelar</button>
              <button type="submit" disabled={saving} className="btn-primary"><Check size={15}/> {saving ? 'Guardando...' : 'Registrar insumo'}</button>
            </div>
          </form>
        </div>
      )}

      {/* Form editar */}
      {modo === 'editar' && (
        <div className="card animate-fadeIn">
          <h2 className="text-base font-bold mb-4 ct-accent">Editar insumo</h2>
          <form onSubmit={handleGuardarEdicion} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="sm:col-span-2"><label className="label">Nombre *</label><input className="input-field" value={editForm.nombre} onChange={e => setEditForm(f => ({...f, nombre: e.target.value}))} required/></div>
            <div>
              <label className="label">Unidad *</label>
              <select className="input-field" value={editForm.unidad} onChange={e => setEditForm(f => ({...f, unidad: e.target.value}))}>
                {UNIDADES.map(u => <option key={u.value} value={u.value}>{u.label}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Stock actual ({editForm.unidad}) *</label>
              <input type="number" step="0.01" min="0" className="input-field" value={editForm.stock_actual} onChange={e => editChange('stock_actual', e.target.value)} required/>
            </div>
            <div>
              <label className="label">Costo total (S/) *</label>
              <input type="number" step="0.01" min="0" className="input-field" value={editForm.costo_total} onChange={e => editChange('costo_total', e.target.value)} required placeholder="Lo que costó todo el stock"/>
              <p className="text-[11px] mt-1 ct-muted">Lo que pagaste por todo el stock. El precio por unidad se recalcula solo.</p>
            </div>
            <div>
              <label className="label">Precio por {editForm.unidad} (S/) *</label>
              <input type="number" step="0.000001" min="0" className="input-field" value={editForm.precio_unitario} onChange={e => editChange('precio_unitario', e.target.value)} required/>
              <p className="text-[11px] mt-1 ct-muted">= Costo total ÷ Stock (se ajusta automáticamente)</p>
            </div>
            <div className="sm:col-span-2 flex gap-3 justify-end">
              <button type="button" onClick={() => setModo('lista')} className="btn-secondary">Cancelar</button>
              <button type="submit" disabled={saving} className="btn-primary"><Check size={15}/> {saving ? 'Guardando...' : 'Guardar cambios'}</button>
            </div>
          </form>
        </div>
      )}

      {/* Lista */}
      <div className="card">
        <div className="search-box mb-4">
          <Search size={15} className="ct-pink-lt"/>
          <input placeholder="Buscar insumo..." value={busqueda} onChange={e => setBusqueda(e.target.value)}/>
        </div>
        {loading ? <div className="flex justify-center py-12"><div className="spinner"/></div>
        : filtrados.length === 0 ? (
          <div className="text-center py-12">
            <Boxes size={40} className="mx-auto mb-3 ct-pink-lt"/>
            <p className="text-sm ct-muted">No hay insumos registrados</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-pink-100 dark:border-pink-900/20">
                  {['Nombre','Unidad','Precio/unidad','Stock','Comprado','Estado','Acciones'].map(h => (
                    <th key={h} className="text-left pb-3 text-xs font-semibold ct-pink-lt uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-pink-50 dark:divide-pink-900/10">
                {filtrados.map(ins => (
                  <tr key={ins.id} className={`table-row-hover ${!ins.activo ? 'opacity-50' : ''}`}>
                    <td className="py-2.5 font-semibold ct-primary">{ins.nombre}</td>
                    <td className="py-2.5"><span className="badge badge-pink">{ins.unidad}</span></td>
                    <td className="py-2.5 font-mono text-xs ct-secondary">S/ {parseFloat(ins.precio_unitario).toFixed(6)} / {ins.unidad}</td>
                    <td className="py-2.5 font-medium ct-primary">{parseFloat(ins.stock_actual).toFixed(2)} <span className="ct-muted">{ins.unidad}</span></td>
                    <td className="py-2.5">{ins.comprado
                      ? <span className="badge badge-green">Sí</span>
                      : <span className="badge badge-yellow">No</span>}</td>
                    <td className="py-2.5"><span className={ins.activo ? 'badge badge-green' : 'badge badge-gray'}>{ins.activo ? 'Activo' : 'Inactivo'}</span></td>
                    <td className="py-2.5">
                      <div className="flex gap-1.5">
                        <button onClick={() => abrirEditar(ins)} className="w-7 h-7 rounded-lg flex items-center justify-center text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-950/30 transition-colors" title="Editar"><Edit size={14}/></button>
                        {ins.activo && <button onClick={() => setRestockInsumo(ins)} className="w-7 h-7 rounded-lg flex items-center justify-center text-green-500 hover:bg-green-50 dark:hover:bg-green-950/30 transition-colors" title="Reabastecer"><Plus size={14}/></button>}
                        {ins.activo && parseFloat(ins.stock_actual) > 0 && <button onClick={() => setMermaInsumo(ins)} className="w-7 h-7 rounded-lg flex items-center justify-center text-amber-500 hover:bg-amber-50 dark:hover:bg-amber-950/30 transition-colors" title="Dar de baja (vencido / merma)"><PackageMinus size={14}/></button>}
                        {ins.activo && <button onClick={() => handleEliminar(ins.id)} className="w-7 h-7 rounded-lg flex items-center justify-center text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors" title="Desactivar"><X size={14}/></button>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Historial de bajas / mermas */}
      {mermas.length > 0 && (
        <div className="card">
          <button onClick={() => setShowMermas(s => !s)} className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <History size={16} className="text-amber-500"/>
              <h3 className="text-base font-bold ct-accent">Bajas registradas</h3>
              <span className="badge badge-yellow text-xs">{mermas.length}</span>
            </div>
            <span className="text-xs ct-muted">{showMermas ? 'Ocultar' : 'Ver'}</span>
          </button>
          {showMermas && (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-pink-100 dark:border-pink-900/20">
                    {['Insumo','Cantidad','Motivo','Fecha'].map(h => (
                      <th key={h} className="text-left pb-2.5 text-xs font-semibold ct-pink-lt uppercase tracking-wide">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-pink-50 dark:divide-pink-900/10">
                  {mermas.map(m => (
                    <tr key={m.id} className="table-row-hover">
                      <td className="py-2.5 font-medium ct-primary">{m.insumo_nombre}</td>
                      <td className="py-2.5 ct-secondary">{m.cantidad.toFixed(2)} {m.unidad}</td>
                      <td className="py-2.5">
                        {m.motivo === 'vencido'
                          ? <span className="badge badge-red">Vencido</span>
                          : <span className="badge badge-gray">{m.detalle || 'Otro'}</span>}
                      </td>
                      <td className="py-2.5 text-xs ct-muted">{m.fecha ? new Date(m.fecha).toLocaleDateString('es-PE') : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
