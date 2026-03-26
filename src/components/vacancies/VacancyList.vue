<template>
  <div class="vacancy-list">
    <!-- Заголовок и действия -->
    <div class="list-header">
      <h2 class="list-title">Вакансии</h2>
      <div class="list-actions">
        <button 
          class="btn btn-secondary btn-small"
          @click="toggleFilters"
        >
          🔍 Фильтры
        </button>
        <router-link 
          to="/vacancies/new" 
          class="btn btn-primary btn-small"
        >
          ➕ Новая вакансия
        </router-link>
      </div>
    </div>

    <!-- Панель фильтров (раскрывающаяся) -->
    <div v-if="showFilters" class="filters-panel card">
      <div class="filters-grid">
        <div class="filter-group">
          <label class="filter-label">Поиск</label>
          <input
            v-model="filters.search"
            type="text"
            class="input"
            placeholder="Название вакансии..."
            @input="debouncedSearch"
          />
        </div>
        
        <div class="filter-group">
          <label class="filter-label">Статус</label>
          <select v-model="filters.activeOnly" class="select">
            <option :value="true">Только активные</option>
            <option :value="false">Все вакансии</option>
          </select>
        </div>
        
        <div class="filter-group">
          <label class="filter-label">Сортировка</label>
          <select v-model="filters.sortBy" class="select">
            <option value="newest">Сначала новые</option>
            <option value="oldest">Сначала старые</option>
            <option value="title">По названию</option>
            <option value="analyses">По количеству анализов</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Состояние загрузки -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Загрузка вакансий...</p>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="error-state">
      <span class="error-icon">❌</span>
      <p>{{ error }}</p>
      <button class="btn btn-secondary" @click="retryLoad">Повторить</button>
    </div>

    <!-- Список вакансий -->
    <div v-else-if="vacancies.length" class="vacancies-grid">
      <VacancyCard
        v-for="vacancy in displayedVacancies"
        :key="vacancy.id"
        :vacancy="vacancy"
        :stats="getVacancyStats(vacancy.id)"
        @view="handleView"
        @edit="handleEdit"
        @clone="handleClone"
        @toggle="handleToggle"
        @delete="handleDelete"
      />
    </div>

    <!-- Пустое состояние -->
    <div v-else class="empty-state">
      <div class="empty-icon">📭</div>
      <h3>Нет вакансий</h3>
      <p>Создайте первую вакансию, чтобы начать анализ резюме</p>
      <router-link to="/vacancies/new" class="btn btn-primary">
        ➕ Создать вакансию
      </router-link>
    </div>

    <!-- Пагинация -->
    <div v-if="totalPages > 1" class="pagination">
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

  <!-- Confirm dialog -->
  <Teleport to="body">
    <Transition name="confirm-fade">
      <div v-if="confirm.show" class="vl-confirm-overlay" @click.self="confirm.show = false">
        <div class="vl-confirm-box">
          <div class="vl-confirm-icon">{{ confirm.icon }}</div>
          <h3>{{ confirm.title }}</h3>
          <p>{{ confirm.message }}</p>
          <div class="vl-confirm-actions">
            <button class="btn btn-secondary" @click="confirm.show = false">Отмена</button>
            <button
              class="btn btn-primary"
              :class="{ 'vl-btn-danger': confirm.danger }"
              @click="confirm.action"
            >{{ confirm.btnText }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useVacanciesStore } from '@/stores/vacancies'
import { useToast } from '@/composables/useToast'
import api from '@/services/api'
import VacancyCard from './VacancyCard.vue'

const router = useRouter()
const vacanciesStore = useVacanciesStore()
const toast = useToast()

// Состояние
const loading = computed(() => vacanciesStore.loading)
const error = computed(() => vacanciesStore.error)
const vacancies = computed(() => vacanciesStore.vacancies)

const showFilters = ref(false)
const currentPage = ref(1)
const pageSize = ref(12)

// Фильтры
const filters = ref({
  search: '',
  activeOnly: true,
  sortBy: 'newest'
})

// Статистика по вакансиям — счётчик анализов
const vacancyStats = ref({})

// Загрузка статистики анализов по всем вакансиям
const loadVacancyStats = async () => {
  try {
    const { data } = await api.get('/analyze/history', { params: { limit: 1000 } })
    const counts = {}
    for (const a of data) {
      if (a.vacancy_id) {
        if (!counts[a.vacancy_id]) counts[a.vacancy_id] = { analysesCount: 0, scores: [] }
        counts[a.vacancy_id].analysesCount++
        if (a.score != null) counts[a.vacancy_id].scores.push(a.score)
      }
    }
    for (const id in counts) {
      const s = counts[id].scores
      counts[id].averageScore = s.length ? s.reduce((a,b) => a+b, 0) / s.length : null
    }
    vacancyStats.value = counts
  } catch (e) { /* тихая ошибка */ }
}

// Confirm dialog
const confirm = reactive({
  show: false, title: '', message: '', icon: '⚠️', btnText: 'OK',
  danger: false, action: null
})

const showConfirm = ({ title, message, icon = '⚠️', btnText = 'Подтвердить', danger = false, action }) => {
  Object.assign(confirm, { show: true, title, message, icon, btnText, danger, action })
}

// Debounced поиск
let searchTimeout
const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    loadVacancies()
  }, 300)
}

// Отображаемые вакансии с учётом сортировки
const displayedVacancies = computed(() => {
  let result = [...vacancies.value]
  
  // Сортировка
  switch (filters.value.sortBy) {
    case 'newest':
      result.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      break
    case 'oldest':
      result.sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
      break
    case 'title':
      result.sort((a, b) => a.title.localeCompare(b.title))
      break
    case 'analyses':
      result.sort((a, b) => {
        const aCount = vacancyStats.value[a.id]?.analysesCount || 0
        const bCount = vacancyStats.value[b.id]?.analysesCount || 0
        return bCount - aCount
      })
      break
  }
  
  return result
})

// Общее количество страниц
const totalPages = computed(() => 
  Math.ceil(vacancies.value.length / pageSize.value)
)

// Загрузка вакансий
const loadVacancies = async () => {
  await vacanciesStore.fetchVacancies({
    skip: (currentPage.value - 1) * pageSize.value,
    limit: pageSize.value,
    activeOnly: filters.value.activeOnly,
    search: filters.value.search
  })
}

// Получить статистику для вакансии
const getVacancyStats = (vacancyId) => {
  return vacancyStats.value[vacancyId] || {
    analysesCount: 0,
    averageScore: null,
    matchRate: null
  }
}

// Обработчики действий
const handleView = (id) => {
  router.push(`/vacancies/${id}`)
}

const handleEdit = (id) => {
  router.push(`/vacancies/${id}/edit`)
}

const handleClone = async (id) => {
  showConfirm({
    title: 'Создать копию?',
    message: 'Будет создана полная копия этой вакансии.',
    icon: '📋', btnText: 'Создать',
    action: async () => {
      confirm.show = false
      try {
        await vacanciesStore.cloneVacancy(id)
        toast.success('Вакансия успешно клонирована')
      } catch {
        toast.error('Не удалось клонировать вакансию')
      }
    }
  })
}

const handleToggle = async (id) => {
  const vacancy = vacancies.value.find(v => v.id === id)
  if (!vacancy) return
  const toArchive = vacancy.is_active
  showConfirm({
    title: toArchive ? 'Перевести в архив?' : 'Активировать вакансию?',
    message: toArchive
      ? `Вакансия «${vacancy.title}» будет перемещена в архив.`
      : `Вакансия «${vacancy.title}» снова станет активной.`,
    icon: toArchive ? '📦' : '▶️',
    btnText: toArchive ? 'В архив' : 'Активировать',
    danger: toArchive,
    action: async () => {
      confirm.show = false
      try {
        await vacanciesStore.updateVacancy(id, { is_active: !vacancy.is_active })
        toast.success(toArchive ? 'Вакансия перемещена в архив' : 'Вакансия активирована')
      } catch {
        toast.error('Не удалось изменить статус вакансии')
      }
    }
  })
}

const handleDelete = async (id) => {
  const vacancy = vacancies.value.find(v => v.id === id)
  showConfirm({
    title: 'Удалить вакансию?',
    message: `Вакансия «${vacancy?.title || ''}» будет удалена безвозвратно.`,
    icon: '🗑️', btnText: 'Удалить', danger: true,
    action: async () => {
      confirm.show = false
      try {
        await vacanciesStore.deleteVacancy(id)
        toast.success('Вакансия удалена')
      } catch {
        toast.error('Не удалось удалить вакансию')
      }
    }
  })
}

const toggleFilters = () => {
  showFilters.value = !showFilters.value
}

const changePage = (page) => {
  currentPage.value = page
  loadVacancies()
}

const retryLoad = () => {
  loadVacancies()
}

// Следим за изменениями фильтров
watch(
  () => [filters.value.activeOnly, filters.value.sortBy],
  () => {
    currentPage.value = 1
    loadVacancies()
  }
)

// Загружаем при монтировании
onMounted(() => {
  loadVacancies()
  loadVacancyStats()
})
</script>

<style scoped>
.vacancy-list {
  max-width: 1200px;
  margin: 0 auto;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing);
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.list-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text);
}

.list-actions {
  display: flex;
  gap: var(--spacing-xs);
}

.filters-panel {
  margin-bottom: var(--spacing);
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-sm);
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xxs);
}

.filter-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-light);
  margin-left: 4px;
}

.select {
  padding: 12px;
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  font-size: 14px;
  font-family: inherit;
  background: var(--color-surface-lighter);
  color: var(--color-text);
  cursor: pointer;
  transition: var(--transition);
}

.select:hover {
  border-color: var(--color-primary);
}

.select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-soft);
}

.vacancies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: var(--spacing);
  margin-bottom: var(--spacing);
}

.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: var(--spacing) * 2;
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
  margin-bottom: var(--spacing-sm);
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

@media (max-width: 768px) {
  .vacancies-grid {
    grid-template-columns: 1fr;
  }
  
  .list-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .list-actions {
    width: 100%;
  }
  
  .list-actions .btn {
    flex: 1;
  }
}

/* Confirm dialog */
.vl-confirm-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.45); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: 9000; padding: 24px;
}
.vl-confirm-box {
  background: var(--color-surface); border-radius: var(--border-radius);
  max-width: 420px; width: 90%; padding: var(--spacing);
  text-align: center; box-shadow: 0 24px 60px rgba(18,78,115,.2);
}
.vl-confirm-icon { font-size: 40px; margin-bottom: 12px; }
.vl-confirm-box h3 { font-size: 18px; font-weight: 600; margin-bottom: 8px; color: var(--color-text); }
.vl-confirm-box p { color: var(--color-text-light); font-size: 14px; line-height: 1.5; margin-bottom: var(--spacing); }
.vl-confirm-actions { display: flex; gap: 12px; justify-content: center; }
.vl-btn-danger { background: #ef4444 !important; color: white !important; }
.confirm-fade-enter-active, .confirm-fade-leave-active { transition: all .2s ease; }
.confirm-fade-enter-from, .confirm-fade-leave-to { opacity: 0; }
.confirm-fade-enter-from .vl-confirm-box { transform: scale(.95); }

</style>
