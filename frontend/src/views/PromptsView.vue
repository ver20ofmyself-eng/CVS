<template>
  <div class="prompts-view">
    <div class="container">

      <!-- Заголовок -->
      <div class="page-header">
        <h1 class="page-title">⚙️ Управление промптами</h1>
        <button class="btn btn-primary" @click="openCreate">
          ➕ Новый промпт
        </button>
      </div>

      <!-- Фильтры -->
      <div class="filters-panel card">
        <div class="filters-row">
          <div class="filter-group">
            <label class="filter-label">🔍 Поиск по названию</label>
            <input v-model="filters.search" type="text" class="input" placeholder="Название промпта..." />
          </div>
          <div class="filter-group">
            <label class="filter-label">📅 Создан от</label>
            <input v-model="filters.dateFrom" type="date" class="input" />
          </div>
          <div class="filter-group">
            <label class="filter-label">📅 Создан до</label>
            <input v-model="filters.dateTo" type="date" class="input" />
          </div>
          <div class="filter-group">
            <label class="filter-label">Статус</label>
            <select v-model="filters.status" class="select">
              <option value="all">Все</option>
              <option value="active">Активные</option>
              <option value="archived">Архив</option>
            </select>
          </div>
          <button class="btn btn-secondary filter-reset" @click="resetFilters">Сбросить</button>
        </div>
      </div>

      <!-- Загрузка -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка промптов...</p>
      </div>

      <!-- Ошибка -->
      <div v-else-if="error" class="error-state">
        <span>❌</span><p>{{ error }}</p>
        <button class="btn btn-primary" @click="loadPrompts">Повторить</button>
      </div>

      <!-- Список -->
      <template v-else>
        <div v-if="!filteredPrompts.length" class="empty-state">
          <span class="empty-icon">📭</span>
          <p>Промпты не найдены</p>
          <button class="btn btn-primary" @click="openCreate">Создать первый промпт</button>
        </div>

        <div v-else class="prompts-list">
          <div
            v-for="prompt in filteredPrompts"
            :key="prompt.id"
            class="prompt-card"
            :class="{ 'is-active': prompt.is_default, 'is-archived': !prompt.is_active }"
          >
            <!-- Статус-полоска -->
            <div class="card-status-bar">
              <span v-if="prompt.is_default" class="badge badge-active">✅ Активный</span>
              <span v-else-if="!prompt.is_active" class="badge badge-archived">📦 Архив</span>
              <span v-else class="badge badge-inactive">○ Неактивный</span>

              <span class="prompt-version">v{{ prompt.version }}</span>
            </div>

            <!-- Контент -->
            <div class="card-body">
              <h3 class="prompt-name">{{ prompt.name }}</h3>
              <p class="prompt-description">{{ prompt.description || '—' }}</p>
              <p class="prompt-preview">{{ truncate(prompt.system_prompt, 120) }}</p>

              <div class="prompt-meta">
                <span>🗓 {{ formatDate(prompt.created_at) }}</span>
                <span v-if="prompt.updated_at !== prompt.created_at">✏️ {{ formatDate(prompt.updated_at) }}</span>
              </div>
            </div>

            <!-- Действия -->
            <div class="card-actions">
              <button
                v-if="!prompt.is_default && prompt.is_active"
                class="btn btn-secondary btn-sm"
                @click="setActive(prompt)"
                title="Сделать активным"
              >
                ✅ Сделать активным
              </button>

              <button
                v-if="!isSystemPrompt(prompt)"
                class="btn btn-secondary btn-sm"
                @click="openEdit(prompt)"
                title="Редактировать"
              >
                ✏️
              </button>

              <button
                v-if="!isSystemPrompt(prompt) && prompt.is_active"
                class="btn btn-secondary btn-sm"
                @click="archivePrompt(prompt)"
                title="Архивировать"
              >
                📦
              </button>

              <button
                v-if="!isSystemPrompt(prompt) && !prompt.is_active"
                class="btn btn-secondary btn-sm"
                @click="restorePrompt(prompt)"
                title="Восстановить"
              >
                ♻️
              </button>

              <button
                v-if="!isSystemPrompt(prompt)"
                class="btn btn-sm btn-danger"
                @click="deletePrompt(prompt)"
                title="Удалить"
              >
                🗑️
              </button>

              <button class="btn btn-secondary btn-sm" @click="viewHistory(prompt)" title="История">
                📜
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- ── Модалка создания/редактирования ─────────────────────────────────── -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="modal.show" class="modal-overlay" @click.self="closeModal">
          <div class="modal-content">
            <div class="modal-header">
              <h3>{{ modal.isEdit ? 'Редактировать промпт' : 'Новый промпт' }}</h3>
              <button class="close-btn" @click="closeModal">×</button>
            </div>

            <div class="modal-body">
              <div class="form-group">
                <label class="form-label">Название <span class="required">*</span></label>
                <input v-model="modal.form.name" type="text" class="input" placeholder="default_cv_analyzer" :disabled="modal.isEdit && isSystemPrompt(modal.prompt)" />
                <span class="hint">Уникальный технический идентификатор (латиница, подчёркивания)</span>
              </div>

              <div class="form-group">
                <label class="form-label">Описание</label>
                <input v-model="modal.form.description" type="text" class="input" placeholder="Краткое описание назначения промпта" />
              </div>

              <div class="form-group">
                <label class="form-label">System Prompt <span class="required">*</span></label>
                <textarea v-model="modal.form.system_prompt" class="textarea" rows="6" placeholder="Ты опытный HR-специалист..."></textarea>
              </div>

              <div class="form-group">
                <label class="form-label">User Template <span class="required">*</span></label>
                <textarea v-model="modal.form.user_prompt_template" class="textarea" rows="10"
                  placeholder="Доступные переменные: {title}, {location}, {salary_range}, {key_skills}, {description_text}, {comment_for_ai}, {cv_text}"></textarea>
                <span class="hint">Переменные: <code>{'{'}title{'}'}</code> <code>{'{'}key_skills{'}'}</code> <code>{'{'}description_text{'}'}</code> <code>{'{'}cv_text{'}'}</code></span>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">Temperature</label>
                  <input v-model.number="modal.form.parameters.temperature" type="number" class="input" min="0" max="2" step="0.1" />
                </div>
                <div class="form-group">
                  <label class="form-label">Max tokens</label>
                  <input v-model.number="modal.form.parameters.max_tokens" type="number" class="input" min="100" max="8000" step="100" />
                </div>
              </div>

              <div v-if="modal.error" class="alert-error">⚠️ {{ modal.error }}</div>
            </div>

            <div class="modal-footer">
              <button class="btn btn-secondary" @click="closeModal">Отмена</button>
              <button class="btn btn-primary" @click="savePrompt" :disabled="modal.saving">
                <span v-if="modal.saving" class="spinner-sm"></span>
                <span v-else>{{ modal.isEdit ? 'Сохранить' : 'Создать' }}</span>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ── Модалка истории ──────────────────────────────────────────────────── -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="historyModal.show" class="modal-overlay" @click.self="historyModal.show = false">
          <div class="modal-content modal-wide">
            <div class="modal-header">
              <h3>📜 История: {{ historyModal.promptName }}</h3>
              <button class="close-btn" @click="historyModal.show = false">×</button>
            </div>
            <div class="modal-body">
              <div v-if="historyModal.loading" class="loading-inline">
                <div class="spinner"></div>
              </div>
              <div v-else-if="!historyModal.items.length" class="empty-inline">
                Изменений не было
              </div>
              <div v-else class="history-list">
                <div v-for="h in historyModal.items" :key="h.id" class="history-item">
                  <div class="history-meta">
                    <span class="history-version">v{{ h.version }}</span>
                    <span class="history-date">{{ formatDate(h.changed_at) }}</span>
                    <span class="history-comment">{{ h.change_comment || 'Обновление' }}</span>
                  </div>
                  <div class="history-preview">{{ truncate(h.system_prompt, 100) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ── Confirm dialog ──────────────────────────────────────────────────── -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="confirm.show" class="modal-overlay confirm-overlay" @click.self="confirm.show = false">
          <div class="confirm-box">
            <div class="confirm-icon">{{ confirm.icon }}</div>
            <h3>{{ confirm.title }}</h3>
            <p>{{ confirm.message }}</p>
            <div class="confirm-actions">
              <button class="btn btn-secondary" @click="confirm.show = false">Отмена</button>
              <button class="btn btn-primary" :class="{ 'btn-danger': confirm.danger }" @click="confirm.action">
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
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import api from '@/services/api'

// ── Состояние ─────────────────────────────────────────────────────────────────
const prompts = ref([])
const loading = ref(true)
const error   = ref(null)

const filters = reactive({
  search:   '',
  dateFrom: '',
  dateTo:   '',
  status:   'all'
})

// ── Модалки ───────────────────────────────────────────────────────────────────
const modal = reactive({
  show: false, isEdit: false, saving: false, error: '', prompt: null,
  form: { name: '', description: '', system_prompt: '', user_prompt_template: '', parameters: { temperature: 0.3, max_tokens: 1500 } }
})

const historyModal = reactive({ show: false, loading: false, items: [], promptName: '' })

const confirm = reactive({ show: false, title: '', message: '', icon: '⚠️', btnText: 'Подтвердить', danger: false, action: null })

// ── Системный промпт — нельзя редактировать/удалять ──────────────────────────
const SYSTEM_PROMPT_NAME = 'default_cv_analyzer'
const isSystemPrompt = (p) => p?.name === SYSTEM_PROMPT_NAME

// ── Computed ──────────────────────────────────────────────────────────────────
const filteredPrompts = computed(() => {
  return prompts.value.filter(p => {
    if (filters.search && !p.name.toLowerCase().includes(filters.search.toLowerCase()) &&
        !(p.description || '').toLowerCase().includes(filters.search.toLowerCase())) return false
    if (filters.status === 'active' && !p.is_active) return false
    if (filters.status === 'archived' && p.is_active) return false
    if (filters.dateFrom && p.created_at < filters.dateFrom) return false
    if (filters.dateTo && p.created_at > filters.dateTo + 'T23:59') return false
    return true
  })
})

// ── Загрузка ──────────────────────────────────────────────────────────────────
const loadPrompts = async () => {
  loading.value = true
  error.value   = null
  try {
    const { data } = await api.get('/prompts/?active_only=false&limit=100')
    // Сортируем: сначала дефолтный, потом активные, потом архив
    data.sort((a, b) => {
      if (a.is_default) return -1
      if (b.is_default) return 1
      if (a.is_active !== b.is_active) return b.is_active - a.is_active
      return new Date(b.created_at) - new Date(a.created_at)
    })
    prompts.value = data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Не удалось загрузить промпты'
  } finally {
    loading.value = false
  }
}

// ── CRUD ──────────────────────────────────────────────────────────────────────
const openCreate = () => {
  modal.isEdit = false
  modal.prompt = null
  modal.error  = ''
  modal.form   = { name: '', description: '', system_prompt: '', user_prompt_template: '', parameters: { temperature: 0.3, max_tokens: 1500 } }
  modal.show   = true
}

const openEdit = (prompt) => {
  modal.isEdit = true
  modal.prompt = prompt
  modal.error  = ''
  modal.form   = {
    name:                 prompt.name,
    description:          prompt.description || '',
    system_prompt:        prompt.system_prompt,
    user_prompt_template: prompt.user_prompt_template,
    parameters:           { temperature: prompt.parameters?.temperature ?? 0.3, max_tokens: prompt.parameters?.max_tokens ?? 1500 }
  }
  modal.show = true
}

const closeModal = () => { modal.show = false }

const savePrompt = async () => {
  if (!modal.form.name || !modal.form.system_prompt || !modal.form.user_prompt_template) {
    modal.error = 'Заполните обязательные поля: название, system prompt, user template'
    return
  }
  modal.saving = true
  modal.error  = ''
  try {
    const payload = {
      name:                 modal.form.name,
      description:          modal.form.description || undefined,
      system_prompt:        modal.form.system_prompt,
      user_prompt_template: modal.form.user_prompt_template,
      parameters:           modal.form.parameters
    }
    if (modal.isEdit) {
      await api.put(`/prompts/${modal.prompt.id}`, payload)
    } else {
      await api.post('/prompts/', payload)
    }
    closeModal()
    await loadPrompts()
  } catch (err) {
    modal.error = err.response?.data?.detail || 'Ошибка сохранения'
  } finally {
    modal.saving = false
  }
}

// ── Сделать активным ──────────────────────────────────────────────────────────
const setActive = (prompt) => {
  showConfirm({
    title:   'Сделать активным?',
    message: `Промпт «${prompt.name}» станет активным. Предыдущий активный промпт будет деактивирован.`,
    icon:    '✅',
    btnText: 'Сделать активным',
    action:  async () => {
      try {
        // Деактивируем текущий дефолтный
        const current = prompts.value.find(p => p.is_default)
        if (current) await api.put(`/prompts/${current.id}`, { is_default: false })
        // Активируем выбранный
        await api.put(`/prompts/${prompt.id}`, { is_default: true, is_active: true })
        await loadPrompts()
      } catch (e) { console.error(e) }
      confirm.show = false
    }
  })
}

// ── Архивировать / Восстановить ───────────────────────────────────────────────
const archivePrompt = (prompt) => {
  showConfirm({
    title:   'Архивировать промпт?',
    message: prompt.is_default
      ? '⚠️ Это активный промпт! После архивирования активным станет системный (default_cv_analyzer).'
      : `Промпт «${prompt.name}» будет перемещён в архив.`,
    icon:    '📦',
    btnText: 'Архивировать',
    danger:  prompt.is_default,
    action:  async () => {
      try {
        await api.delete(`/prompts/${prompt.id}`)   // soft delete = is_active: false
        // Если архивируем активный — восстанавливаем системный
        if (prompt.is_default) {
          const sys = prompts.value.find(p => isSystemPrompt(p))
          if (sys) await api.put(`/prompts/${sys.id}`, { is_default: true, is_active: true })
        }
        await loadPrompts()
      } catch (e) { console.error(e) }
      confirm.show = false
    }
  })
}

const restorePrompt = async (prompt) => {
  try {
    await api.put(`/prompts/${prompt.id}`, { is_active: true })
    await loadPrompts()
  } catch (e) { console.error(e) }
}

const deletePrompt = (prompt) => {
  showConfirm({
    title:   'Удалить промпт?',
    message: `Промпт «${prompt.name}» будет удалён безвозвратно. Это действие нельзя отменить.`,
    icon:    '🗑️',
    btnText: 'Удалить',
    danger:  true,
    action:  async () => {
      try {
        await api.delete(`/prompts/${prompt.id}`)
        await loadPrompts()
      } catch (e) { console.error(e) }
      confirm.show = false
    }
  })
}

// ── История ───────────────────────────────────────────────────────────────────
const viewHistory = async (prompt) => {
  historyModal.promptName = prompt.name
  historyModal.items      = []
  historyModal.loading    = true
  historyModal.show       = true
  try {
    const { data } = await api.get(`/prompts/${prompt.id}/history`)
    historyModal.items = data
  } catch (e) { console.error(e) }
  historyModal.loading = false
}

// ── Утилиты ───────────────────────────────────────────────────────────────────
const showConfirm = ({ title, message, icon = '⚠️', btnText = 'Подтвердить', danger = false, action }) => {
  Object.assign(confirm, { show: true, title, message, icon, btnText, danger, action })
}

const resetFilters = () => {
  filters.search = ''; filters.dateFrom = ''; filters.dateTo = ''; filters.status = 'all'
}

const formatDate = (d) => {
  if (!d) return '—'
  try { return format(new Date(d), 'dd.MM.yyyy HH:mm', { locale: ru }) } catch { return d }
}

const truncate = (text, len) => {
  if (!text) return '—'
  return text.length <= len ? text : text.slice(0, len) + '...'
}

onMounted(loadPrompts)
</script>

<style scoped>
.prompts-view { padding: var(--spacing) 0; min-height: calc(100vh - 140px); }

.page-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: var(--spacing);
}
.page-title { font-size: 28px; font-weight: 700; color: var(--color-text); }

/* Filters */
.filters-panel { padding: var(--spacing-sm); margin-bottom: var(--spacing); }
.filters-row { display: flex; gap: var(--spacing-sm); align-items: flex-end; flex-wrap: wrap; }
.filter-group { display: flex; flex-direction: column; gap: 5px; min-width: 160px; flex: 1; }
.filter-label { font-size: 13px; font-weight: 600; color: var(--color-text-muted); }
.filter-reset { align-self: flex-end; white-space: nowrap; }

/* Prompts list */
.prompts-list { display: flex; flex-direction: column; gap: var(--spacing-sm); }

.prompt-card {
  background: var(--color-surface); border-radius: var(--border-radius);
  border: 1px solid var(--color-border); overflow: hidden; transition: var(--transition);
}
.prompt-card:hover { box-shadow: 0 8px 30px var(--color-shadow); }
.prompt-card.is-active { border-color: var(--color-primary); border-width: 2px; }
.prompt-card.is-archived { opacity: 0.65; }

.card-status-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px var(--spacing-sm);
  background: var(--color-surface-darker); border-bottom: 1px solid var(--color-border);
}
.badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 10px; border-radius: var(--border-radius-pill); font-size: 12px; font-weight: 600;
}
.badge-active { background: var(--color-primary-soft); color: var(--color-primary-dark); }
.badge-inactive { background: var(--color-surface); color: var(--color-text-muted); border: 1px solid var(--color-border); }
.badge-archived { background: #f3f4f6; color: #6b7280; }
.prompt-version { font-size: 12px; color: var(--color-text-muted); font-style: italic; }

.card-body { padding: var(--spacing-sm) var(--spacing-sm) 0; }
.prompt-name { font-size: 16px; font-weight: 700; color: var(--color-text); margin-bottom: 4px; font-family: monospace; }
.prompt-description { font-size: 13px; color: var(--color-text-muted); margin-bottom: 6px; }
.prompt-preview {
  font-size: 13px; color: var(--color-text-light);
  background: var(--color-surface-darker); border-radius: 8px;
  padding: 8px 10px; line-height: 1.5; margin-bottom: 8px;
  white-space: pre-wrap; word-break: break-word;
}
.prompt-meta { display: flex; gap: var(--spacing-sm); font-size: 12px; color: var(--color-text-muted); padding-bottom: var(--spacing-xs); }

.card-actions {
  display: flex; gap: 8px; flex-wrap: wrap;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-top: 1px solid var(--color-border); background: var(--color-surface-darker);
}
.btn-sm { padding: 5px 12px; font-size: 13px; }
.btn-danger { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }
.btn-danger:hover { background: #ef4444; color: white; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center;
  z-index: 9000; padding: var(--spacing);
}
.modal-content {
  background: var(--color-surface); border-radius: var(--border-radius);
  width: 100%; max-width: 680px; max-height: 90vh; overflow-y: auto;
  box-shadow: 0 24px 60px rgba(18,78,115,0.2);
}
.modal-wide { max-width: 780px; }
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: var(--spacing); border-bottom: 1px solid var(--color-border);
}
.modal-header h3 { font-size: 18px; font-weight: 600; color: var(--color-text); }
.close-btn {
  width: 32px; height: 32px; border: none; border-radius: 50%;
  background: var(--color-surface-darker); font-size: 20px;
  cursor: pointer; transition: var(--transition); display: flex; align-items: center; justify-content: center;
}
.close-btn:hover { background: var(--color-primary-soft); }
.modal-body { padding: var(--spacing); display: flex; flex-direction: column; gap: var(--spacing-sm); }
.modal-footer {
  display: flex; justify-content: flex-end; gap: var(--spacing-xs);
  padding: var(--spacing); border-top: 1px solid var(--color-border);
}

.form-group { display: flex; flex-direction: column; gap: 5px; }
.form-label { font-size: 13px; font-weight: 600; color: var(--color-text-light); }
.required { color: #ef4444; }
.hint { font-size: 12px; color: var(--color-text-muted); }
.hint code { background: var(--color-surface-darker); padding: 1px 5px; border-radius: 4px; font-size: 11px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-sm); }

.alert-error {
  padding: 10px 14px; background: var(--color-error);
  color: var(--color-error-text); border-radius: var(--border-radius-sm); font-size: 14px;
}

/* History */
.history-list { display: flex; flex-direction: column; gap: var(--spacing-xs); }
.history-item {
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-surface-darker); border-radius: var(--border-radius-sm);
  border-left: 3px solid var(--color-primary);
}
.history-meta { display: flex; gap: var(--spacing-sm); margin-bottom: 4px; font-size: 13px; }
.history-version { font-weight: 700; color: var(--color-primary); }
.history-date { color: var(--color-text-muted); }
.history-comment { color: var(--color-text-light); font-style: italic; }
.history-preview { font-size: 12px; color: var(--color-text-muted); white-space: pre-wrap; }

/* Confirm */
.confirm-overlay { z-index: 9500; }
.confirm-box {
  background: var(--color-surface); border-radius: var(--border-radius);
  max-width: 420px; width: 90%; padding: var(--spacing);
  text-align: center; box-shadow: 0 24px 60px rgba(18,78,115,0.2);
}
.confirm-icon { font-size: 40px; margin-bottom: var(--spacing-xs); }
.confirm-box h3 { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
.confirm-box p { color: var(--color-text-light); font-size: 14px; line-height: 1.5; margin-bottom: var(--spacing); }
.confirm-actions { display: flex; gap: var(--spacing-xs); justify-content: center; }

/* States */
.loading-state, .error-state, .empty-state {
  text-align: center; padding: calc(var(--spacing) * 2);
  background: var(--color-surface); border-radius: var(--border-radius); border: 1px solid var(--color-border);
}
.empty-icon { font-size: 48px; display: block; margin-bottom: var(--spacing-sm); }
.loading-inline, .empty-inline { text-align: center; padding: var(--spacing); color: var(--color-text-muted); }

.spinner {
  width: 36px; height: 36px; border: 3px solid var(--color-border);
  border-top-color: var(--color-primary); border-radius: 50%;
  animation: spin 0.7s linear infinite; margin: 0 auto var(--spacing-sm);
}
.spinner-sm {
  display: inline-block; width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.3); border-top-color: white;
  border-radius: 50%; animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Transitions */
.modal-enter-active, .modal-leave-active { transition: all 0.2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal-content, .modal-enter-from .confirm-box { transform: scale(0.95); }

@media (max-width: 768px) {
  .filters-row { flex-direction: column; }
  .filter-group { min-width: 100%; }
  .form-row { grid-template-columns: 1fr; }
  .card-actions { flex-wrap: wrap; }
}
</style>
