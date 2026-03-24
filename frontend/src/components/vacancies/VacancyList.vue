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
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useVacanciesStore } from '@/stores/vacancies'
import VacancyCard from './VacancyCard.vue'

const router = useRouter()
const vacanciesStore = useVacanciesStore()

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

// Статистика по вакансиям (заглушка, позже будет из API)
const vacancyStats = ref({})

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
  if (confirm('Создать копию этой вакансии?')) {
    try {
      await vacanciesStore.cloneVacancy(id)
    } catch (error) {
      // Ошибка уже в store
    }
  }
}

const handleToggle = async (id) => {
  const vacancy = vacancies.value.find(v => v.id === id)
  if (vacancy) {
    await vacanciesStore.updateVacancy(id, {
      is_active: !vacancy.is_active
    })
  }
}

const handleDelete = async (id) => {
  if (confirm('Вы уверены? Вакансия будет перемещена в архив.')) {
    try {
      await vacanciesStore.deleteVacancy(id)
    } catch (error) {
      // Ошибка уже в store
    }
  }
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
</style>
