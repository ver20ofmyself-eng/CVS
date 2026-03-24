import { defineStore } from 'pinia'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user:    null,
    token:   localStorage.getItem('token') || null,
    loading: false,
    error:   null
  }),

  getters: {
    isAuthenticated: s => !!s.token,
    isAdmin:         s => s.user?.is_admin || false,
    userName:        s => s.user?.full_name || s.user?.email || 'Пользователь'
  },

  actions: {
    async login(email, password) {
      this.loading = true
      this.error   = null
      try {
        const form = new URLSearchParams()
        form.append('username', email)
        form.append('password', password)

        const { data } = await api.post('/auth/login', form, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })

        this.token = data.access_token
        localStorage.setItem('token', this.token)
        await this.fetchUser()
        return true
      } catch (err) {
        this.error = err.response?.data?.detail || 'Ошибка входа'
        return false
      } finally {
        this.loading = false
      }
    },

    async register(userData) {
      this.loading = true
      this.error   = null
      try {
        const { data } = await api.post('/auth/register', userData)
        this.token = data.access_token
        localStorage.setItem('token', this.token)
        await this.fetchUser()
        return true
      } catch (err) {
        this.error = err.response?.data?.detail || 'Ошибка регистрации'
        return false
      } finally {
        this.loading = false
      }
    },

    async fetchUser() {
      if (!this.token) return
      try {
        const { data } = await api.get('/auth/me')
        this.user = data
      } catch {
        this.logout()
      }
    },

    async logout() {
      try { await api.post('/auth/logout') } catch { /* ignore */ }
      this.user  = null
      this.token = null
      localStorage.removeItem('token')
    }
  }
})
