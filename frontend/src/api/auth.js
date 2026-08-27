import axios from 'axios'
import api from './axios'

export const login = async (correo, password) => {
  const formData = new URLSearchParams()
  formData.append('username', correo)
  formData.append('password', password)
  const res = await axios.post('/api/auth/login', formData.toString(), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return res.data
}

export const getMe = () => api.get('/auth/me').then(r => r.data)
export const getUsuarios = () => api.get('/auth/usuarios').then(r => r.data)
export const crearUsuario = (data) => api.post('/auth/usuarios', data).then(r => r.data)
export const actualizarUsuario = (id, data) => api.put(`/auth/usuarios/${id}`, data).then(r => r.data)
