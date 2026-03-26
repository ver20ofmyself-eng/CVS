<template>
  <div class="analysis-detail-view">
    <div class="container">
      <!-- Хлебные крошки -->
      <div class="breadcrumbs">
        <router-link to="/history" class="breadcrumb-link">
          ← К истории анализов
        </router-link>
      </div>

      <!-- Состояние загрузки -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка анализа...</p>
      </div>

      <!-- Ошибка -->
      <div v-else-if="error" class="error-state">
        <span class="error-icon">❌</span>
        <p>{{ error }}</p>
        <button class="btn btn-primary" @click="loadAnalysis">Повторить</button>
        <router-link to="/history" class="btn btn-secondary">
          К истории
        </router-link>
      </div>

      <!-- Контент -->
      <template v-else-if="analysis">
        <!-- Шапка с действиями -->
        <div class="detail-header">
          <div class="title-section">
            <h1 class="page-title">{{ analysis.analysis_title || ('Анализ #' + analysis.id) }}</h1>
            <span class="analysis-mode" :class="modeClass">
              {{ analysis.mode }}
            </span>
          </div>

          <div class="header-actions">
            <button 
              class="action-btn copy"
              @click="copyShareLink"
              title="Копировать ссылку"
            >
              🔗
            </button>
            <button 
              class="action-btn export"
              @click="exportAnalysis"
              title="Экспортировать"
            >
              📥
            </button>
            <button 
              class="action-btn delete"
              @click="handleDelete"
              title="Удалить"
            >
              🗑️
            </button>
          </div>
        </div>

        <!-- Ссылки: вакансия (слева) + резюме кандидата (справа) -->
        <div class="analysis-links-row">
          <router-link
            v-if="analysis.vacancy_id"
            :to="`/vacancies/${analysis.vacancy_id}`"
            class="vacancy-link-content"
          >
            <span class="link-icon">📋</span>
            {{ analysis.vacancy_title || 'Вакансия' }}
            <span class="link-arrow">→</span>
          </router-link>
          <span v-else class="vacancy-link-placeholder"></span>

          <a
            v-if="analysis.source_url"
            :href="analysis.source_url"
            target="_blank"
            rel="noopener noreferrer"
            class="source-link-content"
          >
            <span class="link-icon">📄</span>
            Резюме кандидата
            <span class="link-arrow">↗</span>
          </a>
        </div>

        <!-- Основная информация (сетка) -->
        <div class="info-grid">
          <!-- Левая колонка - Оценка и рекомендация -->
          <div class="info-card score-card">
            <div class="score-display">
              <div class="score-circle" :class="scoreCircleClass">
                <span class="score-value">{{ analysis.score }}/10</span>
              </div>
              <div class="recommendation" :class="recommendationClass">
                {{ analysis.recommendation || 'Не определено' }}
              </div>
            </div>

            <div class="quick-stats">
              <div class="stat-item">
                <span class="stat-label">Опыт</span>
                <span class="stat-value">{{ analysis.experience_years || '?' }} лет</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Локация</span>
                <span class="stat-value" :class="locationMatchClass">
                  {{ formatLocationMatch(analysis.location_match) }}
                </span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Зарплата</span>
                <span class="stat-value" :class="salaryMatchClass">
                  {{ formatSalaryMatch(analysis.salary_match) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Правая колонка - Метаданные -->
          <div class="info-card metadata-card">
            <h3 class="card-title">📊 Метаданные</h3>
            <div class="metadata-grid">
              <div class="metadata-item">
                <span class="metadata-label">Дата анализа:</span>
                <span class="metadata-value">{{ formatFullDate(analysis.created_at) }}</span>
              </div>
              <div class="metadata-item">
                <span class="metadata-label">Время обработки:</span>
                <span class="metadata-value">{{ analysis.processing_time?.toFixed(2) || '—' }} сек</span>
              </div>
              <div class="metadata-item">
                <span class="metadata-label">Использовано токенов:</span>
                <span class="metadata-value">{{ analysis.tokens_used || 0 }}</span>
              </div>
              <div class="metadata-item">
                <span class="metadata-label">Промпт:</span>
                <span class="metadata-value">{{ analysis.prompt_used || 'default' }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Навыки -->
        <div class="skills-section">
          <div class="skills-grid">
            <!-- Совпавшие навыки -->
            <div class="skills-card matched">
              <h3 class="card-title">
                <span class="title-icon">✅</span>
                Совпавшие навыки
                <span class="skill-count">{{ analysis.matched_skills?.length || 0 }}</span>
              </h3>
              <div class="skills-list">
                <span 
                  v-for="skill in analysis.matched_skills" 
                  :key="skill"
                  class="skill-tag matched"
                >
                  {{ skill }}
                </span>
                <span v-if="!analysis.matched_skills?.length" class="no-skills">
                  Нет совпавших навыков
                </span>
              </div>
            </div>

            <!-- Отсутствующие навыки -->
            <div class="skills-card missing">
              <h3 class="card-title">
                <span class="title-icon">❌</span>
                Отсутствующие навыки
                <span class="skill-count">{{ analysis.missing_skills?.length || 0 }}</span>
              </h3>
              <div class="skills-list">
                <span 
                  v-for="skill in analysis.missing_skills" 
                  :key="skill"
                  class="skill-tag missing"
                >
                  {{ skill }}
                </span>
                <span v-if="!analysis.missing_skills?.length" class="no-skills">
                  Все необходимые навыки присутствуют
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Сильные и слабые стороны -->
        <div class="strengths-weaknesses" v-if="hasStrengthsOrWeaknesses">
          <div class="sw-grid">
            <div class="sw-card strengths" v-if="analysis.ai_response?.strengths?.length">
              <h3 class="card-title">
                <span class="title-icon">💪</span>
                Сильные стороны
              </h3>
              <ul class="sw-list">
                <li 
                  v-for="(item, index) in analysis.ai_response.strengths" 
                  :key="index"
                >
                  {{ item }}
                </li>
              </ul>
            </div>

            <div class="sw-card weaknesses" v-if="analysis.ai_response?.weaknesses?.length">
              <h3 class="card-title">
                <span class="title-icon">📉</span>
                Риски и слабые стороны
              </h3>
              <ul class="sw-list">
                <li 
                  v-for="(item, index) in analysis.ai_response.weaknesses" 
                  :key="index"
                >
                  {{ item }}
                </li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Сводка от AI -->
        <div class="summary-section" v-if="analysis.ai_response?.summary">
          <h3 class="section-title">📝 Сводка анализа</h3>
          <div class="summary-content">
            <p>{{ analysis.ai_response.summary }}</p>
          </div>
        </div>

        <!-- Сырой ответ AI (для разработчиков/продвинутых) -->
        <div class="raw-response-section">
          <div class="section-header" @click="showRawResponse = !showRawResponse">
            <h3 class="section-title">
              🔧 Сырой ответ AI
              <span class="toggle-icon">{{ showRawResponse ? '▼' : '▶' }}</span>
            </h3>
          </div>
          
          <div v-if="showRawResponse" class="raw-response-content">
            <pre>{{ JSON.stringify(analysis.ai_response, null, 2) }}</pre>
          </div>
        </div>

        <!-- Полный текст резюме -->
        <div class="cv-section">
          <h3 class="section-title">📄 Полный текст резюме</h3>
          <div class="cv-content">
            <pre>{{ analysis.cv_text }}</pre>
          </div>
        </div>

        <!-- Действия внизу -->
        <div class="bottom-actions">
          <button class="btn btn-secondary" @click="goBack">
            ← Назад к истории
          </button>
          <button 
            class="btn btn-primary" 
            @click="repeatAnalysis"
            :disabled="!canRepeat"
          >
            🔄 Повторить анализ
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import { useToast } from '@/composables/useToast'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'

const route = useRoute()
const router = useRouter()
const toast = useToast()

// Состояние
const analysis = ref(null)
const loading = ref(true)
const error = ref(null)
const showRawResponse = ref(false)

// Computed
const modeClass = computed(() => ({
  'mode-mock': analysis.value?.mode === 'MOCK',
  'mode-real': analysis.value?.mode === 'REAL'
}))

const scoreCircleClass = computed(() => {
  const score = analysis.value?.score || 0
  if (score >= 8) return 'score-high'
  if (score >= 5) return 'score-medium'
  return 'score-low'
})

const recommendationClass = computed(() => {
  const rec = analysis.value?.recommendation || ''
  if (rec.includes('Пригласить')) return 'rec-invite'
  if (rec.includes('Рассмотреть')) return 'rec-consider'
  return 'rec-reject'
})

const locationMatchClass = computed(() => {
  const match = analysis.value?.location_match
  if (match === 'yes') return 'match-yes'
  if (match === 'no') return 'match-no'
  return 'match-unknown'
})

const salaryMatchClass = computed(() => {
  const match = analysis.value?.salary_match
  if (match === 'match') return 'match-yes'
  if (match === 'above' || match === 'below') return 'match-partial'
  return 'match-unknown'
})

const hasStrengthsOrWeaknesses = computed(() => {
  const ai = analysis.value?.ai_response
  return ai?.strengths?.length || ai?.weaknesses?.length
})

const canRepeat = computed(() => {
  return analysis.value?.vacancy_id
})

// Загрузка анализа
const loadAnalysis = async () => {
  const analysisId = parseInt(route.params.id)
  
  if (isNaN(analysisId)) {
    error.value = 'Неверный ID анализа'
    loading.value = false
    return
  }

  loading.value = true
  error.value = null

  try {
    const response = await api.get(`/analyze/history/${analysisId}`)
    analysis.value = response.data
  } catch (err) {
    console.error('Ошибка загрузки анализа:', err)
    
    if (err.response?.status === 404) {
      error.value = 'Анализ не найден'
    } else {
      error.value = 'Не удалось загрузить анализ'
    }
  } finally {
    loading.value = false
  }
}

// Форматирование
const formatFullDate = (dateString) => {
  if (!dateString) return ''
  return format(new Date(dateString), 'dd.MM.yyyy HH:mm:ss', { locale: ru })
}

const formatLocationMatch = (match) => {
  if (match === 'yes') return '✅ Соответствует'
  if (match === 'no') return '❌ Не соответствует'
  return '❓ Не указано'
}

const formatSalaryMatch = (match) => {
  if (match === 'match') return '✅ Входит в вилку'
  if (match === 'above') return '⬆️ Выше ожиданий'
  if (match === 'below') return '⬇️ Ниже ожиданий'
  return '❓ Не указано'
}

// Действия
const goBack = () => {
  router.push('/history')
}

const repeatAnalysis = () => {
  if (!analysis.value?.vacancy_id) return
  toast.info('Откройте расширение на странице резюме и выберите эту вакансию для повторного анализа')
}

const copyShareLink = async () => {
  const url = window.location.href
  try {
    await navigator.clipboard.writeText(url)
    toast.success('Ссылка скопирована')
  } catch (err) {
    console.error('Ошибка копирования:', err)
    toast.error('Не удалось скопировать ссылку')
  }
}

const exportAnalysis = () => {
  if (!analysis.value) return
  
  const data = {
    ...analysis.value,
    exported_at: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `analysis_${analysis.value.id}_${format(new Date(), 'yyyyMMdd_HHmm')}.json`
  a.click()
  URL.revokeObjectURL(url)
}

const handleDelete = async () => {
  if (!confirm('Вы уверены, что хотите удалить этот анализ?')) return
  
  try {
    await api.delete(`/analyze/history/${analysis.value.id}`)
    toast.success('Анализ удалён')
    router.push('/history')
  } catch (err) {
    console.error('Ошибка удаления:', err)
    toast.error('Не удалось удалить анализ')
  }
}

// Загрузка при монтировании
onMounted(() => {
  loadAnalysis()
})
</script>

<style scoped>
.analysis-detail-view {
  padding: var(--spacing) 0;
  min-height: calc(100vh - 140px);
}

.breadcrumbs {
  margin-bottom: var(--spacing);
}

.breadcrumb-link {
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: 14px;
  transition: var(--transition);
  display: inline-flex;
  align-items: center;
}

.breadcrumb-link:hover {
  color: var(--color-primary);
}

/* Шапка */
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing);
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.title-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.analysis-mode {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: var(--border-radius-pill);
  font-weight: 500;
}

.mode-mock {
  background: var(--color-surface-darker);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}

.mode-real {
  background: #10b981;
  color: white;
}

.header-actions {
  display: flex;
  gap: var(--spacing-xxs);
}

.action-btn {
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

.action-btn:hover {
  transform: translateY(-2px);
}

.action-btn.copy:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.action-btn.export:hover {
  border-color: #10b981;
  background: #d1fae5;
}

.action-btn.delete:hover {
  border-color: #ef4444;
  background: #fee2e2;
}

/* Ссылка на вакансию */
/* Ряд ссылок: вакансия + резюме */
.analysis-links-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing);
  flex-wrap: wrap;
}

.vacancy-link-placeholder {
  flex: 1;
}

.vacancy-link-content {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xxs);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-primary-soft);
  border-radius: var(--border-radius-pill);
  color: var(--color-primary-dark);
  text-decoration: none;
  font-size: 14px;
  transition: var(--transition);
  font-weight: 500;
}

.vacancy-link-content:hover {
  background: var(--color-primary);
  color: white;
  transform: translateX(4px);
}

.source-link-content {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xxs);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-success);
  border-radius: var(--border-radius-pill);
  color: var(--color-success-text);
  text-decoration: none;
  font-size: 14px;
  transition: var(--transition);
  font-weight: 500;
  border: 1px solid var(--color-success-border);
}

.source-link-content:hover {
  background: #10b981;
  color: white;
  border-color: #059669;
  transform: translateX(-4px);
}

.link-icon {
  font-size: 16px;
}

.link-arrow {
  font-size: 16px;
}

/* Сетка */
.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing);
  margin-bottom: var(--spacing);
}

.info-card {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  border: 1px solid var(--color-border);
  transition: var(--transition);
}

.info-card:hover {
  box-shadow: 0 8px 30px var(--color-shadow);
}

/* Карточка с оценкой */
.score-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing);
}

.score-display {
  display: flex;
  align-items: center;
  gap: var(--spacing);
  flex-wrap: wrap;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: conic-gradient(from 0deg, var(--color-primary) 0deg, var(--color-border) 0deg);
  position: relative;
}

.score-circle::before {
  content: '';
  position: absolute;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: var(--color-surface);
}

.score-value {
  position: relative;
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text);
  z-index: 1;
}

.score-circle.score-high {
  background: conic-gradient(from 0deg, #10b981 0deg, #10b981 288deg, var(--color-border) 288deg);
}

.score-circle.score-medium {
  background: conic-gradient(from 0deg, #fbbf24 0deg, #fbbf24 180deg, var(--color-border) 180deg);
}

.score-circle.score-low {
  background: conic-gradient(from 0deg, #ef4444 0deg, #ef4444 144deg, var(--color-border) 144deg);
}

.recommendation {
  flex: 1;
  font-size: 18px;
  font-weight: 600;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-pill);
  text-align: center;
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

.quick-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-xs);
  padding-top: var(--spacing-xs);
  border-top: 1px solid var(--color-border);
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 11px;
  color: var(--color-text-muted);
  margin-bottom: 2px;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
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

/* Метаданные */
.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing-sm);
  display: flex;
  align-items: center;
  gap: var(--spacing-xxs);
}

.metadata-grid {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.metadata-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-xxs) 0;
  border-bottom: 1px solid var(--color-border);
}

.metadata-item:last-child {
  border-bottom: none;
}

.metadata-label {
  font-size: 13px;
  color: var(--color-text-muted);
}

.metadata-value {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text);
}

/* Навыки */
.skills-section {
  margin-bottom: var(--spacing);
}

.skills-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing);
}

.skills-card {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  border: 1px solid var(--color-border);
  transition: var(--transition);
}

.skills-card:hover {
  box-shadow: 0 8px 30px var(--color-shadow);
}

.skills-card.matched {
  border-left: 6px solid #10b981;
}

.skills-card.missing {
  border-left: 6px solid #ef4444;
}

.title-icon {
  font-size: 18px;
}

.skill-count {
  margin-left: auto;
  font-size: 12px;
  background: var(--color-surface-darker);
  padding: 2px 8px;
  border-radius: var(--border-radius-pill);
  color: var(--color-text-muted);
}

.skills-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 60px;
}

.skill-tag {
  padding: 6px 12px;
  border-radius: var(--border-radius-pill);
  font-size: 13px;
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

.no-skills {
  color: var(--color-text-muted);
  font-style: italic;
  font-size: 14px;
  padding: var(--spacing-xs);
}

/* Сильные и слабые стороны */
.strengths-weaknesses {
  margin-bottom: var(--spacing);
}

.sw-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing);
}

.sw-card {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  border: 1px solid var(--color-border);
  transition: var(--transition);
}

.sw-card:hover {
  box-shadow: 0 8px 30px var(--color-shadow);
}

.sw-card.strengths {
  border-left: 6px solid #10b981;
}

.sw-card.weaknesses {
  border-left: 6px solid #ef4444;
}

.sw-list {
  margin: 0;
  padding-left: 20px;
  color: var(--color-text);
  font-size: 14px;
  line-height: 1.6;
}

.sw-list li {
  margin-bottom: 8px;
}

.sw-list li::marker {
  color: var(--color-primary);
}

/* Сводка */
.summary-section {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  margin-bottom: var(--spacing);
  border: 1px solid var(--color-border);
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing-sm);
}

.summary-content {
  background: var(--color-surface-darker);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing);
  font-size: 15px;
  line-height: 1.6;
  color: var(--color-text);
  border-left: 4px solid var(--color-primary);
}

/* Сырой ответ */
.raw-response-section {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  margin-bottom: var(--spacing);
  border: 1px solid var(--color-border);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.toggle-icon {
  font-size: 14px;
  color: var(--color-text-muted);
  transition: var(--transition);
}

.section-header:hover .toggle-icon {
  color: var(--color-primary);
}

.raw-response-content {
  margin-top: var(--spacing);
  background: #1e1e1e;
  border-radius: var(--border-radius-sm);
  padding: var(--spacing);
  overflow-x: auto;
}

.raw-response-content pre {
  margin: 0;
  color: #d4d4d4;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  line-height: 1.5;
}

/* Текст резюме */
.cv-section {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  margin-bottom: var(--spacing);
  border: 1px solid var(--color-border);
}

.cv-content {
  background: var(--color-surface-darker);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing);
  max-height: 500px;
  overflow-y: auto;
}

.cv-content pre {
  margin: 0;
  font-family: 'Source Sans 3', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.cv-content::-webkit-scrollbar {
  width: 8px;
}

.cv-content::-webkit-scrollbar-track {
  background: var(--color-surface-darker);
  border-radius: 4px;
}

.cv-content::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 4px;
}

.cv-content::-webkit-scrollbar-thumb:hover {
  background: var(--color-primary);
}

/* Действия внизу */
.bottom-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--spacing);
}

/* Загрузка и ошибки */
.loading-state,
.error-state {
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

.error-state .btn {
  margin: 0 var(--spacing-xs);
}

/* Адаптивность */
@media (max-width: 768px) {
  .info-grid,
  .skills-grid,
  .sw-grid {
    grid-template-columns: 1fr;
  }
  
  .detail-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .score-display {
    flex-direction: column;
    align-items: center;
  }
  
  .quick-stats {
    grid-template-columns: 1fr;
    gap: var(--spacing-xs);
  }
  
  .stat-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .stat-label {
    margin-bottom: 0;
  }
  
  .bottom-actions {
    flex-direction: column;
    gap: var(--spacing-xs);
  }
  
  .bottom-actions .btn {
    width: 100%;
  }
}
</style>
