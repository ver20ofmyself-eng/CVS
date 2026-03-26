<template>
  <div class="vf">
    <form @submit.prevent="handleSubmit">

      <!-- ── Основная информация ────────────────────────────────────────── -->
      <section class="vf-section">
        <h3 class="vf-section-title">Основная информация</h3>
        <div class="vf-grid">
          <div class="vf-field vf-full">
            <label class="vf-label">Название вакансии <span class="vf-req">*</span></label>
            <input
              v-model="form.title"
              type="text"
              class="vf-input"
              :class="{ 'vf-input--error': errors.title }"
              placeholder="Например: Senior Python Developer"
              @blur="validateTitle"
            />
            <span v-if="errors.title" class="vf-error-msg">{{ errors.title }}</span>
          </div>

          <div class="vf-field">
            <label class="vf-label">Локация</label>
            <input v-model="form.location" type="text" class="vf-input" placeholder="Москва, удалённо, гибрид..." />
          </div>

          <div class="vf-field vf-toggle-field">
            <label class="vf-label">Статус вакансии</label>
            <label class="vf-toggle">
              <input v-model="form.is_active" type="checkbox" class="vf-toggle-input" />
              <span class="vf-toggle-track">
                <span class="vf-toggle-thumb"></span>
              </span>
              <span class="vf-toggle-label">{{ form.is_active ? 'Активна' : 'В архиве' }}</span>
            </label>
          </div>
        </div>
      </section>

      <!-- ── Зарплатная вилка ──────────────────────────────────────────── -->
      <section class="vf-section">
        <h3 class="vf-section-title">Зарплатная вилка</h3>
        <p class="vf-section-hint">Оба поля необязательны. Если «от» больше «до» — значения автоматически поменяются.</p>
        <div class="vf-grid vf-salary-grid">
          <div class="vf-field">
            <label class="vf-label">От</label>
            <input
              v-model.number="form.salary_range.min"
              type="number"
              class="vf-input"
              placeholder="100 000"
              min="0"
              step="1000"
              @blur="normalizeSalary"
            />
          </div>
          <div class="vf-field">
            <label class="vf-label">До</label>
            <input
              v-model.number="form.salary_range.max"
              type="number"
              class="vf-input"
              placeholder="200 000"
              min="0"
              step="1000"
              @blur="normalizeSalary"
            />
          </div>
          <div class="vf-field">
            <label class="vf-label">Валюта</label>
            <select v-model="form.salary_range.currency" class="vf-select">
              <option value="RUB">🇷🇺 RUB</option>
              <option value="USD">🇺🇸 USD</option>
              <option value="EUR">🇪🇺 EUR</option>
              <option value="KZT">🇰🇿 KZT</option>
            </select>
          </div>
        </div>
      </section>

      <!-- ── Ключевые навыки ───────────────────────────────────────────── -->
      <section class="vf-section">
        <h3 class="vf-section-title">
          Ключевые навыки
          <span class="vf-title-badge">Enter · «,» · «;» разделяют навыки</span>
        </h3>
        <div class="vf-skills-box" :class="{ 'vf-skills-box--focus': skillsFocused }">
          <div class="vf-skills-tags">
            <span v-for="(skill, i) in form.key_skills" :key="i" class="vf-skill-tag">
              {{ skill }}
              <button type="button" class="vf-skill-del" @click="removeSkill(i)">×</button>
            </span>
            <input
              ref="skillInputRef"
              v-model="newSkill"
              class="vf-skills-input"
              placeholder="Введите навык или вставьте список через «;»..."
              @keydown.enter.prevent="addSkillsFromInput"
              @keydown.188.prevent="addSkillsFromInput"
              @keydown.delete="onSkillDelete"
              @input="onSkillInput"
              @paste.prevent="onSkillPaste"
              @focus="skillsFocused = true"
              @blur="skillsFocused = false"
            />
          </div>
        </div>
        <div v-if="skillSuggestions.length" class="vf-suggestions">
          <span
            v-for="s in skillSuggestions"
            :key="s"
            class="vf-suggestion"
            @click="addSuggested(s)"
          >{{ s }}</span>
        </div>
      </section>

      <!-- ── Описание вакансии (Telegram-like редактор) ────────────────── -->
      <section class="vf-section">
        <h3 class="vf-section-title">Описание вакансии</h3>

        <!-- Тулбар -->
        <div class="vf-toolbar">
          <button type="button" class="vf-tb" :class="{ active: fmt.bold }"       @mousedown.prevent="toggle('bold')"          title="Жирный · Ctrl+B"><b>B</b></button>
          <button type="button" class="vf-tb" :class="{ active: fmt.italic }"     @mousedown.prevent="toggle('italic')"        title="Курсив · Ctrl+I"><i>I</i></button>
          <button type="button" class="vf-tb" :class="{ active: fmt.underline }"  @mousedown.prevent="toggle('underline')"     title="Подчёркнутый"><u>U</u></button>
          <button type="button" class="vf-tb" :class="{ active: fmt.strike }"     @mousedown.prevent="toggle('strikeThrough')" title="Зачёркнутый"><s>S</s></button>
          <button type="button" class="vf-tb vf-tb-mono" :class="{ active: fmt.code }" @mousedown.prevent="insertInlineCode" title="Код">〈/〉</button>
          <div class="vf-tb-divider"></div>
          <button type="button" class="vf-tb" :class="{ active: fmt.ul }" @mousedown.prevent="toggle('insertUnorderedList')" title="Список">• —</button>
          <button type="button" class="vf-tb" :class="{ active: fmt.ol }" @mousedown.prevent="toggle('insertOrderedList')"   title="Нумерованный список">1.</button>
          <div class="vf-tb-divider"></div>
          <button type="button" class="vf-tb" @mousedown.prevent="setBlock('h3')" title="Заголовок H3">H3</button>
          <button type="button" class="vf-tb" @mousedown.prevent="setBlock('p')"  title="Обычный абзац">P</button>
          <div class="vf-tb-divider"></div>
          <button type="button" class="vf-tb" @mousedown.prevent="undo" title="Отменить · Ctrl+Z">↩</button>
          <button type="button" class="vf-tb" @mousedown.prevent="redo" title="Повторить · Ctrl+Y">↪</button>
          <button type="button" class="vf-tb vf-tb-clear" @mousedown.prevent="clearFormat" title="Убрать форматирование">✕</button>
        </div>

        <!-- Редактируемая область -->
        <div
          ref="editorRef"
          class="vf-editor"
          contenteditable="true"
          @input="onEditorInput"
          @keyup="updateFormatState"
          @mouseup="updateFormatState"
          @paste="onEditorPaste"
          @keydown="onEditorKeydown"
        ></div>

        <p class="vf-editor-hint">AI использует текстовую версию, генерируемую автоматически из форматированного содержимого.</p>
      </section>

      <!-- ── Комментарий для AI ────────────────────────────────────────── -->
      <section class="vf-section">
        <h3 class="vf-section-title">
          Комментарий для AI
          <span class="vf-title-badge">дополнительные инструкции</span>
        </h3>
        <textarea
          v-model="form.comment_for_ai"
          class="vf-textarea"
          rows="4"
          placeholder="Например: особое внимание на микросервисы, английский не обязателен..."
        ></textarea>
      </section>

      <!-- ── Шаблоны (аккордеон) ───────────────────────────────────────── -->
      <section class="vf-section">
        <div class="vf-accordion-header" @click="showTemplates = !showTemplates">
          <h3 class="vf-section-title vf-section-title--mb0">📋 Шаблоны сообщений</h3>
          <span class="vf-accordion-chevron" :class="{ rotated: showTemplates }">▶</span>
        </div>
        <Transition name="accordion">
          <div v-if="showTemplates" class="vf-accordion-body">
            <div v-for="(tpl, key) in templateConfig" :key="key" class="vf-field">
              <label class="vf-label">{{ tpl.label }}</label>
              <textarea v-model="form.templates[key]" class="vf-textarea" :rows="tpl.rows" :placeholder="tpl.placeholder"></textarea>
            </div>
          </div>
        </Transition>
      </section>

      <!-- ── Действия ──────────────────────────────────────────────────── -->
      <div class="vf-actions">
        <button type="button" class="btn btn-secondary" @click="handleCancel">Отмена</button>
        <button type="submit" class="btn btn-primary" :disabled="isSubmitting || !isValid">
          <span v-if="isSubmitting" class="spinner spinner-sm"></span>
          <span v-else>{{ isEditing ? 'Сохранить изменения' : 'Создать вакансию' }}</span>
        </button>
      </div>

    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useVacanciesStore } from '@/stores/vacancies'
import { useToast } from '@/composables/useToast'

const props = defineProps({ vacancyId: { type: Number, default: null } })

const router         = useRouter()
const vacanciesStore = useVacanciesStore()
const toast          = useToast()

// ── Форма ──────────────────────────────────────────────────────────────────────
const form = reactive({
  title: '', location: '',
  salary_range: { min: null, max: null, currency: 'RUB' },
  key_skills: [],
  description_html: '',
  comment_for_ai: '',
  templates: { hh_invitation: '', messenger_invitation: '', interview_questions: '', rejection: '' },
  is_active: true
})

const errors        = reactive({ title: '' })
const isSubmitting  = ref(false)
const showTemplates = ref(false)
const skillsFocused = ref(false)
const newSkill      = ref('')
const skillInputRef = ref(null)
const editorRef     = ref(null)

// Состояние форматирования (для активных кнопок тулбара)
const fmt = reactive({ bold: false, italic: false, underline: false, strike: false, code: false, ul: false, ol: false })

const templateConfig = {
  hh_invitation:        { label: 'Приглашение на hh.ru',       rows: 3, placeholder: 'Здравствуйте! Приглашаем вас на вакансию...' },
  messenger_invitation: { label: 'Приглашение в мессенджер',   rows: 3, placeholder: 'Привет! 👋 Рассматриваешь новые возможности?...' },
  interview_questions:  { label: 'Вопросы для интервью',       rows: 4, placeholder: '1. Расскажи о своём опыте...' },
  rejection:            { label: 'Шаблон отказа',              rows: 3, placeholder: 'Благодарим за интерес к вакансии...' }
}

// ── Навыки ─────────────────────────────────────────────────────────────────────
const popularSkills = [
  'Python','JavaScript','Java','C++','C#','React','Vue','Angular','Node.js','Django',
  'FastAPI','Flask','Spring','SQL','PostgreSQL','MySQL','MongoDB','Redis','Docker',
  'Kubernetes','AWS','GCP','Azure','Git','Linux','TypeScript','Go','Rust','PHP','Ruby'
]

const skillSuggestions = computed(() => {
  if (!newSkill.value || newSkill.value.length < 2) return []
  const q = newSkill.value.toLowerCase()
  return popularSkills.filter(s => s.toLowerCase().includes(q) && !form.key_skills.includes(s)).slice(0, 5)
})

function parseAndAddSkills(raw) {
  raw.split(/[;,\n]+/).map(s => s.trim()).filter(Boolean).forEach(s => {
    if (!form.key_skills.includes(s)) form.key_skills.push(s)
  })
  newSkill.value = ''
}
const addSkillsFromInput = () => { if (newSkill.value.trim()) parseAndAddSkills(newSkill.value) }
const onSkillInput = () => { if (newSkill.value.includes(';') || newSkill.value.includes(',')) parseAndAddSkills(newSkill.value) }
const onSkillPaste = (e) => parseAndAddSkills((e.clipboardData || window.clipboardData).getData('text'))
const onSkillDelete = (e) => { if (e.target.value === '' && form.key_skills.length) form.key_skills.pop() }
const addSuggested = (s) => { if (!form.key_skills.includes(s)) form.key_skills.push(s); newSkill.value = '' }
const removeSkill = (i) => form.key_skills.splice(i, 1)

// ── Зарплата — нормализация ────────────────────────────────────────────────────
const normalizeSalary = () => {
  const { min, max } = form.salary_range
  if (min && max && min > max) {
    // меняем местами
    form.salary_range.min = max
    form.salary_range.max = min
  }
}

// ── Редактор ───────────────────────────────────────────────────────────────────
const toggle = (cmd) => {
  document.execCommand(cmd, false, null)
  editorRef.value?.focus()
  updateFormatState()
}

const setBlock = (tag) => {
  // Сначала убираем предыдущий блок-форматирование, потом применяем нужный
  document.execCommand('formatBlock', false, tag)
  editorRef.value?.focus()
}

const clearFormat = () => {
  document.execCommand('removeFormat', false, null)
  document.execCommand('formatBlock', false, 'p')
  editorRef.value?.focus()
}

const insertInlineCode = () => {
  const sel = window.getSelection()
  if (!sel || sel.isCollapsed) {
    document.execCommand('insertHTML', false, '<code>код</code>')
  } else {
    const text = sel.toString()
    document.execCommand('insertHTML', false, `<code>${text}</code>`)
  }
  editorRef.value?.focus()
}

const undo = () => { document.execCommand('undo', false, null); editorRef.value?.focus() }
const redo = () => { document.execCommand('redo', false, null); editorRef.value?.focus() }

const updateFormatState = () => {
  fmt.bold      = document.queryCommandState('bold')
  fmt.italic    = document.queryCommandState('italic')
  fmt.underline = document.queryCommandState('underline')
  fmt.strike    = document.queryCommandState('strikeThrough')
  fmt.ul        = document.queryCommandState('insertUnorderedList')
  fmt.ol        = document.queryCommandState('insertOrderedList')
}

const onEditorInput = () => {
  form.description_html = editorRef.value?.innerHTML || ''
  updateFormatState()
}

const onEditorPaste = (e) => {
  e.preventDefault()
  // Вставляем только plain text
  const text = (e.clipboardData || window.clipboardData).getData('text/plain')
  document.execCommand('insertText', false, text)
}

const onEditorKeydown = (e) => {
  // Ctrl+B/I/U/Z/Y — нативная поддержка, только обновляем состояние
  if (e.ctrlKey || e.metaKey) {
    setTimeout(updateFormatState, 0)
  }
}

// ── Валидация ──────────────────────────────────────────────────────────────────
const isEditing = computed(() => !!props.vacancyId)
const isValid   = computed(() => form.title && form.title.length >= 3)

const validateTitle = () => {
  if (!form.title)              errors.title = 'Название обязательно'
  else if (form.title.length < 3) errors.title = 'Минимум 3 символа'
  else                          errors.title = ''
}

// ── Загрузка ───────────────────────────────────────────────────────────────────
const loadVacancy = async () => {
  try {
    const v = await vacanciesStore.fetchVacancy(props.vacancyId)
    form.title          = v.title
    form.location       = v.location || ''
    form.salary_range   = v.salary_range || { min: null, max: null, currency: 'RUB' }
    form.key_skills     = v.key_skills || []
    const html          = v.description_html || (v.description_text ? v.description_text.replace(/\n/g, '<br>') : '')
    form.description_html = html
    form.comment_for_ai = v.comment_for_ai || ''
    form.templates      = v.templates || { hh_invitation: '', messenger_invitation: '', interview_questions: '', rejection: '' }
    form.is_active      = v.is_active
    await nextTick()
    if (editorRef.value) editorRef.value.innerHTML = html
  } catch (e) { console.error('Ошибка загрузки:', e) }
}

// ── Отправка ───────────────────────────────────────────────────────────────────
const handleCancel = () => router.push('/vacancies')

const handleSubmit = async () => {
  validateTitle()
  if (errors.title) return

  isSubmitting.value = true
  try {
    const tmp = document.createElement('div')
    tmp.innerHTML = form.description_html
    const descText = tmp.textContent || tmp.innerText || ''

    const payload = {
      title:            form.title,
      location:         form.location || undefined,
      salary_range: {
        min:      form.salary_range.min  || undefined,
        max:      form.salary_range.max  || undefined,
        currency: form.salary_range.currency
      },
      key_skills:       form.key_skills,
      description_html: form.description_html || undefined,
      description_text: descText || undefined,
      comment_for_ai:   form.comment_for_ai || undefined,
      templates:        form.templates,
      is_active:        form.is_active
    }

    if (isEditing.value) await vacanciesStore.updateVacancy(props.vacancyId, payload)
    else                 await vacanciesStore.createVacancy(payload)

    toast.success(isEditing.value ? 'Вакансия обновлена' : 'Вакансия создана')
    router.push('/vacancies')
  } catch (e) {
    console.error('Ошибка сохранения:', e)
    toast.error('Не удалось сохранить вакансию')
  }
  finally { isSubmitting.value = false }
}

onMounted(async () => {
  if (isEditing.value) await loadVacancy()
  else if (editorRef.value) editorRef.value.innerHTML = ''
})
</script>

<style scoped>
/* ── Корень ────────────────────────────────────────────────────────────────── */
.vf { max-width: 860px; margin: 0 auto; display: flex; flex-direction: column; gap: var(--spacing-sm); }

/* ── Секции ────────────────────────────────────────────────────────────────── */
.vf-section {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  border: 1px solid var(--color-border);
  transition: var(--transition);
}
.vf-section:hover { box-shadow: 0 6px 28px var(--color-shadow); }

.vf-section-title {
  font-size: 15px; font-weight: 700; letter-spacing: 0.02em;
  color: var(--color-text); margin-bottom: var(--spacing-sm);
  display: flex; align-items: center; gap: var(--spacing-xs); flex-wrap: wrap;
}
.vf-section-title--mb0 { margin-bottom: 0; }
.vf-title-badge {
  font-size: 11px; font-weight: 500; color: var(--color-text-muted);
  background: var(--color-surface-darker); border-radius: var(--border-radius-pill);
  padding: 2px 9px; white-space: nowrap;
}
.vf-section-hint { font-size: 13px; color: var(--color-text-muted); margin-bottom: var(--spacing-sm); }

/* ── Сетка ─────────────────────────────────────────────────────────────────── */
.vf-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-sm); }
.vf-full { grid-column: 1 / -1; }
.vf-salary-grid { grid-template-columns: 1fr 1fr 140px; }

/* ── Поля ──────────────────────────────────────────────────────────────────── */
.vf-field { display: flex; flex-direction: column; gap: 6px; }
.vf-toggle-field { justify-content: flex-end; }

.vf-label {
  font-size: 12px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.06em; color: var(--color-text-muted);
}
.vf-req { color: #e53e3e; }

.vf-input, .vf-select, .vf-textarea {
  width: 100%; padding: 11px 14px;
  border: 1.5px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  font-size: 14px; font-family: inherit;
  background: var(--color-surface-lighter); color: var(--color-text);
  transition: var(--transition); outline: none;
}
.vf-input:hover, .vf-select:hover, .vf-textarea:hover { border-color: rgba(16,106,183,0.35); }
.vf-input:focus, .vf-select:focus, .vf-textarea:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-soft);
}
.vf-input--error { border-color: #e53e3e !important; background: #fff5f5; }

/* Сообщение об ошибке — явный контрастный цвет */
.vf-error-msg {
  font-size: 12px;
  color: #c53030;
  background: #fff5f5;
  border: 1px solid #fed7d7;
  border-radius: 8px;
  padding: 4px 10px;
  display: inline-block;
}

.vf-textarea { resize: vertical; min-height: 90px; }
.vf-select { cursor: pointer; }

/* ── Toggle ────────────────────────────────────────────────────────────────── */
.vf-toggle { display: flex; align-items: center; gap: 10px; cursor: pointer; user-select: none; }
.vf-toggle-input { display: none; }
.vf-toggle-track {
  width: 44px; height: 24px; border-radius: 12px;
  background: var(--color-border-strong); position: relative; transition: background 0.2s;
  flex-shrink: 0;
}
.vf-toggle-input:checked ~ .vf-toggle-track { background: var(--color-primary); }
.vf-toggle-thumb {
  position: absolute; top: 3px; left: 3px;
  width: 18px; height: 18px; border-radius: 50%; background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.2); transition: left 0.2s;
}
.vf-toggle-input:checked ~ .vf-toggle-track .vf-toggle-thumb { left: 23px; }
.vf-toggle-label { font-size: 14px; color: var(--color-text); font-weight: 500; }

/* ── Навыки ────────────────────────────────────────────────────────────────── */
.vf-skills-box {
  border: 1.5px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  padding: 8px 10px;
  background: var(--color-surface-lighter);
  transition: var(--transition);
  min-height: 48px;
}
.vf-skills-box--focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-soft); }
.vf-skills-tags { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }

.vf-skill-tag {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 4px 10px;
  background: var(--color-primary-soft);
  border: 1px solid rgba(16,106,183,0.2);
  border-radius: var(--border-radius-pill);
  font-size: 13px; font-weight: 500; color: var(--color-primary-dark);
}
.vf-skill-del {
  background: none; border: none; cursor: pointer;
  color: var(--color-primary); font-size: 16px; line-height: 1;
  padding: 0 1px; opacity: 0.6; transition: opacity 0.15s;
}
.vf-skill-del:hover { opacity: 1; }
.vf-skills-input {
  flex: 1; min-width: 140px; border: none; outline: none;
  padding: 4px 6px; font-size: 14px; background: transparent; color: var(--color-text);
}
.vf-suggestions { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.vf-suggestion {
  padding: 3px 10px; background: var(--color-surface-darker);
  border: 1px dashed rgba(16,106,183,0.3); border-radius: var(--border-radius-pill);
  font-size: 12px; color: var(--color-primary); cursor: pointer; transition: var(--transition);
}
.vf-suggestion:hover { background: var(--color-primary-soft); border-style: solid; }

/* ── Редактор ──────────────────────────────────────────────────────────────── */
.vf-toolbar {
  display: flex; align-items: center; gap: 2px; flex-wrap: wrap;
  padding: 6px 10px;
  background: var(--color-surface-darker);
  border: 1.5px solid var(--color-border);
  border-bottom: none;
  border-radius: var(--border-radius-sm) var(--border-radius-sm) 0 0;
}
.vf-tb {
  padding: 5px 10px; min-width: 34px; border: 1px solid transparent;
  border-radius: 8px; font-size: 13px; font-family: inherit;
  cursor: pointer; transition: var(--transition);
  color: var(--color-text-light); background: none; line-height: 1.4;
}
.vf-tb:hover  { background: var(--color-primary-soft); color: var(--color-primary); }
.vf-tb.active { background: var(--color-primary-soft); color: var(--color-primary); border-color: rgba(16,106,183,0.25); }
.vf-tb-mono   { font-family: monospace; font-size: 12px; }
.vf-tb-clear  { color: #e53e3e; }
.vf-tb-clear:hover { background: #fff5f5; color: #c53030; }
.vf-tb-divider { width: 1px; height: 20px; background: var(--color-border); margin: 0 3px; flex-shrink: 0; }

.vf-editor {
  min-height: 200px; max-height: 480px; overflow-y: auto;
  padding: 14px 16px;
  border: 1.5px solid var(--color-border);
  border-radius: 0 0 var(--border-radius-sm) var(--border-radius-sm);
  background: var(--color-surface-lighter); color: var(--color-text);
  font-size: 14px; line-height: 1.75; font-family: inherit;
  outline: none; transition: border-color 0.2s, box-shadow 0.2s;
}
.vf-editor:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-soft); }
.vf-editor:deep(h1),.vf-editor:deep(h2),.vf-editor:deep(h3) { font-weight: 700; color: var(--color-text); margin: 10px 0 5px; }
.vf-editor:deep(ul),.vf-editor:deep(ol) { padding-left: 22px; margin: 6px 0; }
.vf-editor:deep(li) { margin: 3px 0; }
.vf-editor:deep(code) { background: var(--color-surface-darker); padding: 1px 6px; border-radius: 5px; font-family: monospace; font-size: 13px; }
.vf-editor:deep(p) { margin: 4px 0; }
.vf-editor[contenteditable="true"]:empty::before {
  content: "Введите описание вакансии — поддерживается форматирование...";
  color: var(--color-text-muted); pointer-events: none;
}
.vf-editor-hint { font-size: 12px; color: var(--color-text-muted); margin-top: 7px; padding-left: 2px; }

/* ── Аккордеон шаблонов ────────────────────────────────────────────────────── */
.vf-accordion-header { display: flex; justify-content: space-between; align-items: center; cursor: pointer; padding: 4px 0; }
.vf-accordion-chevron { font-size: 12px; color: var(--color-text-muted); transition: transform 0.2s; }
.vf-accordion-chevron.rotated { transform: rotate(90deg); }
.vf-accordion-body { padding-top: var(--spacing-sm); display: flex; flex-direction: column; gap: var(--spacing-sm); }
.accordion-enter-active,.accordion-leave-active { transition: all 0.25s ease; overflow: hidden; }
.accordion-enter-from,.accordion-leave-to { opacity: 0; max-height: 0; padding-top: 0; }
.accordion-enter-to,.accordion-leave-from { max-height: 600px; }

/* ── Кнопки ─────────────────────────────────────────────────────────────────── */
.vf-actions { display: flex; justify-content: flex-end; gap: var(--spacing-xs); padding-top: var(--spacing-xs); }

@media (max-width: 768px) {
  .vf-grid,.vf-salary-grid { grid-template-columns: 1fr; }
  .vf-actions { flex-direction: column; }
  .vf-actions .btn { width: 100%; }
}
</style>
