import { defineStore } from 'pinia'
import api from '@/services/api'

export const useVacanciesStore = defineStore('vacancies', {
    state: () => ({
        vacancies: [],
        currentVacancy: null,
        loading: false,
        error: null,
        pagination: {
            total: 0,
            skip: 0,
            limit: 20
        }
    }),

    getters: {
        activeVacancies: (state) => state.vacancies.filter(v => v.is_active),
        totalActive: (state) => state.vacancies.filter(v => v.is_active).length,
        getVacancyById: (state) => (id) => state.vacancies.find(v => v.id === id)
    },

    actions: {
        // Загрузить список вакансий
        async fetchVacancies(params = {}) {
            this.loading = true
            this.error = null

            try {
                const response = await api.get('/vacancies/', {
                    params: {
                        skip: params.skip || 0,
                        limit: params.limit || 20,
                        active_only: params.activeOnly !== false,
                        search: params.search || ''
                    }
                })

                this.vacancies = response.data.items
                this.pagination.total = response.data.total
                this.pagination.skip = params.skip || 0
                this.pagination.limit = params.limit || 20

                return response.data
            } catch (error) {
                this.error = error.response?.data?.detail || 'Ошибка загрузки вакансий'
                throw error
            } finally {
                this.loading = false
            }
        },

        // Загрузить одну вакансию
        async fetchVacancy(id) {
            this.loading = true
            this.error = null

            try {
                const response = await api.get(`/vacancies/${id}`)
                this.currentVacancy = response.data
                return response.data
            } catch (error) {
                this.error = error.response?.data?.detail || 'Ошибка загрузки вакансии'
                throw error
            } finally {
                this.loading = false
            }
        },

        // Создать вакансию
        async createVacancy(vacancyData) {
            this.loading = true
            this.error = null

            try {
                const response = await api.post('/vacancies/', vacancyData)
                await this.fetchVacancies()
                return response.data
            } catch (error) {
                this.error = error.response?.data?.detail || 'Ошибка создания вакансии'
                throw error
            } finally {
                this.loading = false
            }
        },

        // Обновить вакансию
        async updateVacancy(id, vacancyData) {
            this.loading = true
            this.error = null

            try {
                const response = await api.put(`/vacancies/${id}`, vacancyData)
                await this.fetchVacancies()
                return response.data
            } catch (error) {
                this.error = error.response?.data?.detail || 'Ошибка обновления вакансии'
                throw error
            } finally {
                this.loading = false
            }
        },

        // Мягкое удаление (деактивация)
        async deleteVacancy(id) {
            this.loading = true
            this.error = null

            try {
                await api.delete(`/vacancies/${id}`)
                await this.fetchVacancies()
                return true
            } catch (error) {
                this.error = error.response?.data?.detail || 'Ошибка удаления вакансии'
                throw error
            } finally {
                this.loading = false
            }
        },

        // Клонировать вакансию
        async cloneVacancy(id) {
            this.loading = true
            this.error = null

            try {
                const response = await api.post(`/vacancies/${id}/clone`)
                await this.fetchVacancies()
                return response.data
            } catch (error) {
                this.error = error.response?.data?.detail || 'Ошибка клонирования вакансии'
                throw error
            } finally {
                this.loading = false
            }
        }
    }
})
