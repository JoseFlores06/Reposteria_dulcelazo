import api from './axios'

export const getGastosMarketing = () => api.get('/gastos-marketing').then(r => r.data)
export const getCanalesMarketing = () => api.get('/gastos-marketing/canales').then(r => r.data)
export const crearGastoMarketing = (data) => api.post('/gastos-marketing', data).then(r => r.data)
export const actualizarGastoMarketing = (id, data) => api.patch(`/gastos-marketing/${id}`, data).then(r => r.data)
export const eliminarGastoMarketing = (id) => api.delete(`/gastos-marketing/${id}`).then(r => r.data)
