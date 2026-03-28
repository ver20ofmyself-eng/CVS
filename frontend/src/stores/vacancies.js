import { defineStore } from 'pinia'
import api from '@/services/api'

export const useVacanciesStore = defineStore('vacancies', {
  state: () => ({
    vacancies: [],
    currentVacancy: null,
    loading: false,
    error: null,
    pagination: { total: 0, skip: 0, limit: 50 }
  }),

  getters: {
    activeVacancies:    (s) => s.vacancies.filter(v => v.status === 'active'),
    completedVacancies: (s) => s.vacancies.filter(v => v.status === 'completed'),
    archivedVacancies:  (s) => s.vacancies.filter(v => v.status === 'archived'),
    totalActive:        (s) => s.vacancies.filter(v => v.status === 'active').length,
    getVacancyById:     (s) => (id) => s.vacancies.find(v => v.id === id),
  },

  actions: {
    async fetchVacancies(params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await api.get('/vacancies/', {
          params: {
            skip: params.skip || 0,
            limit: params.limit || 50,
            status: params.status || undefined,
            active_only: params.activeOnly || false,
            search: params.search || undefined,
            client: params.client || undefined,
          }
        })
        this.vacancies = response.data.items
        this.pagination.total = response.data.total
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Ошибка загрузки вакансий'
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchVacancy(id) {
      this.loading = true
      this.error = null
      try {
        const { data } = await api.get(`/vacancies/${id}`)
        this.currentVacancy = data
        return data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Ошибка загрузки вакансии'
        throw error
      } finally {
        this.loading = false
      }
    },

    async createVacancy(data) {
      this.loading = true
      this.error = null
      try {
        const response = await api.post('/vacancies/', data)
        await this.fetchVacancies()
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Ошибка создания'
        throw error
      } finally { this.loading = false }
    },

    async updateVacancy(id, data) {
      this.loading = true
      this.error = null
      try {
        const response = await api.put(`/vacancies/${id}`, data)
        await this.fetchVacancies()
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Ошибка обновления'
        throw error
      } finally { this.loading = false }
    },

    async deleteVacancy(id) {
      this.loading = true
      try {
        await api.delete(`/vacancies/${id}`)
        await this.fetchVacancies()
        return true
      } catch (error) {
        this.error = error.response?.data?.detail || 'Ошибка удаления'
        throw error
      } finally { this.loading = false }
    },

    async cloneVacancy(id) {
      this.loading = true
      try {
        const response = await api.post(`/vacancies/${id}/clone`)
        await this.fetchVacancies()
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Ошибка клонирования'
        throw error
      } finally { this.loading = false }
    },

    async completeVacancy(id) {
      this.loading = true
      try {
        const response = await api.post(`/vacancies/${id}/complete`)
        await this.fetchVacancies()
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Ошибка завершения'
        throw error
      } finally { this.loading = false }
    },

    async reopenVacancy(id) {
      this.loading = true
      try {
        const response = await api.post(`/vacancies/${id}/reopen`)
        await this.fetchVacancies()
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Ошибка возобновления'
        throw error
      } finally { this.loading = false }
    },
  }
})
