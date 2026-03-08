import axios from 'axios'

const api = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json'
    }
})

// Интерсептор для добавления токена
api.interceptors.request.use(
    config => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        console.log('🌐 Request:', config.method.toUpperCase(), config.url)
        return config
    },
    error => Promise.reject(error)
)

// Интерсептор для обработки ошибок
api.interceptors.response.use(
    response => {
        console.log('✅ Response:', response.status, response.config.url)
        return response
    },
    error => {
        console.error('❌ API Error:', {
            url: error.config?.url,
            status: error.response?.status,
            data: error.response?.data
        })
        if (error.response?.status === 401) {
            localStorage.removeItem('token')
        }
        return Promise.reject(error)
    }
)

export default api
