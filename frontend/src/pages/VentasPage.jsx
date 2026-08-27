import { useState, useEffect, useCallback, useRef } from 'react'
import { getVentas, crearVenta, marcarPagado, cambiarEstado, descargarBoleta } from '../api/ventas'
import { getClientes, crearCliente, getDirecciones } from '../api/clientes'
import { getProductos } from '../api/productos'
import { getPaquetes } from '../api/paquetes'
import { getPromociones } from '../api/promociones'
import {
  ShoppingBag, Plus, Eye, FileText, CheckCircle, X, Search,
  User, AlertTriangle, Calendar, Clock, PackageX, Truck
} from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'

const METODOS_PAGO = ['efectivo', 'yape', 'plin', 'transferencia', 'tarjeta']
const FUENTES_MARKETING = [
  { value: '', label: 'Ninguno' },
  { value: 'facebook', label: 'Facebook' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'tiktok', label: 'TikTok' },
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'google_ads', label: 'Google Ads' },
  { value: 'otro', label: 'Otro' },
]
const UNIDAD_A_HORAS = { horas: 1, dias: 24, semanas: 168 }

// Suma el tiempo de preparación de los productos del carrito, convertido a horas
function prepHorasTotal(items) {
  return items
    .filter(i => i.item_tipo === 'producto' && i.tiempo_preparacion && i.unidad_tiempo)
    .reduce((acc, i) => {
      const factor = UNIDAD_A_HORAS[i.unidad_tiempo] || 1
      return acc + parseFloat(i.tiempo_preparacion) * factor * i.cantidad
    }, 0)
}

function ModalOverlay({ children }) {
  return (
    <div className="modal-overlay">
      <div className="animate-fadeIn w-full flex items-center justify-center">{children}</div>
    </div>
  )
}

function ModalNuevoCliente({ onClose, onCreado }) {
  const [form, setForm] = useState({ nombres: '', apellidos: '', telefono: '', correo: '' })
  const [saving, setSaving] = useState(false)
  const handleSubmit = async (e) => {
    e.preventDefault(); setSaving(true)
    try { const res = await crearCliente(form); toast.success('Cliente registrado'); onCreado(res.cliente); onClose() }
    catch (err) { toast.error(err.response?.data?.detail || 'Error') }
    finally { setSaving(false) }
  }
  return (
    <ModalOverlay>
      <div className="modal-card max-w-md">
        <div className="flex justify-between items-center mb-5">
          <h3 className="text-base font-bold ct-primary">Registrar nuevo cliente</h3>
          <button onClick={onClose} className="w-8 h-8 rounded-xl flex items-center justify-center hover:bg-primary-50 ct-pink-lt transition-colors"><X size={18} /></button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Nombres *</label><input className="input-field" value={form.nombres} onChange={e => setForm(f=>({...f,nombres:e.target.value}))} required /></div>
            <div><label className="label">Apellidos *</label><input className="input-field" value={form.apellidos} onChange={e => setForm(f=>({...f,apellidos:e.target.value}))} required /></div>
          </div>
          <div><label className="label">Teléfono</label><input className="input-field" value={form.telefono} onChange={e => setForm(f=>({...f,telefono:e.target.value}))} /></div>
          <div><label className="label">Correo</label><input type="email" className="input-field" value={form.correo} onChange={e => setForm(f=>({...f,correo:e.target.value}))} /></div>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-primary">{saving?'Guardando...':'Registrar cliente'}</button>
          </div>
        </form>
      </div>
    </ModalOverlay>
  )
}

function ModalVerVenta({ venta, onClose }) {
  return (
    <ModalOverlay>
      <div className="modal-card max-w-lg max-h-[85vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-5">
          <div>
            <h3 className="text-base font-bold ct-primary">Venta #{venta.id}</h3>
            <p className="text-xs mt-0.5 ct-muted">{new Date(venta.fecha_hora).toLocaleString('es-PE')}</p>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-xl flex items-center justify-center hover:bg-primary-50 ct-pink-lt transition-colors"><X size={18} /></button>
        </div>
        <div className="grid grid-cols-2 gap-3 mb-5">
          {[['Cliente',venta.cliente_nombre],['Método de pago',venta.metodo_pago],['Vendedor',venta.colaborador_nombre],['Estado pago',venta.estado_pago]].map(([k,v]) => (
            <div key={k} className="bg-rose-softer rounded-xl p-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider ct-pink-lt mb-0.5">{k}</p>
              <p className="text-sm font-medium capitalize ct-primary">{v||'—'}</p>
            </div>
          ))}
          {venta.direccion_entrega && (
            <div className="col-span-2 bg-rose-softer rounded-xl p-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider ct-pink-lt mb-0.5">📍 Dirección de entrega</p>
              <p className="text-sm font-medium ct-primary">{venta.direccion_entrega}</p>
            </div>
          )}
          {!venta.direccion_entrega && (
            <div className="col-span-2 bg-rose-softer rounded-xl p-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider ct-pink-lt mb-0.5">📍 Entrega</p>
              <p className="text-sm font-medium ct-primary">🏪 Recojo en tienda</p>
            </div>
          )}
        </div>
        {venta.fecha_entrega && (
          <div className="flex items-center gap-2 text-sm bg-rose-softer rounded-xl p-3 mb-4">
            <Calendar size={15} className="text-primary-500" />
            <span className="font-medium text-primary-600">Entrega: {new Date(venta.fecha_entrega).toLocaleString('es-PE')}</span>
          </div>
        )}
        <div className="border border-pink-100 dark:border-pink-900/20 rounded-xl overflow-hidden mb-4">
          <table className="w-full text-sm">
            <thead className="bg-primary-50/50 dark:bg-primary-950/20">
              <tr>
                <th className="text-left px-3 py-2.5 text-xs font-semibold ct-pink-lt uppercase tracking-wide">Item</th>
                <th className="text-center px-3 py-2.5 text-xs font-semibold ct-pink-lt uppercase tracking-wide">Cant.</th>
                <th className="text-right px-3 py-2.5 text-xs font-semibold ct-pink-lt uppercase tracking-wide">Subtotal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-pink-50 dark:divide-pink-900/20">
              {(venta.items||[]).map(item => (
                <tr key={item.id}>
                  <td className="px-3 py-2.5 font-medium ct-primary">{item.nombre_snapshot}</td>
                  <td className="px-3 py-2.5 text-center ct-secondary">{item.cantidad}</td>
                  <td className="px-3 py-2.5 text-right font-semibold text-primary-600">S/ {parseFloat(item.subtotal).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex justify-between items-center mb-4">
          {venta.notas && <p className="text-xs ct-muted italic">Nota: {venta.notas}</p>}
          <div className="ml-auto text-right">
            <p className="text-xs ct-pink-lt mb-0.5">Total</p>
            <p className="text-2xl font-bold text-primary-600">S/ {parseFloat(venta.total).toFixed(2)}</p>
          </div>
        </div>
        <button onClick={onClose} className="btn-secondary w-full">Cerrar</button>
      </div>
    </ModalOverlay>
  )
}

function ModalConfirmacion({ titulo, mensaje, onConfirmar, onCancelar, tipo='advertencia', textoConfirmar='Confirmar', soloAceptar=false }) {
  return (
    <ModalOverlay>
      <div className="modal-card max-w-sm">
        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-4 ${tipo==='error'?'bg-red-100':'bg-amber-100'}`}>
          <AlertTriangle size={22} className={tipo==='error'?'text-red-500':'text-amber-500'} />
        </div>
        <h3 className="font-bold text-base mb-2 ct-primary">{titulo}</h3>
        <p className="text-sm mb-5 ct-secondary">{mensaje}</p>
        <div className="flex gap-3 justify-end">
          {!soloAceptar && <button onClick={onCancelar} className="btn-secondary">Cancelar</button>}
          <button onClick={onConfirmar} className="btn-primary">{textoConfirmar}</button>
        </div>
      </div>
    </ModalOverlay>
  )
}

const tipoBadge = { producto:'badge badge-blue', paquete:'badge badge-green', promocion:'badge badge-pink' }
const estadoVentaLabel = (e) => ({completada:'Entregado',en_proceso:'En proceso',cancelada:'Cancelada'}[e]||e)
const estadoVentaClass = (e) => ({completada:'badge badge-blue',en_proceso:'badge badge-orange',cancelada:'badge badge-red'}[e]||'badge badge-gray')

export default function VentasPage() {
  const { usuario } = useAuth()
  const [ventas,setVentas] = useState([])
  const [clientes,setClientes] = useState([])
  const [itemsCatalogo,setItemsCatalogo] = useState([])
  const [loading,setLoading] = useState(true)
  const [orden,setOrden] = useState('desc')
  const [verVenta,setVerVenta] = useState(null)
  const [modalNuevoCliente,setModalNuevoCliente] = useState(false)
  const [guardando,setGuardando] = useState(false)
  const [modalConfirm,setModalConfirm] = useState(null)
  const [form,setForm] = useState({cliente_id:'',metodo_pago:'efectivo',notas:'',fecha_entrega:'',fuente_marketing:'',direccion_entrega:'',items:[]})
  const [busquedaCliente,setBusquedaCliente] = useState('')
  const [busquedaItem,setBusquedaItem] = useState('')
  const [clienteSeleccionado,setClienteSeleccionado] = useState(null)
  const [showClienteDropdown,setShowClienteDropdown] = useState(false)
  const [showItemDropdown,setShowItemDropdown] = useState(false)
  const [dirsCliente,setDirsCliente] = useState([])
  const [dirCustom,setDirCustom] = useState(false)
  const clienteRef = useRef(null)
  const itemRef = useRef(null)

  const cargar = useCallback(() => {
    setLoading(true)
    Promise.all([getVentas({orden}),getClientes(),getProductos(true),getPaquetes(true),getPromociones(true)])
      .then(([v,c,prods,paqs,promos]) => {
        setVentas(v); setClientes(c)
        setItemsCatalogo([
          ...prods.map(p=>({id:p.id,tipo:'producto',nombre:p.nombre,precio:p.precio_venta,foto:p.foto,tiempo_preparacion:p.tiempo_preparacion,unidad_tiempo:p.unidad_tiempo,tiene_insumos:p.insumos&&p.insumos.length>0})),
          ...paqs.map(p=>({id:p.id,tipo:'paquete',nombre:p.nombre,precio:p.precio_venta})),
          ...promos.filter(p=>p.activa_ahora).map(p=>({id:p.id,tipo:'promocion',nombre:p.nombre,precio:p.precio_promocion})),
        ])
      }).catch(()=>toast.error('Error al cargar datos')).finally(()=>setLoading(false))
  },[orden])

  useEffect(()=>{cargar()},[cargar])
  useEffect(()=>{
    const fn=(e)=>{
      if(clienteRef.current&&!clienteRef.current.contains(e.target))setShowClienteDropdown(false)
      if(itemRef.current&&!itemRef.current.contains(e.target))setShowItemDropdown(false)
    }
    document.addEventListener('mousedown',fn); return()=>document.removeEventListener('mousedown',fn)
  },[])

  const agregarItem = (item) => {
    const ex=form.items.find(i=>i.item_tipo===item.tipo&&i.item_id===item.id)
    if(ex) setForm(f=>({...f,items:f.items.map(i=>i.item_tipo===item.tipo&&i.item_id===item.id?{...i,cantidad:i.cantidad+1}:i)}))
    else setForm(f=>({...f,items:[...f.items,{item_tipo:item.tipo,item_id:item.id,nombre:item.nombre,precio:item.precio,cantidad:1,tiene_insumos:item.tiene_insumos,tiempo_preparacion:item.tiempo_preparacion,unidad_tiempo:item.unidad_tiempo}]}))
    setBusquedaItem(''); setShowItemDropdown(false)
  }
  const quitarItem=(idx)=>setForm(f=>({...f,items:f.items.filter((_,i)=>i!==idx)}))
  const setCantidad=(idx,v)=>setForm(f=>({...f,items:f.items.map((item,i)=>i===idx?{...item,cantidad:Math.max(1,parseInt(v)||1)}:item)}))
  const total=form.items.reduce((acc,i)=>acc+parseFloat(i.precio||0)*i.cantidad,0)
  const clientesMostrados=(busquedaCliente?clientes.filter(c=>`${c.nombres} ${c.apellidos}`.toLowerCase().includes(busquedaCliente.toLowerCase())):clientes).slice(0,6)
  const itemsMostrados=(busquedaItem?itemsCatalogo.filter(i=>i.nombre.toLowerCase().includes(busquedaItem.toLowerCase())):itemsCatalogo).slice(0,8)
  const seleccionarCliente=(c)=>{
    setClienteSeleccionado(c)
    setDirCustom(false)
    setForm(f=>({...f,cliente_id:c.id,direccion_entrega:''}))
    setBusquedaCliente(''); setShowClienteDropdown(false)
    // Cargar direcciones del cliente
    if(c.direcciones && c.direcciones.length > 0){
      setDirsCliente(c.direcciones)
      // Pre-seleccionar la principal si existe
      const principal = c.direcciones.find(d=>d.principal)
      if(principal) setForm(f=>({...f,cliente_id:c.id,direccion_entrega:principal.label}))
    } else {
      getDirecciones(c.id).then(dirs=>{
        setDirsCliente(dirs)
        const principal = dirs.find(d=>d.principal)
        if(principal) setForm(f=>({...f,direccion_entrega:principal.label}))
      }).catch(()=>setDirsCliente([]))
    }
  }

  const validarYRegistrar = () => {
    if(!form.cliente_id){toast.error('Selecciona un cliente');return}
    if(!form.items.length){toast.error('Agrega al menos un producto');return}
    const sinInsumos=form.items.filter(i=>i.item_tipo==='producto'&&i.tiene_insumos===false)
    if(sinInsumos.length){setModalConfirm({tipo:'error',titulo:'Sin insumos configurados',mensaje:`${sinInsumos.map(i=>i.nombre).join(', ')} — Ve a Productos y configura los insumos.`,esBloqueo:true});return}
    // Si hay fecha de entrega, avisa (sin bloquear) cuando el tiempo de prep no alcanza
    if(form.fecha_entrega){
      const horasPrep=prepHorasTotal(form.items)
      if(horasPrep>0){
        const horasDisp=(new Date(form.fecha_entrega)-new Date())/3600000
        if(horasPrep>horasDisp){const dias=Math.ceil(horasPrep/24);setModalConfirm({tipo:'advertencia',titulo:'Tiempo de preparación ajustado',mensaje:`Preparación estimada: ${horasPrep.toFixed(1)} h (~${dias} día${dias!==1?'s':''}). ¿Confirmar de todas formas?`,esBloqueo:false});return}
      }
    }
    ejecutarRegistro()
  }

  const ejecutarRegistro = async () => {
    setModalConfirm(null); setGuardando(true)
    try {
      const res = await crearVenta({cliente_id:form.cliente_id,metodo_pago:form.metodo_pago,notas:form.notas||null,fecha_entrega:form.fecha_entrega?new Date(form.fecha_entrega).toISOString():null,fuente_marketing:form.fuente_marketing||null,direccion_entrega:form.direccion_entrega||null,items:form.items.map(i=>({item_tipo:i.item_tipo,item_id:i.item_id,cantidad:i.cantidad}))})
      toast.success('Venta registrada correctamente')
      // Mostrar alertas de stock bajo post-venta
      if (res.alertas_stock?.length) {
        toast(`⚠️ Stock bajo: ${res.alertas_stock.slice(0,3).join(', ')}${res.alertas_stock.length>3?'...':''}`, {
          duration: 7000,
          style: { background: '#fff7ed', color: '#9a3412', border: '1px solid #fdba74' },
        })
      }
      setForm({cliente_id:'',metodo_pago:'efectivo',notas:'',fecha_entrega:'',fuente_marketing:'',direccion_entrega:'',items:[]}); setClienteSeleccionado(null); setDirsCliente([]); setDirCustom(false); cargar()
    } catch(err){
      const detail = err.response?.data?.detail
      if (detail?.tipo === 'stock_insuficiente') {
        setModalConfirm({
          tipo: 'error',
          titulo: 'Stock insuficiente para este pedido',
          mensaje: 'No hay suficientes insumos:\n' + (detail.errores||[]).join('\n'),
          esBloqueo: true,
        })
      } else {
        toast.error(typeof detail === 'string' ? detail : 'Error al registrar la venta')
      }
    }
    finally{setGuardando(false)}
  }

  const handleMarcarPagado=async(id)=>{try{await marcarPagado(id);toast.success('Marcada como pagada');cargar()}catch{toast.error('Error')}}
  const handleMarcarEntregado=async(id)=>{try{await cambiarEstado(id,'completada');toast.success('Marcada como entregada');cargar()}catch{toast.error('Error')}}
  const handleBoleta=async(id)=>{try{const blob=await descargarBoleta(id);const url=window.URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`boleta_${id}.pdf`;a.click();window.URL.revokeObjectURL(url)}catch{toast.error('Error al generar boleta')}}

  const productosSinInsumos=form.items.filter(i=>i.item_tipo==='producto'&&i.tiene_insumos===false)
  const horasPrep=prepHorasTotal(form.items)
  const horasDisp=form.fecha_entrega?(new Date(form.fecha_entrega)-new Date())/3600000:null
  const tiempoInsuf=horasDisp!==null&&horasPrep>0&&horasPrep>horasDisp

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      {verVenta&&<ModalVerVenta venta={verVenta} onClose={()=>setVerVenta(null)}/>}
      {modalNuevoCliente&&<ModalNuevoCliente onClose={()=>setModalNuevoCliente(false)} onCreado={(c)=>{setClientes(p=>[...p,c]);seleccionarCliente(c)}}/>}
      {modalConfirm&&<ModalConfirmacion titulo={modalConfirm.titulo} mensaje={modalConfirm.mensaje} tipo={modalConfirm.tipo} soloAceptar={modalConfirm.esBloqueo} textoConfirmar={modalConfirm.esBloqueo?'Entendido':'Sí, registrar'} onCancelar={()=>setModalConfirm(null)} onConfirmar={modalConfirm.esBloqueo?()=>setModalConfirm(null):ejecutarRegistro}/>}

      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{background:'linear-gradient(135deg,#ec4899,#be185d)'}}>
          <ShoppingBag size={20} className="text-white"/>
        </div>
        <div>
          <h1 className="page-title">Ventas</h1>
          <p className="page-subtitle">{ventas.length} ventas registradas</p>
        </div>
      </div>

      {/* Form */}
      <div className="card">
        <h2 className="text-base font-bold mb-4 ct-accent">Nueva venta</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="label">Vendedor</label>
            <div className="input-field bg-rose-soft ct-secondary">{usuario?.nombres} {usuario?.apellidos}</div>
          </div>
          <div>
            <label className="label">Método de pago</label>
            <select className="input-field" value={form.metodo_pago} onChange={e=>setForm(f=>({...f,metodo_pago:e.target.value}))}>
              {METODOS_PAGO.map(m=><option key={m} value={m}>{m.charAt(0).toUpperCase()+m.slice(1)}</option>)}
            </select>
          </div>

          {/* Cliente */}
          <div className="relative" ref={clienteRef}>
            <label className="label flex items-center gap-1.5">
              Cliente <span className="text-red-400">*</span>
              {!clienteSeleccionado&&<span className="normal-case tracking-normal font-normal text-red-300 text-[10px]">requerido</span>}
            </label>
            {clienteSeleccionado ? (
              <div className="input-field flex items-center gap-2" style={{background:'#f0fdf4',borderColor:'#86efac'}}>
                <User size={14} className="text-green-600"/>
                <span className="flex-1 text-sm font-medium text-green-700">{clienteSeleccionado.nombres} {clienteSeleccionado.apellidos}</span>
                <button onClick={()=>{setClienteSeleccionado(null);setDirCustom(false);setDirsCliente([]);setForm(f=>({...f,cliente_id:'',direccion_entrega:''}))}}><X size={14} className="text-gray-400"/></button>
              </div>
            ) : (
              <>
                <div className="flex gap-2">
                  <input className="input-field flex-1" style={{borderColor:'#fca5a5'}} placeholder="Toca para ver o escribe para buscar..."
                    value={busquedaCliente} onChange={e=>{setBusquedaCliente(e.target.value);setShowClienteDropdown(true)}} onFocus={()=>setShowClienteDropdown(true)}/>
                  <button type="button" onClick={()=>setModalNuevoCliente(true)} className="btn-secondary text-xs px-3"><Plus size={13}/> Nuevo</button>
                </div>
                {showClienteDropdown&&clientesMostrados.length>0&&(
                  <div className="dropdown-menu absolute top-full left-0 right-16 z-20 mt-1.5 animate-fadeIn">
                    {clientesMostrados.map(c=>(
                      <div key={c.id} className="dropdown-item" onMouseDown={()=>seleccionarCliente(c)}>
                        <div>
                          <p className="font-medium text-sm ct-primary">{c.nombres} {c.apellidos}</p>
                          {c.telefono&&<p className="text-xs ct-muted">{c.telefono}</p>}
                        </div>
                        <User size={13} className="ct-pink-lt"/>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>

          {/* Fecha entrega */}
          <div>
            <label className="label flex items-center gap-1.5">
              <Calendar size={12}/> Fecha de entrega
              <span className="normal-case tracking-normal font-normal ct-pink-lt text-[10px]">(opcional)</span>
            </label>
            <input type="datetime-local" className="input-field" value={form.fecha_entrega} onChange={e=>setForm(f=>({...f,fecha_entrega:e.target.value}))} min={new Date().toISOString().slice(0,16)}/>
          </div>

          <div>
            <label className="label flex items-center gap-1.5">
              📣 ¿Por dónde nos escribió?
              <span className="normal-case tracking-normal font-normal ct-pink-lt text-[10px]">(para marketing)</span>
            </label>
            <select className="input-field" value={form.fuente_marketing} onChange={e=>setForm(f=>({...f,fuente_marketing:e.target.value}))}>
              {FUENTES_MARKETING.map(f=><option key={f.value} value={f.value}>{f.label}</option>)}
            </select>
          </div>

          {/* Dirección de entrega */}
          <div className="sm:col-span-2">
            <label className="label flex items-center gap-1.5">
              📍 Dirección de entrega
              <span className="normal-case tracking-normal font-normal ct-pink-lt text-[10px]">(aparece en la boleta)</span>
            </label>
            {clienteSeleccionado ? (
              <div className="space-y-2">
                <select
                  className="input-field"
                  value={dirCustom ? '__custom__' : form.direccion_entrega}
                  onChange={e=>{
                    const v = e.target.value
                    if (v === '__custom__') { setDirCustom(true); setForm(f=>({...f,direccion_entrega:''})) }
                    else { setDirCustom(false); setForm(f=>({...f,direccion_entrega:v})) }
                  }}
                >
                  <option value="">🏪 Recojo en tienda</option>
                  {dirsCliente.map(d=>(
                    <option key={d.id} value={d.label}>{d.principal?'⭐ ':''}{d.etiqueta.charAt(0).toUpperCase()+d.etiqueta.slice(1)}: {d.direccion}{d.distrito?`, ${d.distrito}`:''}</option>
                  ))}
                  <option value="__custom__">✏️ Escribir otra dirección...</option>
                </select>
                {dirCustom && (
                  <input
                    className="input-field"
                    placeholder="Escribe la dirección de entrega..."
                    value={form.direccion_entrega}
                    onChange={e=>setForm(f=>({...f,direccion_entrega:e.target.value}))}
                    autoFocus
                  />
                )}
                {!dirCustom && !form.direccion_entrega && (
                  <p className="text-xs ct-muted flex items-center gap-1">🏪 Se registrará como <strong>Recojo en tienda</strong></p>
                )}
              </div>
            ) : (
              <div className="input-field bg-rose-soft ct-muted text-sm">Selecciona un cliente para ver sus direcciones</div>
            )}
          </div>
          <div>
            <label className="label">Notas</label>
            <input className="input-field" placeholder="Observaciones del pedido..." value={form.notas} onChange={e=>setForm(f=>({...f,notas:e.target.value}))}/>
          </div>
        </div>

        {productosSinInsumos.length>0&&(
          <div className="alert-error mb-4">
            <PackageX size={18} className="text-red-500 shrink-0 mt-0.5"/>
            <div><p className="text-sm font-semibold text-red-700">Productos sin insumos</p><p className="text-xs text-red-500 mt-0.5">{productosSinInsumos.map(i=>i.nombre).join(', ')}</p></div>
          </div>
        )}
        {tiempoInsuf&&(
          <div className="alert-warning mb-4">
            <Clock size={18} className="text-amber-500 shrink-0 mt-0.5"/>
            <div><p className="text-sm font-semibold text-amber-700">Tiempo ajustado</p><p className="text-xs text-amber-600 mt-0.5">Preparación: <strong>{horasPrep.toFixed(1)} h</strong> · Disponible: <strong>{horasDisp?.toFixed(1)} h</strong></p></div>
          </div>
        )}

        {/* Buscador items */}
        <div className="mb-4">
          <label className="label">Agregar al pedido</label>
          <div className="relative" ref={itemRef}>
            <div className="search-box">
              <Search size={15} className="ct-pink-lt"/>
              <input placeholder="Toca para ver catálogo o escribe para buscar..." value={busquedaItem}
                onChange={e=>{setBusquedaItem(e.target.value);setShowItemDropdown(true)}} onFocus={()=>setShowItemDropdown(true)}/>
            </div>
            {showItemDropdown&&itemsMostrados.length>0&&(
              <div className="dropdown-menu absolute top-full left-0 right-0 z-20 mt-1.5 max-h-64 overflow-y-auto animate-fadeIn">
                {itemsMostrados.map(item=>(
                  <div key={`${item.tipo}-${item.id}`} className="dropdown-item" onMouseDown={()=>agregarItem(item)}>
                    <span className="flex items-center gap-2.5">
                      <span className={tipoBadge[item.tipo]}>{item.tipo}</span>
                      <span className="font-medium text-sm ct-primary">{item.nombre}</span>
                      {item.tipo==='producto'&&item.tiene_insumos===false&&<span className="text-xs text-red-400 flex items-center gap-0.5"><AlertTriangle size={10}/> sin insumos</span>}
                    </span>
                    <span className="font-bold text-primary-600 text-sm">S/ {parseFloat(item.precio||0).toFixed(2)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {form.items.length>0&&(
          <div className="border border-pink-100 dark:border-pink-900/20 rounded-2xl overflow-hidden mb-4">
            <table className="w-full text-sm">
              <thead className="bg-primary-50/60 dark:bg-primary-950/20">
                <tr>
                  <th className="text-left px-4 py-2.5 text-xs font-semibold ct-pink-lt uppercase tracking-wide">Producto</th>
                  <th className="text-center px-3 py-2.5 text-xs font-semibold ct-pink-lt uppercase tracking-wide w-24">Cant.</th>
                  <th className="text-right px-3 py-2.5 text-xs font-semibold ct-pink-lt uppercase tracking-wide">P. Unit.</th>
                  <th className="text-right px-4 py-2.5 text-xs font-semibold ct-pink-lt uppercase tracking-wide">Subtotal</th>
                  <th className="w-10"/>
                </tr>
              </thead>
              <tbody className="divide-y divide-pink-50 dark:divide-pink-900/10">
                {form.items.map((item,idx)=>(
                  <tr key={idx} className={`table-row-hover ${item.tiene_insumos===false?'bg-red-50/50 dark:bg-red-950/20':''}`}>
                    <td className="px-4 py-2.5 font-medium ct-primary">
                      {item.nombre}
                      {item.tiene_insumos===false&&<span className="ml-2 badge badge-red">sin insumos</span>}
                    </td>
                    <td className="px-3 py-2.5 text-center">
                      <input type="number" min="1" className="input-field w-20 text-center py-1 text-sm" value={item.cantidad} onChange={e=>setCantidad(idx,e.target.value)}/>
                    </td>
                    <td className="px-3 py-2.5 text-right ct-secondary">S/ {parseFloat(item.precio||0).toFixed(2)}</td>
                    <td className="px-4 py-2.5 text-right font-bold text-primary-600">S/ {(parseFloat(item.precio||0)*item.cantidad).toFixed(2)}</td>
                    <td className="py-2.5 pr-2"><button onClick={()=>quitarItem(idx)} className="w-7 h-7 rounded-lg flex items-center justify-center text-rose-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"><X size={14}/></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="bg-primary-50/40 dark:bg-primary-950/20 px-4 py-3 flex justify-between items-center">
              <p className="text-xs ct-pink-lt font-medium">{form.items.length} ítem{form.items.length!==1?'s':''}</p>
              <div className="text-right">
                <p className="text-xs ct-pink-lt">Total</p>
                <p className="text-xl font-bold text-primary-600">S/ {total.toFixed(2)}</p>
              </div>
            </div>
          </div>
        )}
        <div className="flex justify-end">
          <button onClick={validarYRegistrar} disabled={guardando||!form.items.length||!form.cliente_id} className="btn-primary">
            <Plus size={16}/> {guardando?'Registrando...':'Registrar venta'}
          </button>
        </div>
      </div>

      {/* Historial */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold ct-accent">Historial de ventas</h2>
          <select className="input-field w-40 text-sm" value={orden} onChange={e=>setOrden(e.target.value)}>
            <option value="desc">Más recientes</option>
            <option value="asc">Más antiguas</option>
          </select>
        </div>
        {loading?<div className="flex justify-center py-12"><div className="spinner"/></div>
        :ventas.length===0?(
          <div className="text-center py-12">
            <ShoppingBag size={40} className="mx-auto mb-3 ct-pink-lt"/>
            <p className="text-sm ct-muted">No hay ventas registradas aún</p>
          </div>
        ):(
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-pink-100 dark:border-pink-900/20">
                  {['#','Fecha','Entrega','Cliente','Total','Pago','Estado',''].map(h=>(
                    <th key={h} className="text-left pb-3 text-xs font-semibold ct-pink-lt uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-pink-50 dark:divide-pink-900/10">
                {ventas.map(v=>(
                  <tr key={v.id} className="table-row-hover">
                    <td className="py-3 font-mono text-xs ct-pink-lt">#{v.id}</td>
                    <td className="py-3 text-xs ct-secondary">
                      {new Date(v.fecha_hora).toLocaleDateString('es-PE')}<br/>
                      <span className="ct-muted">{new Date(v.fecha_hora).toLocaleTimeString('es-PE',{hour:'2-digit',minute:'2-digit'})}</span>
                    </td>
                    <td className="py-3 text-xs">
                      {v.fecha_entrega
                        ?<span className="flex items-center gap-1 text-primary-600 font-medium"><Calendar size={11}/>{new Date(v.fecha_entrega).toLocaleDateString('es-PE')}</span>
                        :<span className="ct-pink-lt opacity-50">—</span>}
                    </td>
                    <td className="py-3 font-medium ct-primary">{v.cliente_nombre}</td>
                    <td className="py-3 font-bold text-primary-600">S/ {parseFloat(v.total).toFixed(2)}</td>
                    <td className="py-3"><span className={v.estado_pago==='pagado'?'badge badge-green':'badge badge-yellow'}>{v.estado_pago}</span></td>
                    <td className="py-3"><span className={estadoVentaClass(v.estado_venta)}>{estadoVentaLabel(v.estado_venta)}</span></td>
                    <td className="py-3 pr-1">
                      <div className="flex gap-1">
                        <button onClick={()=>setVerVenta(v)} className="w-7 h-7 rounded-lg flex items-center justify-center text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/30 transition-colors" title="Ver"><Eye size={14}/></button>
                        {v.estado_pago!=='pagado'&&<button onClick={()=>handleMarcarPagado(v.id)} className="w-7 h-7 rounded-lg flex items-center justify-center text-green-500 hover:bg-green-50 dark:hover:bg-green-950/30 transition-colors" title="Pagado"><CheckCircle size={14}/></button>}
                        {v.estado_venta==='en_proceso'&&<button onClick={()=>handleMarcarEntregado(v.id)} className="w-7 h-7 rounded-lg flex items-center justify-center text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-950/30 transition-colors" title="Entregado"><Truck size={14}/></button>}
                        <button onClick={()=>handleBoleta(v.id)} className="w-7 h-7 rounded-lg flex items-center justify-center text-amber-500 hover:bg-amber-50 dark:hover:bg-amber-950/30 transition-colors" title="Boleta"><FileText size={14}/></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
