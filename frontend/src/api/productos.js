import api from './axios'

export const getProductos = (activo) => api.get('/productos', { params: activo !== undefined ? { activo } : {} }).then(r => r.data)
export const getProducto = (id) => api.get(`/productos/${id}`).then(r => r.data)
export const costearProducto = (data) => api.post('/productos/costear', data).then(r => r.data)

export const crearProducto = (formData) =>
  api.post('/productos', formData, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data)

export const actualizarProducto = (id, formData) =>
  api.put(`/productos/${id}`, formData, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data)

export const eliminarProducto = (id) => api.delete(`/productos/${id}`).then(r => r.data)
