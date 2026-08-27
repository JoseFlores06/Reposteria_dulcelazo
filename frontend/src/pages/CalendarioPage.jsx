import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Calendar, Sparkles, CheckCircle2, XCircle, Loader, ExternalLink, Unlink, RefreshCw } from 'lucide-react'
import { getEstadoCalendario, getAuthUrl, desconectarCalendario, getEventos } from '../api/calendario'
import toast from 'react-hot-toast'

export default function CalendarioPage() {
  const [searchParams] = useSearchParams()
  const [estado, setEstado] = useState(null)
  const [loading, setLoading] = useState(true)
  const [conectando, setConectando] = useState(false)
  const [eventos, setEventos] = useState([])
  const [cargandoEventos, setCargandoEventos] = useState(false)
  const pollingRef = useRef(null)

  const cargarEstado = async () => {
    setLoading(true)
    try {
      const res = await getEstadoCalendario()
      setEstado(res)
      if (res.conectado) cargarEventos()
    } catch { setEstado({ conectado: false, mensaje: 'Error al verificar estado' }) }
    finally { setLoading(false) }
  }

  const cargarEventos = async () => {
    setCargandoEventos(true)
    try {
      const res = await getEventos()
      setEventos(res.eventos || [])
    } catch { setEventos([]) }
    finally { setCargandoEventos(false) }
  }

  const iniciarPolling = () => {
    // Cada 2.5s verifica si el usuario completó el OAuth en la otra pestaña
    const interval = setInterval(async () => {
      try {
        const res = await getEstadoCalendario()
        if (res.conectado) {
          clearInterval(interval)
          pollingRef.current = null
          setConectando(false)
          setEstado(res)
          cargarEventos()
          toast.success(`¡Google Calendar conectado como ${res.cuenta_email || 'tu cuenta'}!`)
        }
      } catch { /* silencioso */ }
    }, 2500)
    pollingRef.current = interval
  }

  useEffect(() => {
    if (searchParams.get('conectado') === 'true') {
      toast.success('¡Google Calendar conectado correctamente!')
    } else if (searchParams.get('error')) {
      toast.error(`Error al conectar: ${searchParams.get('error')}`)
    }
    cargarEstado()
    return () => { if (pollingRef.current) clearInterval(pollingRef.current) }
  }, [])

  const handleConectar = async () => {
    setConectando(true)
    try {
      const res = await getAuthUrl()
      // Abrir en nueva pestaña para no interrumpir la app
      window.open(res.url, '_blank', 'noopener,noreferrer')
      toast('Completa la autorización en la nueva pestaña. Esta página se actualizará sola.', {
        duration: 8000,
        icon: '🔗',
      })
      iniciarPolling()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al obtener URL de autorización')
      setConectando(false)
    }
  }

  const handleDesconectar = async () => {
    if (!confirm('¿Desconectar Google Calendar? Los eventos ya creados no se eliminarán.')) return
    try {
      await desconectarCalendario()
      toast.success('Google Calendar desconectado')
      setEstado({ conectado: false, mensaje: 'Desconectado' })
      setEventos([])
    } catch { toast.error('Error al desconectar') }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{background:'linear-gradient(135deg,#ec4899,#be185d)'}}>
          <Calendar size={20} className="text-white"/>
        </div>
        <div>
          <h1 className="page-title">Calendario</h1>
          <p className="page-subtitle">Integración con Google Calendar</p>
        </div>
      </div>

      {/* Card de estado */}
      <div className="card">
        {loading ? (
          <div className="flex items-center gap-3 py-4">
            <Loader size={20} className="text-primary-400 animate-spin"/>
            <p className="text-sm ct-muted">Verificando estado de conexión...</p>
          </div>
        ) : estado?.conectado ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3">
                <CheckCircle2 size={24} className="text-green-500 shrink-0"/>
                <div>
                  <p className="font-bold text-sm text-green-700">Conectado a Google Calendar</p>
                  {estado.cuenta_email && (
                    <p className="text-xs ct-muted mt-0.5">
                      Cuenta: <span className="font-semibold text-primary-600">{estado.cuenta_email}</span>
                    </p>
                  )}
                  <p className="text-xs ct-muted">Los eventos de ventas y alertas de stock se crearán automáticamente</p>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <button onClick={cargarEventos} className="btn-secondary text-xs flex items-center gap-1.5">
                  <RefreshCw size={12}/> Actualizar
                </button>
                <button onClick={handleConectar} disabled={conectando} className="btn-secondary text-xs flex items-center gap-1.5">
                  <ExternalLink size={12}/> {conectando ? 'Abriendo...' : 'Cambiar cuenta'}
                </button>
                <button onClick={handleDesconectar} className="btn-secondary text-xs flex items-center gap-1.5 text-red-500 border-red-200">
                  <Unlink size={12}/> Desconectar
                </button>
              </div>
            </div>

            {/* Funciones activas */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-pink-100 dark:border-pink-900/20">
              {[
                { icon: '📦', titulo: 'Stock bajo', desc: 'Evento automático cuando algún insumo queda sin stock suficiente' },
                { icon: '🧁', titulo: 'Entrega de pedidos', desc: 'Recordatorio automático al registrar una venta con fecha de entrega' },
              ].map(f => (
                <div key={f.titulo} className="flex items-start gap-3 p-3 rounded-xl bg-rose-softer">
                  <span className="text-xl">{f.icon}</span>
                  <div>
                    <p className="text-sm font-semibold ct-primary">{f.titulo}</p>
                    <p className="text-xs ct-muted mt-0.5">{f.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-5">
            <div className="flex items-start gap-3">
              <XCircle size={20} className="text-rose-400 mt-0.5 shrink-0"/>
              <div>
                <p className="font-bold text-sm ct-primary">No conectado</p>
                <p className="text-xs ct-muted mt-0.5">
                  Conecta tu cuenta de Google para que el sistema cree eventos automáticamente al hacer ventas y cuando el stock esté bajo.
                </p>
              </div>
            </div>

            {/* Instrucciones */}
            <div className="rounded-2xl p-4 bg-rose-softer">
              <p className="text-xs font-bold uppercase tracking-wider ct-accent mb-3">Qué se configura automáticamente:</p>
              <ul className="space-y-2 text-xs ct-secondary">
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-400 shrink-0"/>
                  Evento de alerta cuando algún insumo tiene poco stock
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-400 shrink-0"/>
                  Recordatorio de entrega al registrar ventas con fecha de entrega
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-400 shrink-0"/>
                  Todos los eventos aparecen en tu Google Calendar personal
                </li>
              </ul>
            </div>

            <div className="flex items-center gap-3">
              <button onClick={handleConectar} disabled={conectando} className="btn-primary flex items-center gap-2">
                <ExternalLink size={15}/>
                {conectando ? 'Abriendo Google...' : 'Conectar Google Calendar'}
              </button>
              <p className="text-xs ct-muted">Te redirigirá a Google para autorizar el acceso</p>
            </div>
          </div>
        )}
      </div>

      {/* Próximos eventos */}
      {estado?.conectado && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-bold ct-accent">Próximos eventos</h3>
            {cargandoEventos && <Loader size={16} className="text-primary-400 animate-spin"/>}
          </div>

          {eventos.length === 0 ? (
            <div className="text-center py-10">
              <Calendar size={36} className="mx-auto mb-2 ct-pink-lt"/>
              <p className="text-sm ct-muted">No hay eventos próximos en tu calendario</p>
            </div>
          ) : (
            <div className="space-y-3">
              {eventos.map(e => (
                <div key={e.id} className="flex items-start gap-3 p-3 rounded-xl bg-rose-softer">
                  <Calendar size={16} className="text-primary-400 mt-0.5 shrink-0"/>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold ct-primary truncate">{e.titulo}</p>
                    {e.inicio && (
                      <p className="text-xs ct-muted mt-0.5">
                        {new Date(e.inicio).toLocaleString('es-PE', {dateStyle:'medium', timeStyle:'short'})}
                      </p>
                    )}
                    {e.descripcion && (
                      <p className="text-xs ct-secondary mt-1 line-clamp-2">{e.descripcion}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Info adicional */}
      <div className="card">
        <div className="flex items-start gap-3">
          <Sparkles size={16} className="text-primary-400 mt-0.5 shrink-0"/>
          <div>
            <p className="text-sm font-bold ct-accent mb-2">Usos de IA (Groq) en el sistema</p>
            <ul className="text-xs ct-secondary space-y-1.5">
              <li><span className="font-semibold text-primary-600">Promociones:</span> Sugerencias automáticas de descuento para cada producto</li>
              <li><span className="font-semibold text-primary-600">Análisis de ventas:</span> Recomendaciones de negocio basadas en tus datos del mes</li>
              <li><span className="font-semibold text-primary-600">Alertas de stock:</span> Mensajes personalizados cuando los insumos están bajos</li>
              <li><span className="font-semibold text-primary-600">Nombres de productos:</span> Sugerencias creativas al crear nuevos productos (próximamente en el formulario)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
