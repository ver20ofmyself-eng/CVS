import axios from 'axios'
import router from '@/router'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' }
})

// ── Request interceptor — добавляем Bearer токен ───────────────────────────────
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  error => Promise.reject(error)
)

// ── Response interceptor — единая обработка ошибок ────────────────────────────
api.interceptors.response.use(
  response => response,
  error => {
    const status = error.response?.status

    if (status === 401) {
      // Токен истёк или невалиден
      localStorage.removeItem('token')
      router.push({ name: 'login' }).catch(() => {})
    }

    return Promise.reject(error)
  }
)

export default api
