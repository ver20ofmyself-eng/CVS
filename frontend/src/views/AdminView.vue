<template>
  <div class="admin-view">
    <div class="container">
      <!-- Заголовок -->
      <div class="page-header">
        <h1 class="page-title">
          ⚙️ Админ-панель
          <span class="admin-badge">Администратор</span>
        </h1>
        
        <!-- Кнопка создания нового промпта -->
        <button class="btn btn-primary" @click="openPromptModal()">
          ➕ Новый промпт
        </button>
      </div>

      <!-- Состояние загрузки -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка промптов...</p>
      </div>

      <!-- Ошибка -->
      <div v-else-if="error" class="error-state">
        <span class="error-icon">❌</span>
        <p>{{ error }}</p>
        <button class="btn btn-primary" @click="loadPrompts">Повторить</button>
      </div>

      <!-- Список промптов -->
      <div v-else class="prompts-list">
        <!-- Фильтры -->
        <div class="filters-bar">
          <div class="search-box">
            <input
              v-model="filters.search"
              type="text"
              class="input"
              placeholder="🔍 Поиск по названию..."
              @input="debouncedSearch"
            />
          </div>
          
          <label class="filter-checkbox">
            <input
              v-model="filters.showInactive"
              type="checkbox"
            />
            <span>Показывать неактивные</span>
          </label>
        </div>

        <!-- Карточки промптов -->
        <div class="prompts-grid">
          <div 
            v-for="prompt in filteredPrompts" 
            :key="prompt.id"
            class="prompt-card"
            :class="{ 
              'inactive': !prompt.is_active,
              'default': prompt.is_default 
            }"
          >
            <div class="prompt-header">
              <div class="prompt-title">
                <h3>{{ prompt.name }}</h3>
                <div class="prompt-badges">
                  <span v-if="prompt.is_default" class="badge default">⭐ По умолчанию</span>
                  <span v-if="!prompt.is_active" class="badge inactive">📦 Неактивен</span>
                  <span class="badge version">v{{ prompt.version }}</span>
                </div>
              </div>
              <div class="prompt-actions">
                <button 
                  class="icon-btn" 
                  @click="viewHistory(prompt)"
                  title="История изменений"
                >
                  📜
                </button>
                <button 
                  class="icon-btn" 
                  @click="testPrompt(prompt)"
                  title="Тестировать"
                >
                  🧪
                </button>
                <button 
                  class="icon-btn" 
                  @click="openPromptModal(prompt)"
                  title="Редактировать"
                >
                  ✏️
                </button>
                <button 
                  class="icon-btn" 
                  @click="togglePromptStatus(prompt)"
                  :title="prompt.is_active ? 'Деактивировать' : 'Активировать'"
                >
                  {{ prompt.is_active ? '🔴' : '🟢' }}
                </button>
              </div>
            </div>

            <p class="prompt-description">{{ prompt.description || 'Нет описания' }}</p>

            <div class="prompt-preview">
              <div class="preview-label">System prompt:</div>
              <pre class="preview-text">{{ truncate(prompt.system_prompt, 150) }}</pre>
            </div>

            <div class="prompt-preview">
              <div class="preview-label">User template:</div>
              <pre class="preview-text">{{ truncate(prompt.user_prompt_template, 150) }}</pre>
            </div>

            <div class="prompt-footer">
              <span class="meta">Создан: {{ formatDate(prompt.created_at) }}</span>
              <span class="meta">Обновлён: {{ formatDate(prompt.updated_at) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Модальное окно для создания/редактирования промпта -->
      <Teleport to="body">
        <div v-if="showPromptModal" class="modal-overlay" @click.self="closePromptModal">
          <div class="modal-content modal-lg">
            <div class="modal-header">
              <h3>{{ editingPrompt ? 'Редактирование промпта' : 'Новый промпт' }}</h3>
              <button class="close-btn" @click="closePromptModal">×</button>
            </div>

            <div class="modal-body">
              <form @submit.prevent="savePrompt" class="prompt-form">
                <!-- Основная информация -->
                <div class="form-grid">
                  <div class="form-group full-width">
                    <label class="form-label">Название *</label>
                    <input
                      v-model="promptForm.name"
                      type="text"
                      class="input"
                      required
                      placeholder="Уникальное имя промпта"
                    />
                  </div>

                  <div class="form-group full-width">
                    <label class="form-label">Описание</label>
                    <input
                      v-model="promptForm.description"
                      type="text"
                      class="input"
                      placeholder="Краткое описание назначения"
                    />
                  </div>

                  <div class="form-group full-width">
                    <label class="form-label">System Prompt *</label>
                    <textarea
                      v-model="promptForm.system_prompt"
                      class="textarea"
                      rows="4"
                      required
                      placeholder="Роль и инструкции для AI"
                    ></textarea>
                  </div>

                  <div class="form-group full-width">
                    <label class="form-label">User Prompt Template *</label>
                    <textarea
                      v-model="promptForm.user_prompt_template"
                      class="textarea"
                      rows="6"
                      required
                      placeholder="Шаблон с переменными {title}, {key_skills}, {cv_text} и т.д."
                    ></textarea>
                    <div class="template-variables">
                      <span class="variables-label">Доступные переменные:</span>
                      <code class="variable">title</code>
                      <code class="variable">location</code>
                      <code class="variable">salary_range</code>
                      <code class="variable">key_skills</code>
                      <code class="variable">description_text</code>
                      <code class="variable">comment_for_ai</code>
                      <code class="variable">cv_text</code>
                    </div>
                  </div>

                  <!-- Параметры -->
                  <div class="form-group">
                    <label class="form-label">Temperature</label>
                    <input
                      v-model.number="promptForm.parameters.temperature"
                      type="number"
                      step="0.1"
                      min="0"
                      max="2"
                      class="input"
                    />
                  </div>

                  <div class="form-group">
                    <label class="form-label">Max Tokens</label>
                    <input
                      v-model.number="promptForm.parameters.max_tokens"
                      type="number"
                      min="1"
                      max="4000"
                      class="input"
                    />
                  </div>

                  <div class="form-group">
                    <label class="form-label">Top P</label>
                    <input
                      v-model.number="promptForm.parameters.top_p"
                      type="number"
                      step="0.1"
                      min="0"
                      max="1"
                      class="input"
                    />
                  </div>

                  <!-- Настройки -->
                  <div class="form-group checkbox-group">
                    <label class="checkbox-label">
                      <input
                        v-model="promptForm.is_active"
                        type="checkbox"
                      />
                      <span>Активен</span>
                    </label>
                  </div>

                  <div class="form-group checkbox-group">
                    <label class="checkbox-label">
                      <input
                        v-model="promptForm.is_default"
                        type="checkbox"
                        :disabled="promptForm.is_default && editingPrompt?.is_default"
                      />
                      <span>По умолчанию</span>
                    </label>
                  </div>
                </div>

                <!-- Response Format (JSON редактор) -->
                <div class="form-group full-width">
                  <label class="form-label">Response Format (JSON)</label>
                  <textarea
                    v-model="responseFormatJson"
                    class="textarea json-editor"
                    rows="8"
                    placeholder='{
  "type": "object",
  "properties": {
    "score": { "type": "number" }
  }
}'
                  ></textarea>
                  <div v-if="responseFormatError" class="error-text">
                    {{ responseFormatError }}
                  </div>
                </div>
              </form>
            </div>

            <div class="modal-footer">
              <button class="btn btn-secondary" @click="closePromptModal">
                Отмена
              </button>
              <button 
                class="btn btn-primary" 
                @click="savePrompt"
                :disabled="!isPromptFormValid"
              >
                {{ editingPrompt ? 'Сохранить' : 'Создать' }}
              </button>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- Модальное окно истории изменений -->
      <Teleport to="body">
        <div v-if="showHistoryModal" class="modal-overlay" @click.self="showHistoryModal = false">
          <div class="modal-content">
            <div class="modal-header">
              <h3>История изменений: {{ selectedPrompt?.name }}</h3>
              <button class="close-btn" @click="showHistoryModal = false">×</button>
            </div>

            <div class="modal-body">
              <div v-if="history.loading" class="mini-loading">
                <div class="spinner-small"></div>
                <span>Загрузка истории...</span>
              </div>

              <div v-else-if="history.error" class="mini-error">
                Не удалось загрузить историю
              </div>

              <div v-else-if="history.items.length" class="history-list">
                <div 
                  v-for="item in history.items" 
                  :key="item.id"
                  class="history-item"
                >
                  <div class="history-header">
                    <span class="history-version">v{{ item.version }}</span>
                    <span class="history-date">{{ formatFullDate(item.changed_at) }}</span>
                  </div>
                  
                  <div class="history-changes">
                    <div class="change">
                      <span class="change-label">System:</span>
                      <pre class="change-value">{{ truncate(item.system_prompt, 100) }}</pre>
                    </div>
                    <div class="change">
                      <span class="change-label">User:</span>
                      <pre class="change-value">{{ truncate(item.user_prompt_template, 100) }}</pre>
                    </div>
                  </div>

                  <div v-if="item.change_comment" class="history-comment">
                    💬 {{ item.change_comment }}
                  </div>
                </div>
              </div>

              <div v-else class="empty-history">
                Нет записей об изменениях
              </div>
            </div>

            <div class="modal-footer">
              <button class="btn btn-secondary" @click="showHistoryModal = false">
                Закрыть
              </button>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- Модальное окно тестирования промпта -->
      <Teleport to="body">
        <div v-if="showTestModal" class="modal-overlay" @click.self="showTestModal = false">
          <div class="modal-content">
            <div class="modal-header">
              <h3>Тестирование промпта: {{ selectedTestPrompt?.name }}</h3>
              <button class="close-btn" @click="showTestModal = false">×</button>
            </div>

            <div class="modal-body">
              <div class="test-form">
                <div class="form-group">
                  <label class="form-label">Тестовый текст резюме</label>
                  <textarea
                    v-model="testData.cvText"
                    class="textarea"
                    rows="6"
                    placeholder="Вставьте тестовое резюме..."
                  ></textarea>
                </div>

                <button 
                  class="btn btn-primary" 
                  @click="runTest"
                  :disabled="testLoading"
                >
                  <span v-if="testLoading" class="spinner-small"></span>
                  <span>{{ testLoading ? 'Тестирование...' : 'Запустить тест' }}</span>
                </button>

                <div v-if="testResult" class="test-result">
                  <h4>Результат:</h4>
                  <pre>{{ JSON.stringify(testResult, null, 2) }}</pre>
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <button class="btn btn-secondary" @click="showTestModal = false">
                Закрыть
              </button>
            </div>
          </div>
        </div>
      </Teleport>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'

const authStore = useAuthStore()

// Проверка прав администратора
if (!authStore.isAdmin) {
  // Редирект на дашборд, но лучше сделать это в роутере
  // Здесь просто показываем сообщение
  console.warn('Доступ запрещён: требуется роль администратора')
}

// Состояние
const loading = ref(true)
const error = ref(null)
const prompts = ref([])

// Фильтры
const filters = reactive({
  search: '',
  showInactive: false
})

// Модальные окна
const showPromptModal = ref(false)
const showHistoryModal = ref(false)
const showTestModal = ref(false)
const editingPrompt = ref(null)
const selectedPrompt = ref(null)
const testingPrompt = ref(null)

// Форма промпта
const promptForm = reactive({
  name: '',
  description: '',
  system_prompt: '',
  user_prompt_template: '',
  response_format: {},
  parameters: {
    temperature: 0.3,
    max_tokens: 1500,
    top_p: 0.9
  },
  is_active: true,
  is_default: false
})

// JSON редактор
const responseFormatJson = ref('{}')
const responseFormatError = ref('')

// История
const history = reactive({
  loading: false,
  error: false,
  items: []
})

// Тестирование
const testData = reactive({
  cvText: ''
})
const testLoading = ref(false)
const testResult = ref(null)

// Debounced поиск
let searchTimeout
const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    // Фильтрация происходит на клиенте
  }, 300)
}

// Computed
const filteredPrompts = computed(() => {
  return prompts.value.filter(p => {
    // Поиск по названию
    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      if (!p.name.toLowerCase().includes(searchLower)) {
        return false
      }
    }
    
    // Фильтр неактивных
    if (!filters.showInactive && !p.is_active) {
      return false
    }
    
    return true
  })
})

const isPromptFormValid = computed(() => {
  return promptForm.name && 
         promptForm.system_prompt && 
         promptForm.user_prompt_template
})

// Загрузка промптов
const loadPrompts = async () => {
  loading.value = true
  error.value = null
  
  try {
    const response = await api.get('/prompts/')
    prompts.value = response.data
  } catch (err) {
    console.error('Ошибка загрузки промптов:', err)
    error.value = 'Не удалось загрузить промпты'
  } finally {
    loading.value = false
  }
}

// Работа с модалками
const openPromptModal = (prompt = null) => {
  editingPrompt.value = prompt
  
  if (prompt) {
    // Режим редактирования
    Object.assign(promptForm, {
      name: prompt.name,
      description: prompt.description || '',
      system_prompt: prompt.system_prompt,
      user_prompt_template: prompt.user_prompt_template,
      parameters: prompt.parameters || {
        temperature: 0.3,
        max_tokens: 1500,
        top_p: 0.9
      },
      is_active: prompt.is_active,
      is_default: prompt.is_default
    })
    responseFormatJson.value = JSON.stringify(prompt.response_format || {}, null, 2)
  } else {
    // Режим создания
    Object.assign(promptForm, {
      name: '',
      description: '',
      system_prompt: '',
      user_prompt_template: '',
      parameters: {
        temperature: 0.3,
        max_tokens: 1500,
        top_p: 0.9
      },
      is_active: true,
      is_default: false
    })
    responseFormatJson.value = '{}'
  }
  
  responseFormatError.value = ''
  showPromptModal.value = true
}

const closePromptModal = () => {
  showPromptModal.value = false
  editingPrompt.value = null
}

// Сохранение промпта
const savePrompt = async () => {
  if (!isPromptFormValid.value) return
  
  // Парсим JSON
  try {
    promptForm.response_format = JSON.parse(responseFormatJson.value)
    responseFormatError.value = ''
  } catch (err) {
    responseFormatError.value = 'Неверный формат JSON'
    return
  }
  
  try {
    if (editingPrompt.value) {
      // Обновление
      await api.put(`/prompts/${editingPrompt.value.id}`, promptForm)
    } else {
      // Создание
      await api.post('/prompts/', promptForm)
    }
    
    await loadPrompts()
    closePromptModal()
    
  } catch (err) {
    console.error('Ошибка сохранения промпта:', err)
    alert('Не удалось сохранить промпт')
  }
}

// Переключение статуса
const togglePromptStatus = async (prompt) => {
  try {
    await api.put(`/prompts/${prompt.id}`, {
      is_active: !prompt.is_active
    })
    
    await loadPrompts()
    
  } catch (err) {
    console.error('Ошибка изменения статуса:', err)
    alert('Не удалось изменить статус')
  }
}

// История изменений
const viewHistory = async (prompt) => {
  selectedPrompt.value = prompt
  showHistoryModal.value = true
  
  history.loading = true
  history.error = false
  
  try {
    const response = await api.get(`/prompts/${prompt.id}/history`)
    history.items = response.data
  } catch (err) {
    console.error('Ошибка загрузки истории:', err)
    history.error = true
  } finally {
    history.loading = false
  }
}

// Тестирование
const selectedTestPrompt = ref(null)  // переменная для хранения
const testPrompt = (prompt) => {      // функция
    selectedTestPrompt.value = prompt
    testData.cvText = ''
    testResult.value = null
    showTestModal.value = true
}

const runTest = async () => {
  if (!testData.cvText.trim()) {
    alert('Введите текст резюме для тестирования')
    return
  }
  
  testLoading.value = true
  testResult.value = null
  
  try {
    // Используем реальный эндпоинт анализа с указанием промпта
    const response = await api.post('/analyze/', {
      vacancy_id: 1, // Тестовая вакансия (нужно создать или использовать существующую)
      cv_text: testData.cvText,
      prompt_name: testingPrompt.value.name
    })
    
    testResult.value = response.data
    
  } catch (err) {
    console.error('Ошибка тестирования:', err)
    alert('Ошибка при тестировании промпта')
  } finally {
    testLoading.value = false
  }
}

// Форматирование
const formatDate = (dateString) => {
  if (!dateString) return ''
  return format(new Date(dateString), 'dd MMM yyyy', { locale: ru })
}

const formatFullDate = (dateString) => {
  if (!dateString) return ''
  return format(new Date(dateString), 'dd.MM.yyyy HH:mm', { locale: ru })
}

const truncate = (text, length) => {
  if (!text) return ''
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}

// Монтирование
onMounted(() => {
  loadPrompts()
})
</script>

<style scoped>
.admin-view {
  padding: var(--spacing) 0;
  min-height: calc(100vh - 140px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing);
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.page-title {
  font-size: 32px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.admin-badge {
  font-size: 14px;
  background: #8b5cf6;
  color: white;
  padding: 4px 12px;
  border-radius: var(--border-radius-pill);
  font-weight: 500;
}

/* Фильтры */
.filters-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing);
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.search-box {
  flex: 1;
  min-width: 250px;
}

.filter-checkbox {
  display: flex;
  align-items: center;
  gap: var(--spacing-xxs);
  cursor: pointer;
  font-size: 14px;
  color: var(--color-text);
}

/* Сетка промптов */
.prompts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: var(--spacing);
}

.prompt-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  transition: var(--transition);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.prompt-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px var(--color-shadow);
}

.prompt-card.inactive {
  opacity: 0.7;
  background: var(--color-surface-darker);
}

.prompt-card.default {
  border-left: 6px solid #fbbf24;
}

.prompt-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-xs);
}

.prompt-title {
  flex: 1;
}

.prompt-title h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 var(--spacing-xxs) 0;
}

.prompt-badges {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--border-radius-pill);
  font-size: 11px;
  font-weight: 500;
}

.badge.default {
  background: #fbbf24;
  color: #1e293b;
}

.badge.inactive {
  background: var(--color-border);
  color: var(--color-text-muted);
}

.badge.version {
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.prompt-actions {
  display: flex;
  gap: 4px;
}

.icon-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: var(--color-surface-darker);
  cursor: pointer;
  transition: var(--transition);
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-btn:hover {
  transform: translateY(-2px);
}

.icon-btn:nth-child(1):hover {
  background: #c3e0f2;
}

.icon-btn:nth-child(2):hover {
  background: #fef3c7;
}

.icon-btn:nth-child(3):hover {
  background: #dcfce7;
}

.icon-btn:nth-child(4):hover {
  background: #fee2e2;
}

.prompt-description {
  font-size: 13px;
  color: var(--color-text-light);
  margin-bottom: var(--spacing-xs);
}

.prompt-preview {
  background: var(--color-surface-darker);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing-xs);
}

.preview-label {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-bottom: 2px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.preview-text {
  margin: 0;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  color: var(--color-text);
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.5;
}

.prompt-footer {
  display: flex;
  justify-content: space-between;
  margin-top: var(--spacing-xs);
  padding-top: var(--spacing-xs);
  border-top: 1px solid var(--color-border);
  font-size: 11px;
  color: var(--color-text-muted);
}

/* Модальное окно */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  max-width: 800px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  animation: slideUp 0.3s ease;
}

.modal-content.modal-lg {
  max-width: 1000px;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  background: var(--color-surface);
  z-index: 1;
}

.modal-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: var(--color-surface-darker);
  font-size: 20px;
  cursor: pointer;
  transition: var(--transition);
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: var(--color-primary-soft);
  transform: rotate(90deg);
}

.modal-body {
  padding: var(--spacing);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-xs);
  padding: var(--spacing);
  border-top: 1px solid var(--color-border);
  position: sticky;
  bottom: 0;
  background: var(--color-surface);
}

/* Форма промпта */
.prompt-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xxs);
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.form-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-light);
  margin-left: 4px;
}

.textarea {
  width: 100%;
  padding: 12px;
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  font-size: 14px;
  font-family: inherit;
  background: var(--color-surface-lighter);
  color: var(--color-text);
  transition: var(--transition);
  resize: vertical;
}

.textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-soft);
}

.textarea.json-editor {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
}

.template-variables {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-muted);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}

.variables-label {
  margin-right: 4px;
}

.variable {
  background: var(--color-surface-darker);
  padding: 2px 6px;
  border-radius: 4px;
  color: var(--color-primary);
  font-family: monospace;
}

.checkbox-group {
  flex-direction: row;
  align-items: center;
  gap: var(--spacing-xxs);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-xxs);
  cursor: pointer;
  font-size: 14px;
  color: var(--color-text);
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--color-primary);
}

.error-text {
  font-size: 12px;
  color: #ef4444;
  margin-top: 2px;
}

/* История изменений */
.history-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing);
}

.history-item {
  background: var(--color-surface-darker);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xs);
  padding-bottom: var(--spacing-xs);
  border-bottom: 1px solid var(--color-border);
}

.history-version {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-primary);
}

.history-date {
  font-size: 12px;
  color: var(--color-text-muted);
}

.history-changes {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-xs);
}

.change {
  display: flex;
  gap: var(--spacing-xs);
}

.change-label {
  min-width: 60px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.change-value {
  flex: 1;
  margin: 0;
  font-family: monospace;
  font-size: 11px;
  color: var(--color-text);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.history-comment {
  font-size: 12px;
  color: var(--color-primary);
  padding-top: var(--spacing-xs);
  border-top: 1px dashed var(--color-border);
}

.empty-history {
  text-align: center;
  padding: var(--spacing);
  color: var(--color-text-muted);
  font-style: italic;
}

/* Тестирование */
.test-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing);
}

.test-result {
  background: var(--color-surface-darker);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing);
  margin-top: var(--spacing);
}

.test-result h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing-xs);
}

.test-result pre {
  margin: 0;
  font-family: monospace;
  font-size: 12px;
  color: var(--color-text);
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Загрузка и ошибки */
.loading-state,
.error-state {
  text-align: center;
  padding: calc(var(--spacing) * 2);
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

.spinner-small {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid var(--color-border);
  border-top: 2px solid var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: var(--spacing-xxs);
  vertical-align: middle;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.mini-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xxs);
  padding: var(--spacing);
  color: var(--color-text-muted);
}

.mini-error {
  text-align: center;
  padding: var(--spacing);
  color: var(--color-error-text);
  background: var(--color-error);
  border-radius: var(--border-radius-sm);
}

.error-icon {
  font-size: 48px;
  margin-bottom: var(--spacing-sm);
  display: block;
}

.error-state p {
  color: var(--color-error-text);
  margin-bottom: var(--spacing);
}

/* Адаптивность */
@media (max-width: 768px) {
  .prompts-grid {
    grid-template-columns: 1fr;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .page-header .btn {
    width: 100%;
  }
  
  .filters-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .modal-content {
    width: 95%;
  }
  
  .prompt-header {
    flex-direction: column;
  }
  
  .prompt-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
