<template>
  <div
    class="vc"
    :class="[`vc--${vacancy.status || 'active'}`, { 'vc--inactive': vacancy.status === 'archived' }]"
    @click="$emit('view', vacancy.id)"
  >
    <!-- Цветная полоса статуса -->
    <div class="vc-status-bar" :class="`bar--${vacancy.status || 'active'}`"></div>

    <div class="vc-body">
      <!-- Заголовок -->
      <div class="vc-header">
        <div class="vc-title-row">
          <h3 class="vc-title">{{ vacancy.title }}</h3>
          <span class="vc-status-tag" :class="`tag--${vacancy.status || 'active'}`">
            {{ statusLabel }}
          </span>
        </div>
        <div class="vc-subtitle" v-if="vacancy.location || vacancy.client">
          <span v-if="vacancy.location" class="vc-location">📍 {{ vacancy.location }}</span>
          <span v-if="vacancy.client" class="vc-client">👤 {{ vacancy.client }}</span>
        </div>
      </div>

      <!-- Зарплата -->
      <div class="vc-salary" v-if="hasSalary">
        💰 {{ formatSalary }}
      </div>

      <!-- Навыки -->
      <div class="vc-skills" v-if="vacancy.key_skills?.length">
        <span
          v-for="skill in vacancy.key_skills.slice(0, 5)"
          :key="skill"
          class="vc-skill"
        >{{ skill }}</span>
        <span v-if="vacancy.key_skills.length > 5" class="vc-skill vc-skill--more">
          +{{ vacancy.key_skills.length - 5 }}
        </span>
      </div>

      <!-- Мини-статистика -->
      <div class="vc-stats" v-if="stats.analysesCount > 0">
        <span class="vc-stat">📊 {{ stats.analysesCount }} {{ pluralize(stats.analysesCount, ['анализ', 'анализа', 'анализов']) }}</span>
        <span class="vc-stat" v-if="stats.averageScore">· ⭐ {{ stats.averageScore.toFixed(0) }}%</span>
      </div>

      <!-- Дата -->
      <div class="vc-meta">
        <span class="vc-date">{{ formatDate(vacancy.created_at) }}</span>
      </div>
    </div>

    <!-- Действия -->
    <div class="vc-actions" @click.stop>
      <!-- Левая группа: опасные -->
      <div class="vc-actions-left">
        <button class="vc-btn vc-btn--danger" @click="$emit('archive', vacancy.id)" title="В архив" v-if="vacancy.status !== 'archived'">📦</button>
        <button class="vc-btn vc-btn--danger" @click="$emit('delete', vacancy.id)" title="Удалить">🗑️</button>
      </div>
      <!-- Правая группа: активные -->
      <div class="vc-actions-right">
        <button class="vc-btn vc-btn--complete" @click="$emit('complete', vacancy.id)" title="Завершить" v-if="vacancy.status === 'active'">✅</button>
        <button class="vc-btn vc-btn--reopen" @click="$emit('reopen', vacancy.id)" title="Возобновить" v-if="vacancy.status !== 'active'">▶️</button>
        <button class="vc-btn vc-btn--neutral" @click="$emit('clone', vacancy.id)" title="Клонировать">📋</button>
        <button class="vc-btn vc-btn--primary" @click="$emit('edit', vacancy.id)" title="Редактировать">✏️</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatDistance } from 'date-fns'
import { ru } from 'date-fns/locale'

const props = defineProps({
  vacancy: { type: Object, required: true },
  stats: { type: Object, default: () => ({ analysesCount: 0, averageScore: null }) },
})

defineEmits(['view', 'edit', 'clone', 'archive', 'delete', 'complete', 'reopen'])

const statusLabel = computed(() => {
  const map = { active: 'Активна', completed: 'Завершена', archived: 'В архиве' }
  return map[props.vacancy.status] || map.active
})

const hasSalary = computed(() => {
  const sr = props.vacancy.salary_range
  return sr && (sr.min || sr.max)
})

const formatSalary = computed(() => {
  const sr = props.vacancy.salary_range
  if (!sr) return ''
  const fmt = (v) => new Intl.NumberFormat('ru-RU').format(v)
  const parts = []
  if (sr.min) parts.push(`от ${fmt(sr.min)}`)
  if (sr.max) parts.push(`до ${fmt(sr.max)}`)
  return `${parts.join(' ')} ${sr.currency || 'RUB'}`
})

const formatDate = (d) => {
  if (!d) return ''
  return formatDistance(new Date(d), new Date(), { addSuffix: true, locale: ru })
}

const pluralize = (count, words) => {
  const cases = [2, 0, 1, 1, 1, 2]
  return words[count % 100 > 4 && count % 100 < 20 ? 2 : cases[Math.min(count % 10, 5)]]
}
</script>

<style scoped>
.vc {
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  overflow: hidden;
  transition: var(--transition);
  cursor: pointer;
  position: relative;
}
.vc:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 40px var(--color-shadow-strong);
}
.vc--archived { opacity: 0.6; }

/* Цветная полоса */
.vc-status-bar { height: 4px; flex-shrink: 0; }
.bar--active    { background: #10b981; }
.bar--completed { background: #f59e0b; }
.bar--archived  { background: #9ca3af; }

.vc-body { padding: var(--spacing-sm) var(--spacing); flex: 1; }

.vc-header { margin-bottom: var(--spacing-xs); }
.vc-title-row { display: flex; align-items: center; gap: var(--spacing-xs); flex-wrap: wrap; margin-bottom: 4px; }
.vc-title { font-size: 17px; font-weight: 600; color: var(--color-text); margin: 0; flex: 1; line-height: 1.3; }
.vc-status-tag {
  font-size: 11px; font-weight: 600; padding: 2px 10px;
  border-radius: var(--border-radius-pill); white-space: nowrap;
}
.tag--active    { background: #ecfdf5; color: #065f46; }
.tag--completed { background: #fffbeb; color: #92400e; }
.tag--archived  { background: #f3f4f6; color: #6b7280; }

.vc-subtitle { display: flex; gap: var(--spacing-sm); font-size: 13px; color: var(--color-text-light); flex-wrap: wrap; }
.vc-location, .vc-client { display: flex; align-items: center; gap: 3px; }

.vc-salary {
  font-size: 15px; font-weight: 600; color: var(--color-primary-dark);
  margin-bottom: var(--spacing-xs);
}

.vc-skills { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: var(--spacing-xs); }
.vc-skill {
  padding: 3px 10px; background: var(--color-primary-soft); border: 1px solid rgba(16,106,183,0.15);
  border-radius: var(--border-radius-pill); font-size: 12px; color: var(--color-primary-dark);
}
.vc-skill--more { background: var(--color-surface-darker); color: var(--color-text-muted); border-color: var(--color-border); }

.vc-stats {
  display: flex; gap: var(--spacing-xs); font-size: 13px; color: var(--color-text-light);
  margin-bottom: var(--spacing-xxs);
}

.vc-meta { font-size: 12px; color: var(--color-text-muted); }

/* Действия */
.vc-actions {
  display: flex; justify-content: space-between; align-items: center;
  padding: var(--spacing-xxs) var(--spacing-sm);
  border-top: 1px solid var(--color-border);
  background: var(--color-surface-darker);
}
.vc-actions-left, .vc-actions-right { display: flex; gap: 4px; }

.vc-btn {
  width: 34px; height: 34px; border: 1.5px solid var(--color-border); border-radius: 50%;
  background: var(--color-surface); cursor: pointer; transition: var(--transition);
  font-size: 15px; display: flex; align-items: center; justify-content: center;
}
.vc-btn:hover { transform: translateY(-2px); }
.vc-btn--primary:hover  { background: var(--color-primary-soft); border-color: var(--color-primary); }
.vc-btn--neutral:hover  { background: #e0f2fe; border-color: #0ea5e9; }
.vc-btn--complete:hover { background: #ecfdf5; border-color: #10b981; }
.vc-btn--reopen:hover   { background: #ecfdf5; border-color: #10b981; }
.vc-btn--danger:hover   { background: #fef2f2; border-color: #ef4444; }

@media (max-width: 640px) {
  .vc-body { padding: var(--spacing-xs) var(--spacing-sm); }
  .vc-actions { flex-wrap: wrap; gap: 4px; }
}
</style>
