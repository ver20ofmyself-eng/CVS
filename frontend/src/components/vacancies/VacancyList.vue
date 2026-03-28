<template>
  <div class="vl">
    <!-- Заголовок -->
    <div class="vl-header">
      <h2 class="vl-title">Вакансии</h2>
      <div class="vl-header-actions">
        <button class="btn btn-secondary btn-small" @click="showFilters = !showFilters">
          🔍 Фильтры {{ hasActiveFilters ? '•' : '' }}
        </button>
        <router-link to="/vacancies/new" class="btn btn-primary btn-small">
          ➕ Новая вакансия
        </router-link>
      </div>
    </div>

    <!-- Фильтры -->
    <div v-if="showFilters" class="vl-filters card">
      <div class="vl-filters-grid">
        <div class="vl-filter">
          <label>Поиск</label>
          <input v-model="filters.search" type="text" class="input" placeholder="Название..." @input="debouncedSearch" />
        </div>
        <div class="vl-filter">
          <label>Статус</label>
          <select v-model="filters.status" class="select" @change="loadVacancies">
            <option value="">Все</option>
            <option value="active">Активные</option>
            <option value="completed">Завершённые</option>
            <option value="archived">В архиве</option>
          </select>
        </div>
        <div class="vl-filter">
          <label>Заказчик</label>
          <input v-model="filters.client" type="text" class="input" placeholder="Название компании..." @input="debouncedSearch" />
        </div>
        <div class="vl-filter">
          <label>Сортировка</label>
          <select v-model="filters.sortBy" class="select">
            <option value="status">По статусу</option>
            <option value="newest">Сначала новые</option>
            <option value="oldest">Сначала старые</option>
            <option value="title">По названию</option>
          </select>
        </div>
      </div>
      <div class="vl-filters-actions">
        <button class="btn btn-text" @click="resetFilters">🧹 Сбросить</button>
        <span class="vl-count">Найдено: {{ sortedVacancies.length }}</span>
      </div>
    </div>

    <!-- Загрузка -->
    <div v-if="loading" class="vl-state"><div class="spinner"></div><p>Загрузка вакансий...</p></div>

    <!-- Ошибка -->
    <div v-else-if="error" class="vl-state">
      <span class="vl-state-icon">❌</span><p>{{ error }}</p>
      <button class="btn btn-primary" @click="loadVacancies">Повторить</button>
    </div>

    <!-- Список с группировкой -->
    <template v-else-if="sortedVacancies.length">
      <!-- Группы по статусу (когда сортировка по статусу) -->
      <template v-if="filters.sortBy === 'status'">
        <template v-for="group in statusGroups" :key="group.key">
          <div v-if="group.items.length" class="vl-group">
            <div class="vl-group-header">
              <span class="vl-group-dot" :class="`dot--${group.key}`"></span>
              <h3 class="vl-group-title">{{ group.label }}</h3>
              <span class="vl-group-count">{{ group.items.length }}</span>
            </div>
            <div class="vl-grid">
              <VacancyCard
                v-for="v in group.items" :key="v.id"
                :vacancy="v" :stats="getStats(v.id)"
                @view="goView" @edit="goEdit" @clone="doClone"
                @archive="doArchive" @delete="doDelete"
                @complete="doComplete" @reopen="doReopen"
              />
            </div>
          </div>
        </template>
      </template>

      <!-- Плоский список (другие сортировки) -->
      <div v-else class="vl-grid">
        <VacancyCard
          v-for="v in sortedVacancies" :key="v.id"
          :vacancy="v" :stats="getStats(v.id)"
          @view="goView" @edit="goEdit" @clone="doClone"
          @archive="doArchive" @delete="doDelete"
          @complete="doComplete" @reopen="doReopen"
        />
      </div>
    </template>

    <!-- Пустое состояние -->
    <div v-else class="vl-state vl-empty">
      <div class="vl-state-icon">📭</div>
      <h3>Нет вакансий</h3>
      <p v-if="hasActiveFilters">Попробуйте изменить фильтры</p>
      <p v-else>Создайте первую вакансию, чтобы начать анализ резюме</p>
      <button v-if="hasActiveFilters" class="btn btn-secondary" @click="resetFilters">Сбросить фильтры</button>
      <router-link v-else to="/vacancies/new" class="btn btn-primary">➕ Создать вакансию</router-link>
    </div>

    <!-- Confirm dialog -->
    <Teleport to="body">
      <Transition name="confirm-fade">
        <div v-if="confirm.show" class="vl-overlay" @click.self="confirm.show = false">
          <div class="vl-confirm">
            <div class="vl-confirm-icon">{{ confirm.icon }}</div>
            <h3>{{ confirm.title }}</h3>
            <p>{{ confirm.message }}</p>
            <div class="vl-confirm-btns">
              <button class="btn btn-secondary" @click="confirm.show = false">Отмена</button>
              <button class="btn" :class="confirm.danger ? 'btn-danger' : 'btn-primary'" @click="confirm.action">
                {{ confirm.btnText }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useVacanciesStore } from '@/stores/vacancies'
import { useToast } from '@/composables/useToast'
import api from '@/services/api'
import VacancyCard from './VacancyCard.vue'

const router = useRouter()
const store = useVacanciesStore()
const toast = useToast()

const loading = computed(() => store.loading)
const error = computed(() => store.error)
const vacancies = computed(() => store.vacancies)

const showFilters = ref(false)
const filters = reactive({ search: '', status: '', client: '', sortBy: 'status' })
const vacancyStats = ref({})
const confirm = reactive({ show: false, title: '', message: '', icon: '⚠️', btnText: 'OK', danger: false, action: null })

const hasActiveFilters = computed(() => filters.search || filters.status || filters.client)

// Сортировка
const sortedVacancies = computed(() => {
  let list = [...vacancies.value]
  switch (filters.sortBy) {
    case 'newest': list.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)); break
    case 'oldest': list.sort((a, b) => new Date(a.created_at) - new Date(b.created_at)); break
    case 'title':  list.sort((a, b) => a.title.localeCompare(b.title)); break
    default: // status — сортировка уже с бэкенда
      break
  }
  return list
})

// Группы по статусу
const statusGroups = computed(() => [
  { key: 'active',    label: 'Активные',     items: sortedVacancies.value.filter(v => v.status === 'active') },
  { key: 'completed', label: 'Завершённые',  items: sortedVacancies.value.filter(v => v.status === 'completed') },
  { key: 'archived',  label: 'В архиве',     items: sortedVacancies.value.filter(v => v.status === 'archived') },
])

const getStats = (id) => vacancyStats.value[id] || { analysesCount: 0, averageScore: null }

// Загрузка
const loadVacancies = async () => {
  await store.fetchVacancies({
    status: filters.status || undefined,
    search: filters.search || undefined,
    client: filters.client || undefined,
  })
}

const loadStats = async () => {
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
      counts[id].averageScore = s.length ? s.reduce((a, b) => a + b, 0) / s.length : null
    }
    vacancyStats.value = counts
  } catch { /* silent */ }
}

let searchTimeout
const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(loadVacancies, 300)
}

const resetFilters = () => {
  filters.search = ''; filters.status = ''; filters.client = ''; filters.sortBy = 'status'
  loadVacancies()
}

// Навигация
const goView = (id) => router.push(`/vacancies/${id}`)
const goEdit = (id) => router.push(`/vacancies/${id}/edit`)

// Confirm helpers
const showConfirm = (opts) => Object.assign(confirm, { show: true, ...opts })

const doClone = (id) => showConfirm({
  title: 'Создать копию?', message: 'Будет создана полная копия вакансии.', icon: '📋', btnText: 'Создать', danger: false,
  action: async () => { confirm.show = false; try { await store.cloneVacancy(id); toast.success('Вакансия клонирована') } catch { toast.error('Ошибка клонирования') } }
})

const doComplete = (id) => {
  const v = vacancies.value.find(x => x.id === id)
  showConfirm({
    title: 'Завершить вакансию?', message: `Вакансия «${v?.title}» будет отмечена как завершённая.`, icon: '✅', btnText: 'Завершить', danger: false,
    action: async () => { confirm.show = false; try { await store.completeVacancy(id); toast.success('Вакансия завершена') } catch { toast.error('Ошибка') } }
  })
}

const doReopen = (id) => {
  const v = vacancies.value.find(x => x.id === id)
  showConfirm({
    title: 'Возобновить вакансию?', message: `Вакансия «${v?.title}» снова станет активной.`, icon: '▶️', btnText: 'Возобновить', danger: false,
    action: async () => { confirm.show = false; try { await store.reopenVacancy(id); toast.success('Вакансия активирована') } catch { toast.error('Ошибка') } }
  })
}

const doArchive = (id) => {
  const v = vacancies.value.find(x => x.id === id)
  showConfirm({
    title: 'Перевести в архив?', message: `Вакансия «${v?.title}» будет перемещена в архив.`, icon: '📦', btnText: 'В архив', danger: true,
    action: async () => { confirm.show = false; try { await store.deleteVacancy(id); toast.success('Вакансия в архиве') } catch { toast.error('Ошибка') } }
  })
}

const doDelete = (id) => {
  const v = vacancies.value.find(x => x.id === id)
  showConfirm({
    title: 'Удалить вакансию?', message: `Вакансия «${v?.title}» будет удалена.`, icon: '🗑️', btnText: 'Удалить', danger: true,
    action: async () => { confirm.show = false; try { await store.deleteVacancy(id); toast.success('Вакансия удалена') } catch { toast.error('Ошибка') } }
  })
}

onMounted(() => { loadVacancies(); loadStats() })
</script>

<style scoped>
.vl { max-width: 1200px; margin: 0 auto; }

.vl-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing); flex-wrap: wrap; gap: var(--spacing-sm); }
.vl-title { font-size: 28px; font-weight: 600; color: var(--color-text); }
.vl-header-actions { display: flex; gap: var(--spacing-xs); }

/* Фильтры */
.vl-filters { padding: var(--spacing-sm); margin-bottom: var(--spacing); animation: slideDown 0.2s ease; }
@keyframes slideDown { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
.vl-filters-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: var(--spacing-xs); margin-bottom: var(--spacing-xs); }
.vl-filter { display: flex; flex-direction: column; gap: 4px; }
.vl-filter label { font-size: 12px; font-weight: 600; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.04em; }
.vl-filters-actions { display: flex; justify-content: space-between; align-items: center; padding-top: var(--spacing-xs); border-top: 1px solid var(--color-border); }
.vl-count { font-size: 13px; color: var(--color-text-muted); }

/* Группы */
.vl-group { margin-bottom: var(--spacing); }
.vl-group-header { display: flex; align-items: center; gap: var(--spacing-xs); margin-bottom: var(--spacing-xs); padding: 0 4px; }
.vl-group-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.dot--active    { background: #10b981; }
.dot--completed { background: #f59e0b; }
.dot--archived  { background: #9ca3af; }
.vl-group-title { font-size: 15px; font-weight: 600; color: var(--color-text-light); margin: 0; }
.vl-group-count { font-size: 12px; color: var(--color-text-muted); background: var(--color-surface-darker); padding: 2px 8px; border-radius: var(--border-radius-pill); }

/* Сетка */
.vl-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: var(--spacing-sm); }

/* Состояния */
.vl-state { text-align: center; padding: 48px var(--spacing); background: var(--color-surface); border-radius: var(--border-radius); border: 1px solid var(--color-border); }
.vl-state-icon { font-size: 48px; display: block; margin-bottom: var(--spacing-sm); opacity: 0.5; }
.vl-state h3 { font-size: 20px; margin-bottom: var(--spacing-xs); }
.vl-state p { color: var(--color-text-muted); margin-bottom: var(--spacing); }

/* Confirm */
.vl-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 9000; padding: 24px; }
.vl-confirm { background: var(--color-surface); border-radius: var(--border-radius); max-width: 420px; width: 90%; padding: var(--spacing); text-align: center; box-shadow: 0 24px 60px rgba(18,78,115,.2); }
.vl-confirm-icon { font-size: 40px; margin-bottom: 12px; }
.vl-confirm h3 { font-size: 18px; font-weight: 600; margin-bottom: 8px; color: var(--color-text); }
.vl-confirm p { color: var(--color-text-light); font-size: 14px; line-height: 1.5; margin-bottom: var(--spacing); }
.vl-confirm-btns { display: flex; gap: 12px; justify-content: center; }
.btn-danger { background: #ef4444; color: white; }
.btn-danger:hover { background: #dc2626; }
.confirm-fade-enter-active, .confirm-fade-leave-active { transition: all .2s ease; }
.confirm-fade-enter-from, .confirm-fade-leave-to { opacity: 0; }

@media (max-width: 768px) {
  .vl-grid { grid-template-columns: 1fr; }
  .vl-header { flex-direction: column; align-items: stretch; }
  .vl-header-actions { width: 100%; }
  .vl-header-actions .btn { flex: 1; }
}
</style>
