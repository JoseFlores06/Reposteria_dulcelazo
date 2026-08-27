import api from './axios'

export const getGastos = (params) => api.get('/marketing/gastos', { params }).then(r => r.data)
export const crearGasto = (data) => api.post('/marketing/gastos', data).then(r => r.data)
export const actualizarGasto = (id, data) => api.put(`/marketing/gastos/${id}`, data).then(r => r.data)
export const eliminarGasto = (id) => api.delete(`/marketing/gastos/${id}`).then(r => r.data)
export const getEstadisticas = (params) => api.get('/marketing/estadisticas', { params }).then(r => r.data)
export const getMensajesWhatsapp = () => api.get('/marketing/mensajes-whatsapp').then(r => r.data)
export const getPromptsCanva = (params) => api.get('/marketing/prompts-canva', { params }).then(r => r.data)
export const getDashboard = (params) => api.get('/finanzas/dashboard', { params }).then(r => r.data)
export const getVentasDetalle = (params) => api.get('/finanzas/ventas-detalle', { params }).then(r => r.data)
export const getMarketingFinanzas = (params) => api.get('/finanzas/marketing', { params }).then(r => r.data)
