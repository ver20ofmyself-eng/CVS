<template>
  <div class="history-view">
    <div class="container">
      <!-- Заголовок -->
      <div class="page-header">
        <h1 class="page-title">История анализов</h1>
        
        <!-- Кнопки экспорта -->
        <div class="export-buttons">
          <button 
            class="btn btn-secondary btn-small"
            @click="exportData('csv')"
            :disabled="!filteredAnalyses.length"
          >
            📥 CSV
          </button>
          <button 
            class="btn btn-secondary btn-small"
            @click="exportData('json')"
            :disabled="!filteredAnalyses.length"
          >
            📥 JSON
          </button>
        </div>
      </div>

      <!-- Панель фильтров -->
      <div class="filters-panel card">
        <div class="filters-grid">
          <!-- Поиск по тексту -->
          <div class="filter-group">
            <label class="filter-label">🔍 Поиск</label>
            <input
              v-model="filters.search"
              type="text"
              class="input"
              placeholder="Текст резюме..."
              @input="debouncedSearch"
            />
          </div>

          <!-- Фильтр по вакансии -->
          <div class="filter-group">
            <label class="filter-label">📋 Вакансия</label>
            <select v-model="filters.vacancyId" class="select">
              <option :value="null">Все вакансии</option>
              <option 
                v-for="vacancy in vacancies" 
                :key="vacancy.id" 
                :value="vacancy.id"
              >
                {{ vacancy.title }}
              </option>
            </select>
          </div>

          <!-- Фильтр по минимальной оценке -->
          <div class="filter-group">
            <label class="filter-label">⭐ Минимальная оценка</label>
            <select v-model="filters.minScore" class="select">
              <option :value="null">Любая</option>
              <option value="8">8 и выше</option>
              <option value="5">5 и выше</option>
              <option value="3">3 и выше</option>
            </select>
          </div>

          <!-- Фильтр по рекомендации -->
          <div class="filter-group">
            <label class="filter-label">📊 Рекомендация</label>
            <select v-model="filters.recommendation" class="select">
              <option :value="null">Все</option>
              <option value="Пригласить на интервью">✅ Пригласить</option>
              <option value="Рекомендуется к рассмотрению">👍 Рекомендуется</option>
              <option value="Рассмотреть с оговорками">🤔 С оговорками</option>
              <option value="Не рекомендуется">👎 Не рекомендуется</option>
              <option value="Не подходит">❌ Не подходит</option>
            </select>
          </div>

          <!-- Фильтр по режиму -->
          <div class="filter-group">
            <label class="filter-label">🤖 Режим</label>
            <select v-model="filters.mode" class="select">
              <option :value="null">Все</option>
              <option value="MOCK">🧪 MOCK</option>
              <option value="REAL">🔴 REAL</option>
            </select>
          </div>

          <!-- Период -->
          <div class="filter-group">
            <label class="filter-label">📅 Период</label>
            <select v-model="filters.period" class="select" @change="applyPeriodFilter">
              <option value="all">За всё время</option>
              <option value="today">Сегодня</option>
              <option value="week">Последние 7 дней</option>
              <option value="month">Последние 30 дней</option>
              <option value="custom">Свой период</option>
            </select>
          </div>

          <!-- Кастомные даты -->
          <div v-if="filters.period === 'custom'" class="filter-group full-width">
            <div class="date-range">
              <input
                v-model="filters.dateFrom"
                type="date"
                class="input"
                placeholder="С"
              />
              <span class="date-separator">—</span>
              <input
                v-model="filters.dateTo"
                type="date"
                class="input"
                placeholder="По"
              />
            </div>
          </div>
        </div>

        <!-- Кнопки управления фильтрами -->
        <div class="filters-actions">
          <button class="btn btn-text" @click="resetFilters">
            🧹 Сбросить фильтры
          </button>
          <span class="results-count">
            Найдено: {{ filteredAnalyses.length }}
          </span>
        </div>
      </div>

      <!-- Статистика (сводка) -->
      <div class="stats-summary card" v-if="filteredAnalyses.length">
        <div class="stats-summary-grid">
          <div class="stat-item">
            <span class="stat-value">{{ statsSummary.total }}</span>
            <span class="stat-label">Всего</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ statsSummary.averageScore.toFixed(1) }}</span>
            <span class="stat-label">Средняя оценка</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ statsSummary.invitationRate }}%</span>
            <span class="stat-label">Приглашений</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ statsSummary.uniqueVacancies }}</span>
            <span class="stat-label">Вакансий</span>
          </div>
        </div>
      </div>

      <!-- Состояние загрузки -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка истории анализов...</p>
      </div>

      <!-- Ошибка -->
      <div v-else-if="error" class="error-state">
        <span class="error-icon">❌</span>
        <p>{{ error }}</p>
        <button class="btn btn-primary" @click="loadHistory">Повторить</button>
      </div>

      <!-- Список анализов -->
      <div v-else-if="filteredAnalyses.length" class="analyses-list">
        <div 
          v-for="analysis in paginatedAnalyses" 
          :key="analysis.id"
          class="analysis-card"
          @click="goToAnalysis(analysis.id)"
        >
          <!-- Верхняя часть карточки -->
          <div class="analysis-header">
            <div class="analysis-title">
              <h3>{{ analysis.analysis_title || analysis.vacancy_title || 'Анализ #' + analysis.id }}</h3>
              <span class="analysis-vacancy-tag" v-if="analysis.vacancy_title">📋 {{ analysis.vacancy_title }}</span>
            </div>
            <div class="analysis-score" :class="getScoreClass(analysis.score)">
              {{ analysis.score }}%
            </div>
          </div>

          <!-- Основная информация -->
          <div class="analysis-body">
            <!-- Превью резюме -->
            <p class="analysis-preview">{{ analysis.cv_text_preview }}</p>

            <!-- Навыки (если есть) -->
            <div class="analysis-skills" v-if="analysis.matched_skills?.length">
              <span class="skills-label">✅ Совпало:</span>
              <div class="skills-tags">
                <span 
                  v-for="skill in analysis.matched_skills.slice(0, 5)" 
                  :key="skill"
                  class="skill-tag matched"
                >
                  {{ skill }}
                </span>
                <span 
                  v-if="analysis.matched_skills.length > 5" 
                  class="skill-tag more"
                >
                  +{{ analysis.matched_skills.length - 5 }}
                </span>
              </div>
            </div>

            <div class="analysis-skills" v-if="analysis.missing_skills?.length">
              <span class="skills-label">❌ Отсутствует:</span>
              <div class="skills-tags">
                <span 
                  v-for="skill in analysis.missing_skills.slice(0, 3)" 
                  :key="skill"
                  class="skill-tag missing"
                >
                  {{ skill }}
                </span>
                <span 
                  v-if="analysis.missing_skills.length > 3" 
                  class="skill-tag more"
                >
                  +{{ analysis.missing_skills.length - 3 }}
                </span>
              </div>
            </div>

            <!-- Детали (опыт, локация, зарплата) -->
            <div class="analysis-details">
              <span v-if="analysis.experience_years" class="detail">
                🕒 {{ analysis.experience_years }} лет
              </span>
              <span v-if="analysis.location_match" class="detail" :class="locationMatchClass(analysis.location_match)">
                📍 {{ formatLocationMatch(analysis.location_match) }}
              </span>
              <span v-if="analysis.salary_match" class="detail" :class="salaryMatchClass(analysis.salary_match)">
                💰 {{ formatSalaryMatch(analysis.salary_match) }}
              </span>
            </div>
          </div>

          <!-- Нижняя часть карточки -->
          <div class="analysis-footer">
            <div class="analysis-meta">
              <span class="meta-item" :title="formatFullDate(analysis.created_at)">
                🕐 {{ formatDate(analysis.created_at) }}
              </span>
              <span class="meta-item">
                🤖 {{ analysis.mode }}
              </span>
              <span class="meta-item" v-if="analysis.prompt_used">
                📝 {{ analysis.prompt_used }}
              </span>
            </div>
            
            <div class="analysis-recommendation" :class="recommendationClass(analysis.recommendation)">
              {{ analysis.recommendation || 'Не определено' }}
            </div>
          </div>
        </div>

        <!-- Пагинация -->
        <div class="pagination" v-if="totalPages > 1">
          <button 
            class="pagination-btn"
            :disabled="currentPage === 1"
            @click="changePage(currentPage - 1)"
          >
            ←
          </button>
          
          <span class="pagination-info">
            {{ currentPage }} из {{ totalPages }}
          </span>
          
          <button 
            class="pagination-btn"
            :disabled="currentPage === totalPages"
            @click="changePage(currentPage + 1)"
          >
            →
          </button>
        </div>
      </div>

      <!-- Пустое состояние -->
      <div v-else class="empty-state">
        <div class="empty-icon">📭</div>
        <h3>Нет анализов</h3>
        <p v-if="hasActiveFilters">
          Попробуйте изменить параметры фильтрации
        </p>
        <p v-else>
          Начните анализировать резюме с помощью расширения
        </p>
        <button v-if="hasActiveFilters" class="btn btn-secondary" @click="resetFilters">
          Сбросить фильтры
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onActivated, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useVacanciesStore } from '@/stores/vacancies'
import { useToast } from '@/composables/useToast'
import api from '@/services/api'
import { format as dateFmt, formatDistance, subDays, startOfDay, endOfDay } from 'date-fns'
import { ru } from 'date-fns/locale'

const router = useRouter()
const vacanciesStore = useVacanciesStore()
const toast = useToast()

// Состояние
const analyses = ref([])
const loading = ref(true)
const error = ref(null)

// Пагинация
const currentPage = ref(1)
const pageSize = ref(20)

// Фильтры
const filters = reactive({
  search: '',
  vacancyId: null,
  minScore: null,
  recommendation: null,
  mode: null,
  period: 'all',
  dateFrom: null,
  dateTo: null
})

// Загруженные вакансии для фильтра
const vacancies = computed(() => vacanciesStore.vacancies)

// Debounced поиск
let searchTimeout
const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
  }, 300)
}

// Применение фильтра периода
const applyPeriodFilter = () => {
  const today = new Date()
  
  switch (filters.period) {
    case 'today':
      filters.dateFrom = dateFmt(startOfDay(today), 'yyyy-MM-dd')
      filters.dateTo = dateFmt(endOfDay(today), 'yyyy-MM-dd')
      break
    case 'week':
      filters.dateFrom = dateFmt(subDays(today, 7), 'yyyy-MM-dd')
      filters.dateTo = dateFmt(today, 'yyyy-MM-dd')
      break
    case 'month':
      filters.dateFrom = dateFmt(subDays(today, 30), 'yyyy-MM-dd')
      filters.dateTo = dateFmt(today, 'yyyy-MM-dd')
      break
    case 'custom':
      // Оставляем текущие значения
      break
    default:
      filters.dateFrom = null
      filters.dateTo = null
  }
  
  currentPage.value = 1
}

// Фильтрованные анализы
const filteredAnalyses = computed(() => {
  return analyses.value.filter(a => {
    // Поиск по тексту
    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      const textMatch = 
        a.cv_text_preview?.toLowerCase().includes(searchLower) ||
        a.vacancy_title?.toLowerCase().includes(searchLower)
      if (!textMatch) return false
    }
    
    // По вакансии
    if (filters.vacancyId && a.vacancy_id !== filters.vacancyId) {
      return false
    }
    
    // По минимальной оценке
    if (filters.minScore && (a.score || 0) < parseInt(filters.minScore)) {
      return false
    }
    
    // По рекомендации
    if (filters.recommendation && a.recommendation !== filters.recommendation) {
      return false
    }
    
    // По режиму
    if (filters.mode && a.mode !== filters.mode) {
      return false
    }
    
    // По дате
    if (filters.dateFrom) {
      const analysisDate = new Date(a.created_at)
      const fromDate = new Date(filters.dateFrom)
      if (analysisDate < fromDate) return false
    }
    
    if (filters.dateTo) {
      const analysisDate = new Date(a.created_at)
      const toDate = new Date(filters.dateTo)
      toDate.setHours(23, 59, 59, 999)
      if (analysisDate > toDate) return false
    }
    
    return true
  })
})

// Статистика по отфильтрованным
const statsSummary = computed(() => {
  const filtered = filteredAnalyses.value
  
  if (!filtered.length) {
    return {
      total: 0,
      averageScore: 0,
      invitationRate: 0,
      uniqueVacancies: 0
    }
  }
  
  const total = filtered.length
  const avgScore = filtered.reduce((sum, a) => sum + (a.score || 0), 0) / total
  const invitations = filtered.filter(a => 
    a.recommendation?.includes('Пригласить')
  ).length
  const uniqueVacancies = new Set(filtered.map(a => a.vacancy_id).filter(Boolean)).size
  
  return {
    total,
    averageScore: avgScore,
    invitationRate: Math.round((invitations / total) * 100),
    uniqueVacancies
  }
})

// Пагинированные анализы
const paginatedAnalyses = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredAnalyses.value.slice(start, end)
})

// Общее количество страниц
const totalPages = computed(() => 
  Math.ceil(filteredAnalyses.value.length / pageSize.value)
)

// Есть ли активные фильтры
const hasActiveFilters = computed(() => {
  return (
    filters.search ||
    filters.vacancyId ||
    filters.minScore ||
    filters.recommendation ||
    filters.mode ||
    filters.period !== 'all'
  )
})

// Загрузка истории
const loadHistory = async () => {
  loading.value = true
  error.value = null
  
  try {
    const response = await api.get('/analyze/history', {
      params: {
        limit: 1000 // Загружаем много, фильтруем на клиенте
      }
    })
    
    analyses.value = response.data
    
    // Если в URL есть параметр vacancy, применяем фильтр
    const urlParams = new URLSearchParams(window.location.search)
    const vacancyParam = urlParams.get('vacancy')
    if (vacancyParam) {
      filters.vacancyId = parseInt(vacancyParam)
    }
    
  } catch (err) {
    console.error('Ошибка загрузки истории:', err)
    error.value = 'Не удалось загрузить историю анализов'
  } finally {
    loading.value = false
  }
}

// Загрузка вакансий для фильтра
const loadVacancies = async () => {
  await vacanciesStore.fetchVacancies({ limit: 100 })
}

// Сброс фильтров
const resetFilters = () => {
  filters.search = ''
  filters.vacancyId = null
  filters.minScore = null
  filters.recommendation = null
  filters.mode = null
  filters.period = 'all'
  filters.dateFrom = null
  filters.dateTo = null
  currentPage.value = 1
}

// Смена страницы
const changePage = (page) => {
  currentPage.value = page
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Переход к детальному просмотру
const goToAnalysis = (id) => {
  router.push(`/history/${id}`)
}

// Экспорт данных
const exportData = async (exportFormat) => {
  try {
    const response = await api.get('/analyze/export', {
      params: { export_format: exportFormat },
      responseType: exportFormat === 'csv' ? 'text' : 'json'
    })
    
    let content, filename, type
    
    if (exportFormat === 'csv') {
      content = response.data
      filename = `analyses_${dateFmt(new Date(), 'yyyyMMdd_HHmm')}.csv`
      type = 'text/csv'
    } else {
      content = JSON.stringify(response.data, null, 2)
      filename = `analyses_${dateFmt(new Date(), 'yyyyMMdd_HHmm')}.json`
      type = 'application/json'
    }
    
    const blob = new Blob([content], { type })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
    toast.success(`Экспорт в ${exportFormat.toUpperCase()} завершён`)
    
  } catch (err) {
    console.error('Ошибка экспорта:', err)
    toast.error('Не удалось экспортировать данные')
  }
}

// Форматирование дат
const formatDate = (dateString) => {
  if (!dateString) return ''
  return formatDistance(new Date(dateString), new Date(), {
    addSuffix: true,
    locale: ru
  })
}

const formatFullDate = (dateString) => {
  if (!dateString) return ''
  return dateFmt(new Date(dateString), 'dd.MM.yyyy HH:mm', { locale: ru })
}

// Классы для оценок
const getScoreClass = (score) => {
  if (score >= 85) return 'score-high'
  if (score >= 50) return 'score-medium'
  return 'score-low'
}

// Класс для рекомендации
const recommendationClass = (rec) => {
  if (!rec) return ''
  if (rec.includes('Пригласить')) return 'rec-invite'
  if (rec.includes('Рассмотреть')) return 'rec-consider'
  return 'rec-reject'
}

// Классы для локации
const locationMatchClass = (match) => {
  if (match === 'yes') return 'match-yes'
  if (match === 'no') return 'match-no'
  return 'match-unknown'
}

// Классы для зарплаты
const salaryMatchClass = (match) => {
  if (match === 'match') return 'match-yes'
  if (match === 'above' || match === 'below') return 'match-partial'
  return 'match-unknown'
}

// Форматирование локации
const formatLocationMatch = (match) => {
  if (match === 'yes') return 'Соответствует'
  if (match === 'no') return 'Не соответствует'
  return 'Не указано'
}

// Форматирование зарплаты
const formatSalaryMatch = (match) => {
  if (match === 'match') return 'Входит в вилку'
  if (match === 'above') return 'Выше ожиданий'
  if (match === 'below') return 'Ниже ожиданий'
  return 'Не указано'
}

// Следим за фильтрами для сброса страницы
watch(
  () => [filters.search, filters.vacancyId, filters.minScore, filters.recommendation, filters.mode, filters.dateFrom, filters.dateTo],
  () => {
    currentPage.value = 1
  }
)

// Загружаем при монтировании
onMounted(async () => {
  await loadVacancies()
  await loadHistory()
})

// Перезагружаем историю каждый раз при возврате на страницу (keep-alive)
onActivated(async () => {
  await loadHistory()
})
</script>

<style scoped>
.history-view {
  padding: var(--spacing) 0;
  min-height: calc(100vh - 140px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing);
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.page-title {
  font-size: 32px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.export-buttons {
  display: flex;
  gap: var(--spacing-xxs);
}

/* Панель фильтров */
.filters-panel {
  margin-bottom: var(--spacing);
  padding: var(--spacing);
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xxs);
}

.filter-group.full-width {
  grid-column: 1 / -1;
}

.filter-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-light);
  margin-left: 4px;
}

.date-range {
  display: flex;
  align-items: center;
  gap: var(--spacing-xxs);
}

.date-separator {
  color: var(--color-text-muted);
  font-size: 14px;
}

.filters-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--spacing-xs);
  border-top: 1px solid var(--color-border);
}

.results-count {
  font-size: 14px;
  color: var(--color-text-muted);
}

/* Статистика */
.stats-summary {
  margin-bottom: var(--spacing);
  padding: var(--spacing);
}

.stats-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing);
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 28px;
  font-weight: 700;
  color: var(--color-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-muted);
}

/* Карточки анализов */
.analyses-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing);
}

.analysis-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  transition: var(--transition);
  cursor: pointer;
}

.analysis-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px var(--color-shadow);
  border-color: var(--color-primary);
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-sm);
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.analysis-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.analysis-title h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.analysis-vacancy-tag {
  font-size: 12px;
  color: var(--color-primary-dark);
  background: var(--color-primary-soft);
  padding: 3px 10px;
  border-radius: var(--border-radius-pill);
  border: 1px solid rgba(16, 106, 183, 0.2);
  white-space: nowrap;
  font-weight: 500;
}

.analysis-score {
  font-size: 24px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: var(--border-radius-pill);
  color: white;
}

.score-high {
  background: #10b981;
}

.score-medium {
  background: #fbbf24;
  color: #1e293b;
}

.score-low {
  background: #ef4444;
}

.analysis-body {
  margin-bottom: var(--spacing-sm);
}

.analysis-preview {
  font-size: 14px;
  color: var(--color-text);
  line-height: 1.5;
  margin-bottom: var(--spacing-xs);
  padding-bottom: var(--spacing-xs);
  border-bottom: 1px solid var(--color-border);
}

.analysis-skills {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-xs);
  flex-wrap: wrap;
}

.skills-label {
  font-size: 12px;
  color: var(--color-text-muted);
  min-width: 70px;
}

.skills-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  flex: 1;
}

.skill-tag {
  padding: 2px 8px;
  border-radius: var(--border-radius-pill);
  font-size: 11px;
  font-weight: 500;
}

.skill-tag.matched {
  background: var(--color-success);
  color: var(--color-success-text);
}

.skill-tag.missing {
  background: var(--color-warning);
  color: var(--color-warning-text);
}

.skill-tag.more {
  background: var(--color-surface-darker);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}

.analysis-details {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  margin-top: var(--spacing-xs);
}

.detail {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: var(--border-radius-pill);
  background: var(--color-surface-darker);
  border: 1px solid var(--color-border);
}

.match-yes {
  color: #10b981;
}

.match-no {
  color: #ef4444;
}

.match-partial {
  color: #fbbf24;
}

.match-unknown {
  color: var(--color-text-muted);
}

.analysis-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--spacing-xs);
  border-top: 1px solid var(--color-border);
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.analysis-meta {
  display: flex;
  gap: var(--spacing-xs);
  font-size: 11px;
  color: var(--color-text-muted);
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 2px;
}

.analysis-recommendation {
  font-size: 13px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: var(--border-radius-pill);
}

.rec-invite {
  background: var(--color-success);
  color: var(--color-success-text);
}

.rec-consider {
  background: #fef3c7;
  color: #92400e;
}

.rec-reject {
  background: var(--color-warning);
  color: var(--color-warning-text);
}

/* Пагинация */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--spacing);
  margin-top: var(--spacing);
}

.pagination-btn {
  width: 40px;
  height: 40px;
  border: 2px solid var(--color-border);
  border-radius: 50%;
  background: var(--color-surface);
  cursor: pointer;
  transition: var(--transition);
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pagination-btn:hover:not(:disabled) {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
  transform: scale(1.1);
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-info {
  font-size: 14px;
  color: var(--color-text-muted);
}

/* Загрузка и ошибки */
.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: calc(var(--spacing) * 2);
  background: var(--color-surface);
  border-radius: var(--border-radius);
  border: 1px solid var(--color-border);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border);
  border-top: 3px solid var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto var(--spacing-sm);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  font-size: 48px;
  margin-bottom: var(--spacing-sm);
  display: block;
}

.error-state p {
  color: var(--color-error-text);
  margin-bottom: var(--spacing);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: var(--spacing);
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 20px;
  margin-bottom: var(--spacing-xs);
}

.empty-state p {
  color: var(--color-text-muted);
  margin-bottom: var(--spacing);
}

/* Адаптивность */
@media (max-width: 768px) {
  .stats-summary-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .analysis-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .analysis-footer {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .filters-grid {
    grid-template-columns: 1fr;
  }
  
  .date-range {
    flex-direction: column;
  }
  
  .date-separator {
    display: none;
  }
}
</style>
