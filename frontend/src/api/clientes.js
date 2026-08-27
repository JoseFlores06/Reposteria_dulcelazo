import api from './axios'

export const getClientes = () => api.get('/clientes').then(r => r.data)
export const getCliente = (id) => api.get(`/clientes/${id}`).then(r => r.data)
export const getClientesRecurrentes = () => api.get('/clientes/recurrentes').then(r => r.data)
export const crearCliente = (data) => api.post('/clientes', data).then(r => r.data)
export const actualizarCliente = (id, data) => api.put(`/clientes/${id}`, data).then(r => r.data)
export const eliminarCliente = (id) => api.delete(`/clientes/${id}`).then(r => r.data)

// Direcciones
export const getDirecciones = (clienteId) => api.get(`/clientes/${clienteId}/direcciones`).then(r => r.data)
export const crearDireccion = (clienteId, data) => api.post(`/clientes/${clienteId}/direcciones`, data).then(r => r.data)
export const actualizarDireccion = (clienteId, dirId, data) => api.put(`/clientes/${clienteId}/direcciones/${dirId}`, data).then(r => r.data)
export const eliminarDireccion = (clienteId, dirId) => api.delete(`/clientes/${clienteId}/direcciones/${dirId}`).then(r => r.data)
