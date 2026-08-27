import api from './axios'

export const getEstadoCalendario = () => api.get('/calendario/estado').then(r => r.data)
export const getAuthUrl = () => api.get('/calendario/auth-url').then(r => r.data)
export const desconectarCalendario = () => api.delete('/calendario/desconectar').then(r => r.data)
export const getEventos = () => api.get('/calendario/eventos').then(r => r.data)
