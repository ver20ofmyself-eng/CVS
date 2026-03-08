<template>
  <div class="vacancy-card" :class="{ 'inactive': !vacancy.is_active }">
    <div class="card-header">
      <div class="title-section">
        <h3 class="vacancy-title">{{ vacancy.title }}</h3>
        <span class="vacancy-status" :class="statusClass">
          {{ vacancy.is_active ? 'Активна' : 'Архив' }}
        </span>
      </div>
      
      <div class="location" v-if="vacancy.location">
        <span class="icon">📍</span>
        {{ vacancy.location }}
      </div>
    </div>

    <!-- Зарплата -->
    <div class="salary" v-if="vacancy.salary_range?.min || vacancy.salary_range?.max">
      <span class="icon">💰</span>
      <span v-if="vacancy.salary_range.min && vacancy.salary_range.max">
        {{ formatSalary(vacancy.salary_range.min) }} – {{ formatSalary(vacancy.salary_range.max) }}
      </span>
      <span v-else-if="vacancy.salary_range.min">
        от {{ formatSalary(vacancy.salary_range.min) }}
      </span>
      <span v-else-if="vacancy.salary_range.max">
        до {{ formatSalary(vacancy.salary_range.max) }}
      </span>
      <span class="currency">{{ vacancy.salary_range.currency || 'RUB' }}</span>
    </div>

    <!-- Ключевые навыки -->
    <div class="skills" v-if="vacancy.key_skills?.length">
      <span class="icon">🔧</span>
      <div class="skills-list">
        <span 
          v-for="skill in displayedSkills" 
          :key="skill"
          class="skill-tag"
        >
          {{ skill }}
        </span>
        <span 
          v-if="hasMoreSkills" 
          class="skill-tag more-skills"
          :title="hiddenSkills.join(', ')"
        >
          +{{ hiddenSkills.length }}
        </span>
      </div>
    </div>

    <!-- Метаданные -->
    <div class="metadata">
      <span class="meta-item" :title="formatDate(vacancy.created_at, 'full')">
        <span class="icon">📅</span>
        {{ formatDate(vacancy.created_at) }}
      </span>
      <span class="meta-item" v-if="stats.analysesCount !== undefined">
        <span class="icon">📊</span>
        {{ stats.analysesCount }} {{ pluralize(stats.analysesCount, ['анализ', 'анализа', 'анализов']) }}
      </span>
      <span class="meta-item" v-if="stats.averageScore">
        <span class="icon">⭐</span>
        {{ stats.averageScore.toFixed(1) }}
      </span>
    </div>

    <!-- Действия -->
    <div class="card-actions">
      <button 
        class="action-btn view" 
        @click="$emit('view', vacancy.id)"
        title="Просмотр деталей"
      >
        👁️
      </button>
      <button 
        class="action-btn edit" 
        @click="$emit('edit', vacancy.id)"
        title="Редактировать"
      >
        ✏️
      </button>
      <button 
        class="action-btn clone" 
        @click="$emit('clone', vacancy.id)"
        title="Клонировать"
      >
        📋
      </button>
      <button 
        class="action-btn toggle" 
        @click="$emit('toggle', vacancy.id)"
        :title="vacancy.is_active ? 'В архив' : 'Активировать'"
      >
        {{ vacancy.is_active ? '📦' : '▶️' }}
      </button>
      <button 
        class="action-btn delete" 
        @click="$emit('delete', vacancy.id)"
        title="Удалить"
      >
        🗑️
      </button>
    </div>

    <!-- Прогресс-бар анализов (опционально) -->
    <div class="progress-bar" v-if="showProgress && stats.matchRate">
      <div class="progress-fill" :style="{ width: stats.matchRate + '%' }"></div>
      <span class="progress-text">{{ stats.matchRate }}% совпадений</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatDistance, format } from 'date-fns'
import { ru } from 'date-fns/locale'

const props = defineProps({
  vacancy: {
    type: Object,
    required: true
  },
  stats: {
    type: Object,
    default: () => ({
      analysesCount: 0,
      averageScore: null,
      matchRate: null
    })
  },
  showProgress: {
    type: Boolean,
    default: false
  }
})

defineEmits(['view', 'edit', 'clone', 'toggle', 'delete'])

// Статус CSS класс
const statusClass = computed(() => ({
  'status-active': props.vacancy.is_active,
  'status-inactive': !props.vacancy.is_active
}))

// Отображаемые навыки (первые 5)
const displayedSkills = computed(() => 
  props.vacancy.key_skills?.slice(0, 5) || []
)

const hasMoreSkills = computed(() => 
  (props.vacancy.key_skills?.length || 0) > 5
)

const hiddenSkills = computed(() => 
  props.vacancy.key_skills?.slice(5) || []
)

// Форматирование зарплаты
const formatSalary = (value) => {
  if (!value) return ''
  return new Intl.NumberFormat('ru-RU').format(value)
}

// Форматирование даты
const formatDate = (dateString, type = 'relative') => {
  if (!dateString) return ''
  const date = new Date(dateString)
  
  if (type === 'relative') {
    return formatDistance(date, new Date(), { 
      addSuffix: true, 
      locale: ru 
    })
  }
  
  return format(date, 'dd.MM.yyyy HH:mm', { locale: ru })
}

// Плюрализация
const pluralize = (count, words) => {
  const cases = [2, 0, 1, 1, 1, 2]
  return words[
    count % 100 > 4 && count % 100 < 20 
      ? 2 
      : cases[Math.min(count % 10, 5)]
  ]
}
</script>

<style scoped>
.vacancy-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}

.vacancy-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px var(--color-shadow-strong);
}

.vacancy-card.inactive {
  opacity: 0.7;
  background: var(--color-surface-darker);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-xs);
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.title-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.vacancy-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.vacancy-status {
  font-size: 12px;
  padding: 4px 8px;
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

.location {
  color: var(--color-text-light);
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.salary {
  color: var(--color-primary-dark);
  font-weight: 600;
  font-size: 16px;
  margin-bottom: var(--spacing-xs);
  display: flex;
  align-items: center;
  gap: 4px;
}

.currency {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-left: 2px;
}

.skills {
  margin-bottom: var(--spacing-xs);
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.skills-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  flex: 1;
}

.skill-tag {
  padding: 4px 10px;
  background: var(--color-primary-soft);
  border-radius: var(--border-radius-pill);
  font-size: 12px;
  color: var(--color-primary-dark);
  border: 1px solid var(--color-primary);
  white-space: nowrap;
}

.more-skills {
  background: var(--color-surface);
  color: var(--color-text-muted);
  border-color: var(--color-border);
  cursor: help;
}

.metadata {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
  font-size: 12px;
  color: var(--color-text-muted);
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.icon {
  font-size: 14px;
  opacity: 0.7;
}

.card-actions {
  display: flex;
  gap: 8px;
  margin-top: var(--spacing-xs);
  padding-top: var(--spacing-xs);
  border-top: 1px solid var(--color-border);
}

.action-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: var(--color-surface-lighter);
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: var(--transition);
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  transform: translateY(-2px);
}

.action-btn.view:hover {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
}

.action-btn.edit:hover {
  background: #fef3c7;
  border-color: #fbbf24;
}

.action-btn.clone:hover {
  background: #e0f2fe;
  border-color: #0ea5e9;
}

.action-btn.toggle:hover {
  background: #dcfce7;
  border-color: #22c55e;
}

.action-btn.delete:hover {
  background: #fee2e2;
  border-color: #ef4444;
}

.progress-bar {
  margin-top: var(--spacing-xs);
  height: 24px;
  background: var(--color-border);
  border-radius: var(--border-radius-pill);
  position: relative;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  transition: width 0.3s ease;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 11px;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
  white-space: nowrap;
}

@media (max-width: 640px) {
  .vacancy-card {
    padding: var(--spacing-sm);
  }
  
  .card-actions {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .metadata {
    flex-direction: column;
    gap: 4px;
  }
}
</style>
