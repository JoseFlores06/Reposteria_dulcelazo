import { useState, useEffect } from 'react'
import {
  getGastosMarketing, getCanalesMarketing,
  crearGastoMarketing, actualizarGastoMarketing, eliminarGastoMarketing,
} from '../api/gastos_marketing'
import { Megaphone, Plus, Pencil, Trash2, X, Check } from 'lucide-react'
import toast from 'react-hot-toast'

const thClass = 'text-left pb-3 text-xs font-semibold uppercase tracking-wide text-rose-400'

function formatFecha(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleDateString('es-PE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function formatMonto(n) {
  return `S/ ${Number(n).toFixed(2)}`
}

export default function GastosMarketingPage() {
  const [gastos, setGastos] = useState([])
  const [canales, setCanales] = useState([])
  const [cargando, setCargando] = useState(true)
  const [modalAbierto, setModalAbierto] = useState(false)
  const [editando, setEditando] = useState(null)
  const [form, setForm] = useState({ concepto: '', canal: '', monto: '', fecha: '', notas: '' })

  const cargar = async () => {
    try {
      const [gs, cs] = await Promise.all([getGastosMarketing(), getCanalesMarketing()])
      setGastos(gs)
      setCanales(cs)
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => { cargar() }, [])

  const totalGastos = gastos.reduce((s, g) => s + Number(g.monto), 0)

  const abrirCrear = () => {
    setEditando(null)
    setForm({ concepto: '', canal: '', monto: '', fecha: '', notas: '' })
    setModalAbierto(true)
  }

  const abrirEditar = (g) => {
    setEditando(g)
    setForm({
      concepto: g.concepto,
      canal: g.canal || '',
      monto: String(g.monto),
      fecha: g.fecha ? g.fecha.slice(0, 10) : '',
      notas: g.notas || '',
    })
    setModalAbierto(true)
  }

  const guardar = async () => {
    if (!form.concepto.trim() || !form.monto) {
      toast.error('Concepto y monto son obligatorios')
      return
    }
    const payload = {
      concepto: form.concepto.trim(),
      canal: form.canal || null,
      monto: parseFloat(form.monto),
      notas: form.notas || null,
    }
    if (form.fecha) payload.fecha = form.fecha + 'T00:00:00'

    try {
      if (editando) {
        await actualizarGastoMarketing(editando.id, payload)
        toast.success('Gasto actualizado')
      } else {
        await crearGastoMarketing(payload)
        toast.success('Gasto registrado')
      }
      setModalAbierto(false)
      cargar()
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Error al guardar')
    }
  }

  const eliminar = async (id) => {
    if (!window.confirm('¿Eliminar este gasto de marketing?')) return
    try {
      await eliminarGastoMarketing(id)
      toast.success('Gasto eliminado')
      cargar()
    } catch {
      toast.error('Error al eliminar')
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Encabezado */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl flex items-center justify-center text-white"
               style={{ background: 'linear-gradient(135deg, #ec4899, #be185d)' }}>
            <Megaphone size={20} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-rose-950 dark:text-white">Gastos de Marketing</h1>
            <p className="text-xs text-rose-400">Registro de inversión en publicidad y promoción</p>
          </div>
        </div>
        <button
          onClick={abrirCrear}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white"
          style={{ background: 'linear-gradient(135deg, #ec4899, #be185d)' }}
        >
          <Plus size={16} /> Nuevo gasto
        </button>
      </div>

      {/* Resumen */}
      <div className="card p-5 flex items-center gap-4">
        <div>
          <p className="text-xs text-rose-400 uppercase tracking-wide font-semibold">Total registrado</p>
          <p className="text-2xl font-bold text-rose-700 dark:text-rose-300">{formatMonto(totalGastos)}</p>
        </div>
        <div className="ml-auto text-sm text-rose-400">{gastos.length} registro(s)</div>
      </div>

      {/* Tabla */}
      <div className="card overflow-hidden">
        {cargando ? (
          <div className="p-8 text-center text-rose-400">Cargando…</div>
        ) : gastos.length === 0 ? (
          <div className="p-10 text-center">
            <Megaphone size={36} className="mx-auto mb-3 text-rose-200" />
            <p className="text-rose-400">No hay gastos registrados</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-rose-100 dark:border-rose-900/40">
                <th className={`${thClass} px-5 pt-4`}>Fecha</th>
                <th className={`${thClass} pt-4`}>Concepto</th>
                <th className={`${thClass} pt-4`}>Canal</th>
                <th className={`${thClass} pt-4 text-right`}>Monto</th>
                <th className={`${thClass} pt-4`}>Notas</th>
                <th className={`${thClass} px-5 pt-4`}></th>
              </tr>
            </thead>
            <tbody>
              {gastos.map(g => (
                <tr key={g.id} className="border-b border-rose-50 dark:border-rose-900/20 hover:bg-rose-50/50 dark:hover:bg-white/5 transition-colors">
                  <td className="px-5 py-3 text-sm text-rose-700 dark:text-rose-200">{formatFecha(g.fecha)}</td>
                  <td className="py-3 text-sm font-medium text-rose-900 dark:text-white">{g.concepto}</td>
                  <td className="py-3">
                    {g.canal && (
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300">
                        {g.canal}
                      </span>
                    )}
                  </td>
                  <td className="py-3 text-sm font-semibold text-rose-700 dark:text-rose-300 text-right">{formatMonto(g.monto)}</td>
                  <td className="py-3 text-xs text-rose-500 max-w-xs truncate">{g.notas || '-'}</td>
                  <td className="px-5 py-3">
                    <div className="flex gap-2 justify-end">
                      <button onClick={() => abrirEditar(g)} className="p-1.5 rounded-lg hover:bg-rose-100 dark:hover:bg-white/10 text-rose-400 hover:text-rose-600 transition-colors">
                        <Pencil size={14} />
                      </button>
                      <button onClick={() => eliminar(g.id)} className="p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 text-red-400 hover:text-red-600 transition-colors">
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Modal */}
      {modalAbierto && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-[#1a1020] rounded-2xl shadow-2xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold text-rose-950 dark:text-white">
                {editando ? 'Editar gasto' : 'Nuevo gasto de marketing'}
              </h2>
              <button onClick={() => setModalAbierto(false)} className="p-1 rounded-lg hover:bg-rose-50 dark:hover:bg-white/10 text-rose-400">
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-rose-700 dark:text-rose-300 mb-1">Concepto *</label>
                <input
                  className="input-field w-full"
                  placeholder="Ej: Publicidad en Instagram"
                  value={form.concepto}
                  onChange={e => setForm(f => ({ ...f, concepto: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-rose-700 dark:text-rose-300 mb-1">Canal</label>
                <select className="input-field w-full" value={form.canal} onChange={e => setForm(f => ({ ...f, canal: e.target.value }))}>
                  <option value="">Sin especificar</option>
                  {canales.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-rose-700 dark:text-rose-300 mb-1">Monto (S/) *</label>
                  <input
                    type="number" min="0.01" step="0.01"
                    className="input-field w-full"
                    placeholder="0.00"
                    value={form.monto}
                    onChange={e => setForm(f => ({ ...f, monto: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-rose-700 dark:text-rose-300 mb-1">Fecha</label>
                  <input
                    type="date"
                    className="input-field w-full"
                    value={form.fecha}
                    onChange={e => setForm(f => ({ ...f, fecha: e.target.value }))}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-rose-700 dark:text-rose-300 mb-1">Notas</label>
                <textarea
                  className="input-field w-full"
                  rows={2}
                  placeholder="Detalles adicionales…"
                  value={form.notas}
                  onChange={e => setForm(f => ({ ...f, notas: e.target.value }))}
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setModalAbierto(false)}
                className="flex-1 px-4 py-2 rounded-xl text-sm font-medium border border-rose-200 dark:border-rose-800 text-rose-600 hover:bg-rose-50 dark:hover:bg-white/5 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={guardar}
                className="flex-1 px-4 py-2 rounded-xl text-sm font-semibold text-white flex items-center justify-center gap-2"
                style={{ background: 'linear-gradient(135deg, #ec4899, #be185d)' }}
              >
                <Check size={15} />
                {editando ? 'Guardar cambios' : 'Registrar gasto'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
