<template>
  <div class="vacancy-form">
    <form @submit.prevent="handleSubmit" class="form">
      <!-- Основная информация -->
      <div class="form-section">
        <h3 class="section-title">Основная информация</h3>
        
        <div class="form-grid">
          <!-- Название вакансии -->
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

          <!-- Локация -->
          <div class="form-group">
            <label for="location" class="form-label">Локация</label>
            <input
              id="location"
              v-model="form.location"
              type="text"
              class="input"
              placeholder="Москва, удалённо, гибрид..."
              @blur="validateField('location')"
            />
          </div>

          <!-- Статус активности -->
          <div class="form-group">
            <label class="form-label">Статус</label>
            <div class="toggle-group">
              <label class="toggle-label">
                <input
                  v-model="form.is_active"
                  type="checkbox"
                  class="toggle-checkbox"
                />
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
            <input
              id="salary_min"
              v-model.number="form.salary_range.min"
              type="number"
              class="input"
              placeholder="100000"
              min="0"
              step="1000"
            />
          </div>

          <div class="form-group">
            <label for="salary_max" class="form-label">До (₽)</label>
            <input
              id="salary_max"
              v-model.number="form.salary_range.max"
              type="number"
              class="input"
              placeholder="200000"
              min="0"
              step="1000"
            />
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
      </div>

      <!-- Ключевые навыки -->
      <div class="form-section">
        <h3 class="section-title">
          Ключевые навыки
          <span class="section-subtitle">(введите навык и нажмите Enter или запятую)</span>
        </h3>
        
        <div class="skills-input-container">
          <div class="skills-tags">
            <span
              v-for="(skill, index) in form.key_skills"
              :key="index"
              class="skill-tag"
            >
              {{ skill }}
              <button
                type="button"
                class="skill-remove"
                @click="removeSkill(index)"
                title="Удалить"
              >
                ×
              </button>
            </span>
            
            <input
              ref="skillInput"
              v-model="newSkill"
              type="text"
              class="skills-input"
              placeholder="Введите навык..."
              @keydown.enter.prevent="addSkill"
              @keydown.188.prevent="addSkill"
              @keydown.tab="addSkill"
              @keydown.delete="handleSkillDelete"
            />
          </div>
        </div>
        
        <div class="skills-suggestions" v-if="skillSuggestions.length">
          <span
            v-for="suggestion in skillSuggestions"
            :key="suggestion"
            class="suggestion-tag"
            @click="addSuggestedSkill(suggestion)"
          >
            {{ suggestion }}
          </span>
        </div>
      </div>

      <!-- Описание вакансии -->
      <div class="form-section">
        <h3 class="section-title">Описание вакансии</h3>
        
        <div class="description-tabs">
          <button
            type="button"
            class="tab-btn"
            :class="{ active: descriptionMode === 'edit' }"
            @click="descriptionMode = 'edit'"
          >
            ✏️ Редактировать
          </button>
          <button
            type="button"
            class="tab-btn"
            :class="{ active: descriptionMode === 'preview' }"
            @click="descriptionMode = 'preview'"
          >
            👁️ Предпросмотр
          </button>
          <button
            type="button"
            class="tab-btn"
            :class="{ active: descriptionMode === 'split' }"
            @click="descriptionMode = 'split'"
          >
            🔄 Разделить
          </button>
        </div>

        <div class="description-container" :class="descriptionMode">
          <!-- HTML редактор (упрощённый) -->
          <div v-if="['edit', 'split'].includes(descriptionMode)" class="description-edit">
            <label class="form-label">HTML версия (для отображения)</label>
            <textarea
              v-model="form.description_html"
              class="textarea"
              rows="8"
              placeholder="<h3>Обязанности</h3><ul><li>...</li></ul>"
            ></textarea>
            
            <label class="form-label">Текстовая версия (для AI)</label>
            <textarea
              v-model="form.description_text"
              class="textarea"
              rows="6"
              placeholder="Опишите обязанности, требования, условия работы..."
            ></textarea>
          </div>

          <!-- Предпросмотр -->
          <div v-if="['preview', 'split'].includes(descriptionMode)" class="description-preview">
            <div class="preview-content" v-html="form.description_html || '<p>Нет описания</p>'"></div>
          </div>
        </div>
      </div>

      <!-- Комментарий для AI -->
      <div class="form-section">
        <h3 class="section-title">
          Комментарий для AI
          <span class="section-subtitle">(дополнительные инструкции для анализа)</span>
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
            <textarea
              v-model="form.templates.hh_invitation"
              class="textarea"
              rows="3"
              placeholder="Здравствуйте! Приглашаем вас на вакансию..."
            ></textarea>
          </div>

          <div class="form-group">
            <label class="form-label">Приглашение в Telegram/WhatsApp</label>
            <textarea
              v-model="form.templates.messenger_invitation"
              class="textarea"
              rows="3"
              placeholder="Привет! 👋 Рассматриваешь новые возможности?..."
            ></textarea>
          </div>

          <div class="form-group">
            <label class="form-label">Вопросы для интервью</label>
            <textarea
              v-model="form.templates.interview_questions"
              class="textarea"
              rows="4"
              placeholder="1. Расскажи о своём опыте с Python...\n2. ..."
            ></textarea>
          </div>

          <div class="form-group">
            <label class="form-label">Шаблон отказа</label>
            <textarea
              v-model="form.templates.rejection"
              class="textarea"
              rows="3"
              placeholder="Благодарим за интерес к вакансии..."
            ></textarea>
          </div>
        </div>
      </div>

      <!-- Ошибки формы -->
      <div v-if="Object.keys(errors).length" class="form-errors">
        <div class="error-summary">
          <span class="error-icon">⚠️</span>
          <span>Пожалуйста, исправьте ошибки в форме</span>
        </div>
        <ul class="error-list">
          <li v-for="(error, field) in errors" :key="field">{{ error }}</li>
        </ul>
      </div>

      <!-- Действия -->
      <div class="form-actions">
        <button
          type="button"
          class="btn btn-secondary"
          @click="handleCancel"
        >
          Отмена
        </button>
        <button
          type="submit"
          class="btn btn-primary"
          :disabled="isSubmitting || !isValid"
        >
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
  vacancyId: {
    type: Number,
    default: null
  }
})

const router = useRouter()
const vacanciesStore = useVacanciesStore()

// Состояние формы
const form = reactive({
  title: '',
  location: '',
  salary_range: {
    min: null,
    max: null,
    currency: 'RUB'
  },
  key_skills: [],
  description_html: '',
  description_text: '',
  comment_for_ai: '',
  templates: {
    hh_invitation: '',
    messenger_invitation: '',
    interview_questions: '',
    rejection: ''
  },
  is_active: true
})

const newSkill = ref('')
const skillInput = ref(null)
const errors = ref({})
const isSubmitting = ref(false)
const descriptionMode = ref('edit')
const showTemplates = ref(false)

// Популярные навыки для подсказок (можно загружать с бэкенда)
const popularSkills = [
  'Python', 'JavaScript', 'Java', 'C++', 'C#',
  'React', 'Vue', 'Angular', 'Node.js', 'Django',
  'FastAPI', 'Flask', 'Spring', 'SQL', 'PostgreSQL',
  'MySQL', 'MongoDB', 'Redis', 'Docker', 'Kubernetes',
  'AWS', 'GCP', 'Azure', 'Git', 'Linux',
  'TypeScript', 'Go', 'Rust', 'PHP', 'Ruby'
]

// Фильтрованные подсказки
const skillSuggestions = computed(() => {
  if (!newSkill.value || newSkill.value.length < 2) return []
  
  const input = newSkill.value.toLowerCase()
  return popularSkills
    .filter(skill => 
      skill.toLowerCase().includes(input) &&
      !form.key_skills.includes(skill)
    )
    .slice(0, 5)
})

// Режим редактирования
const isEditing = computed(() => !!props.vacancyId)

// Валидация формы
const isValid = computed(() => {
  return form.title && form.title.length >= 3
})

// Валидация поля
const validateField = (field) => {
  const newErrors = { ...errors.value }
  
  switch (field) {
    case 'title':
      if (!form.title) {
        newErrors.title = 'Название обязательно'
      } else if (form.title.length < 3) {
        newErrors.title = 'Название должно быть не короче 3 символов'
      } else {
        delete newErrors.title
      }
      break
      
    case 'salary_range':
      if (form.salary_range.min && form.salary_range.max) {
        if (form.salary_range.min > form.salary_range.max) {
          newErrors.salary_range = 'Минимальная зарплата не может быть больше максимальной'
        } else {
          delete newErrors.salary_range
        }
      }
      break
  }
  
  errors.value = newErrors
}

// Загрузка данных для редактирования
const loadVacancy = async () => {
  try {
    const vacancy = await vacanciesStore.fetchVacancy(props.vacancyId)
    
    // Заполняем форму
    form.title = vacancy.title
    form.location = vacancy.location || ''
    form.salary_range = vacancy.salary_range || { min: null, max: null, currency: 'RUB' }
    form.key_skills = vacancy.key_skills || []
    form.description_html = vacancy.description_html || ''
    form.description_text = vacancy.description_text || ''
    form.comment_for_ai = vacancy.comment_for_ai || ''
    form.templates = vacancy.templates || {
      hh_invitation: '',
      messenger_invitation: '',
      interview_questions: '',
      rejection: ''
    }
    form.is_active = vacancy.is_active
    
  } catch (error) {
    console.error('Ошибка загрузки вакансии:', error)
  }
}

// Добавление навыка
const addSkill = () => {
  const skill = newSkill.value.trim()
  if (skill && !form.key_skills.includes(skill)) {
    form.key_skills.push(skill)
    newSkill.value = ''
    
    // Сброс ошибок
    if (errors.value.skills) {
      delete errors.value.skills
    }
  }
}

// Добавление навыка из подсказки
const addSuggestedSkill = (skill) => {
  if (!form.key_skills.includes(skill)) {
    form.key_skills.push(skill)
    newSkill.value = ''
  }
}

// Удаление навыка
const removeSkill = (index) => {
  form.key_skills.splice(index, 1)
}

// Обработка удаления в пустом поле
const handleSkillDelete = (e) => {
  if (e.target.value === '' && form.key_skills.length > 0) {
    form.key_skills.pop()
  }
}

// Отмена
const handleCancel = () => {
  router.push('/vacancies')
}

// Отправка формы
const handleSubmit = async () => {
  // Валидация
  validateField('title')
  validateField('salary_range')
  
  if (Object.keys(errors.value).length) {
    return
  }
  
  isSubmitting.value = true
  
  try {
    // Подготавливаем данные
    const vacancyData = {
      title: form.title,
      location: form.location || undefined,
      salary_range: {
        min: form.salary_range.min || undefined,
        max: form.salary_range.max || undefined,
        currency: form.salary_range.currency
      },
      key_skills: form.key_skills,
      description_html: form.description_html || undefined,
      description_text: form.description_text || undefined,
      comment_for_ai: form.comment_for_ai || undefined,
      templates: form.templates,
      is_active: form.is_active
    }
    
    if (isEditing.value) {
      await vacanciesStore.updateVacancy(props.vacancyId, vacancyData)
    } else {
      await vacanciesStore.createVacancy(vacancyData)
    }
    
    router.push('/vacancies')
    
  } catch (error) {
    console.error('Ошибка сохранения:', error)
  } finally {
    isSubmitting.value = false
  }
}

// Следим за изменениями зарплаты для валидации
watch(
  () => [form.salary_range.min, form.salary_range.max],
  () => {
    validateField('salary_range')
  }
)

// Загружаем данные при монтировании
onMounted(async () => {
  if (isEditing.value) {
    await loadVacancy()
  }
})
</script>

<style scoped>
.vacancy-form {
  max-width: 900px;
  margin: 0 auto;
}

.form-section {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  margin-bottom: var(--spacing);
  border: 1px solid var(--color-border);
  transition: var(--transition);
}

.form-section:hover {
  box-shadow: 0 8px 30px var(--color-shadow);
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing-sm);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.section-subtitle {
  font-size: 13px;
  font-weight: normal;
  color: var(--color-text-muted);
  margin-left: auto;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-sm);
}

.full-width {
  grid-column: 1 / -1;
}

.salary-grid {
  grid-template-columns: 1fr 1fr 0.5fr;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xxs);
}

.form-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  margin-left: 4px;
}

.required {
  color: var(--color-warning-border);
  margin-left: 2px;
}

.input, .textarea, .select {
  width: 100%;
  padding: 12px;
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  font-size: 14px;
  font-family: inherit;
  background: var(--color-surface-lighter);
  color: var(--color-text);
  transition: var(--transition);
}

.textarea {
  resize: vertical;
  min-height: 100px;
}

.input:hover, .textarea:hover, .select:hover {
  border-color: var(--color-primary);
}

.input:focus, .textarea:focus, .select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-soft);
}

.input.error {
  border-color: var(--color-warning-border);
}

.error-text {
  font-size: 12px;
  color: var(--color-warning-border);
  margin-left: 4px;
}

/* Toggle switch */
.toggle-group {
  display: flex;
  align-items: center;
  height: 100%;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  cursor: pointer;
}

.toggle-checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: var(--color-primary);
}

.toggle-text {
  font-size: 14px;
  color: var(--color-text);
}

/* Skills input */
.skills-input-container {
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  padding: 8px;
  background: var(--color-surface-lighter);
  transition: var(--transition);
}

.skills-input-container:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-soft);
}

.skills-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.skill-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: var(--color-primary-soft);
  border-radius: var(--border-radius-pill);
  font-size: 13px;
  color: var(--color-primary-dark);
  border: 1px solid var(--color-primary);
}

.skill-remove {
  background: none;
  border: none;
  color: var(--color-primary-dark);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  padding: 0 2px;
  opacity: 0.7;
  transition: var(--transition);
}

.skill-remove:hover {
  opacity: 1;
  transform: scale(1.2);
}

.skills-input {
  flex: 1;
  min-width: 150px;
  border: none;
  outline: none;
  padding: 6px;
  font-size: 14px;
  background: transparent;
  color: var(--color-text);
}

.skills-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: var(--spacing-xs);
}

.suggestion-tag {
  padding: 4px 10px;
  background: var(--color-surface);
  border: 1px dashed var(--color-primary);
  border-radius: var(--border-radius-pill);
  font-size: 12px;
  color: var(--color-primary);
  cursor: pointer;
  transition: var(--transition);
}

.suggestion-tag:hover {
  background: var(--color-primary-soft);
  transform: translateY(-1px);
}

/* Description tabs */
.description-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: var(--spacing-xs);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 4px;
}

.tab-btn {
  padding: 8px 16px;
  background: none;
  border: none;
  border-radius: var(--border-radius-pill);
  font-size: 14px;
  cursor: pointer;
  transition: var(--transition);
  color: var(--color-text-muted);
}

.tab-btn:hover {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.tab-btn.active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
  font-weight: 500;
}

.description-container {
  display: grid;
  gap: var(--spacing-sm);
}

.description-container.edit {
  grid-template-columns: 1fr;
}

.description-container.preview {
  grid-template-columns: 1fr;
}

.description-container.split {
  grid-template-columns: 1fr 1fr;
}

.description-edit,
.description-preview {
  background: var(--color-surface-darker);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing-sm);
}

.preview-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text);
}

.preview-content :deep(h1),
.preview-content :deep(h2),
.preview-content :deep(h3) {
  color: var(--color-text);
  margin-bottom: var(--spacing-xs);
}

.preview-content :deep(ul),
.preview-content :deep(ol) {
  padding-left: 20px;
  margin-bottom: var(--spacing-xs);
}

/* Accordion */
.accordion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding: var(--spacing-xs) 0;
}

.accordion-icon {
  font-size: 14px;
  color: var(--color-text-muted);
  transition: var(--transition);
}

.accordion-header:hover .accordion-icon {
  color: var(--color-primary);
}

.accordion-content {
  animation: slideDown 0.3s ease;
  padding-top: var(--spacing-sm);
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

/* Form errors */
.form-errors {
  background: var(--color-error);
  border-left: 6px solid var(--color-error-border);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing-sm);
  margin-bottom: var(--spacing);
}

.error-summary {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  color: var(--color-error-text);
  font-weight: 600;
  margin-bottom: var(--spacing-xs);
}

.error-icon {
  font-size: 18px;
}

.error-list {
  margin-left: 30px;
  color: var(--color-error-text);
  font-size: 14px;
}

.error-list li {
  margin: 4px 0;
}

/* Form actions */
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing);
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 768px) {
  .form-grid,
  .salary-grid {
    grid-template-columns: 1fr;
  }
  
  .description-container.split {
    grid-template-columns: 1fr;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .form-actions .btn {
    width: 100%;
  }
}
</style>
