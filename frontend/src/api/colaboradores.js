import api from './axios'

export const getColaboradores = () => api.get('/colaboradores').then(r => r.data)
export const getColaborador = (id) => api.get(`/colaboradores/${id}`).then(r => r.data)
export const crearColaborador = (data) => api.post('/colaboradores', data).then(r => r.data)
export const actualizarColaborador = (id, data) => api.put(`/colaboradores/${id}`, data).then(r => r.data)
export const eliminarColaborador = (id) => api.delete(`/colaboradores/${id}`).then(r => r.data)
