<template>
  <div class="prompts-view">
    <div class="container">

      <div class="page-header">
        <h1 class="page-title">⚙️ Управление промптами</h1>
        <button class="btn btn-primary" @click="openCreate">➕ Новый промпт</button>
      </div>

      <!-- Фильтры -->
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

      <div v-if="loading" class="state-block"><div class="spinner"></div><p>Загрузка...</p></div>
      <div v-else-if="error" class="state-block card">
        <span class="state-icon">❌</span><p>{{ error }}</p>
        <button class="btn btn-primary" @click="loadPrompts">Повторить</button>
      </div>
      <div v-else-if="!filteredPrompts.length" class="state-block card">
        <span class="state-icon">📭</span><p>Промпты не найдены</p>
        <button class="btn btn-primary" @click="openCreate">Создать первый промпт</button>
      </div>

      <div v-else class="prompts-list">
        <div
          v-for="prompt in filteredPrompts" :key="prompt.id"
          class="prompt-card"
          :class="{ 'is-main': effectiveMain?.id === prompt.id && !isSystem(prompt), 'is-system': isSystem(prompt), 'is-archived': !prompt.is_active }"
        >
          <div class="card-status-bar">
            <div class="badges">
              <span v-if="isSystem(prompt)" class="badge badge-system">🔒 Системный</span>
              <!-- «Основной» на системном — только если нет пользовательского основного -->
              <span v-if="isEffectiveMain(prompt)" class="badge badge-main">⭐ Основной</span>
              <span v-if="!prompt.is_active" class="badge badge-archived">📦 Архив</span>
              <span v-if="!isEffectiveMain(prompt) && prompt.is_active && !isSystem(prompt)" class="badge badge-inactive">○ Неактивный</span>
            </div>
            <span class="prompt-version">v{{ prompt.version }}</span>
          </div>

          <div class="card-body">
            <h3 class="prompt-name">{{ prompt.name }}</h3>
            <p class="prompt-description">{{ prompt.description || '—' }}</p>
            <p class="prompt-preview">{{ truncate(prompt.system_prompt, 100) }}</p>
            <div class="prompt-meta">
              <span>🗓 {{ formatDate(prompt.created_at) }}</span>
              <span v-if="prompt.updated_at && prompt.updated_at !== prompt.created_at">✏️ {{ formatDate(prompt.updated_at) }}</span>
              <span v-if="isSystem(prompt)" class="system-note">Глобальный · только чтение</span>
            </div>
          </div>

          <div class="card-actions">
            <!-- Левая группа: информация -->
            <div class="actions-group">
              <button class="btn btn-secondary btn-sm" @click="openView(prompt)">👁️ Просмотр</button>
              <button class="btn btn-secondary btn-sm" @click="showHistory(prompt)">📜 История</button>
            </div>

            <!-- Центральная группа: активные действия -->
            <div class="actions-group">
              <button v-if="!isSystem(prompt) && !prompt.is_default && prompt.is_active"
                class="btn btn-secondary btn-sm" @click="setMain(prompt)">⭐ Сделать основным</button>
              <button v-if="isSystem(prompt) && hasUserDefault"
                class="btn btn-secondary btn-sm" @click="resetToSystem">↩ Сделать основным</button>
              <button class="btn btn-secondary btn-sm" @click="doClone(prompt)">📋 Клонировать</button>
              <button v-if="!isSystem(prompt)" class="btn btn-secondary btn-sm" @click="openEdit(prompt)">✏️ Редактировать</button>
            </div>

            <!-- Правая группа: опасные -->
            <div class="actions-group actions-group--danger">
              <button v-if="!isSystem(prompt) && prompt.is_active" class="btn btn-secondary btn-sm" @click="doArchive(prompt)" title="Архивировать">📦</button>
              <button v-if="!isSystem(prompt) && !prompt.is_active" class="btn btn-secondary btn-sm" @click="doRestore(prompt)" title="Восстановить">♻️</button>
              <button v-if="!isSystem(prompt)" class="btn btn-sm btn-danger" @click="doDelete(prompt)">🗑️</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Просмотр (read-only) ────────────────────────────────────────────── -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="viewModal.show" class="modal-overlay" @click.self="viewModal.show = false">
          <div class="modal-box modal-wide">
            <div class="modal-header">
              <div class="modal-title-block">
                <h3>{{ viewModal.prompt?.name }}</h3>
                <span v-if="isSystem(viewModal.prompt)" class="badge badge-system badge-sm">🔒 Системный</span>
                <span v-if="isEffectiveMain(viewModal.prompt)" class="badge badge-main badge-sm">⭐ Основной</span>
              </div>
              <button class="close-btn" @click="viewModal.show = false">×</button>
            </div>
            <div class="modal-body" v-if="viewModal.prompt">
              <!-- Описание -->
              <div class="view-section">
                <div class="view-label">Описание</div>
                <div class="view-value">{{ viewModal.prompt.description || '—' }}</div>
              </div>

              <!-- Параметры -->
              <div class="view-section">
                <div class="view-label">Параметры</div>
                <div class="params-grid">
                  <div class="param-item">
                    <div class="param-key">temperature</div>
                    <div class="param-val">{{ viewModal.prompt.parameters?.temperature ?? 0.3 }}</div>
                    <div class="param-hint">Степень «творчества» AI (0 = точный, 2 = хаотичный). Для анализа резюме оптимально 0.1–0.4.</div>
                  </div>
                  <div class="param-item">
                    <div class="param-key">max_tokens</div>
                    <div class="param-val">{{ viewModal.prompt.parameters?.max_tokens ?? 1500 }}</div>
                    <div class="param-hint">Максимальная длина ответа (≈ 0.75 слова/токен). 1500 ≈ 1100 слов. Если ответ обрезается — увеличьте.</div>
                  </div>
                  <div class="param-item">
                    <div class="param-key">версия</div>
                    <div class="param-val">v{{ viewModal.prompt.version }}</div>
                    <div class="param-hint">История изменений — кнопка 📜 на карточке промпта.</div>
                  </div>
                  <div class="param-item">
                    <div class="param-key">создан</div>
                    <div class="param-val">{{ formatDate(viewModal.prompt.created_at) }}</div>
                    <div class="param-hint"></div>
                  </div>
                </div>
              </div>

              <!-- System Prompt -->
              <div class="view-section">
                <div class="view-label-row">
                  <span class="view-label">System Prompt</span>
                  <span class="view-label-hint">задаёт роль и поведение AI — кто он такой</span>
                </div>
                <pre class="view-code">{{ viewModal.prompt.system_prompt }}</pre>
              </div>

              <!-- User Template -->
              <div class="view-section">
                <div class="view-label-row">
                  <span class="view-label">User Template</span>
                  <span class="view-label-hint">конкретный запрос с данными вакансии и резюме</span>
                </div>
                <pre class="view-code">{{ viewModal.prompt.user_prompt_template }}</pre>
                <div class="vars-hint">
                  <span class="vars-title">Доступные переменные:</span>
                  <span v-for="v in VARS" :key="v.name" class="var-chip" :title="v.desc">{{ '{' + v.name + '}' }}</span>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" @click="viewModal.show = false">Закрыть</button>
              <button v-if="!isSystem(viewModal.prompt)" class="btn btn-primary" @click="openEditFromView">✏️ Редактировать</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ── Создание / редактирование ──────────────────────────────────────── -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="modal.show" class="modal-overlay" @click.self="tryCloseModal">
          <div class="modal-box">
            <div class="modal-header">
              <h3>{{ modal.isEdit ? 'Редактировать промпт' : 'Новый промпт' }}</h3>
              <button class="close-btn" @click="tryCloseModal">×</button>
            </div>
            <div class="modal-body">
              <div class="form-group">
                <label class="form-label">Название <span class="req">*</span></label>
                <input v-model="modal.form.name" class="input" placeholder="my_prompt_name" />
                <span class="hint">Уникальный идентификатор в вашем профиле</span>
              </div>
              <div class="form-group">
                <label class="form-label">Описание</label>
                <input v-model="modal.form.description" class="input" placeholder="Краткое описание назначения" />
              </div>

              <!-- System Prompt с подсказкой -->
              <div class="form-group">
                <div class="label-row">
                  <label class="form-label">System Prompt <span class="req">*</span></label>
                  <span class="label-hint">задаёт роль AI («кто он»)</span>
                </div>
                <textarea v-model="modal.form.system_prompt" class="textarea" rows="5"
                  placeholder="Ты опытный HR-специалист..."></textarea>
              </div>

              <!-- User Template с переменными -->
              <div class="form-group">
                <div class="label-row">
                  <label class="form-label">User Template <span class="req">*</span></label>
                  <span class="label-hint">конкретный запрос с данными</span>
                </div>
                <textarea v-model="modal.form.user_prompt_template" class="textarea" rows="10"
                  placeholder="Используйте переменные ниже..."></textarea>
                <!-- Переменные — кликабельные -->
                <div class="vars-box">
                  <span class="vars-title">Вставить переменную:</span>
                  <span
                    v-for="v in VARS" :key="v.name"
                    class="var-chip var-chip-click"
                    :title="v.desc"
                    @click="insertVar(v.name)"
                  >{{ '{' + v.name + '}' }}</span>
                </div>
                <div class="vars-descs">
                  <div v-for="v in VARS" :key="v.name" class="var-desc-row">
                    <code>{{ '{' + v.name + '}' }}</code> — {{ v.desc }}
                  </div>
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">Temperature
                    <span class="form-label-tip">0 = точный, 2 = творческий</span>
                  </label>
                  <input v-model.number="modal.form.temperature" type="number" class="input" min="0" max="2" step="0.1" />
                </div>
                <div class="form-group">
                  <label class="form-label">Max tokens
                    <span class="form-label-tip">длина ответа AI (1500 ≈ 1100 слов)</span>
                  </label>
                  <input v-model.number="modal.form.max_tokens" type="number" class="input" min="100" max="8000" step="100" />
                </div>
              </div>

              <div v-if="modal.error" class="alert-error">⚠️ {{ modal.error }}</div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" @click="tryCloseModal">Отмена</button>
              <button class="btn btn-primary" @click="trySavePrompt" :disabled="modal.saving">
                <span v-if="modal.saving" class="spinner spinner-sm"></span>
                <span v-else>{{ modal.isEdit ? 'Сохранить' : 'Создать' }}</span>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ── История ─────────────────────────────────────────────────────────── -->
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

    <!-- ── Confirm dialog ──────────────────────────────────────────────────── -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="confirm.show" class="modal-overlay" @click.self="confirm.cancel">
          <div class="confirm-box">
            <div class="confirm-icon">{{ confirm.icon }}</div>
            <h3>{{ confirm.title }}</h3>
            <p>{{ confirm.message }}</p>
            <div class="confirm-actions">
              <button class="btn btn-secondary" @click="confirm.cancel">{{ confirm.cancelText || 'Отмена' }}</button>
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

// Переменные промпта с описаниями
const VARS = [
  { name: 'cv_text',          desc: 'Полный текст резюме кандидата' },
  { name: 'title',            desc: 'Название вакансии' },
  { name: 'location',         desc: 'Локация вакансии' },
  { name: 'salary_range',     desc: 'Зарплатная вилка (объект {min, max, currency})' },
  { name: 'key_skills',       desc: 'Ключевые навыки через запятую' },
  { name: 'description_text', desc: 'Текстовое описание вакансии' },
  { name: 'comment_for_ai',   desc: 'Дополнительный комментарий рекрутера для AI' },
]

// ── Состояние ─────────────────────────────────────────────────────────────────
const prompts   = ref([])
const loading   = ref(true)
const error     = ref(null)

const filters = reactive({ search: '', status: 'all', sortBy: 'default_first' })

const viewModal = reactive({ show: false, prompt: null })

const modal = reactive({
  show: false, isEdit: false, saving: false, error: '', prompt: null,
  originalForm: null,  // сохраняем для сравнения isDirty
  form: { name: '', description: '', system_prompt: '', user_prompt_template: '', temperature: 0.3, max_tokens: 1500 }
})

const hist    = reactive({ show: false, loading: false, items: [], name: '' })
const confirm = reactive({ show: false, title: '', message: '', icon: '⚠️', btnText: 'OK', cancelText: 'Отмена', danger: false, action: null, cancel: null })

// ── Computed ──────────────────────────────────────────────────────────────────
// Есть ли пользовательский промпт с is_default=true?
const hasUserDefault = computed(() =>
  prompts.value.some(p => !isSystem(p) && p.is_default && p.is_active)
)

// «Эффективный основной»: если есть пользовательский → он; иначе → системный
const effectiveMain = computed(() => {
  const userMain = prompts.value.find(p => !isSystem(p) && p.is_default && p.is_active)
  if (userMain) return userMain
  return prompts.value.find(p => isSystem(p) && p.is_active) || null
})

const isEffectiveMain = (p) => !!p && effectiveMain.value?.id === p?.id

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

// ── Dirty check ───────────────────────────────────────────────────────────────
const isDirty = () => {
  if (!modal.originalForm) return false
  const o = modal.originalForm, f = modal.form
  return o.name !== f.name || o.description !== f.description ||
         o.system_prompt !== f.system_prompt || o.user_prompt_template !== f.user_prompt_template ||
         o.temperature !== f.temperature || o.max_tokens !== f.max_tokens
}

// ── API ───────────────────────────────────────────────────────────────────────
const loadPrompts = async () => {
  loading.value = true; error.value = null
  try {
    const { data } = await api.get('/prompts/?active_only=false&limit=100')
    prompts.value = data
  } catch (e) { error.value = e.response?.data?.detail || 'Не удалось загрузить промпты' }
  finally { loading.value = false }
}

// ── Просмотр ──────────────────────────────────────────────────────────────────
const openView = (p) => { viewModal.prompt = p; viewModal.show = true }
const openEditFromView = () => { const p = viewModal.prompt; viewModal.show = false; openEdit(p) }

// ── CRUD ──────────────────────────────────────────────────────────────────────
const openCreate = () => {
  const empty = { name: '', description: '', system_prompt: '', user_prompt_template: '', temperature: 0.3, max_tokens: 1500 }
  Object.assign(modal, { show: true, isEdit: false, saving: false, error: '', prompt: null })
  modal.form = { ...empty }
  modal.originalForm = { ...empty }
}

const openEdit = (p) => {
  const f = {
    name: p.name, description: p.description || '',
    system_prompt: p.system_prompt, user_prompt_template: p.user_prompt_template,
    temperature: p.parameters?.temperature ?? 0.3,
    max_tokens:  p.parameters?.max_tokens  ?? 1500,
  }
  Object.assign(modal, { show: true, isEdit: true, saving: false, error: '', prompt: p })
  modal.form = { ...f }
  modal.originalForm = { ...f }
}

// Закрытие с проверкой несохранённых изменений
const tryCloseModal = () => {
  if (isDirty()) {
    showConfirm({
      title: 'Отменить изменения?',
      message: 'Вы внесли изменения. Если закрыть окно — они будут потеряны.',
      icon: '⚠️', btnText: 'Да, отменить', danger: false,
      action: () => { confirm.show = false; modal.show = false },
      cancel: () => { confirm.show = false }
    })
  } else {
    modal.show = false
  }
}

// Сохранение с подтверждением при редактировании
const trySavePrompt = () => {
  if (!modal.form.name || !modal.form.system_prompt || !modal.form.user_prompt_template) {
    modal.error = 'Заполните обязательные поля: название, system prompt, user template'
    return
  }
  if (modal.isEdit) {
    showConfirm({
      title: 'Сохранить изменения?',
      message: 'Старая версия промпта будет сохранена в историю изменений и станет недоступной для использования.',
      icon: '💾', btnText: 'Сохранить', danger: false,
      action: () => { confirm.show = false; savePrompt() },
      cancel: () => { confirm.show = false }
    })
  } else {
    savePrompt()
  }
}

const savePrompt = async () => {
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
    modal.show = false
    await loadPrompts()
  } catch (e) { modal.error = e.response?.data?.detail || 'Ошибка сохранения' }
  finally { modal.saving = false }
}

// Вставить переменную в позицию курсора в user_prompt_template
const insertVar = (name) => {
  const tag = `{${name}}`
  // Ищем последний сфокусированный textarea
  const ta = document.activeElement
  if (ta && ta.tagName === 'TEXTAREA') {
    const start = ta.selectionStart, end = ta.selectionEnd
    modal.form.user_prompt_template =
      modal.form.user_prompt_template.slice(0, start) + tag + modal.form.user_prompt_template.slice(end)
    // Восстанавливаем курсор
    setTimeout(() => { ta.focus(); ta.setSelectionRange(start + tag.length, start + tag.length) }, 0)
  } else {
    modal.form.user_prompt_template += tag
  }
}

// ── Основной промпт ───────────────────────────────────────────────────────────
const setMain = (p) => {
  showConfirm({
    title: 'Сделать основным?',
    message: `Промпт «${p.name}» будет использоваться при анализе резюме. Предыдущий основной будет деактивирован.`,
    icon: '⭐', btnText: 'Сделать основным',
    action: async () => {
      confirm.show = false
      try { await api.put(`/prompts/${p.id}`, { is_default: true, is_active: true }); await loadPrompts() }
      catch(e) { console.error(e) }
    },
    cancel: () => { confirm.show = false }
  })
}

// Вернуть системный промпт как основной (снять пользовательский is_default)
const resetToSystem = () => {
  const sys = prompts.value.find(p => isSystem(p))
  if (!sys) return
  showConfirm({
    title: 'Сделать системный основным?',
    message: 'Все пользовательские основные промпты будут деактивированы. При анализе будет использоваться системный промпт.',
    icon: '🔒', btnText: 'Подтвердить',
    action: async () => {
      confirm.show = false
      try {
        // Посылаем is_default=true на системный — API снимет флаги с пользовательских
        await api.put(`/prompts/${sys.id}`, { is_default: true })
        await loadPrompts()
      } catch(e) { console.error(e) }
    },
    cancel: () => { confirm.show = false }
  })
}

// ── Клонирование ──────────────────────────────────────────────────────────────
const doClone = (p) => {
  showConfirm({
    title: 'Клонировать промпт?',
    message: `Будет создана копия «${p.name}»${isSystem(p) ? ' (системного)' : ''} как ваш пользовательский промпт.`,
    icon: '📋', btnText: 'Клонировать',
    action: async () => {
      confirm.show = false
      try {
        await api.post(`/prompts/${p.id}/clone`)
        await loadPrompts()
      } catch(e) { console.error(e) }
    },
    cancel: () => { confirm.show = false }
  })
}

// ── Архив / Восстановить / Удалить ────────────────────────────────────────────
const doArchive = (p) => {
  showConfirm({
    title: 'Архивировать промпт?',
    message: p.is_default
      ? '⚠️ Это основной промпт! После архивирования будет использоваться системный промпт.'
      : `Промпт «${p.name}» будет перемещён в архив.`,
    icon: '📦', btnText: 'Архивировать', danger: p.is_default,
    action: async () => {
      confirm.show = false
      try { await api.delete(`/prompts/${p.id}`); await loadPrompts() }
      catch(e) { console.error(e) }
    },
    cancel: () => { confirm.show = false }
  })
}

const doRestore = async (p) => {
  try { await api.put(`/prompts/${p.id}`, { is_active: true }); await loadPrompts() }
  catch(e) { console.error(e) }
}

const doDelete = (p) => {
  showConfirm({
    title: 'Удалить промпт?',
    message: `Промпт «${p.name}» будет удалён безвозвратно. Это действие нельзя отменить.`,
    icon: '🗑️', btnText: 'Удалить', danger: true,
    action: async () => {
      confirm.show = false
      try { await api.delete(`/prompts/${p.id}?hard=true`); await loadPrompts() }
      catch(e) { console.error(e) }
    },
    cancel: () => { confirm.show = false }
  })
}

const showHistory = async (p) => {
  hist.name = p.name; hist.items = []; hist.loading = true; hist.show = true
  try { const { data } = await api.get(`/prompts/${p.id}/history`); hist.items = data }
  catch(e) { console.error(e) }
  hist.loading = false
}

const showConfirm = ({ title, message, icon='⚠️', btnText='OK', cancelText='Отмена', danger=false, action, cancel }) => {
  const cancelFn = cancel || (() => { confirm.show = false })
  Object.assign(confirm, { show: true, title, message, icon, btnText, cancelText, danger, action, cancel: cancelFn })
}

const resetFilters = () => { filters.search = ''; filters.status = 'all'; filters.sortBy = 'default_first' }
const formatDate = (d) => { try { return format(new Date(d), 'dd.MM.yy HH:mm', { locale: ru }) } catch { return d || '—' } }
const truncate = (t, n) => !t ? '—' : t.length <= n ? t : t.slice(0, n) + '...'

onMounted(loadPrompts)
</script>

<style scoped>
.prompts-view { padding: var(--spacing) 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing); }
.page-title { font-size: 26px; font-weight: 700; }

.filters-panel { padding: var(--spacing-sm); margin-bottom: var(--spacing); }
.filters-row { display: flex; gap: var(--spacing-xs); align-items: flex-end; flex-wrap: wrap; }
.filter-group { display: flex; flex-direction: column; gap: 5px; min-width: 150px; }
.filter-grow { flex: 1; }
.filter-label { font-size: 12px; font-weight: 600; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: .04em; }

.prompts-list { display: flex; flex-direction: column; gap: var(--spacing-sm); }
.prompt-card { background: var(--color-surface); border-radius: var(--border-radius); border: 1px solid var(--color-border); overflow: hidden; transition: var(--transition); }
.prompt-card:hover { box-shadow: 0 8px 30px var(--color-shadow-strong); transform: translateY(-1px); }
.prompt-card.is-main   { border-color: #d97706; border-width: 2px; }
.prompt-card.is-system { border-color: var(--color-primary); border-width: 2px; }
.prompt-card.is-archived { opacity: .65; }

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
.prompt-name { font-size: 15px; font-weight: 700; font-family: monospace; margin-bottom: 3px; }
.prompt-description { font-size: 13px; color: var(--color-text-muted); margin-bottom: 8px; }
.prompt-preview { font-size: 13px; color: var(--color-text-light); background: var(--color-surface-darker); border-radius: 10px; padding: 8px 12px; line-height: 1.5; margin-bottom: 8px; white-space: pre-wrap; word-break: break-word; }
.prompt-meta { display: flex; gap: var(--spacing-sm); font-size: 12px; color: var(--color-text-muted); flex-wrap: wrap; }
.system-note { color: var(--color-primary); font-style: italic; }

.card-actions { display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; padding: var(--spacing-xs) var(--spacing-sm); border-top: 1px solid var(--color-border); background: var(--color-surface-darker); }
.actions-group { display: flex; gap: 4px; flex-wrap: wrap; }
.actions-group--danger { margin-left: auto; }
.btn-sm { padding: 5px 12px !important; font-size: 12px !important; }
.btn-danger { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }
.btn-danger:hover { background: #ef4444; color: white; }
.btn-danger-solid { background: #ef4444 !important; color: white !important; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 9000; padding: var(--spacing); }
.modal-box { background: var(--color-surface); border-radius: var(--border-radius); width: 100%; max-width: 680px; max-height: 90vh; overflow-y: auto; box-shadow: 0 24px 60px rgba(18,78,115,.2); }
.modal-wide { max-width: 780px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: var(--spacing); border-bottom: 1px solid var(--color-border); gap: var(--spacing-xs); }
.modal-title-block { display: flex; align-items: center; gap: var(--spacing-xs); flex-wrap: wrap; }
.modal-header h3 { font-size: 18px; font-weight: 600; }
.close-btn { width: 32px; height: 32px; border: none; border-radius: 50%; background: var(--color-surface-darker); font-size: 20px; cursor: pointer; transition: var(--transition); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.close-btn:hover { background: var(--color-primary-soft); }
.modal-body { padding: var(--spacing); display: flex; flex-direction: column; gap: var(--spacing-sm); }
.modal-footer { display: flex; justify-content: flex-end; gap: var(--spacing-xs); padding: var(--spacing); border-top: 1px solid var(--color-border); }
.form-group { display: flex; flex-direction: column; gap: 5px; }
.form-label { font-size: 13px; font-weight: 600; color: var(--color-text-light); display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.form-label-tip { font-size: 11px; font-weight: 400; color: var(--color-text-muted); font-style: italic; }
.label-row { display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
.label-hint { font-size: 11px; color: var(--color-text-muted); font-style: italic; }
.req { color: #ef4444; }
.hint { font-size: 12px; color: var(--color-text-muted); }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-sm); }
.alert-error { padding: 10px 14px; background: var(--color-error); color: var(--color-error-text); border-radius: var(--border-radius-sm); font-size: 14px; border-left: 3px solid #ef4444; }

/* Переменные */
.vars-box { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 6px; }
.vars-hint { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 8px; }
.vars-title { font-size: 12px; color: var(--color-text-muted); font-weight: 600; }
.var-chip { font-family: monospace; font-size: 12px; padding: 2px 8px; background: var(--color-surface-darker); border: 1px solid var(--color-border); border-radius: 6px; color: var(--color-primary-dark); white-space: nowrap; }
.var-chip-click { cursor: pointer; transition: var(--transition); }
.var-chip-click:hover { background: var(--color-primary-soft); border-color: var(--color-primary); }
.vars-descs { display: flex; flex-direction: column; gap: 3px; margin-top: 8px; }
.var-desc-row { font-size: 12px; color: var(--color-text-muted); }
.var-desc-row code { background: var(--color-surface-darker); padding: 1px 5px; border-radius: 4px; font-size: 11px; color: var(--color-primary-dark); }

/* View */
.view-section { display: flex; flex-direction: column; gap: 8px; }
.view-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; color: var(--color-text-muted); }
.view-label-row { display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
.view-label-hint { font-size: 11px; color: var(--color-text-muted); font-style: italic; }
.view-value { font-size: 14px; }
.view-code { font-family: monospace; font-size: 13px; background: var(--color-surface-darker); border-radius: var(--border-radius-sm); padding: var(--spacing-sm); line-height: 1.65; white-space: pre-wrap; word-break: break-word; max-height: 300px; overflow-y: auto; border: 1px solid var(--color-border); }
.params-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.param-item { background: var(--color-surface-darker); border-radius: 10px; padding: 10px 14px; display: flex; flex-direction: column; gap: 3px; }
.param-key { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; color: var(--color-text-muted); }
.param-val { font-size: 15px; font-weight: 700; font-family: monospace; color: var(--color-text); }
.param-hint { font-size: 11px; color: var(--color-text-muted); line-height: 1.4; margin-top: 2px; }

/* History */
.history-list { display: flex; flex-direction: column; gap: var(--spacing-xs); }
.history-item { padding: var(--spacing-xs) var(--spacing-sm); background: var(--color-surface-darker); border-radius: var(--border-radius-sm); border-left: 3px solid var(--color-primary); }
.history-meta { display: flex; gap: var(--spacing-sm); margin-bottom: 4px; font-size: 13px; }
.hv { font-weight: 700; color: var(--color-primary); }
.hd { color: var(--color-text-muted); }
.hc { color: var(--color-text-light); font-style: italic; }
.history-preview { font-size: 12px; color: var(--color-text-muted); white-space: pre-wrap; }

/* Confirm */
.confirm-box { background: var(--color-surface); border-radius: var(--border-radius); max-width: 420px; width: 90%; padding: var(--spacing); text-align: center; box-shadow: 0 24px 60px rgba(18,78,115,.2); }
.confirm-icon { font-size: 40px; margin-bottom: var(--spacing-xs); }
.confirm-box h3 { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
.confirm-box p { color: var(--color-text-light); font-size: 14px; line-height: 1.5; margin-bottom: var(--spacing); }
.confirm-actions { display: flex; gap: var(--spacing-xs); justify-content: center; }

.state-block { text-align: center; padding: 40px; }
.state-icon { font-size: 40px; display: block; margin-bottom: 12px; }
.state-inline { text-align: center; padding: 24px; color: var(--color-text-muted); }

.modal-enter-active, .modal-leave-active { transition: all .2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal-box, .modal-enter-from .confirm-box { transform: scale(.95); }

@media (max-width: 768px) {
  .filters-row, .form-row, .params-grid { flex-direction: column; grid-template-columns: 1fr; }
  .filter-group { min-width: 100%; }
}
</style>
