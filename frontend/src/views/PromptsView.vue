<template>
  <div class="prompts-view">
    <div class="container">

      <div class="page-header">
        <h1 class="page-title">⚙️ Управление промптами</h1>
        <button class="btn btn-primary" @click="openCreate">➕ Новый промпт</button>
      </div>

      <!-- Фильтры и сортировка -->
      <div class="filters-panel card">
        <div class="filters-row">
          <div class="filter-group filter-grow">
            <label class="filter-label">🔍 Поиск</label>
            <input v-model="filters.search" type="text" class="input" placeholder="Название или описание..." />
          </div>
          <div class="filter-group">
            <label class="filter-label">Статус</label>
            <select v-model="filters.status" class="select">
              <option value="all">Все</option>
              <option value="active">Активные</option>
              <option value="archived">Архив</option>
            </select>
          </div>
          <div class="filter-group">
            <label class="filter-label">Сортировка</label>
            <select v-model="filters.sortBy" class="select">
              <option value="default_first">По умолчанию</option>
              <option value="created_desc">Дата создания ↓</option>
              <option value="created_asc">Дата создания ↑</option>
              <option value="updated_desc">Дата изменения ↓</option>
              <option value="updated_asc">Дата изменения ↑</option>
              <option value="name_asc">Название А–Я</option>
            </select>
          </div>
          <button class="btn btn-secondary" @click="resetFilters">Сбросить</button>
        </div>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка промптов...</p>
      </div>
      <div v-else-if="error" class="error-state card">
        <span class="state-icon">❌</span><p>{{ error }}</p>
        <button class="btn btn-primary" @click="loadPrompts">Повторить</button>
      </div>
      <div v-else-if="!filteredPrompts.length" class="empty-state card">
        <span class="state-icon">📭</span>
        <p>Промпты не найдены</p>
        <button class="btn btn-primary" @click="openCreate">Создать первый промпт</button>
      </div>

      <div v-else class="prompts-list">
        <div
          v-for="prompt in filteredPrompts"
          :key="prompt.id"
          class="prompt-card"
          :class="{ 'is-main': prompt.is_default, 'is-archived': !prompt.is_active, 'is-system': isSystem(prompt) }"
        >
          <div class="card-status-bar">
            <div class="badges">
              <span v-if="isSystem(prompt)"     class="badge badge-system">🔒 Системный</span>
              <span v-if="prompt.is_default"    class="badge badge-main">⭐ Основной</span>
              <span v-if="!prompt.is_active"    class="badge badge-archived">📦 Архив</span>
              <span v-if="!prompt.is_default && prompt.is_active && !isSystem(prompt)"
                    class="badge badge-inactive">○ Неактивный</span>
            </div>
            <span class="prompt-version">v{{ prompt.version }}</span>
          </div>

          <div class="card-body">
            <h3 class="prompt-name">{{ prompt.name }}</h3>
            <p class="prompt-description">{{ prompt.description || '—' }}</p>
            <p class="prompt-preview">{{ truncate(prompt.system_prompt, 100) }}</p>
            <div class="prompt-meta">
              <span title="Создан">🗓 {{ formatDate(prompt.created_at) }}</span>
              <span v-if="prompt.updated_at && prompt.updated_at !== prompt.created_at" title="Изменён">
                ✏️ {{ formatDate(prompt.updated_at) }}
              </span>
              <span v-if="isSystem(prompt)" class="system-note">Глобальный · нельзя изменить</span>
            </div>
          </div>

          <div class="card-actions">
            <!-- Просмотр — для всех промптов -->
            <button class="btn btn-secondary btn-sm" @click="openView(prompt)" title="Просмотр">👁️ Просмотр</button>

            <!-- Сделать основным — только несистемные неосновные активные -->
            <button
              v-if="!isSystem(prompt) && !prompt.is_default && prompt.is_active"
              class="btn btn-secondary btn-sm"
              @click="setMain(prompt)"
            >⭐ Сделать основным</button>

            <!-- Редактировать — только несистемные -->
            <button v-if="!isSystem(prompt)" class="btn btn-secondary btn-sm" @click="openEdit(prompt)">✏️</button>

            <!-- Архив / Восстановить -->
            <button v-if="!isSystem(prompt) && prompt.is_active"  class="btn btn-secondary btn-sm" @click="doArchive(prompt)" title="Архивировать">📦</button>
            <button v-if="!isSystem(prompt) && !prompt.is_active" class="btn btn-secondary btn-sm" @click="doRestore(prompt)" title="Восстановить">♻️</button>

            <!-- Удалить — только несистемные -->
            <button v-if="!isSystem(prompt)" class="btn btn-sm btn-danger" @click="doDelete(prompt)" title="Удалить навсегда">🗑️</button>

            <!-- История -->
            <button class="btn btn-secondary btn-sm" @click="showHistory(prompt)" title="История изменений">📜</button>
          </div>
        </div>
      </div>
    </div><!-- /container -->

    <!-- ── Просмотр промпта (read-only) ──────────────────────────────────── -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="viewModal.show" class="modal-overlay" @click.self="viewModal.show = false">
          <div class="modal-box modal-wide">
            <div class="modal-header">
              <div class="modal-title-block">
                <h3>{{ viewModal.prompt?.name }}</h3>
                <span v-if="isSystem(viewModal.prompt)" class="badge badge-system badge-sm">🔒 Системный</span>
                <span v-if="viewModal.prompt?.is_default" class="badge badge-main badge-sm">⭐ Основной</span>
              </div>
              <button class="close-btn" @click="viewModal.show = false">×</button>
            </div>
            <div class="modal-body">
              <div v-if="viewModal.prompt" class="view-sections">
                <div class="view-section">
                  <div class="view-label">Описание</div>
                  <div class="view-value">{{ viewModal.prompt.description || '—' }}</div>
                </div>
                <div class="view-section">
                  <div class="view-label">System Prompt</div>
                  <pre class="view-code">{{ viewModal.prompt.system_prompt }}</pre>
                </div>
                <div class="view-section">
                  <div class="view-label">User Template</div>
                  <pre class="view-code">{{ viewModal.prompt.user_prompt_template }}</pre>
                </div>
                <div class="view-section view-params">
                  <div class="view-label">Параметры</div>
                  <div class="params-grid">
                    <div class="param-item">
                      <span class="param-key">temperature</span>
                      <span class="param-val">{{ viewModal.prompt.parameters?.temperature ?? 0.3 }}</span>
                    </div>
                    <div class="param-item">
                      <span class="param-key">max_tokens</span>
                      <span class="param-val">{{ viewModal.prompt.parameters?.max_tokens ?? 1500 }}</span>
                    </div>
                    <div class="param-item">
                      <span class="param-key">version</span>
                      <span class="param-val">v{{ viewModal.prompt.version }}</span>
                    </div>
                    <div class="param-item">
                      <span class="param-key">создан</span>
                      <span class="param-val">{{ formatDate(viewModal.prompt.created_at) }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" @click="viewModal.show = false">Закрыть</button>
              <button v-if="!isSystem(viewModal.prompt)" class="btn btn-primary" @click="openEditFromView">
                ✏️ Редактировать
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ── Создание / редактирование ─────────────────────────────────────── -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="modal.show" class="modal-overlay" @click.self="closeModal">
          <div class="modal-box">
            <div class="modal-header">
              <h3>{{ modal.isEdit ? 'Редактировать промпт' : 'Новый промпт' }}</h3>
              <button class="close-btn" @click="closeModal">×</button>
            </div>
            <div class="modal-body">
              <div class="form-group">
                <label class="form-label">Название <span class="req">*</span></label>
                <input v-model="modal.form.name" class="input" placeholder="my_prompt_name" />
                <span class="hint">Уникальный идентификатор в рамках вашего профиля</span>
              </div>
              <div class="form-group">
                <label class="form-label">Описание</label>
                <input v-model="modal.form.description" class="input" placeholder="Краткое описание" />
              </div>
              <div class="form-group">
                <label class="form-label">System Prompt <span class="req">*</span></label>
                <textarea v-model="modal.form.system_prompt" class="textarea" rows="5"
                  placeholder="Ты опытный HR-специалист..."></textarea>
              </div>
              <div class="form-group">
                <label class="form-label">User Template <span class="req">*</span></label>
                <textarea v-model="modal.form.user_prompt_template" class="textarea" rows="10"
                  placeholder="Доступные переменные: {cv_text}, {title}, {key_skills}, {description_text}, {comment_for_ai}"></textarea>
                <span class="hint">
                  Переменные: <code>{cv_text}</code> <code>{title}</code>
                  <code>{key_skills}</code> <code>{description_text}</code> <code>{comment_for_ai}</code>
                </span>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">Temperature</label>
                  <input v-model.number="modal.form.temperature" type="number" class="input" min="0" max="2" step="0.1" />
                </div>
                <div class="form-group">
                  <label class="form-label">Max tokens</label>
                  <input v-model.number="modal.form.max_tokens" type="number" class="input" min="100" max="8000" step="100" />
                </div>
              </div>
              <div v-if="modal.error" class="alert-error">⚠️ {{ modal.error }}</div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" @click="closeModal">Отмена</button>
              <button class="btn btn-primary" @click="savePrompt" :disabled="modal.saving">
                <span v-if="modal.saving" class="spinner spinner-sm"></span>
                <span v-else>{{ modal.isEdit ? 'Сохранить' : 'Создать' }}</span>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ── История ──────────────────────────────────────────────────────── -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="hist.show" class="modal-overlay" @click.self="hist.show = false">
          <div class="modal-box modal-wide">
            <div class="modal-header">
              <h3>📜 История: {{ hist.name }}</h3>
              <button class="close-btn" @click="hist.show = false">×</button>
            </div>
            <div class="modal-body">
              <div v-if="hist.loading" class="state-inline"><div class="spinner"></div></div>
              <div v-else-if="!hist.items.length" class="state-inline">Изменений не было</div>
              <div v-else class="history-list">
                <div v-for="h in hist.items" :key="h.id" class="history-item">
                  <div class="history-meta">
                    <span class="hv">v{{ h.version }}</span>
                    <span class="hd">{{ formatDate(h.changed_at) }}</span>
                    <span class="hc">{{ h.change_comment || 'Обновление' }}</span>
                  </div>
                  <div class="history-preview">{{ truncate(h.system_prompt, 120) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ── Confirm ──────────────────────────────────────────────────────── -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="confirm.show" class="modal-overlay" @click.self="confirm.show = false">
          <div class="confirm-box">
            <div class="confirm-icon">{{ confirm.icon }}</div>
            <h3>{{ confirm.title }}</h3>
            <p>{{ confirm.message }}</p>
            <div class="confirm-actions">
              <button class="btn btn-secondary" @click="confirm.show = false">Отмена</button>
              <button class="btn btn-primary" :class="{ 'btn-danger-solid': confirm.danger }" @click="confirm.action">
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

const SYSTEM_NAME = 'default_cv_analyzer'
const isSystem = p => p && p.name === SYSTEM_NAME && !p.owner_id

const prompts = ref([])
const loading = ref(true)
const error   = ref(null)

const filters = reactive({ search: '', status: 'all', sortBy: 'default_first' })

const viewModal = reactive({ show: false, prompt: null })

const modal = reactive({
  show: false, isEdit: false, saving: false, error: '', prompt: null,
  form: { name: '', description: '', system_prompt: '', user_prompt_template: '', temperature: 0.3, max_tokens: 1500 }
})

const hist    = reactive({ show: false, loading: false, items: [], name: '' })
const confirm = reactive({ show: false, title: '', message: '', icon: '⚠️', btnText: 'Подтвердить', danger: false, action: null })

// ── Computed ──────────────────────────────────────────────────────────────────
const filteredPrompts = computed(() => {
  let list = [...prompts.value]
  if (filters.search) {
    const q = filters.search.toLowerCase()
    list = list.filter(p => p.name.toLowerCase().includes(q) || (p.description||'').toLowerCase().includes(q))
  }
  if (filters.status === 'active')   list = list.filter(p => p.is_active)
  if (filters.status === 'archived') list = list.filter(p => !p.is_active)

  switch (filters.sortBy) {
    case 'default_first':
      list.sort((a,b) => {
        if (isSystem(a)) return -1; if (isSystem(b)) return 1
        if (a.is_default !== b.is_default) return b.is_default - a.is_default
        if (a.is_active !== b.is_active) return b.is_active - a.is_active
        return new Date(b.created_at) - new Date(a.created_at)
      })
      break
    case 'created_desc': list.sort((a,b) => new Date(b.created_at) - new Date(a.created_at)); break
    case 'created_asc':  list.sort((a,b) => new Date(a.created_at) - new Date(b.created_at)); break
    case 'updated_desc': list.sort((a,b) => new Date(b.updated_at||b.created_at) - new Date(a.updated_at||a.created_at)); break
    case 'updated_asc':  list.sort((a,b) => new Date(a.updated_at||a.created_at) - new Date(b.updated_at||b.created_at)); break
    case 'name_asc':     list.sort((a,b) => a.name.localeCompare(b.name)); break
  }
  return list
})

// ── API ───────────────────────────────────────────────────────────────────────
const loadPrompts = async () => {
  loading.value = true; error.value = null
  try {
    const { data } = await api.get('/prompts/?active_only=false&limit=100')
    prompts.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Не удалось загрузить промпты'
  } finally { loading.value = false }
}

// ── Просмотр ──────────────────────────────────────────────────────────────────
const openView = (p) => { viewModal.prompt = p; viewModal.show = true }

const openEditFromView = () => {
  const p = viewModal.prompt
  viewModal.show = false
  openEdit(p)
}

// ── CRUD ──────────────────────────────────────────────────────────────────────
const openCreate = () => {
  Object.assign(modal, { show: true, isEdit: false, saving: false, error: '', prompt: null })
  modal.form = { name: '', description: '', system_prompt: '', user_prompt_template: '', temperature: 0.3, max_tokens: 1500 }
}

const openEdit = (p) => {
  Object.assign(modal, { show: true, isEdit: true, saving: false, error: '', prompt: p })
  modal.form = {
    name: p.name, description: p.description || '',
    system_prompt: p.system_prompt, user_prompt_template: p.user_prompt_template,
    temperature: p.parameters?.temperature ?? 0.3,
    max_tokens:  p.parameters?.max_tokens  ?? 1500,
  }
}

const closeModal = () => { modal.show = false }

const savePrompt = async () => {
  if (!modal.form.name || !modal.form.system_prompt || !modal.form.user_prompt_template) {
    modal.error = 'Заполните обязательные поля: название, system prompt, user template'
    return
  }
  modal.saving = true; modal.error = ''
  try {
    const payload = {
      name: modal.form.name, description: modal.form.description || undefined,
      system_prompt: modal.form.system_prompt,
      user_prompt_template: modal.form.user_prompt_template,
      parameters: { temperature: modal.form.temperature, max_tokens: modal.form.max_tokens }
    }
    if (modal.isEdit) await api.put(`/prompts/${modal.prompt.id}`, payload)
    else              await api.post('/prompts/', payload)
    closeModal()
    await loadPrompts()
  } catch (e) {
    modal.error = e.response?.data?.detail || 'Ошибка сохранения'
  } finally { modal.saving = false }
}

const setMain = (p) => {
  showConfirm({
    title: 'Сделать основным?',
    message: `Промпт «${p.name}» станет основным для вашего профиля. Предыдущий основной будет деактивирован.`,
    icon: '⭐', btnText: 'Сделать основным',
    action: async () => {
      try { await api.put(`/prompts/${p.id}`, { is_default: true, is_active: true }); await loadPrompts() }
      catch(e) { console.error(e) }
      confirm.show = false
    }
  })
}

const doArchive = (p) => {
  showConfirm({
    title: 'Архивировать промпт?',
    message: p.is_default
      ? '⚠️ Это основной промпт! После архивирования будет использоваться системный промпт.'
      : `Промпт «${p.name}» будет перемещён в архив.`,
    icon: '📦', btnText: 'Архивировать', danger: p.is_default,
    action: async () => {
      try { await api.delete(`/prompts/${p.id}`); await loadPrompts() }
      catch(e) { console.error(e) }
      confirm.show = false
    }
  })
}

const doRestore = async (p) => {
  try { await api.put(`/prompts/${p.id}`, { is_active: true }); await loadPrompts() }
  catch(e) { console.error(e) }
}

const doDelete = (p) => {
  showConfirm({
    title: 'Удалить промпт?',
    message: `Промпт «${p.name}» будет удалён безвозвратно.`,
    icon: '🗑️', btnText: 'Удалить', danger: true,
    action: async () => {
      try { await api.delete(`/prompts/${p.id}?hard=true`); await loadPrompts() }
      catch(e) { console.error(e) }
      confirm.show = false
    }
  })
}

const showHistory = async (p) => {
  hist.name = p.name; hist.items = []; hist.loading = true; hist.show = true
  try { const { data } = await api.get(`/prompts/${p.id}/history`); hist.items = data }
  catch(e) { console.error(e) }
  hist.loading = false
}

const showConfirm = ({ title, message, icon = '⚠️', btnText = 'Подтвердить', danger = false, action }) => {
  Object.assign(confirm, { show: true, title, message, icon, btnText, danger, action })
}

const resetFilters = () => { filters.search = ''; filters.status = 'all'; filters.sortBy = 'default_first' }

const formatDate = (d) => {
  if (!d) return '—'
  try { return format(new Date(d), 'dd.MM.yy HH:mm', { locale: ru }) } catch { return d }
}
const truncate = (t, n) => !t ? '—' : t.length <= n ? t : t.slice(0, n) + '...'

onMounted(loadPrompts)
</script>

<style scoped>
.prompts-view { padding: var(--spacing) 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing); }
.page-title { font-size: 26px; font-weight: 700; color: var(--color-text); }

.filters-panel { padding: var(--spacing-sm); margin-bottom: var(--spacing); }
.filters-row { display: flex; gap: var(--spacing-xs); align-items: flex-end; flex-wrap: wrap; }
.filter-group { display: flex; flex-direction: column; gap: 5px; min-width: 150px; }
.filter-grow { flex: 1; }
.filter-label { font-size: 12px; font-weight: 600; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.04em; }

.prompts-list { display: flex; flex-direction: column; gap: var(--spacing-sm); }
.prompt-card { background: var(--color-surface); border-radius: var(--border-radius); border: 1px solid var(--color-border); overflow: hidden; transition: var(--transition); }
.prompt-card:hover { box-shadow: 0 8px 30px var(--color-shadow-strong); transform: translateY(-1px); }
.prompt-card.is-main { border-color: #d97706; border-width: 2px; }
.prompt-card.is-system { border-color: var(--color-primary); border-width: 2px; }
.prompt-card.is-archived { opacity: 0.62; }

.card-status-bar { display: flex; align-items: center; justify-content: space-between; padding: 8px var(--spacing-sm); background: var(--color-surface-darker); border-bottom: 1px solid var(--color-border); }
.badges { display: flex; gap: 6px; flex-wrap: wrap; }

.badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px; border-radius: var(--border-radius-pill); font-size: 12px; font-weight: 600; }
.badge-sm { font-size: 11px; padding: 2px 8px; }
.badge-system  { background: var(--color-primary-soft); color: var(--color-primary-dark); }
.badge-main    { background: #fef3c7; color: #92400e; }
.badge-inactive { background: var(--color-surface); color: var(--color-text-muted); border: 1px solid var(--color-border); }
.badge-archived { background: #f3f4f6; color: #6b7280; }
.prompt-version { font-size: 12px; color: var(--color-text-muted); font-style: italic; flex-shrink: 0; }

.card-body { padding: var(--spacing-sm); }
.prompt-name { font-size: 15px; font-weight: 700; font-family: monospace; color: var(--color-text); margin-bottom: 3px; }
.prompt-description { font-size: 13px; color: var(--color-text-muted); margin-bottom: 8px; }
.prompt-preview { font-size: 13px; color: var(--color-text-light); background: var(--color-surface-darker); border-radius: 10px; padding: 8px 12px; line-height: 1.5; margin-bottom: 8px; white-space: pre-wrap; word-break: break-word; }
.prompt-meta { display: flex; gap: var(--spacing-sm); font-size: 12px; color: var(--color-text-muted); flex-wrap: wrap; }
.system-note { color: var(--color-primary); font-style: italic; }

.card-actions { display: flex; gap: 6px; flex-wrap: wrap; padding: var(--spacing-xs) var(--spacing-sm); border-top: 1px solid var(--color-border); background: var(--color-surface-darker); }
.btn-sm { padding: 5px 12px !important; font-size: 12px !important; }
.btn-danger { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }
.btn-danger:hover { background: #ef4444; color: white; }
.btn-danger-solid { background: #ef4444 !important; color: white !important; }

/* View modal */
.modal-title-block { display: flex; align-items: center; gap: var(--spacing-xs); flex-wrap: wrap; }
.view-sections { display: flex; flex-direction: column; gap: var(--spacing-sm); }
.view-section { display: flex; flex-direction: column; gap: 6px; }
.view-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-text-muted); }
.view-value { font-size: 14px; color: var(--color-text); }
.view-code { font-family: monospace; font-size: 13px; background: var(--color-surface-darker); border-radius: var(--border-radius-sm); padding: var(--spacing-sm); line-height: 1.6; white-space: pre-wrap; word-break: break-word; max-height: 280px; overflow-y: auto; color: var(--color-text); border: 1px solid var(--color-border); }
.view-params {}
.params-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.param-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: var(--color-surface-darker); border-radius: 10px; }
.param-key { font-size: 12px; color: var(--color-text-muted); font-family: monospace; }
.param-val { font-size: 13px; font-weight: 600; color: var(--color-text); font-family: monospace; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.45); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 9000; padding: var(--spacing); }
.modal-box { background: var(--color-surface); border-radius: var(--border-radius); width: 100%; max-width: 660px; max-height: 90vh; overflow-y: auto; box-shadow: 0 24px 60px rgba(18,78,115,0.2); }
.modal-wide { max-width: 760px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: var(--spacing); border-bottom: 1px solid var(--color-border); gap: var(--spacing-xs); }
.modal-header h3 { font-size: 18px; font-weight: 600; }
.close-btn { width: 32px; height: 32px; border: none; border-radius: 50%; background: var(--color-surface-darker); font-size: 20px; cursor: pointer; transition: var(--transition); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.close-btn:hover { background: var(--color-primary-soft); }
.modal-body { padding: var(--spacing); display: flex; flex-direction: column; gap: var(--spacing-sm); }
.modal-footer { display: flex; justify-content: flex-end; gap: var(--spacing-xs); padding: var(--spacing); border-top: 1px solid var(--color-border); }
.form-group { display: flex; flex-direction: column; gap: 5px; }
.form-label { font-size: 13px; font-weight: 600; color: var(--color-text-light); }
.req { color: #ef4444; }
.hint { font-size: 12px; color: var(--color-text-muted); }
.hint code { background: var(--color-surface-darker); padding: 1px 5px; border-radius: 4px; font-size: 11px; font-family: monospace; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-sm); }
.alert-error { padding: 10px 14px; background: var(--color-error); color: var(--color-error-text); border-radius: var(--border-radius-sm); font-size: 14px; border-left: 3px solid #ef4444; }

.history-list { display: flex; flex-direction: column; gap: var(--spacing-xs); }
.history-item { padding: var(--spacing-xs) var(--spacing-sm); background: var(--color-surface-darker); border-radius: var(--border-radius-sm); border-left: 3px solid var(--color-primary); }
.history-meta { display: flex; gap: var(--spacing-sm); margin-bottom: 4px; font-size: 13px; }
.hv { font-weight: 700; color: var(--color-primary); }
.hd { color: var(--color-text-muted); }
.hc { color: var(--color-text-light); font-style: italic; }
.history-preview { font-size: 12px; color: var(--color-text-muted); white-space: pre-wrap; }

.confirm-box { background: var(--color-surface); border-radius: var(--border-radius); max-width: 420px; width: 90%; padding: var(--spacing); text-align: center; box-shadow: 0 24px 60px rgba(18,78,115,0.2); }
.confirm-icon { font-size: 40px; margin-bottom: var(--spacing-xs); }
.confirm-box h3 { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
.confirm-box p { color: var(--color-text-light); font-size: 14px; line-height: 1.5; margin-bottom: var(--spacing); }
.confirm-actions { display: flex; gap: var(--spacing-xs); justify-content: center; }

.loading-state, .error-state, .empty-state { text-align: center; padding: 40px; }
.state-icon { font-size: 40px; display: block; margin-bottom: 12px; }
.state-inline { text-align: center; padding: 24px; color: var(--color-text-muted); }

.modal-enter-active, .modal-leave-active { transition: all 0.2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal-box, .modal-enter-from .confirm-box { transform: scale(0.95); }

@media (max-width: 768px) {
  .filters-row { flex-direction: column; }
  .filter-group { min-width: 100%; }
  .form-row, .params-grid { grid-template-columns: 1fr; }
}
</style>
