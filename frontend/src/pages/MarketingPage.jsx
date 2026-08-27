import { useState, useEffect } from 'react'
import {
  Megaphone, DollarSign, MessageCircle, Plus, Trash2, Edit, Check, X,
  RefreshCw, Copy, Sparkles, TrendingUp, Users, ShoppingBag, Palette,
  BarChart3
} from 'lucide-react'
import { FaFacebookF, FaInstagram, FaTiktok, FaWhatsapp, FaGoogle, FaBullhorn } from 'react-icons/fa6'
import { getGastos, crearGasto, actualizarGasto, eliminarGasto, getMensajesWhatsapp, getPromptsCanva, getEstadisticas } from '../api/marketing'
import toast from 'react-hot-toast'

const REDES = [
  { value: 'facebook',   label: 'Facebook',   Icon: FaFacebookF, bg: '#1877F2' },
  { value: 'instagram',  label: 'Instagram',  Icon: FaInstagram, bg: 'linear-gradient(45deg,#feda75,#fa7e1e,#d62976,#962fbf,#4f5bd5)' },
  { value: 'tiktok',     label: 'TikTok',     Icon: FaTiktok,    bg: '#010101' },
  { value: 'whatsapp',   label: 'WhatsApp',   Icon: FaWhatsapp,  bg: '#25D366' },
  { value: 'google_ads', label: 'Google Ads', Icon: FaGoogle,    bg: '#4285F4' },
  { value: 'otro',       label: 'Otro',       Icon: FaBullhorn,  bg: '#6B7280' },
]

// Chip con el logo real de la red social (blanco sobre color de marca)
function RedChip({ red, size = 12 }) {
  const r = typeof red === 'string' ? redInfo(red) : red
  const Icon = r.Icon
  return (
    <span
      className="inline-flex items-center justify-center w-6 h-6 rounded-lg shrink-0 shadow-sm"
      style={{ background: r.bg }}
    >
      <Icon size={size} color="#ffffff" />
    </span>
  )
}

const TABS = [
  { id: 'inversion', label: 'Inversión publicitaria', icon: DollarSign },
  { id: 'origen', label: 'Origen de ventas', icon: BarChart3 },
  { id: 'mensajes', label: 'Mensajes WhatsApp', icon: MessageCircle },
]

const redInfo = (red) => REDES.find(r => r.value === red) || REDES[5]

const MESES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
const ANIOS = Array.from({length: 4}, (_, i) => new Date().getFullYear() - i)

export default function MarketingPage() {
  const [tab, setTab] = useState('inversion')
  const [mes, setMes] = useState(new Date().getMonth() + 1)
  const [anio, setAnio] = useState(new Date().getFullYear())

  // Inversión
  const [gastos, setGastos] = useState([])
  const [resumen, setResumen] = useState(null)
  const [loadingGastos, setLoadingGastos] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [editando, setEditando] = useState(null)
  const [form, setForm] = useState({ red_social: 'facebook', monto: '', descripcion: '', num_contactos: '', num_compradores: '', periodo: '' })

  // Origen de ventas (fuente de marketing real registrada en cada venta)
  const [estadisticas, setEstadisticas] = useState([])
  const [loadingEstad, setLoadingEstad] = useState(false)

  // Mensajes
  const [mensajes, setMensajes] = useState([])
  const [loadingMensajes, setLoadingMensajes] = useState(false)
  const [copiadoIdx, setCopiadoIdx] = useState(null)

  // Prompts publicitarios (generados por IA a medida)
  const [prompts, setPrompts] = useState([])
  const [loadingPrompts, setLoadingPrompts] = useState(false)
  const [peticionPrompt, setPeticionPrompt] = useState('')
  const [plataformaPrompt, setPlataformaPrompt] = useState('')

  const cargarGastos = async () => {
    setLoadingGastos(true)
    try {
      const res = await getGastos({ mes, anio })
      setGastos(res.gastos)
      setResumen(res.resumen)
    } catch { toast.error('Error al cargar gastos') }
    finally { setLoadingGastos(false) }
  }

  const cargarEstadisticas = async () => {
    setLoadingEstad(true)
    try {
      const res = await getEstadisticas({ mes, anio })
      setEstadisticas(res.por_fuente || [])
    } catch { toast.error('Error al cargar el origen de ventas') }
    finally { setLoadingEstad(false) }
  }

  const cargarMensajes = async () => {
    setLoadingMensajes(true)
    try {
      const msgRes = await getMensajesWhatsapp()
      setMensajes(msgRes.mensajes || [])
    } catch { toast.error('Error al cargar mensajes') }
    finally { setLoadingMensajes(false) }
  }

  const generarPrompts = async () => {
    setLoadingPrompts(true)
    try {
      const res = await getPromptsCanva({
        peticion: peticionPrompt.trim() || undefined,
        plataforma: plataformaPrompt || undefined,
      })
      setPrompts(res.prompts || [])
    } catch { toast.error('Error al generar prompts') }
    finally { setLoadingPrompts(false) }
  }

  useEffect(() => {
    if (tab === 'inversion') cargarGastos()
    else if (tab === 'origen') cargarEstadisticas()
    else if (tab === 'mensajes') {
      if (mensajes.length === 0) cargarMensajes()
      if (prompts.length === 0) generarPrompts()
    }
  }, [tab, mes, anio])

  const handleGuardar = async () => {
    if (!form.monto || isNaN(parseFloat(form.monto))) {
      toast.error('El monto es requerido')
      return
    }
    try {
      const payload = {
        red_social: form.red_social,
        monto: parseFloat(form.monto),
        descripcion: form.descripcion || null,
        num_contactos: parseInt(form.num_contactos) || 0,
        num_compradores: parseInt(form.num_compradores) || 0,
        periodo: form.periodo || null,
      }
      if (editando) {
        await actualizarGasto(editando.id, payload)
        toast.success('Gasto actualizado')
      } else {
        await crearGasto(payload)
        toast.success('Gasto registrado')
      }
      setShowForm(false)
      setEditando(null)
      setForm({ red_social: 'facebook', monto: '', descripcion: '', num_contactos: '', num_compradores: '', periodo: '' })
      cargarGastos()
    } catch { toast.error('Error al guardar') }
  }

  const handleEditar = (g) => {
    setEditando(g)
    setForm({
      red_social: g.red_social,
      monto: String(g.monto),
      descripcion: g.descripcion || '',
      num_contactos: String(g.num_contactos),
      num_compradores: String(g.num_compradores),
      periodo: g.periodo || '',
    })
    setShowForm(true)
  }

  const handleEliminar = async (id) => {
    if (!confirm('¿Eliminar este gasto?')) return
    try {
      await eliminarGasto(id)
      toast.success('Gasto eliminado')
      cargarGastos()
    } catch { toast.error('Error al eliminar') }
  }

  const copiarMensaje = (texto, idx) => {
    navigator.clipboard.writeText(texto)
    setCopiadoIdx(idx)
    toast.success('¡Mensaje copiado!')
    setTimeout(() => setCopiadoIdx(null), 2000)
  }

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{background:'linear-gradient(135deg,#ec4899,#be185d)'}}>
          <Megaphone size={20} className="text-white"/>
        </div>
        <div>
          <h1 className="page-title">Marketing</h1>
          <p className="page-subtitle">Inversión publicitaria y mensajes para clientes</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 rounded-2xl bg-rose-softer w-fit">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              tab === t.id
                ? 'bg-white dark:bg-[#1a1520] shadow-rose text-primary-700 dark:text-primary-300'
                : 'ct-muted hover:ct-primary'
            }`}
          >
            <t.icon size={15}/>
            {t.label}
          </button>
        ))}
      </div>

      {/* TAB: INVERSIÓN */}
      {tab === 'inversion' && (
        <div className="space-y-4">
          {/* Filtros + botón */}
          <div className="flex flex-wrap items-center gap-3 justify-between">
            <div className="flex gap-2">
              <select className="input-field w-32 text-sm" value={mes} onChange={e => setMes(parseInt(e.target.value))}>
                {MESES.map((m, i) => <option key={i} value={i+1}>{m}</option>)}
              </select>
              <select className="input-field w-28 text-sm" value={anio} onChange={e => setAnio(parseInt(e.target.value))}>
                {ANIOS.map(a => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>
            <button onClick={() => { setShowForm(true); setEditando(null) }} className="btn-primary flex items-center gap-2">
              <Plus size={15}/> Registrar gasto
            </button>
          </div>

          {/* Resumen tarjetas */}
          {resumen && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: 'Total invertido', value: `S/ ${resumen.total_invertido?.toFixed(2)}`, icon: DollarSign, color: 'text-rose-500' },
                { label: 'Contactos totales', value: resumen.total_contactos, icon: Users, color: 'text-blue-500' },
                { label: 'Compradores', value: resumen.total_compradores, icon: ShoppingBag, color: 'text-green-500' },
                { label: 'Tasa conversión', value: resumen.tasa_conversion_global ? `${resumen.tasa_conversion_global}%` : '—', icon: TrendingUp, color: 'text-purple-500' },
              ].map(c => (
                <div key={c.label} className="card py-3 px-4">
                  <div className="flex items-center gap-2 mb-1">
                    <c.icon size={14} className={c.color}/>
                    <p className="text-xs ct-muted">{c.label}</p>
                  </div>
                  <p className="text-xl font-bold ct-primary">{c.value}</p>
                </div>
              ))}
            </div>
          )}

          {/* Formulario */}
          {showForm && (
            <div className="card border-primary-200 dark:border-primary-800">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold ct-accent">{editando ? 'Editar gasto' : 'Nuevo gasto publicitario'}</h3>
                <button onClick={() => { setShowForm(false); setEditando(null) }} className="ct-muted hover:ct-primary">
                  <X size={18}/>
                </button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="label-field">Red social</label>
                  <select className="input-field" value={form.red_social} onChange={e => setForm(f => ({...f, red_social: e.target.value}))}>
                    {REDES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="label-field">Monto (S/)</label>
                  <input type="number" step="0.01" className="input-field" placeholder="0.00" value={form.monto} onChange={e => setForm(f => ({...f, monto: e.target.value}))}/>
                </div>
                <div>
                  <label className="label-field">Período (ej: Junio 2026)</label>
                  <input type="text" className="input-field" placeholder="Junio 2026" value={form.periodo} onChange={e => setForm(f => ({...f, periodo: e.target.value}))}/>
                </div>
                <div>
                  <label className="label-field">Personas que escribieron</label>
                  <input type="number" className="input-field" placeholder="0" value={form.num_contactos} onChange={e => setForm(f => ({...f, num_contactos: e.target.value}))}/>
                </div>
                <div>
                  <label className="label-field">Personas que compraron</label>
                  <input type="number" className="input-field" placeholder="0" value={form.num_compradores} onChange={e => setForm(f => ({...f, num_compradores: e.target.value}))}/>
                </div>
                <div>
                  <label className="label-field">Descripción (opcional)</label>
                  <input type="text" className="input-field" placeholder="Campaña de verano..." value={form.descripcion} onChange={e => setForm(f => ({...f, descripcion: e.target.value}))}/>
                </div>
              </div>
              <div className="flex gap-2 mt-4">
                <button onClick={handleGuardar} className="btn-primary flex items-center gap-2">
                  <Check size={15}/> {editando ? 'Actualizar' : 'Guardar'}
                </button>
                <button onClick={() => { setShowForm(false); setEditando(null) }} className="btn-secondary">Cancelar</button>
              </div>
            </div>
          )}

          {/* Tabla de gastos */}
          <div className="card">
            {loadingGastos ? (
              <div className="flex items-center gap-2 py-6 justify-center">
                <RefreshCw size={16} className="animate-spin text-primary-400"/>
                <span className="text-sm ct-muted">Cargando...</span>
              </div>
            ) : gastos.length === 0 ? (
              <div className="text-center py-10">
                <DollarSign size={36} className="mx-auto mb-2 text-primary-200"/>
                <p className="text-sm ct-muted">No hay gastos registrados para este período</p>
                <button onClick={() => setShowForm(true)} className="btn-primary mt-4 text-sm flex items-center gap-2 mx-auto">
                  <Plus size={14}/> Registrar primer gasto
                </button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-pink-100 dark:border-pink-900/20">
                      <th className="text-left pb-3 text-xs font-semibold ct-pink-lt uppercase tracking-wide">Red social</th>
                      <th className="text-left pb-3 text-xs font-semibold ct-pink-lt uppercase tracking-wide">Monto</th>
                      <th className="text-left pb-3 text-xs font-semibold ct-pink-lt uppercase tracking-wide">Contactos</th>
                      <th className="text-left pb-3 text-xs font-semibold ct-pink-lt uppercase tracking-wide">Compraron</th>
                      <th className="text-left pb-3 text-xs font-semibold ct-pink-lt uppercase tracking-wide">Conversión</th>
                      <th className="text-left pb-3 text-xs font-semibold ct-pink-lt uppercase tracking-wide">Costo/comprador</th>
                      <th className="text-left pb-3 text-xs font-semibold ct-pink-lt uppercase tracking-wide">Período</th>
                      <th className="pb-3"/>
                    </tr>
                  </thead>
                  <tbody>
                    {gastos.map(g => {
                      const red = redInfo(g.red_social)
                      return (
                        <tr key={g.id} className="border-b border-pink-50 dark:border-pink-900/10 hover:bg-rose-softer/50 transition-colors">
                          <td className="py-3">
                            <span className="flex items-center gap-2">
                              <RedChip red={red} />
                              <span className="font-medium ct-primary">{red.label}</span>
                            </span>
                          </td>
                          <td className="py-3 font-bold text-primary-600">S/ {g.monto.toFixed(2)}</td>
                          <td className="py-3 ct-secondary">{g.num_contactos}</td>
                          <td className="py-3 ct-secondary">{g.num_compradores}</td>
                          <td className="py-3">
                            {g.tasa_conversion != null
                              ? <span className={`badge ${g.tasa_conversion >= 10 ? 'badge-green' : g.tasa_conversion >= 5 ? 'badge-yellow' : 'badge-red'}`}>{g.tasa_conversion}%</span>
                              : <span className="ct-muted text-xs">—</span>}
                          </td>
                          <td className="py-3 ct-secondary">{g.costo_por_comprador ? `S/ ${g.costo_por_comprador}` : '—'}</td>
                          <td className="py-3 ct-muted text-xs">{g.periodo || '—'}</td>
                          <td className="py-3">
                            <div className="flex gap-1">
                              <button onClick={() => handleEditar(g)} className="p-1.5 rounded-lg hover:bg-primary-50 dark:hover:bg-white/5 ct-muted hover:text-primary-600 transition-colors">
                                <Edit size={14}/>
                              </button>
                              <button onClick={() => handleEliminar(g.id)} className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-950/30 ct-muted hover:text-red-500 transition-colors">
                                <Trash2 size={14}/>
                              </button>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB: ORIGEN DE VENTAS */}
      {tab === 'origen' && (
        <div className="space-y-4">
          {/* Filtros */}
          <div className="flex flex-wrap items-center gap-3 justify-between">
            <div className="flex gap-2">
              <select className="input-field w-32 text-sm" value={mes} onChange={e => setMes(parseInt(e.target.value))}>
                {MESES.map((m, i) => <option key={i} value={i+1}>{m}</option>)}
              </select>
              <select className="input-field w-28 text-sm" value={anio} onChange={e => setAnio(parseInt(e.target.value))}>
                {ANIOS.map(a => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>
            <button onClick={cargarEstadisticas} disabled={loadingEstad} className="btn-secondary text-sm flex items-center gap-2">
              <RefreshCw size={14} className={loadingEstad ? 'animate-spin' : ''}/> Actualizar
            </button>
          </div>

          <p className="text-xs ct-muted">
            Ventas reales agrupadas por el canal donde te escribió el cliente (campo <strong>"¿Por dónde nos escribió?"</strong> al registrar cada venta). Se actualiza automáticamente con cada venta.
          </p>

          <div className="card">
            {loadingEstad ? (
              <div className="flex items-center gap-2 py-6 justify-center">
                <RefreshCw size={16} className="animate-spin text-primary-400"/>
                <span className="text-sm ct-muted">Cargando...</span>
              </div>
            ) : estadisticas.length === 0 ? (
              <div className="text-center py-10">
                <BarChart3 size={36} className="mx-auto mb-2 text-primary-200"/>
                <p className="text-sm ct-muted">Aún no hay ventas con origen registrado en este período</p>
                <p className="text-xs ct-muted mt-1">Al registrar una venta y elegir por dónde te escribió el cliente, aparecerá aquí.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-pink-100 dark:border-pink-900/20">
                      <th className="text-left pb-3 text-xs font-semibold ct-pink-lt uppercase tracking-wide">Canal</th>
                      <th className="text-left pb-3 text-xs font-semibold ct-pink-lt uppercase tracking-wide">Ventas</th>
                      <th className="text-left pb-3 text-xs font-semibold ct-pink-lt uppercase tracking-wide">Ingresos</th>
                      <th className="text-left pb-3 text-xs font-semibold ct-pink-lt uppercase tracking-wide">Inversión</th>
                      <th className="text-left pb-3 text-xs font-semibold ct-pink-lt uppercase tracking-wide">ROI</th>
                    </tr>
                  </thead>
                  <tbody>
                    {estadisticas.map(s => {
                      const red = redInfo(s.fuente)
                      return (
                        <tr key={s.fuente} className="border-b border-pink-50 dark:border-pink-900/10 hover:bg-rose-softer/50 transition-colors">
                          <td className="py-3">
                            <span className="flex items-center gap-2">
                              <RedChip red={red} />
                              <span className="font-medium ct-primary">{red.label}</span>
                            </span>
                          </td>
                          <td className="py-3"><span className="badge badge-pink">{s.num_ventas}</span></td>
                          <td className="py-3 font-bold text-primary-600">S/ {s.total_ingresos.toFixed(2)}</td>
                          <td className="py-3 ct-secondary">{s.total_gasto ? `S/ ${s.total_gasto.toFixed(2)}` : '—'}</td>
                          <td className="py-3">
                            {s.roi != null
                              ? <span className={`badge ${s.roi >= 0 ? 'badge-green' : 'badge-red'}`}>{s.roi > 0 ? '+' : ''}{s.roi}%</span>
                              : <span className="ct-muted text-xs">—</span>}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB: MENSAJES WHATSAPP */}
      {tab === 'mensajes' && (
        <div className="space-y-5">
          {/* Mensajes IA */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Sparkles size={18} className="text-primary-400"/>
                <h3 className="font-bold ct-accent">Mensajes generados por IA</h3>
                <span className="badge badge-pink text-xs">Groq IA</span>
              </div>
              <button
                onClick={cargarMensajes}
                disabled={loadingMensajes}
                className="btn-secondary text-sm flex items-center gap-2"
              >
                <RefreshCw size={14} className={loadingMensajes ? 'animate-spin' : ''}/>
                {loadingMensajes ? 'Generando...' : 'Generar nuevos'}
              </button>
            </div>
            <p className="text-xs ct-muted mb-4">
              Mensajes humanizados y coloquiales listos para copiar y enviar por WhatsApp. Se generan en base a tus productos, packs y promociones actuales.
            </p>

            {loadingMensajes ? (
              <div className="flex items-center justify-center gap-2 py-12">
                <Sparkles size={20} className="animate-pulse text-primary-400"/>
                <p className="text-sm ct-muted">La IA está redactando mensajes personalizados...</p>
              </div>
            ) : mensajes.length === 0 ? (
              <div className="text-center py-10">
                <MessageCircle size={36} className="mx-auto mb-2 text-primary-200"/>
                <p className="text-sm ct-muted mb-3">Haz clic en "Generar nuevos" para crear mensajes con IA</p>
                <button onClick={cargarMensajes} className="btn-primary flex items-center gap-2 mx-auto">
                  <Sparkles size={14}/> Generar mensajes
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {mensajes.map((m, idx) => (
                  <div key={idx} className="rounded-2xl bg-rose-softer p-4 relative group">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xl">{m.emoji}</span>
                      <p className="text-sm font-bold ct-accent">{m.titulo}</p>
                      <span className="badge badge-pink text-xs ml-auto">{m.tipo}</span>
                    </div>
                    <p className="text-sm ct-secondary leading-relaxed whitespace-pre-wrap">{m.mensaje}</p>
                    <button
                      onClick={() => copiarMensaje(m.mensaje, idx)}
                      className="mt-3 flex items-center gap-1.5 text-xs font-medium text-primary-600 hover:text-primary-800 transition-colors"
                    >
                      {copiadoIdx === idx
                        ? <><Check size={13} className="text-green-500"/> Copiado!</>
                        : <><Copy size={13}/> Copiar mensaje</>
                      }
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card">
            <div className="flex items-center gap-2 mb-3">
              <Palette size={18} className="text-primary-400"/>
              <h3 className="font-bold ct-accent">Prompts para crear anuncios con Canva & ChatGPT</h3>
              <span className="badge badge-pink text-xs">Groq IA</span>
            </div>
            <p className="text-xs ct-muted mb-4">
              La IA crea prompts a tu medida según tus productos y promociones activas. Escribe qué quieres crear o elige una plataforma, y genera ideas listas para copiar.
            </p>

            {/* Controles de generación */}
            <div className="flex flex-col sm:flex-row gap-2 mb-5">
              <input
                className="input-field flex-1"
                placeholder="¿Qué quieres crear? Ej: un flyer para el Día de la Madre con la promo activa"
                value={peticionPrompt}
                onChange={e => setPeticionPrompt(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !loadingPrompts) generarPrompts() }}
              />
              <select className="input-field sm:w-44" value={plataformaPrompt} onChange={e => setPlataformaPrompt(e.target.value)}>
                <option value="">Todas las plataformas</option>
                <option value="Instagram">Instagram</option>
                <option value="Facebook">Facebook</option>
                <option value="TikTok">TikTok</option>
                <option value="WhatsApp">WhatsApp</option>
                <option value="Canva">Canva (diseño)</option>
              </select>
              <button onClick={generarPrompts} disabled={loadingPrompts} className="btn-primary flex items-center gap-2 shrink-0">
                <Sparkles size={14} className={loadingPrompts ? 'animate-pulse' : ''}/>
                {loadingPrompts ? 'Generando...' : 'Generar prompts'}
              </button>
            </div>

            {loadingPrompts ? (
              <div className="flex items-center justify-center gap-2 py-10">
                <Sparkles size={18} className="animate-pulse text-primary-400"/>
                <p className="text-sm ct-muted">La IA está creando prompts a tu medida...</p>
              </div>
            ) : prompts.length === 0 ? (
              <div className="text-center py-8">
                <Palette size={32} className="mx-auto mb-2 text-primary-200"/>
                <p className="text-sm ct-muted">Escribe tu pedido y genera prompts personalizados</p>
              </div>
            ) : (
              <div className="space-y-3">
                {prompts.map((p, idx) => (
                  <div key={idx} className="rounded-2xl bg-rose-softer p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{p.emoji}</span>
                        <div>
                          <p className="text-sm font-bold ct-primary">{p.titulo}</p>
                          <p className="text-xs ct-muted">{p.plataforma}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => copiarMensaje(p.prompt, `p-${idx}`)}
                        className="flex items-center gap-1 text-xs font-medium text-primary-600 hover:text-primary-800 transition-colors shrink-0"
                      >
                        {copiadoIdx === `p-${idx}`
                          ? <><Check size={12} className="text-green-500"/> Copiado!</>
                          : <><Copy size={12}/> Copiar prompt</>
                        }
                      </button>
                    </div>
                    <p className="text-xs ct-secondary leading-relaxed bg-white dark:bg-[#0c0b0e] rounded-xl p-3 font-mono">{p.prompt}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
