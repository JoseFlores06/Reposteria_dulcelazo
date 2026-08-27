import api from './axios'

export const getInsumos = (activo) => api.get('/insumos', { params: activo !== undefined ? { activo } : {} }).then(r => r.data)
export const getInsumo = (id) => api.get(`/insumos/${id}`).then(r => r.data)
export const crearInsumo = (data) => api.post('/insumos', data).then(r => r.data)
export const actualizarInsumo = (id, data) => api.put(`/insumos/${id}`, data).then(r => r.data)
export const reabastecerInsumo = (id, data) => api.post(`/insumos/${id}/reabastecer`, data).then(r => r.data)
export const eliminarInsumo = (id) => api.delete(`/insumos/${id}`).then(r => r.data)
export const registrarMerma = (id, data) => api.post(`/insumos/${id}/merma`, data).then(r => r.data)
export const getMermas = (params) => api.get('/insumos/mermas', { params: params || {} }).then(r => r.data)
