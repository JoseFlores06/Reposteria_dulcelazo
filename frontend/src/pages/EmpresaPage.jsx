import { useState, useEffect } from 'react'
import { getEmpresa, actualizarEmpresa } from '../api/empresa'
import { Building2, Save, CreditCard, Hash, Phone, MapPin, Mail, FileText } from 'lucide-react'
import toast from 'react-hot-toast'

const EMPTY = { nombre: '', ruc: '', numero_yape_plin: '', nro_cuenta_banco: '', cci: '', direccion: '', distrito: '', telefono: '', correo: '' }

export default function EmpresaPage() {
  const [form, setForm] = useState(EMPTY)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    getEmpresa()
      .then(d => setForm({
        nombre: d.nombre || '',
        ruc: d.ruc || '',
        numero_yape_plin: d.numero_yape_plin || '',
        nro_cuenta_banco: d.nro_cuenta_banco || '',
        cci: d.cci || '',
        direccion: d.direccion || '',
        distrito: d.distrito || '',
        telefono: d.telefono || '',
        correo: d.correo || '',
      }))
      .catch(() => toast.error('Error al cargar datos'))
      .finally(() => setLoading(false))
  }, [])

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault(); setSaving(true)
    try { await actualizarEmpresa(form); toast.success('Datos actualizados correctamente') }
    catch { toast.error('Error al guardar') }
    finally { setSaving(false) }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-64"><div className="spinner" /></div>
  )

  return (
    <div className="max-w-2xl mx-auto space-y-5">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #ec4899, #be185d)' }}>
          <Building2 size={20} className="text-white" />
        </div>
        <div>
          <h1 className="page-title">Datos de la empresa</h1>
          <p className="page-subtitle">Información que aparece en boletas y documentos</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">

        {/* Identificación */}
        <div className="card space-y-4">
          <p className="text-xs font-bold uppercase tracking-wider ct-accent flex items-center gap-1.5">
            <FileText size={13}/> Identificación fiscal
          </p>
          <div>
            <label className="label">Razón social / Nombre *</label>
            <input className="input-field" value={form.nombre} onChange={set('nombre')} required placeholder="Dulce Lazo E.I.R.L." />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label flex items-center gap-1.5"><Hash size={11}/> RUC</label>
              <input className="input-field font-mono" value={form.ruc} onChange={set('ruc')} placeholder="20123456789" maxLength={11}/>
            </div>
            <div>
              <label className="label">Correo electrónico</label>
              <input type="email" className="input-field" value={form.correo} onChange={set('correo')} placeholder="contacto@dulcelazo.pe"/>
            </div>
          </div>
        </div>

        {/* Ubicación */}
        <div className="card space-y-4">
          <p className="text-xs font-bold uppercase tracking-wider ct-accent flex items-center gap-1.5">
            <MapPin size={13}/> Dirección y contacto
          </p>
          <div>
            <label className="label">Dirección</label>
            <input className="input-field" value={form.direccion} onChange={set('direccion')} placeholder="Av. Ejemplo 123, Urb. Las Flores"/>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label">Distrito</label>
              <input className="input-field" value={form.distrito} onChange={set('distrito')} placeholder="San Isidro, Lima"/>
            </div>
            <div>
              <label className="label flex items-center gap-1.5"><Phone size={11}/> Teléfono</label>
              <input className="input-field" value={form.telefono} onChange={set('telefono')} placeholder="01-234-5678 / 987654321"/>
            </div>
          </div>
        </div>

        {/* Pagos */}
        <div className="card space-y-4">
          <p className="text-xs font-bold uppercase tracking-wider ct-accent flex items-center gap-1.5">
            <CreditCard size={13}/> Datos de pago
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label flex items-center gap-1.5"><Phone size={11}/> Yape / Plin</label>
              <input className="input-field" value={form.numero_yape_plin} onChange={set('numero_yape_plin')} placeholder="987654321"/>
            </div>
            <div>
              <label className="label">N° Cuenta banco</label>
              <input className="input-field font-mono" value={form.nro_cuenta_banco} onChange={set('nro_cuenta_banco')} placeholder="0011-0111-..."/>
            </div>
            <div className="sm:col-span-2">
              <label className="label">CCI</label>
              <input className="input-field font-mono" value={form.cci} onChange={set('cci')} placeholder="00211..."/>
            </div>
          </div>
        </div>

        {/* Preview aviso */}
        <div className="rounded-2xl bg-rose-softer p-4 text-xs ct-secondary">
          <p className="font-semibold ct-accent mb-1">📄 Datos que aparecen en la boleta:</p>
          <p>Razón social, RUC, dirección, distrito, teléfono, correo y Yape/Plin se imprimen en el encabezado de cada boleta generada.</p>
        </div>

        <div className="flex justify-end">
          <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
            <Save size={15}/> {saving ? 'Guardando...' : 'Guardar cambios'}
          </button>
        </div>
      </form>
    </div>
  )
}
