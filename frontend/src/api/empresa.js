import api from './axios'

export const getEmpresa = () => api.get('/empresa').then(r => r.data)
export const actualizarEmpresa = (data) => api.put('/empresa', data).then(r => r.data)
