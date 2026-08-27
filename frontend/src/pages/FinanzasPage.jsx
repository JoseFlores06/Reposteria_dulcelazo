import { useState, useEffect, useCallback } from 'react'
import {
  getReporteInsumos, getReporteVentas, getReporteGanancia,
  getPagosColaboradores, registrarPago, actualizarPago, eliminarPago,
  getResumenGroq,
} from '../api/finanzas'
import { getVentasDetalle, getDashboard, getMarketingFinanzas } from '../api/marketing'
import { getColaboradores } from '../api/colaboradores'
import {
  TrendingUp, Archive, ShoppingBag, DollarSign, Users, Plus, X, Edit, Check,
  Sparkles, Brain, ChevronDown, ChevronRight, BarChart2, Megaphone, Eye
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import toast from 'react-hot-toast'

const MESES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
const ANIOS = Array.from({length: 5}, (_, i) => new Date().getFullYear() - i)
const CHART_COLORS = ['#ec4899','#f9a8d4','#be185d','#fbcfe8','#9d174d','#f472b6','#db2777','#fce7f3']

const TABS = [
  { id: 'dashboard',       label: 'Dashboard',            icon: BarChart2  },
  { id: 'insumos',         label: 'Insumos',              icon: Archive    },
  { id: 'ventas',          label: 'Ventas',               icon: ShoppingBag },
  { id: 'ventas_detalle',  label: 'Ventas + Ganancia',    icon: TrendingUp  },
  { id: 'ganancia',        label: 'Ganancia',             icon: DollarSign  },
  { id: 'marketing',       label: 'Marketing',            icon: Megaphone   },
  { id: 'pagos',           label: 'Pagos colaboradores',  icon: Users       },
]

function FiltroFecha({ mes, anio, setMes, setAnio }) {
  return (
    <div className="flex gap-2 items-center">
      <select className="input-field w-32 text-sm" value={mes} onChange={e => setMes(parseInt(e.target.value)||'')}>
        <option value="">Todos</option>
        {MESES.map((m, i) => <option key={i} value={i+1}>{m}</option>)}
      </select>
      <select className="input-field w-28 text-sm" value={anio} onChange={e => setAnio(parseInt(e.target.value)||'')}>
        <option value="">Todos</option>
        {ANIOS.map(a => <option key={a} value={a}>{a}</option>)}
      </select>
    </div>
  )
}

const thClass = "text-left pb-3 text-xs font-semibold ct-pink-lt uppercase tracking-wide"

export default function FinanzasPage() {
  const [tab, setTab] = useState('insumos')
  const [mes, setMes] = useState(new Date().getMonth() + 1)
  const [anio, setAnio] = useState(new Date().getFullYear())
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [colaboradores, setColaboradores] = useState([])
  const [formPago, setFormPago] = useState({ colaborador_id: '', monto: '', periodo: '', notas: '' })
  const [guardandoPago, setGuardandoPago] = useState(false)
  const [editandoPago, setEditandoPago] = useState(null)
  const [editMonto, setEditMonto] = useState('')
  const [analisisIA, setAnalisisIA] = useState(null)
  const [cargandoIA, setCargandoIA] = useState(false)
  const [expandida, setExpandida] = useState(null)

  useEffect(() => { getColaboradores().then(setColaboradores).catch(() => {}) }, [])

  const cargarDatos = useCallback(() => {
    setLoading(true)
    setError(null)
    setData(null)

    const params = {}
    if (mes) params.mes = mes
    if (anio) params.anio = anio

    const fnMap = {
      insumos:        getReporteInsumos,
      ventas:         getReporteVentas,
      ganancia:       getReporteGanancia,
      pagos:          getPagosColaboradores,
      ventas_detalle: getVentasDetalle,
      dashboard:      getDashboard,
      marketing:      getMarketingFinanzas,
    }
    const fn = fnMap[tab]
    if (!fn) return

    fn(params)
      .then(res => { setData(res); setError(null) })
      .catch(err => {
        setError(err.response?.data?.detail || 'Error al cargar datos')
        setData(null)
      })
      .finally(() => setLoading(false))
  }, [tab, mes, anio])

  useEffect(() => { cargarDatos() }, [cargarDatos])

  const handleRegistrarPago = async (e) => {
    e.preventDefault()
    if (!formPago.colaborador_id) { toast.error('Selecciona un colaborador'); return }
    if (!formPago.monto || parseFloat(formPago.monto) <= 0) { toast.error('El monto debe ser mayor a 0'); return }
    setGuardandoPago(true)
    try {
      await registrarPago({
        colaborador_id: parseInt(formPago.colaborador_id),
        monto: parseFloat(formPago.monto),
        periodo: formPago.periodo || null,
        notas: formPago.notas || null,
      })
      toast.success('Pago registrado')
      setFormPago({ colaborador_id: '', monto: '', periodo: '', notas: '' })
      cargarDatos()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al registrar pago')
    } finally { setGuardandoPago(false) }
  }

  const handleEditarPago = async (pago) => {
    if (editandoPago?.id === pago.id) {
      // Guardar edición
      try {
        await actualizarPago(pago.id, { monto: parseFloat(editMonto) })
        toast.success('Monto actualizado')
        setEditandoPago(null)
        cargarDatos()
      } catch { toast.error('Error al actualizar') }
    } else {
      setEditandoPago(pago)
      setEditMonto(pago.monto.toString())
    }
  }

  const handleEliminarPago = async (id) => {
    if (!confirm('¿Eliminar este pago?')) return
    try { await eliminarPago(id); toast.success('Pago eliminado'); cargarDatos() }
    catch { toast.error('Error al eliminar') }
  }

  const handleAnalisisIA = async () => {
    setCargandoIA(true)
    try {
      const params = {}
      if (mes) params.mes = mes
      if (anio) params.anio = anio
      const res = await getResumenGroq(params)
      setAnalisisIA(res)
    } catch { toast.error('Error al obtener análisis IA') }
    finally { setCargandoIA(false) }
  }

  const pagosPorColaborador = useCallback(() => {
    if (!Array.isArray(data)) return {}
    const grupos = {}
    for (const p of data) {
      const nombre = p.colaborador_nombre || `#${p.colaborador_id}`
      if (!grupos[nombre]) grupos[nombre] = []
      grupos[nombre].push(p)
    }
    return grupos
  }, [data])

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{background:'linear-gradient(135deg,#ec4899,#be185d)'}}>
          <TrendingUp size={20} className="text-white"/>
        </div>
        <div>
          <h1 className="page-title">Finanzas</h1>
          <p className="page-subtitle">Reportes y control financiero</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-1 p-1 rounded-2xl w-fit" style={{background:'#fce7f3'}}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => { setTab(t.id); setAnalisisIA(null) }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              tab === t.id ? 'bg-white text-primary-600 shadow-sm' : 'ct-pink-lt hover:text-primary-500'
            }`}>
            <t.icon size={14}/> {t.label}
          </button>
        ))}
      </div>

      {/* Filtros */}
      <div className="flex items-center gap-3 flex-wrap">
        <span className="text-xs font-semibold uppercase tracking-wider ct-muted">Período:</span>
        <FiltroFecha mes={mes} anio={anio} setMes={setMes} setAnio={setAnio}/>
        {(tab === 'ventas' || tab === 'ganancia' || tab === 'ventas_detalle') && (
          <button onClick={handleAnalisisIA} disabled={cargandoIA}
            className="btn-secondary text-xs flex items-center gap-1.5 ml-2">
            <Brain size={13} className="text-primary-500"/>
            {cargandoIA ? 'Analizando...' : 'Análisis con IA'}
          </button>
        )}
      </div>

      {/* Análisis IA */}
      {analisisIA && (
        <div className="card animate-fadeIn" style={{background:'linear-gradient(135deg,#fdf2f8,#fce7f3)',border:'1px solid #fbcfe8'}}>
          <div className="flex items-center gap-2 mb-3">
            <Sparkles size={16} className="text-primary-500"/>
            <h3 className="text-sm font-bold ct-accent">Análisis IA — {analisisIA.mes}</h3>
          </div>
          <div className="grid grid-cols-3 gap-3 mb-3">
            <div><p className="text-[10px] ct-muted uppercase tracking-wide">Ventas</p><p className="font-bold ct-primary">{analisisIA.total_ventas}</p></div>
            <div><p className="text-[10px] ct-muted uppercase tracking-wide">Ingresos</p><p className="font-bold text-primary-600">S/ {analisisIA.ingresos?.toFixed(2)}</p></div>
            <div><p className="text-[10px] ct-muted uppercase tracking-wide">Top</p><p className="font-bold ct-primary text-xs">{analisisIA.producto_top}</p></div>
          </div>
          <p className="text-sm ct-secondary italic leading-relaxed">{analisisIA.analisis_ia}</p>
        </div>
      )}

      {/* Contenido */}
      {loading ? (
        <div className="flex justify-center py-12"><div className="spinner"/></div>
      ) : error ? (
        <div className="card text-center py-12">
          <p className="text-red-500 font-medium mb-2">{error}</p>
          <button onClick={cargarDatos} className="btn-secondary text-sm">Reintentar</button>
        </div>
      ) : (
        <>
          {/* INSUMOS */}
          {tab === 'insumos' && data && (
            <div className="space-y-4">
              <div className="card flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl flex items-center justify-center bg-rose-softer">
                  <Archive size={22} className="text-primary-500"/>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide ct-muted">Total valor en stock</p>
                  <p className="text-2xl font-bold ct-primary">S/ {parseFloat(data.total_gasto||0).toFixed(2)}</p>
                </div>
              </div>
              <div className="card overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-pink-100 dark:border-pink-900/20">
                    {['Insumo','Unidad','Stock','P. Unitario','Valor','Fecha'].map(h=><th key={h} className={thClass}>{h}</th>)}
                  </tr></thead>
                  <tbody className="divide-y divide-pink-50 dark:divide-pink-900/10">
                    {(data.insumos||[]).map(i=>(
                      <tr key={i.id} className="table-row-hover">
                        <td className="py-2.5 font-medium ct-primary">{i.nombre}</td>
                        <td className="py-2.5"><span className="badge badge-pink">{i.unidad}</span></td>
                        <td className="py-2.5 ct-secondary">{parseFloat(i.stock_actual).toFixed(2)}</td>
                        <td className="py-2.5 font-mono text-xs ct-secondary">S/ {parseFloat(i.precio_unitario).toFixed(4)}</td>
                        <td className="py-2.5 font-bold text-primary-600">S/ {parseFloat(i.total_valor).toFixed(2)}</td>
                        <td className="py-2.5 text-xs ct-muted">{i.fecha_ingreso?new Date(i.fecha_ingreso).toLocaleDateString('es-PE'):'—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!data.insumos?.length && <p className="text-center py-8 ct-muted text-sm">No hay insumos en este período</p>}
              </div>
            </div>
          )}

          {/* VENTAS */}
          {tab === 'ventas' && data && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[
                  {label:'Ingresos pagados',val:`S/ ${parseFloat(data.total_ingresos||0).toFixed(2)}`,icon:DollarSign,color:'#16a34a',bg:'#d1fae5'},
                  {label:'Número de ventas',val:data.num_ventas||0,icon:ShoppingBag,color:'#1d4ed8',bg:'#dbeafe'},
                ].map(({label,val,icon:Icon,color,bg})=>(
                  <div key={label} className="card flex items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl flex items-center justify-center shrink-0" style={{background:bg}}>
                      <Icon size={22} style={{color}}/>
                    </div>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide ct-muted">{label}</p>
                      <p className="text-2xl font-bold ct-primary">{val}</p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="card overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-pink-100 dark:border-pink-900/20">
                    {['Fecha','Cliente','Total','Pago','Estado'].map(h=><th key={h} className={thClass}>{h}</th>)}
                  </tr></thead>
                  <tbody className="divide-y divide-pink-50 dark:divide-pink-900/10">
                    {(data.ventas||[]).map(v=>(
                      <tr key={v.id} className="table-row-hover">
                        <td className="py-2.5 text-xs ct-muted">{v.fecha_hora?new Date(v.fecha_hora).toLocaleString('es-PE'):'-'}</td>
                        <td className="py-2.5 font-medium ct-primary">{v.cliente}</td>
                        <td className="py-2.5 font-bold text-primary-600">S/ {parseFloat(v.total).toFixed(2)}</td>
                        <td className="py-2.5"><span className={v.estado_pago==='pagado'?'badge badge-green':'badge badge-yellow'}>{v.estado_pago}</span></td>
                        <td className="py-2.5"><span className={v.estado_venta==='completada'?'badge badge-blue':'badge badge-orange'}>{v.estado_venta}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!data.ventas?.length && <p className="text-center py-8 ct-muted text-sm">No hay ventas en este período</p>}
              </div>
            </div>
          )}

          {/* GANANCIA */}
          {tab === 'ganancia' && data && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[
                {label:'Ingresos totales',val:data.ingresos_totales,color:'#16a34a',bg:'#d1fae5'},
                {label:'Gasto en insumos',val:data.gasto_insumos,color:'#dc2626',bg:'#fee2e2'},
                {label:'Ganancia estimada',val:data.ganancia_estimada,color:parseFloat(data.ganancia_estimada||0)>=0?'#15803d':'#dc2626',bg:parseFloat(data.ganancia_estimada||0)>=0?'#dcfce7':'#fee2e2'},
              ].map(({label,val,color,bg})=>(
                <div key={label} className="card text-center" style={{background:bg,borderColor:'transparent'}}>
                  <p className="text-xs font-semibold uppercase tracking-wide mb-2" style={{color,opacity:0.75}}>{label}</p>
                  <p className="text-3xl font-bold" style={{color}}>S/ {parseFloat(val||0).toFixed(2)}</p>
                </div>
              ))}
            </div>
          )}

          {/* DASHBOARD */}
          {tab === 'dashboard' && data && (
            <div className="space-y-5">
              {/* KPIs */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {[
                  { label: 'Total ventas', val: data.totales?.num_ventas, icon: ShoppingBag, color: 'text-blue-500' },
                  { label: 'Ingresos', val: `S/ ${parseFloat(data.totales?.ingresos||0).toFixed(2)}`, icon: DollarSign, color: 'text-green-500' },
                  { label: 'Ticket promedio', val: `S/ ${parseFloat(data.totales?.ticket_promedio||0).toFixed(2)}`, icon: TrendingUp, color: 'text-primary-500' },
                ].map(c => (
                  <div key={c.label} className="card py-3">
                    <div className="flex items-center gap-2 mb-1"><c.icon size={14} className={c.color}/><p className="text-xs ct-muted">{c.label}</p></div>
                    <p className="text-xl font-bold ct-primary">{c.val}</p>
                  </div>
                ))}
              </div>

              {/* Ventas por día de la semana */}
              <div className="card">
                <h3 className="text-sm font-bold ct-accent mb-4">Ventas por día de la semana</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={data.por_dia_semana}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#fce7f3"/>
                    <XAxis dataKey="dia" tick={{fontSize:12}} />
                    <YAxis tick={{fontSize:12}}/>
                    <Tooltip formatter={(v, n) => [n === 'ventas' ? v : `S/ ${v}`, n === 'ventas' ? 'Ventas' : 'Ingresos']}/>
                    <Bar dataKey="ventas" fill="#ec4899" radius={[4,4,0,0]} name="ventas"/>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                {/* Top productos */}
                <div className="card">
                  <h3 className="text-sm font-bold ct-accent mb-4">Productos más vendidos</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={data.top_productos} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#fce7f3"/>
                      <XAxis type="number" tick={{fontSize:11}}/>
                      <YAxis dataKey="nombre" type="category" width={100} tick={{fontSize:10}}/>
                      <Tooltip/>
                      <Bar dataKey="cantidad" fill="#be185d" radius={[0,4,4,0]}/>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Métodos de pago */}
                <div className="card">
                  <h3 className="text-sm font-bold ct-accent mb-4">Métodos de pago</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie data={data.por_metodo_pago} dataKey="cantidad" nameKey="metodo" cx="50%" cy="50%" outerRadius={70} label={({metodo,percent})=>`${metodo} ${(percent*100).toFixed(0)}%`}>
                        {(data.por_metodo_pago||[]).map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]}/>)}
                      </Pie>
                      <Tooltip/>
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Ventas por hora */}
              <div className="card">
                <h3 className="text-sm font-bold ct-accent mb-4">Ventas por hora del día</h3>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={data.por_hora}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#fce7f3"/>
                    <XAxis dataKey="hora" tick={{fontSize:11}}/>
                    <YAxis tick={{fontSize:11}}/>
                    <Tooltip/>
                    <Bar dataKey="ventas" fill="#f9a8d4" radius={[4,4,0,0]}/>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Fuente marketing */}
              {data.por_fuente_marketing?.length > 0 && (
                <div className="card">
                  <h3 className="text-sm font-bold ct-accent mb-4">Ventas por fuente de marketing</h3>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={data.por_fuente_marketing}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#fce7f3"/>
                      <XAxis dataKey="fuente" tick={{fontSize:12}}/>
                      <YAxis tick={{fontSize:12}}/>
                      <Tooltip/>
                      <Bar dataKey="cantidad" fill="#9d174d" radius={[4,4,0,0]}/>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}

          {/* VENTAS CON GANANCIA */}
          {tab === 'ventas_detalle' && data && (
            <div className="space-y-4">
              {/* Resumen */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: 'Ventas', val: data.resumen?.num_ventas, color: 'text-blue-500' },
                  { label: 'Ingresos', val: `S/ ${parseFloat(data.resumen?.total_ingresos||0).toFixed(2)}`, color: 'text-green-600' },
                  { label: 'Ganancia estimada', val: `S/ ${parseFloat(data.resumen?.ganancia_total||0).toFixed(2)}`, color: 'text-primary-600' },
                  { label: 'Margen promedio', val: `${data.resumen?.margen_promedio||0}%`, color: parseFloat(data.resumen?.margen_promedio||0) >= 30 ? 'text-green-600' : 'text-amber-500' },
                ].map(c => (
                  <div key={c.label} className="card py-3">
                    <p className="text-xs ct-muted mb-1">{c.label}</p>
                    <p className={`text-lg font-bold ${c.color}`}>{c.val}</p>
                  </div>
                ))}
              </div>

              <div className="card overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-pink-100 dark:border-pink-900/20">
                      {['', 'Fecha', 'Cliente', 'Fuente', 'Total', 'Costo', 'Ganancia', 'Margen', 'Estado'].map(h => (
                        <th key={h} className={thClass}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(data.ventas||[]).map(v => (
                      <>
                        <tr key={v.id} className="border-b border-pink-50 dark:border-pink-900/10 hover:bg-rose-softer/50 cursor-pointer transition-colors"
                          onClick={() => setExpandida(expandida === v.id ? null : v.id)}>
                          <td className="py-2.5 pl-2">
                            {expandida === v.id ? <ChevronDown size={14} className="text-primary-400"/> : <ChevronRight size={14} className="ct-muted"/>}
                          </td>
                          <td className="py-2.5 text-xs ct-muted">{v.fecha_hora ? new Date(v.fecha_hora).toLocaleDateString('es-PE') : '—'}</td>
                          <td className="py-2.5 font-medium ct-primary">{v.cliente}</td>
                          <td className="py-2.5">
                            {v.fuente_marketing
                              ? <span className="badge badge-pink text-xs">{v.fuente_marketing}</span>
                              : <span className="text-xs ct-muted">orgánico</span>}
                          </td>
                          <td className="py-2.5 font-bold text-green-600">S/ {v.total_venta.toFixed(2)}</td>
                          <td className="py-2.5 ct-secondary">S/ {v.costo_estimado.toFixed(2)}</td>
                          <td className="py-2.5 font-bold text-primary-600">S/ {v.ganancia_estimada.toFixed(2)}</td>
                          <td className="py-2.5">
                            <span className={`badge ${v.margen_pct >= 30 ? 'badge-green' : v.margen_pct >= 15 ? 'badge-yellow' : 'badge-red'}`}>
                              {v.margen_pct}%
                            </span>
                          </td>
                          <td className="py-2.5">
                            <span className={v.estado_pago === 'pagado' ? 'badge badge-green' : 'badge badge-yellow'}>{v.estado_pago}</span>
                          </td>
                        </tr>
                        {expandida === v.id && (
                          <tr key={`exp-${v.id}`} className="bg-rose-softer">
                            <td colSpan={9} className="px-6 py-3">
                              <p className="text-xs font-bold ct-accent mb-2">Detalle por producto:</p>
                              <table className="w-full text-xs">
                                <thead>
                                  <tr className="border-b border-pink-100">
                                    {['Producto','Tipo','Cant.','P. Venta','Costo','Ganancia','Margen'].map(h => (
                                      <th key={h} className="text-left py-1 text-[10px] font-semibold ct-muted uppercase tracking-wide pr-4">{h}</th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {v.items.map((item, idx) => (
                                    <tr key={idx} className="border-b border-pink-50">
                                      <td className="py-1.5 font-medium ct-primary pr-4">{item.nombre}</td>
                                      <td className="py-1.5 ct-muted pr-4">{item.tipo}</td>
                                      <td className="py-1.5 ct-secondary pr-4">{item.cantidad}</td>
                                      <td className="py-1.5 ct-secondary pr-4">S/ {item.precio_venta_unit.toFixed(2)}</td>
                                      <td className="py-1.5 ct-muted pr-4">{item.costo_unit > 0 ? `S/ ${item.costo_unit.toFixed(2)}` : '—'}</td>
                                      <td className="py-1.5 font-semibold text-primary-600 pr-4">S/ {item.ganancia.toFixed(2)}</td>
                                      <td className="py-1.5">
                                        {item.costo_unit > 0
                                          ? <span className={`badge text-[10px] ${item.margen_pct >= 30 ? 'badge-green' : item.margen_pct >= 15 ? 'badge-yellow' : 'badge-red'}`}>{item.margen_pct}%</span>
                                          : <span className="ct-muted">sin costo</span>}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </td>
                          </tr>
                        )}
                      </>
                    ))}
                  </tbody>
                </table>
                {!data.ventas?.length && <p className="text-center py-8 ct-muted text-sm">No hay ventas en este período</p>}
              </div>
            </div>
          )}

          {/* MARKETING (datos desde página Marketing) */}
          {tab === 'marketing' && data && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="card py-3">
                  <p className="text-xs ct-muted mb-1">Total invertido</p>
                  <p className="text-xl font-bold text-rose-500">S/ {parseFloat(data.total_invertido||0).toFixed(2)}</p>
                </div>
                <div className="card py-3">
                  <p className="text-xs ct-muted mb-1">Registros</p>
                  <p className="text-xl font-bold ct-primary">{data.num_gastos}</p>
                </div>
              </div>
              <div className="card overflow-x-auto">
                <p className="text-xs ct-muted mb-3">Los gastos se registran desde la página <strong>Marketing → Inversión publicitaria</strong></p>
                <table className="w-full text-sm">
                  <thead><tr className="border-b border-pink-100 dark:border-pink-900/20">
                    {['Red social','Monto','Contactos','Compradores','Período','Descripción'].map(h=><th key={h} className={thClass}>{h}</th>)}
                  </tr></thead>
                  <tbody className="divide-y divide-pink-50 dark:divide-pink-900/10">
                    {(data.gastos||[]).map(g => (
                      <tr key={g.id} className="table-row-hover">
                        <td className="py-2.5 font-medium ct-primary capitalize">{g.red_social.replace('_',' ')}</td>
                        <td className="py-2.5 font-bold text-rose-500">S/ {parseFloat(g.monto).toFixed(2)}</td>
                        <td className="py-2.5 ct-secondary">{g.num_contactos}</td>
                        <td className="py-2.5 ct-secondary">{g.num_compradores}</td>
                        <td className="py-2.5 text-xs ct-muted">{g.periodo||'—'}</td>
                        <td className="py-2.5 text-xs ct-muted">{g.descripcion||'—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!data.gastos?.length && <p className="text-center py-8 ct-muted text-sm">No hay gastos de marketing en este período</p>}
              </div>
            </div>
          )}

          {/* PAGOS COLABORADORES */}
          {tab === 'pagos' && (
            <div className="space-y-5">
              {/* Formulario registrar */}
              <div className="card">
                <h3 className="text-base font-bold mb-4 ct-accent">Registrar pago</h3>
                <form onSubmit={handleRegistrarPago} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="label">Colaborador *</label>
                    <select className="input-field" value={formPago.colaborador_id} onChange={e=>setFormPago(f=>({...f,colaborador_id:e.target.value}))} required>
                      <option value="">— Seleccionar —</option>
                      {colaboradores.map(c=><option key={c.id} value={c.id}>{c.nombres} {c.apellidos}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="label">Monto (S/) *</label>
                    <input type="number" min="0.01" step="0.01" className="input-field" value={formPago.monto}
                      onChange={e=>setFormPago(f=>({...f,monto:e.target.value}))} required placeholder="0.00"/>
                  </div>
                  <div>
                    <label className="label">Período (mes)</label>
                    <input className="input-field" value={formPago.periodo}
                      onChange={e=>setFormPago(f=>({...f,periodo:e.target.value}))} placeholder="Ej: Junio 2025"/>
                  </div>
                  <div>
                    <label className="label">Notas</label>
                    <input className="input-field" value={formPago.notas}
                      onChange={e=>setFormPago(f=>({...f,notas:e.target.value}))} placeholder="Observaciones..."/>
                  </div>
                  <div className="sm:col-span-2 flex justify-end">
                    <button type="submit" disabled={guardandoPago} className="btn-primary">
                      <Plus size={15}/> {guardandoPago?'Guardando...':'Registrar pago'}
                    </button>
                  </div>
                </form>
              </div>

              {/* Historial agrupado por colaborador */}
              <div className="card">
                <h3 className="text-base font-bold mb-4 ct-accent">Historial de pagos</h3>

                {!Array.isArray(data) || data.length === 0 ? (
                  <div className="text-center py-10">
                    <Users size={36} className="mx-auto mb-2 ct-pink-lt"/>
                    <p className="text-sm ct-muted">No hay pagos en este período</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {Object.entries(pagosPorColaborador()).map(([nombre, pagos]) => (
                      <div key={nombre}>
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="w-7 h-7 rounded-xl flex items-center justify-center text-xs font-bold text-white"
                                 style={{background:'linear-gradient(135deg,#f9a8d4,#be185d)'}}>
                              {nombre.charAt(0)}
                            </div>
                            <p className="text-sm font-bold ct-primary">{nombre}</p>
                          </div>
                          <p className="text-xs ct-muted">
                            Total: <span className="font-bold text-primary-600">
                              S/ {pagos.reduce((a,p)=>a+p.monto,0).toFixed(2)}
                            </span>
                          </p>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead><tr className="border-b border-pink-100 dark:border-pink-900/20">
                              {['Monto','Período','Fecha','Notas',''].map(h=><th key={h} className={thClass}>{h}</th>)}
                            </tr></thead>
                            <tbody className="divide-y divide-pink-50 dark:divide-pink-900/10">
                              {pagos.map(p=>(
                                <tr key={p.id} className="table-row-hover">
                                  <td className="py-2.5">
                                    {editandoPago?.id === p.id ? (
                                      <div className="flex items-center gap-2">
                                        <span className="ct-secondary text-xs">S/</span>
                                        <input type="number" step="0.01" min="0.01"
                                          className="input-field w-28 py-1 text-sm font-bold"
                                          value={editMonto} onChange={e=>setEditMonto(e.target.value)}
                                          autoFocus onKeyDown={e=>e.key==='Escape'&&setEditandoPago(null)}/>
                                      </div>
                                    ) : (
                                      <span className="font-bold text-primary-600">S/ {parseFloat(p.monto).toFixed(2)}</span>
                                    )}
                                  </td>
                                  <td className="py-2.5 ct-secondary">{p.periodo||'—'}</td>
                                  <td className="py-2.5 text-xs ct-muted">{p.fecha?new Date(p.fecha).toLocaleDateString('es-PE'):'—'}</td>
                                  <td className="py-2.5 text-xs ct-muted">{p.notas||'—'}</td>
                                  <td className="py-2.5">
                                    <div className="flex gap-1">
                                      <button onClick={()=>handleEditarPago(p)}
                                        className={`w-7 h-7 rounded-lg flex items-center justify-center transition-colors ${editandoPago?.id===p.id?'text-green-500 hover:bg-green-50':'text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-950/30'}`}
                                        title={editandoPago?.id===p.id?'Guardar':'Editar monto'}>
                                        {editandoPago?.id===p.id?<Check size={14}/>:<Edit size={14}/>}
                                      </button>
                                      {editandoPago?.id===p.id&&(
                                        <button onClick={()=>setEditandoPago(null)}
                                          className="w-7 h-7 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-50 transition-colors">
                                          <X size={14}/>
                                        </button>
                                      )}
                                      <button onClick={()=>handleEliminarPago(p.id)}
                                        className="w-7 h-7 rounded-lg flex items-center justify-center text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors">
                                        <X size={14}/>
                                      </button>
                                    </div>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
