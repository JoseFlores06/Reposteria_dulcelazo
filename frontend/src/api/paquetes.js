import api from './axios'

export const getPaquetes = (activo) => api.get('/paquetes', { params: activo !== undefined ? { activo } : {} }).then(r => r.data)
export const getPaquete = (id) => api.get(`/paquetes/${id}`).then(r => r.data)

export const crearPaquete = (formData) =>
  api.post('/paquetes', formData, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data)

export const actualizarPaquete = (id, formData) =>
  api.put(`/paquetes/${id}`, formData, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data)

export const eliminarPaquete = (id) => api.delete(`/paquetes/${id}`).then(r => r.data)
