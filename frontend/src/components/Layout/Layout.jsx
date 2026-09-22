import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import {
  ShoppingBag, Package, Tag, Users, Building2, Archive,
  Calendar, TrendingUp, LogOut, Menu, X, UserCog, Sun, Moon,
  ChevronRight, Sparkles
} from 'lucide-react'
import { useState, useEffect } from 'react'

const navItems = [
  { to: '/ventas',        label: 'Ventas',        icon: ShoppingBag, soloAdmin: false },
  { to: '/productos',     label: 'Productos',     icon: Package,     soloAdmin: false },
  { to: '/paquetes',      label: 'Paquetes',      icon: Package,     soloAdmin: false },
  { to: '/promociones',   label: 'Promociones',   icon: Tag,         soloAdmin: false },
  { to: '/clientes',      label: 'Clientes',      icon: Users,       soloAdmin: false },
  { to: '/insumos',       label: 'Insumos',       icon: Archive,     soloAdmin: true  },
  { to: '/colaboradores', label: 'Colaboradores', icon: UserCog,     soloAdmin: true  },
  { to: '/empresa',       label: 'Empresa',       icon: Building2,   soloAdmin: true  },
  { to: '/calendario',    label: 'Calendario',    icon: Calendar,    soloAdmin: true  },
  { to: '/finanzas',      label: 'Finanzas',      icon: TrendingUp,  soloAdmin: true  },
  { to: '/usuarios',      label: 'Usuarios',      icon: UserCog,     soloAdmin: true  },
]

const navGroups = [
  { label: 'Principal', items: ['ventas', 'productos', 'paquetes', 'promociones', 'clientes'] },
  { label: 'Administración', items: ['insumos', 'colaboradores', 'empresa', 'calendario', 'finanzas', 'usuarios'] },
]

export default function Layout() {
  const { usuario, isAdmin, logout } = useAuth()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [dark, setDark] = useState(() => localStorage.getItem('theme') === 'dark')

  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }, [dark])

  const handleLogout = () => { logout(); navigate('/login') }

  const items = navItems.filter(item => !item.soloAdmin || isAdmin)
  const getGroupItems = (keys) => items.filter(i => keys.includes(i.to.slice(1)))

  const NavGroup = ({ label, keys }) => {
    const groupItems = getGroupItems(keys)
    if (!groupItems.length) return null
    return (
      <div className="mb-3">
        <p className="px-3 mb-1.5 text-[10px] font-bold uppercase tracking-widest"
           style={{ color: dark ? '#6b3a56' : '#f9a8d4' }}>
          {label}
        </p>
        {groupItems.map(({ to, label: lbl, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={() => setSidebarOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl mb-0.5 text-sm font-medium transition-all duration-150 group relative ${
                isActive
                  ? dark
                    ? 'bg-primary-900 text-primary-300 shadow-sm'
                    : 'bg-primary-500 text-white shadow-rose-md'
                  : dark
                    ? 'text-rose-300/70 hover:bg-white/5 hover:text-rose-200'
                    : 'text-rose-800/60 hover:bg-primary-50 hover:text-primary-700'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={17} className={isActive ? '' : 'opacity-75 group-hover:opacity-100'} />
                <span className="flex-1">{lbl}</span>
                {isActive && <ChevronRight size={14} className="opacity-60" />}
              </>
            )}
          </NavLink>
        ))}
      </div>
    )
  }

  const sidebarBg = dark
    ? 'bg-[#110d14] border-[#2e1f2a]'
    : 'border-[#fce7f3]'

  return (
    <div className={`flex h-screen overflow-hidden ${dark ? 'bg-[#0c0b0e]' : 'bg-[#fdf5f9]'}`}>
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`
        fixed lg:static inset-y-0 left-0 z-30 w-64 flex flex-col
        border-r transition-transform duration-300
        ${sidebarBg}
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}
        style={!dark ? {
          background: 'linear-gradient(180deg, #ffffff 0%, #fdf5f9 100%)',
        } : {}}
      >
        <div className={`px-5 py-4 border-b ${dark ? 'border-[#2e1f2a]' : 'border-[#fce7f3]'}`}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl flex items-center justify-center text-xl shadow-rose"
                 style={{ background: 'linear-gradient(135deg, #ec4899 0%, #be185d 100%)' }}>
              🧁
            </div>
            <div>
              <h1 className={`font-bold text-sm leading-tight ${dark ? 'text-white' : 'text-rose-950'}`}>
                Dulce Lazo
              </h1>
              <p className={`text-[11px] mt-0.5 flex items-center gap-1 ${dark ? 'text-rose-400/60' : 'text-rose-400'}`}>
                <Sparkles size={10} /> Sistema de Gestión
              </p>
            </div>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto py-4 px-3">
          <NavGroup label="Principal" keys={['ventas', 'productos', 'paquetes', 'promociones', 'clientes']} />
          {isAdmin && <NavGroup label="Administración" keys={['insumos', 'colaboradores', 'empresa', 'calendario', 'finanzas', 'usuarios']} />}
        </nav>

        <div className={`px-4 py-4 border-t ${dark ? 'border-[#2e1f2a]' : 'border-[#fce7f3]'}`}>
          <button
            onClick={() => setDark(d => !d)}
            className={`flex items-center gap-2.5 w-full px-3 py-2 rounded-xl text-sm font-medium transition-all mb-3 ${
              dark
                ? 'text-amber-400/80 hover:bg-white/5'
                : 'text-rose-600/70 hover:bg-primary-50'
            }`}
          >
            {dark
              ? <Sun size={16} className="text-amber-400" />
              : <Moon size={16} />
            }
            {dark ? 'Modo claro' : 'Modo oscuro'}
          </button>

          <div className={`flex items-center gap-3 px-3 py-2.5 rounded-xl mb-2 ${dark ? 'bg-white/5' : 'bg-primary-50'}`}>
            <div className="w-8 h-8 rounded-xl flex items-center justify-center text-sm font-bold text-white flex-shrink-0"
                 style={{ background: 'linear-gradient(135deg, #ec4899, #9d174d)' }}>
              {usuario?.nombres?.charAt(0)?.toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className={`text-sm font-semibold truncate ${dark ? 'text-white' : 'text-rose-950'}`}>
                {usuario?.nombres} {usuario?.apellidos?.split(' ')[0]}
              </p>
              <p className={`text-[11px] capitalize ${dark ? 'text-rose-400/60' : 'text-rose-400'}`}>
                {usuario?.rol}
              </p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className={`flex items-center gap-2 w-full px-3 py-2 rounded-xl text-sm font-medium transition-all ${
              dark
                ? 'text-red-400/80 hover:bg-red-950/50'
                : 'text-red-500 hover:bg-red-50'
            }`}
          >
            <LogOut size={15} />
            Cerrar sesión
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <header className={`lg:hidden border-b px-4 py-3 flex items-center gap-3 ${
          dark ? 'bg-[#110d14] border-[#2e1f2a]' : 'bg-white border-[#fce7f3]'
        }`}>
          <button
            onClick={() => setSidebarOpen(true)}
            className={dark ? 'text-rose-300' : 'text-rose-600'}
          >
            <Menu size={22} />
          </button>
          <div className="flex items-center gap-2">
            <span className="text-lg">🧁</span>
            <h1 className={`font-bold text-sm ${dark ? 'text-white' : 'text-rose-950'}`}>
              Dulce Lazo
            </h1>
          </div>
        </header>

        <main className={`flex-1 overflow-y-auto p-4 lg:p-6 ${dark ? 'bg-[#0c0b0e]' : 'bg-[#fdf5f9]'}`}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
