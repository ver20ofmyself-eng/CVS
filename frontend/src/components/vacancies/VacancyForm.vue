<template>
  <div class="vacancy-form">
    <form @submit.prevent="handleSubmit" class="form">

      <!-- Основная информация -->
      <div class="form-section">
        <h3 class="section-title">Основная информация</h3>
        <div class="form-grid">
          <div class="form-group full-width">
            <label for="title" class="form-label">
              Название вакансии <span class="required">*</span>
            </label>
            <input
              id="title"
              v-model="form.title"
              type="text"
              class="input"
              placeholder="Например: Senior Python Developer"
              required
              :class="{ 'error': errors.title }"
              @blur="validateField('title')"
            />
            <span v-if="errors.title" class="error-text">{{ errors.title }}</span>
          </div>

          <div class="form-group">
            <label for="location" class="form-label">Локация</label>
            <input
              id="location"
              v-model="form.location"
              type="text"
              class="input"
              placeholder="Москва, удалённо, гибрид..."
            />
          </div>

          <div class="form-group">
            <label class="form-label">Статус</label>
            <div class="toggle-group">
              <label class="toggle-label">
                <input v-model="form.is_active" type="checkbox" class="toggle-checkbox" />
                <span class="toggle-text">{{ form.is_active ? 'Активна' : 'В архиве' }}</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Зарплатная вилка -->
      <div class="form-section">
        <h3 class="section-title">Зарплатная вилка</h3>
        <div class="form-grid salary-grid">
          <div class="form-group">
            <label for="salary_min" class="form-label">От (₽)</label>
            <input id="salary_min" v-model.number="form.salary_range.min" type="number" class="input" placeholder="100000" min="0" step="1000" />
          </div>
          <div class="form-group">
            <label for="salary_max" class="form-label">До (₽)</label>
            <input id="salary_max" v-model.number="form.salary_range.max" type="number" class="input" placeholder="200000" min="0" step="1000" />
          </div>
          <div class="form-group">
            <label for="currency" class="form-label">Валюта</label>
            <select id="currency" v-model="form.salary_range.currency" class="select">
              <option value="RUB">🇷🇺 RUB</option>
              <option value="USD">🇺🇸 USD</option>
              <option value="EUR">🇪🇺 EUR</option>
              <option value="KZT">🇰🇿 KZT</option>
            </select>
          </div>
        </div>
        <span v-if="errors.salary_range" class="error-text">{{ errors.salary_range }}</span>
      </div>

      <!-- Ключевые навыки — задача 2: добавлена поддержка ";" -->
      <div class="form-section">
        <h3 class="section-title">
          Ключевые навыки
          <span class="section-subtitle">Enter, запятая или точка с запятой «;» разделяют навыки. Можно вставить список: «python;flask;docker»</span>
        </h3>

        <div class="skills-input-container">
          <div class="skills-tags">
            <span v-for="(skill, index) in form.key_skills" :key="index" class="skill-tag">
              {{ skill }}
              <button type="button" class="skill-remove" @click="removeSkill(index)" title="Удалить">×</button>
            </span>
            <input
              ref="skillInput"
              v-model="newSkill"
              type="text"
              class="skills-input"
              placeholder="Введите навык или вставьте список через «;»..."
              @keydown.enter.prevent="addSkillsFromInput"
              @keydown.188.prevent="addSkillsFromInput"
              @keydown.delete="handleSkillDelete"
              @input="handleSkillInput"
              @paste.prevent="handleSkillPaste"
            />
          </div>
        </div>

        <div class="skills-suggestions" v-if="skillSuggestions.length">
          <span v-for="suggestion in skillSuggestions" :key="suggestion" class="suggestion-tag" @click="addSuggestedSkill(suggestion)">
            {{ suggestion }}
          </span>
        </div>
      </div>

      <!-- Описание вакансии — задача 3: единый WYSIWYG-редактор -->
      <div class="form-section">
        <h3 class="section-title">Описание вакансии</h3>

        <!-- Панель форматирования -->
        <div class="editor-toolbar">
          <button type="button" class="toolbar-btn" @click="execCmd('bold')" title="Жирный (Ctrl+B)"><b>B</b></button>
          <button type="button" class="toolbar-btn" @click="execCmd('italic')" title="Курсив (Ctrl+I)"><i>I</i></button>
          <button type="button" class="toolbar-btn" @click="execCmd('underline')" title="Подчёркнутый"><u>U</u></button>
          <div class="toolbar-divider"></div>
          <button type="button" class="toolbar-btn" @click="execCmd('insertUnorderedList')" title="Маркированный список">• —</button>
          <button type="button" class="toolbar-btn" @click="execCmd('insertOrderedList')" title="Нумерованный список">1.</button>
          <div class="toolbar-divider"></div>
          <button type="button" class="toolbar-btn" @click="execHeading('h3')" title="Заголовок">H3</button>
          <button type="button" class="toolbar-btn" @click="execCmd('removeFormat')" title="Убрать форматирование">✕</button>
        </div>

        <!-- Редактируемая область -->
        <div
          ref="editorRef"
          class="rich-editor"
          contenteditable="true"
          @input="onEditorInput"
          @paste="onEditorPaste"
        ></div>

        <p class="editor-hint">Поддерживается форматирование: жирный, курсив, списки, заголовки. При анализе AI использует текстовую версию.</p>
      </div>

      <!-- Комментарий для AI -->
      <div class="form-section">
        <h3 class="section-title">
          Комментарий для AI
          <span class="section-subtitle">дополнительные инструкции для анализа</span>
        </h3>
        <textarea
          v-model="form.comment_for_ai"
          class="textarea"
          rows="4"
          placeholder="Например: Особое внимание обращать на опыт с микросервисами, знание английского не обязательно..."
        ></textarea>
      </div>

      <!-- Шаблоны сообщений (аккордеон) -->
      <div class="form-section">
        <div class="accordion-header" @click="showTemplates = !showTemplates">
          <h3 class="section-title">📋 Шаблоны сообщений</h3>
          <span class="accordion-icon">{{ showTemplates ? '▼' : '▶' }}</span>
        </div>
        <div v-if="showTemplates" class="accordion-content">
          <div class="form-group">
            <label class="form-label">Приглашение на hh.ru</label>
            <textarea v-model="form.templates.hh_invitation" class="textarea" rows="3" placeholder="Здравствуйте! Приглашаем вас на вакансию..."></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">Приглашение в Telegram/WhatsApp</label>
            <textarea v-model="form.templates.messenger_invitation" class="textarea" rows="3" placeholder="Привет! 👋 Рассматриваешь новые возможности?..."></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">Вопросы для интервью</label>
            <textarea v-model="form.templates.interview_questions" class="textarea" rows="4" placeholder="1. Расскажи о своём опыте с Python..."></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">Шаблон отказа</label>
            <textarea v-model="form.templates.rejection" class="textarea" rows="3" placeholder="Благодарим за интерес к вакансии..."></textarea>
          </div>
        </div>
      </div>

      <!-- Ошибки формы -->
      <div v-if="Object.keys(errors).length" class="form-errors">
        <div class="error-summary">
          <span class="error-icon">⚠️</span>
          <span>Пожалуйста, исправьте ошибки в форме</span>
        </div>
      </div>

      <!-- Действия -->
      <div class="form-actions">
        <button type="button" class="btn btn-secondary" @click="handleCancel">Отмена</button>
        <button type="submit" class="btn btn-primary" :disabled="isSubmitting || !isValid">
          <span v-if="isSubmitting" class="spinner"></span>
          <span v-else>{{ isEditing ? 'Сохранить' : 'Создать вакансию' }}</span>
        </button>
      </div>

    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useVacanciesStore } from '@/stores/vacancies'

const props = defineProps({
  vacancyId: { type: Number, default: null }
})

const router = useRouter()
const vacanciesStore = useVacanciesStore()

// ── Форма ──────────────────────────────────────────────────────────────────────
const form = reactive({
  title: '',
  location: '',
  salary_range: { min: null, max: null, currency: 'RUB' },
  key_skills: [],
  description_html: '',
  comment_for_ai: '',
  templates: { hh_invitation: '', messenger_invitation: '', interview_questions: '', rejection: '' },
  is_active: true
})

const newSkill      = ref('')
const skillInput    = ref(null)
const editorRef     = ref(null)
const errors        = ref({})
const isSubmitting  = ref(false)
const showTemplates = ref(false)

// ── Навыки ─────────────────────────────────────────────────────────────────────
const popularSkills = [
  'Python','JavaScript','Java','C++','C#','React','Vue','Angular','Node.js','Django',
  'FastAPI','Flask','Spring','SQL','PostgreSQL','MySQL','MongoDB','Redis','Docker',
  'Kubernetes','AWS','GCP','Azure','Git','Linux','TypeScript','Go','Rust','PHP','Ruby'
]

const skillSuggestions = computed(() => {
  if (!newSkill.value || newSkill.value.length < 2) return []
  const input = newSkill.value.toLowerCase()
  return popularSkills
    .filter(s => s.toLowerCase().includes(input) && !form.key_skills.includes(s))
    .slice(0, 5)
})

/** Разбивает строку по разделителям: ; , Enter и добавляет навыки */
function parseAndAddSkills(raw) {
  const parts = raw.split(/[;,\n]+/).map(s => s.trim()).filter(Boolean)
  parts.forEach(skill => {
    if (skill && !form.key_skills.includes(skill)) {
      form.key_skills.push(skill)
    }
  })
  newSkill.value = ''
}

const addSkillsFromInput = () => {
  if (newSkill.value.trim()) parseAndAddSkills(newSkill.value)
}

/** При вводе символа ";" — немедленно разбиваем */
const handleSkillInput = (e) => {
  if (newSkill.value.includes(';') || newSkill.value.includes(',')) {
    parseAndAddSkills(newSkill.value)
  }
}

/** Вставка из буфера — тоже разбиваем по разделителям */
const handleSkillPaste = (e) => {
  const text = (e.clipboardData || window.clipboardData).getData('text')
  parseAndAddSkills(text)
}

const addSuggestedSkill = (skill) => {
  if (!form.key_skills.includes(skill)) {
    form.key_skills.push(skill)
    newSkill.value = ''
  }
}

const removeSkill = (index) => form.key_skills.splice(index, 1)

const handleSkillDelete = (e) => {
  if (e.target.value === '' && form.key_skills.length > 0) form.key_skills.pop()
}

// ── WYSIWYG редактор ───────────────────────────────────────────────────────────
function execCmd(cmd) {
  document.execCommand(cmd, false, null)
  editorRef.value?.focus()
}

function execHeading(tag) {
  document.execCommand('formatBlock', false, tag)
  editorRef.value?.focus()
}

function onEditorInput() {
  form.description_html = editorRef.value?.innerHTML || ''
}

function onEditorPaste(e) {
  // Вставка как plain text, сохраняя переносы строк
  e.preventDefault()
  const text = (e.clipboardData || window.clipboardData).getData('text/plain')
  document.execCommand('insertText', false, text)
}

// ── Валидация ──────────────────────────────────────────────────────────────────
const isEditing = computed(() => !!props.vacancyId)
const isValid   = computed(() => form.title && form.title.length >= 3)

const validateField = (field) => {
  const e = { ...errors.value }
  if (field === 'title') {
    if (!form.title) e.title = 'Название обязательно'
    else if (form.title.length < 3) e.title = 'Минимум 3 символа'
    else delete e.title
  }
  if (field === 'salary_range') {
    if (form.salary_range.min && form.salary_range.max && form.salary_range.min > form.salary_range.max)
      e.salary_range = 'Минимальная зарплата не может быть больше максимальной'
    else delete e.salary_range
  }
  errors.value = e
}

// ── Загрузка для редактирования ────────────────────────────────────────────────
const loadVacancy = async () => {
  try {
    const vacancy = await vacanciesStore.fetchVacancy(props.vacancyId)
    form.title        = vacancy.title
    form.location     = vacancy.location || ''
    form.salary_range = vacancy.salary_range || { min: null, max: null, currency: 'RUB' }
    form.key_skills   = vacancy.key_skills || []
    // Загружаем description: предпочитаем html, иначе text
    const html = vacancy.description_html || ''
    const text = vacancy.description_text || ''
    form.description_html = html || (text ? text.replace(/\n/g, '<br>') : '')
    form.comment_for_ai   = vacancy.comment_for_ai || ''
    form.templates = vacancy.templates || { hh_invitation: '', messenger_invitation: '', interview_questions: '', rejection: '' }
    form.is_active = vacancy.is_active

    // Инициализируем редактор
    await nextTick()
    if (editorRef.value) editorRef.value.innerHTML = form.description_html
  } catch (err) {
    console.error('Ошибка загрузки вакансии:', err)
  }
}

// ── Отправка ───────────────────────────────────────────────────────────────────
const handleCancel  = () => router.push('/vacancies')

const handleSubmit = async () => {
  validateField('title')
  validateField('salary_range')
  if (Object.keys(errors.value).length) return

  isSubmitting.value = true
  try {
    // Формируем и text-версию из HTML для AI
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = form.description_html
    const descriptionText = tempDiv.textContent || tempDiv.innerText || ''

    const vacancyData = {
      title:            form.title,
      location:         form.location || undefined,
      salary_range:     { min: form.salary_range.min || undefined, max: form.salary_range.max || undefined, currency: form.salary_range.currency },
      key_skills:       form.key_skills,
      description_html: form.description_html || undefined,
      description_text: descriptionText || undefined,   // AI-версия автоматически
      comment_for_ai:   form.comment_for_ai || undefined,
      templates:        form.templates,
      is_active:        form.is_active
    }

    if (isEditing.value) await vacanciesStore.updateVacancy(props.vacancyId, vacancyData)
    else                 await vacanciesStore.createVacancy(vacancyData)

    router.push('/vacancies')
  } catch (err) {
    console.error('Ошибка сохранения:', err)
  } finally {
    isSubmitting.value = false
  }
}

watch(() => [form.salary_range.min, form.salary_range.max], () => validateField('salary_range'))

onMounted(async () => {
  if (isEditing.value) await loadVacancy()
  else if (editorRef.value) editorRef.value.innerHTML = ''
})
</script>

<style scoped>
.vacancy-form { max-width: 900px; margin: 0 auto; }

.form-section {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  margin-bottom: var(--spacing);
  border: 1px solid var(--color-border);
  transition: var(--transition);
}
.form-section:hover { box-shadow: 0 8px 30px var(--color-shadow); }

.section-title {
  font-size: 18px; font-weight: 600; color: var(--color-text);
  margin-bottom: var(--spacing-sm);
  display: flex; align-items: center; gap: var(--spacing-xs); flex-wrap: wrap;
}
.section-subtitle { font-size: 13px; font-weight: normal; color: var(--color-text-muted); margin-left: auto; }

.form-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--spacing-sm); }
.full-width { grid-column: 1 / -1; }
.salary-grid { grid-template-columns: 1fr 1fr 0.5fr; }
.form-group { display: flex; flex-direction: column; gap: var(--spacing-xxs); }
.form-label { font-size: 14px; font-weight: 600; color: var(--color-text); margin-left: 4px; }
.required { color: var(--color-warning-border); margin-left: 2px; }

.input, .textarea, .select {
  width: 100%; padding: 12px;
  border: 2px solid var(--color-border); border-radius: var(--border-radius-sm);
  font-size: 14px; font-family: inherit;
  background: var(--color-surface-lighter); color: var(--color-text); transition: var(--transition);
}
.textarea { resize: vertical; min-height: 100px; }
.input:hover, .textarea:hover, .select:hover { border-color: var(--color-primary); }
.input:focus, .textarea:focus, .select:focus {
  outline: none; border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-soft);
}
.input.error { border-color: var(--color-warning-border); }
.error-text { font-size: 12px; color: var(--color-warning-border); margin-left: 4px; }

/* Toggle */
.toggle-group { display: flex; align-items: center; height: 100%; }
.toggle-label { display: flex; align-items: center; gap: var(--spacing-xs); cursor: pointer; }
.toggle-checkbox { width: 20px; height: 20px; cursor: pointer; accent-color: var(--color-primary); }
.toggle-text { font-size: 14px; color: var(--color-text); }

/* Skills */
.skills-input-container {
  border: 2px solid var(--color-border); border-radius: var(--border-radius-sm);
  padding: 8px; background: var(--color-surface-lighter); transition: var(--transition);
}
.skills-input-container:focus-within { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-soft); }
.skills-tags { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.skill-tag {
  display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px;
  background: var(--color-primary-soft); border-radius: var(--border-radius-pill);
  font-size: 13px; color: var(--color-primary-dark); border: 1px solid var(--color-primary);
}
.skill-remove {
  background: none; border: none; color: var(--color-primary-dark);
  font-size: 18px; line-height: 1; cursor: pointer; padding: 0 2px; opacity: 0.7; transition: var(--transition);
}
.skill-remove:hover { opacity: 1; transform: scale(1.2); }
.skills-input {
  flex: 1; min-width: 150px; border: none; outline: none; padding: 6px;
  font-size: 14px; background: transparent; color: var(--color-text);
}
.skills-suggestions { display: flex; flex-wrap: wrap; gap: 6px; margin-top: var(--spacing-xs); }
.suggestion-tag {
  padding: 4px 10px; background: var(--color-surface); border: 1px dashed var(--color-primary);
  border-radius: var(--border-radius-pill); font-size: 12px; color: var(--color-primary);
  cursor: pointer; transition: var(--transition);
}
.suggestion-tag:hover { background: var(--color-primary-soft); transform: translateY(-1px); }

/* WYSIWYG Editor */
.editor-toolbar {
  display: flex; align-items: center; gap: 2px; flex-wrap: wrap;
  padding: 6px 8px; background: var(--color-surface-darker);
  border: 2px solid var(--color-border); border-bottom: none;
  border-radius: var(--border-radius-sm) var(--border-radius-sm) 0 0;
}
.toolbar-btn {
  padding: 4px 10px; background: var(--color-surface); border: 1px solid var(--color-border);
  border-radius: 6px; font-size: 13px; cursor: pointer; transition: var(--transition);
  color: var(--color-text); font-family: inherit;
}
.toolbar-btn:hover { background: var(--color-primary-soft); border-color: var(--color-primary); color: var(--color-primary); }
.toolbar-divider { width: 1px; height: 22px; background: var(--color-border); margin: 0 4px; }

.rich-editor {
  min-height: 180px; max-height: 500px; overflow-y: auto;
  padding: 14px 16px;
  border: 2px solid var(--color-border); border-radius: 0 0 var(--border-radius-sm) var(--border-radius-sm);
  background: var(--color-surface-lighter); color: var(--color-text);
  font-size: 14px; line-height: 1.7; font-family: inherit;
  transition: var(--transition); outline: none;
}
.rich-editor:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-soft); }
.rich-editor:deep(h1), .rich-editor:deep(h2), .rich-editor:deep(h3) {
  font-weight: 600; color: var(--color-text); margin: 8px 0 4px;
}
.rich-editor:deep(ul), .rich-editor:deep(ol) { padding-left: 20px; margin: 6px 0; }
.rich-editor:deep(li) { margin: 2px 0; }
.rich-editor[contenteditable="true"]:empty:before {
  content: "Введите описание вакансии...";
  color: var(--color-text-muted); pointer-events: none;
}

.editor-hint { font-size: 12px; color: var(--color-text-muted); margin-top: 6px; padding-left: 4px; }

/* Accordion */
.accordion-header { display: flex; justify-content: space-between; align-items: center; cursor: pointer; padding: var(--spacing-xs) 0; }
.accordion-icon { font-size: 14px; color: var(--color-text-muted); transition: var(--transition); }
.accordion-header:hover .accordion-icon { color: var(--color-primary); }
.accordion-content { animation: slideDown 0.3s ease; padding-top: var(--spacing-sm); display: flex; flex-direction: column; gap: var(--spacing-sm); }
@keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }

/* Form errors */
.form-errors {
  background: var(--color-error); border-left: 6px solid var(--color-error-border);
  border-radius: var(--border-radius-sm); padding: var(--spacing-sm); margin-bottom: var(--spacing);
}
.error-summary { display: flex; align-items: center; gap: var(--spacing-xs); color: var(--color-error-text); font-weight: 600; }
.error-icon { font-size: 18px; }

/* Actions */
.form-actions { display: flex; justify-content: flex-end; gap: var(--spacing-sm); margin-top: var(--spacing); }

.spinner {
  display: inline-block; width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3); border-radius: 50%;
  border-top-color: white; animation: spin 0.8s linear infinite; margin-right: 8px;
}
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .form-grid, .salary-grid { grid-template-columns: 1fr; }
  .form-actions { flex-direction: column; }
  .form-actions .btn { width: 100%; }
}
</style>
