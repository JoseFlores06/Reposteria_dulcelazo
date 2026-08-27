import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import { Mail, Lock, Sparkles } from 'lucide-react'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ correo: '', password: '' })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await login(form.correo, form.password)
      toast.success('¡Bienvenida al sistema!')
      navigate('/ventas')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Credenciales incorrectas')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex" style={{ background: 'linear-gradient(135deg, #fdf2f8 0%, #fce7f3 40%, #fbcfe8 100%)' }}>
      {/* Panel izquierdo decorativo, oculto en mobile */}
      <div className="hidden lg:flex lg:w-1/2 flex-col items-center justify-center p-16 relative">
        <div className="absolute top-20 left-20 w-48 h-48 rounded-full opacity-20"
             style={{ background: 'radial-gradient(circle, #ec4899 0%, transparent 70%)' }} />
        <div className="absolute bottom-32 right-16 w-32 h-32 rounded-full opacity-15"
             style={{ background: 'radial-gradient(circle, #be185d 0%, transparent 70%)' }} />
        <div className="absolute top-1/2 left-1/3 w-20 h-20 rounded-full opacity-10"
             style={{ background: 'radial-gradient(circle, #f472b6 0%, transparent 70%)' }} />

        <div className="relative z-10 text-center">
          <div className="text-8xl mb-6 drop-shadow-lg">🧁</div>
          <h1 className="text-4xl font-bold mb-3 ct-heading">
            Dulce Lazo
          </h1>
          <p className="text-lg mb-8" style={{ color: '#be185d', opacity: 0.7 }}>
            Con amor, hecho a mano 🌸
          </p>
          <div className="flex flex-col gap-3 text-sm ct-accent opacity-60">
            <div className="flex items-center gap-2 justify-center">
              <span className="w-1.5 h-1.5 rounded-full bg-primary-400" />
              Gestión de ventas y pedidos
            </div>
            <div className="flex items-center gap-2 justify-center">
              <span className="w-1.5 h-1.5 rounded-full bg-primary-400" />
              Control de insumos y costos
            </div>
            <div className="flex items-center gap-2 justify-center">
              <span className="w-1.5 h-1.5 rounded-full bg-primary-400" />
              Reportes financieros
            </div>
          </div>
        </div>
      </div>

      {/* Panel derecho: formulario de acceso */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6">
        <div className="w-full max-w-sm">
          <div className="lg:hidden text-center mb-8">
            <div className="text-6xl mb-3">🧁</div>
            <h1 className="text-2xl font-bold ct-heading">Dulce Lazo</h1>
          </div>

          <div className="bg-white rounded-3xl p-8" style={{ boxShadow: '0 24px 64px rgba(236, 72, 153, 0.15)' }}>
            <div className="mb-7">
              <h2 className="text-xl font-bold ct-primary">Iniciar sesión</h2>
              <p className="text-sm mt-1 ct-muted">
                Ingresa tus credenciales para continuar
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="label">Correo electrónico</label>
                <div className="relative">
                  <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 ct-pink-lt" />
                  <input
                    type="email"
                    className="input-field pl-10"
                    placeholder="correo@dulcelazo.pe"
                    value={form.correo}
                    onChange={(e) => setForm(f => ({ ...f, correo: e.target.value }))}
                    required
                    autoFocus
                  />
                </div>
              </div>

              <div>
                <label className="label">Contraseña</label>
                <div className="relative">
                  <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 ct-pink-lt" />
                  <input
                    type="password"
                    className="input-field pl-10"
                    placeholder="••••••••"
                    value={form.password}
                    onChange={(e) => setForm(f => ({ ...f, password: e.target.value }))}
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full py-3 text-sm mt-2"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                    Ingresando...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <Sparkles size={15} />
                    Ingresar al sistema
                  </span>
                )}
              </button>
            </form>
          </div>

          <p className="text-center text-xs mt-5" style={{ color: '#d4a0b8' }}>
            Dulce Lazo © {new Date().getFullYear()} · Sistema de Gestión
          </p>
        </div>
      </div>
    </div>
  )
}
