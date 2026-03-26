<template>
  <div class="vacancy-detail-view">
    <div class="container">
      <!-- Хлебные крошки -->
      <div class="breadcrumbs">
        <router-link to="/vacancies" class="breadcrumb-link">
          ← К списку вакансий
        </router-link>
      </div>

      <!-- Состояние загрузки -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка вакансии...</p>
      </div>

      <!-- Ошибка -->
      <div v-else-if="error" class="error-state">
        <span class="error-icon">❌</span>
        <p>{{ error }}</p>
        <button class="btn btn-secondary" @click="retryLoad">Повторить</button>
        <router-link to="/vacancies" class="btn btn-primary">
          К списку вакансий
        </router-link>
      </div>

      <!-- Контент -->
      <template v-else-if="vacancy">
        <!-- Шапка с действиями -->
        <div class="detail-header">
          <div class="title-section">
            <h1 class="vacancy-title">{{ vacancy.title }}</h1>
            <span class="vacancy-status" :class="statusClass">
              {{ vacancy.is_active ? 'Активна' : 'В архиве' }}
            </span>
          </div>

          <div class="header-actions">
            <button 
              class="action-btn edit" 
              @click="goToEdit"
              title="Редактировать"
            >
              ✏️ Редактировать
            </button>
            <button 
              class="action-btn clone" 
              @click="handleClone"
              title="Клонировать"
            >
              📋 Клонировать
            </button>
            <button 
              class="action-btn toggle" 
              @click="handleToggle"
              :title="vacancy.is_active ? 'В архив' : 'Активировать'"
            >
              {{ vacancy.is_active ? '📦 В архив' : '▶️ Активировать' }}
            </button>
            <button 
              class="action-btn delete" 
              @click="handleDelete"
              title="Удалить"
            >
              🗑️ Удалить
            </button>
          </div>
        </div>

        <!-- Основная информация (сетка) -->
        <div class="info-grid">
          <!-- Левая колонка -->
          <div class="info-column">
            <!-- Локация и зарплата -->
            <div class="info-card">
              <h3 class="card-title">📍 Локация и зарплата</h3>
              <div class="info-content">
                <div class="info-row">
                  <span class="info-label">Локация:</span>
                  <span class="info-value">{{ vacancy.location || 'Не указана' }}</span>
                </div>
                <div class="info-row" v-if="vacancy.salary_range?.min || vacancy.salary_range?.max">
                  <span class="info-label">Зарплата:</span>
                  <span class="info-value salary">
                    {{ formatSalaryRange(vacancy.salary_range) }}
                    <span class="currency">{{ vacancy.salary_range.currency || 'RUB' }}</span>
                  </span>
                </div>
              </div>
            </div>

            <!-- Ключевые навыки -->
            <div class="info-card">
              <h3 class="card-title">🔧 Ключевые навыки</h3>
              <div class="skills-list">
                <span 
                  v-for="skill in vacancy.key_skills" 
                  :key="skill"
                  class="skill-tag"
                >
                  {{ skill }}
                </span>
                <span v-if="!vacancy.key_skills?.length" class="no-data">
                  Навыки не указаны
                </span>
              </div>
            </div>

            <!-- Комментарий для AI -->
            <div class="info-card" v-if="vacancy.comment_for_ai">
              <h3 class="card-title">🤖 Комментарий для AI</h3>
              <p class="comment-text">{{ vacancy.comment_for_ai }}</p>
            </div>
          </div>

          <!-- Правая колонка - Статистика -->
          <div class="stats-column">
            <div class="stats-card">
              <h3 class="card-title">📊 Статистика анализов</h3>
              
              <div class="stats-grid">
                <div class="stat-item">
                  <span class="stat-value">{{ stats.totalAnalyses }}</span>
                  <span class="stat-label">Всего анализов</span>
                </div>
                <div class="stat-item">
                  <span class="stat-value">{{ stats.averageScore.toFixed(1) }}/10</span>
                  <span class="stat-label">Средняя оценка</span>
                </div>
                <div class="stat-item">
                  <span class="stat-value">{{ stats.invitationRate }}%</span>
                  <span class="stat-label">Приглашений</span>
                </div>
                <div class="stat-item">
                  <span class="stat-value">{{ stats.uniqueCandidates }}</span>
                  <span class="stat-label">Уникальных</span>
                </div>
              </div>

              <!-- Распределение оценок (круговой прогресс) -->
              <div class="score-distribution">
                <h4 class="subsection-title">Распределение оценок</h4>
                <div class="distribution-bars">
                  <div class="distribution-bar">
                    <span class="bar-label">Высокие (8-10)</span>
                    <div class="bar-container">
                      <div 
                        class="bar-fill high" 
                        :style="{ width: stats.highScorePercent + '%' }"
                      ></div>
                    </div>
                    <span class="bar-value">{{ stats.highScoreCount }}</span>
                  </div>
                  <div class="distribution-bar">
                    <span class="bar-label">Средние (5-7)</span>
                    <div class="bar-container">
                      <div 
                        class="bar-fill medium" 
                        :style="{ width: stats.mediumScorePercent + '%' }"
                      ></div>
                    </div>
                    <span class="bar-value">{{ stats.mediumScoreCount }}</span>
                  </div>
                  <div class="distribution-bar">
                    <span class="bar-label">Низкие (0-4)</span>
                    <div class="bar-container">
                      <div 
                        class="bar-fill low" 
                        :style="{ width: stats.lowScorePercent + '%' }"
                      ></div>
                    </div>
                    <span class="bar-value">{{ stats.lowScoreCount }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Часто встречающиеся навыки -->
            <div class="skills-stats-card" v-if="stats.topMatchedSkills?.length">
              <h3 class="card-title">📈 Часто совпадающие навыки</h3>
              <div class="top-skills-list">
                <div 
                  v-for="skill in stats.topMatchedSkills.slice(0, 5)" 
                  :key="skill.name"
                  class="top-skill-item"
                >
                  <span class="skill-name">{{ skill.name }}</span>
                  <span class="skill-count">{{ skill.count }} раз</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Описание вакансии -->
        <div class="description-section">
          <h3 class="section-title">📝 Описание вакансии</h3>
          <div class="rich-description" v-html="sanitizeHtml(vacancy.description_html || vacancy.description_text || '<p class=\'no-description\'>Описание отсутствует</p>')"></div>
        </div>

        <!-- Шаблоны сообщений -->
        <div class="templates-section" v-if="hasTemplates">
          <h3 class="section-title">📋 Шаблоны сообщений</h3>
          
          <div class="templates-grid">
            <div class="template-card" v-if="vacancy.templates?.hh_invitation">
              <h4 class="template-title">📧 Приглашение на hh.ru</h4>
              <p class="template-preview">{{ truncate(vacancy.templates.hh_invitation, 150) }}</p>
              <button class="copy-btn" @click="copyToClipboard(vacancy.templates.hh_invitation)">
                📋 Копировать
              </button>
            </div>

            <div class="template-card" v-if="vacancy.templates?.messenger_invitation">
              <h4 class="template-title">💬 Приглашение в мессенджер</h4>
              <p class="template-preview">{{ truncate(vacancy.templates.messenger_invitation, 150) }}</p>
              <button class="copy-btn" @click="copyToClipboard(vacancy.templates.messenger_invitation)">
                📋 Копировать
              </button>
            </div>

            <div class="template-card" v-if="vacancy.templates?.interview_questions">
              <h4 class="template-title">❓ Вопросы для интервью</h4>
              <p class="template-preview">{{ truncate(vacancy.templates.interview_questions, 150) }}</p>
              <button class="copy-btn" @click="copyToClipboard(vacancy.templates.interview_questions)">
                📋 Копировать
              </button>
            </div>

            <div class="template-card" v-if="vacancy.templates?.rejection">
              <h4 class="template-title">📨 Шаблон отказа</h4>
              <p class="template-preview">{{ truncate(vacancy.templates.rejection, 150) }}</p>
              <button class="copy-btn" @click="copyToClipboard(vacancy.templates.rejection)">
                📋 Копировать
              </button>
            </div>
          </div>
        </div>

        <!-- История анализов -->
        <div class="history-section">
          <div class="section-header">
            <h3 class="section-title">📜 История анализов по этой вакансии</h3>
            <router-link :to="`/history?vacancy=${vacancy.id}`" class="view-all-link">
              Смотреть все →
            </router-link>
          </div>

          <div v-if="history.loading" class="history-loading">
            <div class="spinner-small"></div>
            <span>Загрузка истории...</span>
          </div>

          <div v-else-if="history.error" class="history-error">
            Не удалось загрузить историю
          </div>

          <div v-else-if="history.items.length" class="history-list">
            <div 
              v-for="analysis in history.items.slice(0, 5)" 
              :key="analysis.id"
              class="history-item"
              @click="goToAnalysis(analysis.id)"
            >
              <div class="history-item-header">
                <span class="history-title-text">{{ analysis.analysis_title || ('Анализ #' + analysis.id) }}</span>
                <span class="history-score" :class="getScoreClass(analysis.score)">
                  {{ analysis.score }}/10
                </span>
              </div>
              <p class="history-preview">{{ analysis.cv_text_preview }}</p>
              <div class="history-footer">
                <span class="history-recommendation">{{ analysis.recommendation }}</span>
                <span class="history-date">{{ formatDate(analysis.created_at) }}</span>
              </div>
            </div>

            <router-link 
              v-if="history.total > 5" 
              :to="`/history?vacancy=${vacancy.id}`" 
              class="view-more-link"
            >
              Показать все {{ history.total }} анализов →
            </router-link>
          </div>

          <div v-else class="history-empty">
            <p>По этой вакансии ещё нет анализов</p>
            <p class="history-hint">
              💡 Откройте расширение на hh.ru и выберите эту вакансию для анализа
            </p>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useVacanciesStore } from '@/stores/vacancies'
import { useToast } from '@/composables/useToast'
import api from '@/services/api'
import { formatDistance } from 'date-fns'
import { ru } from 'date-fns/locale'

const route = useRoute()
const router = useRouter()
const vacanciesStore = useVacanciesStore()
const toast = useToast()

// Базовая санитизация HTML — удаляет скрипты и опасные атрибуты
const sanitizeHtml = (html) => {
  if (!html) return ''
  const tmp = document.createElement('div')
  tmp.innerHTML = html
  // Удаляем script/iframe/object/embed
  tmp.querySelectorAll('script, iframe, object, embed, link, style').forEach(el => el.remove())
  // Удаляем on* атрибуты
  tmp.querySelectorAll('*').forEach(el => {
    Array.from(el.attributes).forEach(attr => {
      if (attr.name.startsWith('on') || attr.value.includes('javascript:')) {
        el.removeAttribute(attr.name)
      }
    })
  })
  return tmp.innerHTML
}

// Состояние
const vacancy = ref(null)
const loading = ref(true)
const error = ref(null)

// История анализов
const history = reactive({
  items: [],
  total: 0,
  loading: false,
  error: false
})

// Статистика
const stats = ref({
  totalAnalyses: 0,
  averageScore: 0,
  invitationRate: 0,
  uniqueCandidates: 0,
  highScoreCount: 0,
  mediumScoreCount: 0,
  lowScoreCount: 0,
  highScorePercent: 0,
  mediumScorePercent: 0,
  lowScorePercent: 0,
  topMatchedSkills: []
})

// Computed
const statusClass = computed(() => ({
  'status-active': vacancy.value?.is_active,
  'status-inactive': !vacancy.value?.is_active
}))

const hasTemplates = computed(() => {
  const t = vacancy.value?.templates
  return t && Object.values(t).some(v => v && v.trim())
})

// Загрузка данных
const loadData = async () => {
  const vacancyId = parseInt(route.params.id)
  
  if (isNaN(vacancyId)) {
    error.value = 'Неверный ID вакансии'
    loading.value = false
    return
  }

  try {
    // Загружаем вакансию
    vacancy.value = await vacanciesStore.fetchVacancy(vacancyId)
    
    // Загружаем историю анализов
    await loadHistory(vacancyId)
    
    // Загружаем статистику
    await loadStats(vacancyId)
    
  } catch (err) {
    console.error('Ошибка загрузки:', err)
    error.value = 'Не удалось загрузить информацию о вакансии'
  } finally {
    loading.value = false
  }
}

// Загрузка истории анализов
const loadHistory = async (vacancyId) => {
  history.loading = true
  history.error = false
  
  try {
    const response = await api.get('/analyze/history', {
      params: {
        vacancy_id: vacancyId,
        limit: 100
      }
    })
    
    history.items = response.data
    history.total = response.data.length
    
    // Рассчитываем статистику на основе истории
    calculateStats(response.data)
    
  } catch (err) {
    console.error('Ошибка загрузки истории:', err)
    history.error = true
  } finally {
    history.loading = false
  }
}

// Загрузка дополнительной статистики (если есть отдельный эндпоинт)
const loadStats = async (vacancyId) => {
  try {
    const response = await api.get('/analyze/stats', {
      params: { days: 365 }
    })
    // Здесь можно обработать общую статистику
  } catch (err) {
    console.error('Ошибка загрузки статистики:', err)
  }
}

// Расчёт статистики на основе истории
const calculateStats = (analyses) => {
  if (!analyses.length) {
    stats.value = {
      totalAnalyses: 0,
      averageScore: 0,
      invitationRate: 0,
      uniqueCandidates: 0,
      highScoreCount: 0,
      mediumScoreCount: 0,
      lowScoreCount: 0,
      highScorePercent: 0,
      mediumScorePercent: 0,
      lowScorePercent: 0,
      topMatchedSkills: []
    }
    return
  }

  const total = analyses.length
  
  // Подсчёт оценок
  const highScore = analyses.filter(a => a.score >= 8).length
  const mediumScore = analyses.filter(a => a.score >= 5 && a.score < 8).length
  const lowScore = analyses.filter(a => a.score < 5).length
  
  // Средняя оценка
  const avgScore = analyses.reduce((sum, a) => sum + (a.score || 0), 0) / total
  
  // Процент приглашений
  const invitations = analyses.filter(a => 
    a.recommendation?.includes('Пригласить')
  ).length
  
  // Уникальные кандидаты (по превью текста - упрощённо)
  const uniquePreviews = new Set(analyses.map(a => a.cv_text_preview)).size
  
  // Подсчёт частоты навыков
  const skillCount = {}
  analyses.forEach(a => {
    a.matched_skills?.forEach(skill => {
      skillCount[skill] = (skillCount[skill] || 0) + 1
    })
  })
  
  const topSkills = Object.entries(skillCount)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)

  stats.value = {
    totalAnalyses: total,
    averageScore: avgScore,
    invitationRate: Math.round((invitations / total) * 100),
    uniqueCandidates: uniquePreviews,
    highScoreCount: highScore,
    mediumScoreCount: mediumScore,
    lowScoreCount: lowScore,
    highScorePercent: Math.round((highScore / total) * 100),
    mediumScorePercent: Math.round((mediumScore / total) * 100),
    lowScorePercent: Math.round((lowScore / total) * 100),
    topMatchedSkills: topSkills
  }
}

// Форматирование зарплаты
const formatSalaryRange = (range) => {
  if (!range) return 'Не указана'
  
  const parts = []
  if (range.min) parts.push(`от ${range.min.toLocaleString()}`)
  if (range.max) parts.push(`до ${range.max.toLocaleString()}`)
  
  return parts.join(' ') || 'Не указана'
}

// Форматирование даты
const formatDate = (dateString) => {
  if (!dateString) return ''
  return formatDistance(new Date(dateString), new Date(), {
    addSuffix: true,
    locale: ru
  })
}

// Класс для оценки
const getScoreClass = (score) => {
  if (score >= 8) return 'score-high'
  if (score >= 5) return 'score-medium'
  return 'score-low'
}

// Обрезка текста
const truncate = (text, length) => {
  if (!text) return ''
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}

// Копирование в буфер обмена
const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    toast.success('Скопировано в буфер обмена')
  } catch (err) {
    console.error('Ошибка копирования:', err)
    toast.error('Не удалось скопировать')
  }
}

// Действия
const goToEdit = () => {
  router.push(`/vacancies/${vacancy.value.id}/edit`)
}

const handleClone = async () => {
  if (confirm('Создать копию этой вакансии?')) {
    try {
      await vacanciesStore.cloneVacancy(vacancy.value.id)
      router.push('/vacancies')
    } catch (err) {
      console.error('Ошибка клонирования:', err)
    }
  }
}

const handleToggle = async () => {
  try {
    await vacanciesStore.updateVacancy(vacancy.value.id, {
      is_active: !vacancy.value.is_active
    })
    // Обновляем локальное состояние
    vacancy.value.is_active = !vacancy.value.is_active
  } catch (err) {
    console.error('Ошибка изменения статуса:', err)
  }
}

const handleDelete = async () => {
  if (confirm('Вы уверены? Вакансия будет перемещена в архив.')) {
    try {
      await vacanciesStore.deleteVacancy(vacancy.value.id)
      router.push('/vacancies')
    } catch (err) {
      console.error('Ошибка удаления:', err)
    }
  }
}

const goToAnalysis = (id) => {
  router.push(`/history/${id}`)
}

const retryLoad = () => {
  error.value = null
  loading.value = true
  loadData()
}

// Монтирование
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.vacancy-detail-view {
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

.vacancy-title {
  font-size: 32px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.vacancy-status {
  font-size: 14px;
  padding: 6px 12px;
  border-radius: var(--border-radius-pill);
  font-weight: 500;
}

.status-active {
  background: var(--color-success);
  color: var(--color-success-text);
}

.status-inactive {
  background: var(--color-border);
  color: var(--color-text-muted);
}

.header-actions {
  display: flex;
  gap: var(--spacing-xxs);
  flex-wrap: wrap;
}

.action-btn {
  padding: 10px 16px;
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius-pill);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: 14px;
  cursor: pointer;
  transition: var(--transition);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.action-btn:hover {
  transform: translateY(-2px);
}

.action-btn.edit:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.action-btn.clone:hover {
  border-color: #0ea5e9;
  background: #e0f2fe;
}

.action-btn.toggle:hover {
  border-color: #22c55e;
  background: #dcfce7;
}

.action-btn.delete:hover {
  border-color: #ef4444;
  background: #fee2e2;
}

/* Сетка */
.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing);
  margin-bottom: var(--spacing);
}

.info-card,
.stats-card,
.skills-stats-card {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  border: 1px solid var(--color-border);
  transition: var(--transition);
  height: fit-content;
}

.info-card:hover,
.stats-card:hover,
.skills-stats-card:hover {
  box-shadow: 0 8px 30px var(--color-shadow);
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing-sm);
  padding-bottom: var(--spacing-xs);
  border-bottom: 2px solid var(--color-border);
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.info-row {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.info-label {
  font-size: 14px;
  color: var(--color-text-muted);
  min-width: 80px;
}

.info-value {
  font-size: 16px;
  color: var(--color-text);
  font-weight: 500;
}

.salary {
  color: var(--color-primary-dark);
  font-weight: 600;
}

.currency {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-left: 4px;
}

.skills-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.skill-tag {
  padding: 6px 12px;
  background: var(--color-primary-soft);
  border-radius: var(--border-radius-pill);
  font-size: 13px;
  color: var(--color-primary-dark);
  border: 1px solid var(--color-primary);
}

.no-data {
  color: var(--color-text-muted);
  font-style: italic;
  font-size: 14px;
}

.comment-text {
  font-size: 15px;
  line-height: 1.6;
  color: var(--color-text);
  background: var(--color-surface-darker);
  padding: var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  border-left: 4px solid var(--color-primary);
}

/* Статистика */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing);
}

.stat-item {
  text-align: center;
  padding: var(--spacing-xs);
  background: var(--color-surface-darker);
  border-radius: var(--border-radius-sm);
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

.score-distribution {
  margin-top: var(--spacing);
}

.subsection-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing-xs);
}

.distribution-bars {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.distribution-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.bar-label {
  font-size: 12px;
  color: var(--color-text-muted);
  min-width: 80px;
}

.bar-container {
  flex: 1;
  height: 8px;
  background: var(--color-border);
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.bar-fill.high {
  background: #10b981;
}

.bar-fill.medium {
  background: #fbbf24;
}

.bar-fill.low {
  background: #ef4444;
}

.bar-value {
  font-size: 12px;
  color: var(--color-text-muted);
  min-width: 40px;
  text-align: right;
}

/* Топ навыки */
.top-skills-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.top-skill-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-xxs) 0;
  border-bottom: 1px solid var(--color-border);
}

.top-skill-item:last-child {
  border-bottom: none;
}

.skill-name {
  font-size: 14px;
  color: var(--color-text);
}

.skill-count {
  font-size: 12px;
  color: var(--color-text-muted);
  background: var(--color-surface-darker);
  padding: 2px 8px;
  border-radius: var(--border-radius-pill);
}

/* Описание */
.description-section {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  margin-bottom: var(--spacing);
  border: 1px solid var(--color-border);
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing-sm);
}











.formatted-description :deep(h1),
.formatted-description :deep(h2),
.formatted-description :deep(h3) {
  color: var(--color-text);
  margin-bottom: var(--spacing-xs);
}

.formatted-description :deep(ul),
.formatted-description :deep(ol) {
  padding-left: 20px;
  margin-bottom: var(--spacing-xs);
}



.raw-description pre {
  font-family: 'Source Sans 3', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text);
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Шаблоны */
.templates-section {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  margin-bottom: var(--spacing);
  border: 1px solid var(--color-border);
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing);
}

.template-card {
  background: var(--color-surface-darker);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  transition: var(--transition);
}

.template-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px var(--color-shadow);
}

.template-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing-xs);
}

.template-preview {
  font-size: 13px;
  color: var(--color-text-light);
  line-height: 1.5;
  margin-bottom: var(--spacing-xs);
  min-height: 60px;
}

.copy-btn {
  padding: 6px 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-pill);
  font-size: 12px;
  cursor: pointer;
  transition: var(--transition);
  color: var(--color-text);
}

.copy-btn:hover {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
  transform: translateY(-1px);
}

/* История */
.history-section {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  border: 1px solid var(--color-border);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.view-all-link {
  color: var(--color-primary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: var(--transition);
}

.view-all-link:hover {
  color: var(--color-primary-dark);
  transform: translateX(4px);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.history-item {
  background: var(--color-surface-darker);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: var(--transition);
}

.history-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px var(--color-shadow);
  border-color: var(--color-primary);
}

.history-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xs);
}

.history-title-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: var(--spacing-xs);
}

.history-date {
  font-size: 12px;
  color: var(--color-text-muted);
}

.history-score {
  font-size: 16px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--border-radius-pill);
}

.score-high {
  background: #10b981;
  color: white;
}

.score-medium {
  background: #fbbf24;
  color: #1e293b;
}

.score-low {
  background: #ef4444;
  color: white;
}

.history-preview {
  font-size: 13px;
  color: var(--color-text);
  margin-bottom: var(--spacing-xs);
  line-height: 1.5;
}

.history-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-recommendation {
  font-size: 12px;
  color: var(--color-primary);
  font-weight: 500;
}

.history-mode {
  font-size: 11px;
  color: var(--color-text-muted);
  background: var(--color-surface);
  padding: 2px 6px;
  border-radius: var(--border-radius-pill);
}

.view-more-link {
  display: block;
  text-align: center;
  padding: var(--spacing-sm);
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
  transition: var(--transition);
}

.view-more-link:hover {
  color: var(--color-primary-dark);
  background: var(--color-primary-soft);
  border-radius: var(--border-radius-sm);
}

.history-empty {
  text-align: center;
  padding: var(--spacing);
  color: var(--color-text-muted);
}

.history-hint {
  font-size: 13px;
  margin-top: var(--spacing-xs);
  color: var(--color-text-light);
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

.spinner-small {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border);
  border-top: 2px solid var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state .error-icon {
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

.history-loading,
.history-error {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
  padding: var(--spacing);
  color: var(--color-text-muted);
}

/* Адаптивность */
@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .detail-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
  }
  
  .action-btn {
    flex: 1;
  }
  
  .vacancy-title {
    font-size: 24px;
  }
  
  .templates-grid {
    grid-template-columns: 1fr;
  }
}

.rich-description {
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-text);
  padding: var(--spacing-sm);
  background: var(--color-surface-darker);
  border-radius: var(--border-radius-sm);
  border: 1px solid var(--color-border);
}

.rich-description :deep(h1),
.rich-description :deep(h2),
.rich-description :deep(h3) {
  font-weight: 600;
  color: var(--color-text);
  margin: 12px 0 6px;
}

.rich-description :deep(ul),
.rich-description :deep(ol) {
  padding-left: 20px;
  margin: 6px 0;
}

.rich-description :deep(li) { margin: 3px 0; }

.rich-description :deep(b),
.rich-description :deep(strong) { font-weight: 700; }

.rich-description :deep(p) { margin: 6px 0; }

.rich-description :deep(.no-description) { color: var(--color-text-muted); font-style: italic; }

</style>