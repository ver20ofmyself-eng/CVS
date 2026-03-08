import { defineStore } from 'pinia'
import api from '../services/api'

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: null,
        token: localStorage.getItem('token'),
        loading: false,
        error: null
    }),

    getters: {
        isAuthenticated: (state) => !!state.token,
        isAdmin: (state) => state.user?.is_admin || false,
        userName: (state) => state.user?.full_name || state.user?.email || 'Пользователь'
    },

    actions: {
        async login(email, password) {
            this.loading = true
            this.error = null

            try {
                const formData = new URLSearchParams()
                formData.append('username', email)
                formData.append('password', password)

                const response = await api.post('/auth/login', formData, {
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
                })

                this.token = response.data.access_token
                localStorage.setItem('token', this.token)

                await this.fetchUser()

                return true
            } catch (error) {
                this.error = error.response?.data?.detail || 'Ошибка входа'
                return false
            } finally {
                this.loading = false
            }
        },

        async register(userData) {
            this.loading = true
            this.error = null

            try {
                const response = await api.post('/auth/register', userData)

                this.token = response.data.access_token
                localStorage.setItem('token', this.token)

                await this.fetchUser()

                return true
            } catch (error) {
                this.error = error.response?.data?.detail || 'Ошибка регистрации'
                return false
            } finally {
                this.loading = false
            }
        },

        async fetchUser() {
            if (!this.token) return

            try {
                const response = await api.get('/auth/me')
                this.user = response.data
            } catch (error) {
                console.error('Ошибка загрузки пользователя:', error)
                this.logout()
            }
        },

        async logout() {
            try {
                // Опционально: уведомляем бэкенд о выходе
                await api.post('/auth/logout').catch(() => { })
            } finally {
                this.user = null
                this.token = null
                localStorage.removeItem('token')
            }
        }
    }
})
