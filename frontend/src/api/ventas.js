import api from './axios'

export const getVentas = (params) => api.get('/ventas', { params }).then(r => r.data)
export const getVenta = (id) => api.get(`/ventas/${id}`).then(r => r.data)
export const crearVenta = (data) => api.post('/ventas', data).then(r => r.data)
export const marcarPagado = (id) => api.patch(`/ventas/${id}/marcar-pagado`).then(r => r.data)
export const cambiarEstado = (id, estado) => api.patch(`/ventas/${id}/estado`, null, { params: { estado } }).then(r => r.data)
export const descargarBoleta = (id) => api.get(`/ventas/${id}/boleta`, { responseType: 'blob' }).then(r => r.data)
