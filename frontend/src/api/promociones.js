import api from './axios'

export const getPromociones = (soloActivas) => api.get('/promociones', { params: soloActivas !== undefined ? { solo_activas: soloActivas } : {} }).then(r => r.data)
export const getPromocion = (id) => api.get(`/promociones/${id}`).then(r => r.data)
export const sugerirIA = (itemTipo, itemId) => api.get(`/promociones/sugerir-ia/${itemTipo}/${itemId}`).then(r => r.data)

export const crearPromocion = (formData) =>
  api.post('/promociones', formData, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data)

export const actualizarPromocion = (id, formData) =>
  api.put(`/promociones/${id}`, formData, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data)

export const togglePromocion = (id) => api.patch(`/promociones/${id}/toggle`).then(r => r.data)
export const eliminarPromocion = (id) => api.delete(`/promociones/${id}`).then(r => r.data)
