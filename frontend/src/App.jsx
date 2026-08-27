import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout/Layout'
import LoginPage from './pages/LoginPage'
import EmpresaPage from './pages/EmpresaPage'
import InsumosPage from './pages/InsumosPage'
import ProductosPage from './pages/ProductosPage'
import PaquetesPage from './pages/PaquetesPage'
import PromocionesPage from './pages/PromocionesPage'
import ClientesPage from './pages/ClientesPage'
import ColaboradoresPage from './pages/ColaboradoresPage'
import CalendarioPage from './pages/CalendarioPage'
import MarketingPage from './pages/MarketingPage'
import VentasPage from './pages/VentasPage'
import FinanzasPage from './pages/FinanzasPage'
import UsuariosPage from './pages/UsuariosPage'

function RutaProtegida({ children, soloAdmin = false }) {
  const { usuario, isAdmin } = useAuth()
  if (!usuario) return <Navigate to="/login" replace />
  if (soloAdmin && !isAdmin) return <Navigate to="/ventas" replace />
  return children
}

function AppRoutes() {
  const { usuario } = useAuth()

  return (
    <Routes>
      <Route path="/login" element={usuario ? <Navigate to="/ventas" replace /> : <LoginPage />} />
      <Route path="/" element={<RutaProtegida><Layout /></RutaProtegida>}>
        <Route index element={<Navigate to="/ventas" replace />} />
        <Route path="ventas" element={<VentasPage />} />
        <Route path="productos" element={<ProductosPage />} />
        <Route path="paquetes" element={<PaquetesPage />} />
        <Route path="promociones" element={<PromocionesPage />} />
        <Route path="clientes" element={<ClientesPage />} />
        <Route path="empresa" element={<RutaProtegida soloAdmin><EmpresaPage /></RutaProtegida>} />
        <Route path="insumos" element={<RutaProtegida soloAdmin><InsumosPage /></RutaProtegida>} />
        <Route path="colaboradores" element={<RutaProtegida soloAdmin><ColaboradoresPage /></RutaProtegida>} />
        <Route path="calendario" element={<RutaProtegida soloAdmin><CalendarioPage /></RutaProtegida>} />
        <Route path="marketing" element={<RutaProtegida soloAdmin><MarketingPage /></RutaProtegida>} />
        <Route path="finanzas" element={<RutaProtegida soloAdmin><FinanzasPage /></RutaProtegida>} />
        <Route path="usuarios" element={<RutaProtegida soloAdmin><UsuariosPage /></RutaProtegida>} />
      </Route>
      <Route path="*" element={<Navigate to="/ventas" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
