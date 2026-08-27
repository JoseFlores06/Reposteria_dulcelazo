import api from './axios'

export const getReporteInsumos = (params) => api.get('/finanzas/insumos', { params }).then(r => r.data)
export const getReporteVentas = (params) => api.get('/finanzas/ventas', { params }).then(r => r.data)
export const getReporteGanancia = (params) => api.get('/finanzas/ganancia', { params }).then(r => r.data)
export const getPagosColaboradores = (params) => api.get('/finanzas/pagos-colaboradores', { params }).then(r => r.data)
export const registrarPago = (data) => api.post('/finanzas/pagos-colaboradores', data).then(r => r.data)
export const actualizarPago = (id, data) => api.put(`/finanzas/pagos-colaboradores/${id}`, data).then(r => r.data)
export const eliminarPago = (id) => api.delete(`/finanzas/pagos-colaboradores/${id}`).then(r => r.data)
export const getResumenGroq = (params) => api.get('/finanzas/resumen-groq', { params }).then(r => r.data)
