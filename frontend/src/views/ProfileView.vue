<template>
  <div class="profile-view">
    <div class="container">
      <!-- Заголовок -->
      <h1 class="page-title">Профиль</h1>

      <!-- Состояние загрузки -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка профиля...</p>
      </div>

      <!-- Ошибка -->
      <div v-else-if="error" class="error-state">
        <span class="error-icon">❌</span>
        <p>{{ error }}</p>
        <button class="btn btn-primary" @click="loadData">Повторить</button>
      </div>

      <!-- Контент -->
      <template v-else>
        <!-- Сетка профиля -->
        <div class="profile-grid">
          <!-- Левая колонка - Информация о пользователе -->
          <div class="info-card">
            <h2 class="card-title">
              <span class="title-icon">👤</span>
              Личные данные
            </h2>

            <div class="user-info">
              <div class="info-row">
                <span class="info-label">Email:</span>
                <span class="info-value">{{ user.email }}</span>
              </div>
              
              <div class="info-row">
                <span class="info-label">Имя:</span>
                <span v-if="editing" class="info-edit">
                  <input
                    v-model="editForm.fullName"
                    type="text"
                    class="input"
                    placeholder="Введите имя"
                  />
                </span>
                <span v-else class="info-value">
                  {{ user.full_name || 'Не указано' }}
                </span>
              </div>

              <div class="info-row">
                <span class="info-label">Статус:</span>
                <span class="info-value">
                  <span class="role-badge" :class="{ 'role-admin': user.is_admin }">
                    {{ user.is_admin ? 'Администратор' : 'Пользователь' }}
                  </span>
                </span>
              </div>

              <div class="info-row">
                <span class="info-label">Дата регистрации:</span>
                <span class="info-value">{{ formatDate(user.created_at) }}</span>
              </div>

              <div class="info-row">
                <span class="info-label">Последний вход:</span>
                <span class="info-value">{{ formatDate(user.last_login) || '—' }}</span>
              </div>
            </div>

            <!-- Кнопки действий -->
            <div class="profile-actions">
              <button 
                v-if="!editing" 
                class="btn btn-secondary" 
                @click="startEditing"
              >
                ✏️ Редактировать
              </button>
              <template v-else>
                <button class="btn btn-primary" @click="saveProfile">
                  💾 Сохранить
                </button>
                <button class="btn btn-text" @click="cancelEditing">
                  Отмена
                </button>
              </template>
            </div>

            <!-- Смена пароля — аккордеон -->
            <div class="password-change">
              <div class="password-toggle-header" @click="showPasswordChange = !showPasswordChange">
                <h3 class="subsection-title">🔐 Смена пароля</h3>
                <span class="accordion-icon">{{ showPasswordChange ? '▼' : '▶' }}</span>
              </div>
              <div v-if="showPasswordChange" class="password-form-wrap">
              
              <div class="password-form">
                <div class="form-group">
                  <label class="form-label">Текущий пароль</label>
                  <input
                    v-model="passwordForm.current"
                    type="password"
                    class="input"
                    placeholder="••••••••"
                  />
                </div>

                <div class="form-group">
                  <label class="form-label">Новый пароль</label>
                  <input
                    v-model="passwordForm.new"
                    type="password"
                    class="input"
                    placeholder="Минимум 6 символов"
                  />
                  <div v-if="passwordForm.new" class="password-strength" :class="passwordStrengthClass">
                    {{ passwordStrengthText }}
                  </div>
                </div>

                <div class="form-group">
                  <label class="form-label">Подтверждение</label>
                  <input
                    v-model="passwordForm.confirm"
                    type="password"
                    class="input"
                    :class="{ 'error': !passwordsMatch && passwordForm.confirm }"
                  />
                  <div v-if="passwordForm.confirm && !passwordsMatch" class="error-text">
                    Пароли не совпадают
                  </div>
                </div>

                <button 
                  class="btn btn-secondary"
                  @click="changePassword"
                  :disabled="!canChangePassword"
                >
                  Обновить пароль
                </button>
              </div>
              </div>
            </div>
          </div>

          <!-- Правая колонка - Тариф -->
          <div class="tariff-card">
            <h2 class="card-title">
              <span class="title-icon">💎</span>
              Текущий тариф
            </h2>

            <div v-if="tariff.loading" class="mini-loading">
              <div class="spinner-small"></div>
              <span>Загрузка...</span>
            </div>

            <div v-else class="tariff-info">
              <!-- Индикатор остатка -->
              <div class="analyses-left">
                <div class="progress-circle" :style="progressStyle">
                  <span class="progress-value">{{ tariff.analyses_left }}</span>
                </div>
                <div class="analyses-text">
                  <span class="analyses-count">{{ tariff.analyses_left }}</span>
                  <span class="analyses-label">анализов осталось</span>
                </div>
              </div>

              <!-- Детали тарифа -->
              <div class="tariff-details">
                <div class="detail-row">
                  <span class="detail-label">Тариф:</span>
                  <span class="detail-value highlight">{{ tariff.tariff_name || 'Бесплатный' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Лимит:</span>
                  <span class="detail-value">{{ tariff.tariff_limit || 50 }} анализов</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Приобретён:</span>
                  <span class="detail-value">{{ formatDate(tariff.purchased_at) || '—' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Истекает:</span>
                  <span class="detail-value">{{ formatDate(tariff.expires_at) || 'Бессрочно' }}</span>
                </div>
              </div>

              <!-- Кнопка смены тарифа -->
              <button class="btn btn-primary btn-full" @click="showTariffSelector = true">
                📦 Сменить тариф
              </button>
            </div>
          </div>
        </div>

        <!-- История платежей -->
        <div class="payments-section">
          <h2 class="section-title">📋 История платежей</h2>

          <div v-if="payments.loading" class="mini-loading">
            <div class="spinner-small"></div>
            <span>Загрузка истории...</span>
          </div>

          <div v-else-if="payments.error" class="mini-error">
            Не удалось загрузить историю платежей
          </div>

          <div v-else-if="payments.items.length" class="payments-list">
            <table class="payments-table">
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Тариф</th>
                  <th>Сумма</th>
                  <th>Статус</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="payment in payments.items" :key="payment.id">
                  <td>{{ formatPaymentDate(payment.created_at) }}</td>
                  <td>{{ payment.tariff_name || '—' }}</td>
                  <td>{{ formatAmount(payment.amount, payment.currency) }}</td>
                  <td>
                    <span class="payment-status" :class="getPaymentStatusClass(payment.status)">
                      {{ payment.status }}
                    </span>
                  </td>
                  <td>
                    <button 
                      v-if="payment.receipt_url" 
                      class="receipt-btn"
                      @click="downloadReceipt(payment)"
                      title="Скачать чек"
                    >
                      📄
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-else class="empty-payments">
            <p>У вас пока нет платежей</p>
          </div>
        </div>

        <!-- Модалка выбора тарифа -->
        <Teleport to="body">
          <div v-if="showTariffSelector" class="modal-overlay" @click.self="showTariffSelector = false">
            <div class="modal-content">
              <div class="modal-header">
                <h3>Выберите тариф</h3>
                <button class="close-btn" @click="showTariffSelector = false">×</button>
              </div>

              <div class="modal-body">
                <div class="tariffs-grid">
                  <div 
                    v-for="t in availableTariffs" 
                    :key="t.id"
                    class="tariff-option"
                    :class="{ 
                      'selected': selectedTariff === t.id,
                      'current': t.id === currentTariffId 
                    }"
                    @click="selectedTariff = t.id"
                  >
                    <h4 class="tariff-name">{{ t.name }}</h4>
                    <div class="tariff-price">{{ formatAmount(t.price) }}</div>
                    <div class="tariff-limit">{{ t.analyses_limit }} анализов</div>
                    <div class="tariff-badge" v-if="t.id === currentTariffId">Текущий</div>
                  </div>
                </div>

                <div class="tariff-info-note">
                  <p>💡 Все тарифы действуют бессрочно</p>
                  <p>🔐 Оплата происходит через защищённый шлюз</p>
                </div>
              </div>

              <div class="modal-footer">
                <button class="btn btn-secondary" @click="showTariffSelector = false">
                  Отмена
                </button>
                <button 
                  class="btn btn-primary" 
                  @click="purchaseTariff"
                  :disabled="!selectedTariff || selectedTariff === currentTariffId"
                >
                  {{ selectedTariff === currentTariffId ? 'Текущий тариф' : 'Перейти к оплате' }}
                </button>
              </div>
            </div>
          </div>
        </Teleport>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'

const authStore = useAuthStore()

// Состояние
const loading = ref(true)
const error = ref(null)
const user = ref(null)
const editing = ref(false)
const showPasswordChange = ref(false)
const showTariffSelector = ref(false)
const selectedTariff = ref(null)
const availableTariffs = ref([])

// Форма редактирования
const editForm = reactive({
  fullName: ''
})

// Форма смены пароля
const passwordForm = reactive({
  current: '',
  new: '',
  confirm: ''
})

// Тариф
const tariff = reactive({
  loading: false,
  analyses_left: 0,
  tariff_name: null,
  tariff_limit: null,
  purchased_at: null,
  expires_at: null
})

// Платежи
const payments = reactive({
  loading: false,
  error: false,
  items: []
})

// Computed
const currentTariffId = computed(() => {
  // Нужно будет добавить, когда будет эндпоинт
  return null
})

const passwordsMatch = computed(() => {
  return passwordForm.new === passwordForm.confirm
})

const canChangePassword = computed(() => {
  return passwordForm.current && 
         passwordForm.new && 
         passwordForm.new.length >= 6 && 
         passwordsMatch.value
})

const passwordStrengthClass = computed(() => {
  const pwd = passwordForm.new
  if (!pwd) return ''
  
  let score = 0
  if (pwd.length >= 8) score++
  if (/[a-z]/.test(pwd)) score++
  if (/[A-Z]/.test(pwd)) score++
  if (/[0-9]/.test(pwd)) score++
  if (/[^a-zA-Z0-9]/.test(pwd)) score++
  
  if (score <= 2) return 'strength-weak'
  if (score <= 4) return 'strength-medium'
  return 'strength-strong'
})

const passwordStrengthText = computed(() => {
  const pwd = passwordForm.new
  if (!pwd) return ''
  if (pwd.length < 6) return 'Слишком короткий'
  
  let score = 0
  if (pwd.length >= 8) score++
  if (/[a-z]/.test(pwd)) score++
  if (/[A-Z]/.test(pwd)) score++
  if (/[0-9]/.test(pwd)) score++
  if (/[^a-zA-Z0-9]/.test(pwd)) score++
  
  if (score <= 2) return 'Слабый'
  if (score <= 4) return 'Средний'
  return 'Сильный'
})

const progressStyle = computed(() => {
  const limit = tariff.tariff_limit || 50
  const left = tariff.analyses_left || 0
  const percentage = (left / limit) * 100
  return {
    background: `conic-gradient(var(--color-primary) 0deg, var(--color-primary) ${percentage * 3.6}deg, var(--color-border) ${percentage * 3.6}deg)`
  }
})

// Загрузка данных
const loadData = async () => {
  loading.value = true
  error.value = null
  
  try {
    // Загружаем пользователя
    await authStore.fetchUser()
    user.value = authStore.user
    
    // Загружаем тариф
    await loadTariff()
    
    // Загружаем платежи
    await loadPayments()
    
    // Загружаем доступные тарифы
    await loadTariffs()
    
  } catch (err) {
    console.error('Ошибка загрузки профиля:', err)
    error.value = 'Не удалось загрузить профиль'
  } finally {
    loading.value = false
  }
}

const loadTariff = async () => {
  tariff.loading = true
  
  try {
    const response = await api.get('/tariffs/my')
    Object.assign(tariff, response.data)
  } catch (err) {
    console.error('Ошибка загрузки тарифа:', err)
  } finally {
    tariff.loading = false
  }
}

const loadPayments = async () => {
  payments.loading = true
  payments.error = false
  
  try {
    const response = await api.get('/payments/history')
    payments.items = response.data
  } catch (err) {
    console.error('Ошибка загрузки платежей:', err)
    payments.error = true
  } finally {
    payments.loading = false
  }
}

const loadTariffs = async () => {
  try {
    const response = await api.get('/tariffs/')
    availableTariffs.value = response.data
  } catch (err) {
    console.error('Ошибка загрузки тарифов:', err)
  }
}

// Редактирование профиля
const startEditing = () => {
  editForm.fullName = user.value.full_name || ''
  editing.value = true
}

const cancelEditing = () => {
  editing.value = false
  editForm.fullName = user.value.full_name || ''
}

const saveProfile = async () => {
  try {
    await api.put('/profile/', {
      full_name: editForm.fullName
    })
    
    user.value.full_name = editForm.fullName
    editing.value = false
    
  } catch (err) {
    console.error('Ошибка сохранения профиля:', err)
    alert('Не удалось сохранить изменения')
  }
}

// Смена пароля
const changePassword = async () => {
  if (!canChangePassword.value) return
  
  try {
    await api.post('/auth/change-password', {
      current_password: passwordForm.current,
      new_password: passwordForm.new
    })
    
    // Очищаем форму
    passwordForm.current = ''
    passwordForm.new = ''
    passwordForm.confirm = ''
    
    alert('Пароль успешно изменён')
    
  } catch (err) {
    console.error('Ошибка смены пароля:', err)
    alert('Не удалось сменить пароль. Проверьте текущий пароль.')
  }
}

// Покупка тарифа
const purchaseTariff = async () => {
  if (!selectedTariff.value) return
  
  try {
    // Здесь будет интеграция с платёжной системой
    // Пока просто имитируем
    alert('В демо-режиме покупка тарифов не доступна')
    showTariffSelector.value = false
    
  } catch (err) {
    console.error('Ошибка покупки:', err)
    alert('Не удалось совершить покупку')
  }
}

// Форматирование
const formatDate = (dateString) => {
  if (!dateString) return ''
  return format(new Date(dateString), 'dd MMMM yyyy', { locale: ru })
}

const formatPaymentDate = (dateString) => {
  if (!dateString) return ''
  return format(new Date(dateString), 'dd.MM.yyyy HH:mm', { locale: ru })
}

const formatAmount = (amount, currency = 'RUB') => {
  if (!amount) return '—'
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: currency
  }).format(amount)
}

const getPaymentStatusClass = (status) => {
  const statusMap = {
    'completed': 'status-success',
    'pending': 'status-pending',
    'failed': 'status-failed',
    'refunded': 'status-refunded'
  }
  return statusMap[status] || 'status-unknown'
}

const downloadReceipt = (payment) => {
  if (payment.receipt_url) {
    window.open(payment.receipt_url, '_blank')
  }
}

// Монтирование
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.profile-view {
  padding: var(--spacing) 0;
  min-height: calc(100vh - 140px);
}

.page-title {
  font-size: 32px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing);
}

/* Сетка */
.profile-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing);
  margin-bottom: var(--spacing);
}

.info-card,
.tariff-card {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  border: 1px solid var(--color-border);
  transition: var(--transition);
}

.info-card:hover,
.tariff-card:hover {
  box-shadow: 0 8px 30px var(--color-shadow);
}

.card-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing);
  display: flex;
  align-items: center;
  gap: var(--spacing-xxs);
}

.title-icon {
  font-size: 24px;
}

/* Информация о пользователе */
.user-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing);
}

.info-row {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
  padding-bottom: var(--spacing-xxs);
  border-bottom: 1px solid var(--color-border);
}

.info-label {
  min-width: 140px;
  font-size: 14px;
  color: var(--color-text-muted);
}

.info-value {
  font-size: 15px;
  color: var(--color-text);
  font-weight: 500;
}

.info-edit {
  flex: 1;
}

.role-badge {
  display: inline-block;
  padding: 4px 10px;
  background: var(--color-surface-darker);
  border-radius: var(--border-radius-pill);
  font-size: 13px;
  color: var(--color-text);
}

.role-admin {
  background: #8b5cf6;
  color: white;
}

.profile-actions {
  display: flex;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing);
}

/* Смена пароля */
.password-change {
  margin-top: var(--spacing);
  padding-top: var(--spacing);
  border-top: 2px solid var(--color-border);
}

.subsection-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing-sm);
}

.password-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xxs);
}

.form-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-light);
  margin-left: 4px;
}

.password-strength {
  font-size: 12px;
  margin-top: 2px;
  padding-left: 4px;
}

.strength-weak {
  color: #ef4444;
}

.strength-medium {
  color: #fbbf24;
}

.strength-strong {
  color: #10b981;
}

.error-text {
  font-size: 12px;
  color: #ef4444;
  margin-top: 2px;
}

/* Тариф */
.tariff-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing);
}

.analyses-left {
  display: flex;
  align-items: center;
  gap: var(--spacing);
  padding: var(--spacing-sm);
  background: var(--color-surface-darker);
  border-radius: var(--border-radius-sm);
}

.progress-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: conic-gradient(from 0deg, var(--color-primary) 0deg, var(--color-border) 0deg);
  position: relative;
  flex-shrink: 0;
}

.progress-circle::before {
  content: '';
  position: absolute;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--color-surface-darker);
}

.progress-value {
  position: relative;
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text);
  z-index: 1;
}

.analyses-text {
  flex: 1;
}

.analyses-count {
  display: block;
  font-size: 32px;
  font-weight: 700;
  color: var(--color-primary);
  line-height: 1.2;
}

.analyses-label {
  font-size: 13px;
  color: var(--color-text-muted);
}

.tariff-details {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm);
  background: var(--color-surface-darker);
  border-radius: var(--border-radius-sm);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  font-size: 14px;
  color: var(--color-text-muted);
}

.detail-value {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text);
}

.detail-value.highlight {
  color: var(--color-primary);
  font-weight: 600;
}

.btn-full {
  width: 100%;
}

/* История платежей */
.payments-section {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  border: 1px solid var(--color-border);
  margin-top: var(--spacing);
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing);
}

.payments-table {
  width: 100%;
  border-collapse: collapse;
}

.payments-table th {
  text-align: left;
  padding: var(--spacing-xs) var(--spacing-xxs);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-muted);
  border-bottom: 2px solid var(--color-border);
}

.payments-table td {
  padding: var(--spacing-xs) var(--spacing-xxs);
  font-size: 14px;
  color: var(--color-text);
  border-bottom: 1px solid var(--color-border);
}

.payment-status {
  display: inline-block;
  padding: 4px 8px;
  border-radius: var(--border-radius-pill);
  font-size: 12px;
  font-weight: 500;
}

.status-success {
  background: #10b981;
  color: white;
}

.status-pending {
  background: #fbbf24;
  color: #1e293b;
}

.status-failed {
  background: #ef4444;
  color: white;
}

.status-refunded {
  background: var(--color-surface-darker);
  color: var(--color-text-muted);
}

.receipt-btn {
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

.receipt-btn:hover {
  background: var(--color-primary-soft);
  transform: translateY(-2px);
}

.empty-payments {
  text-align: center;
  padding: var(--spacing);
  color: var(--color-text-muted);
  font-style: italic;
}

/* Модалка */
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

.tariffs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing);
  margin-bottom: var(--spacing);
}

.tariff-option {
  background: var(--color-surface-darker);
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  padding: var(--spacing);
  cursor: pointer;
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}

.tariff-option:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px var(--color-shadow);
  border-color: var(--color-primary);
}

.tariff-option.selected {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.tariff-option.current {
  opacity: 0.7;
  cursor: default;
}

.tariff-option.current:hover {
  transform: none;
  border-color: var(--color-border);
}

.tariff-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing-xs);
}

.tariff-price {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: 4px;
}

.tariff-limit {
  font-size: 14px;
  color: var(--color-text-muted);
}

.tariff-badge {
  position: absolute;
  top: 10px;
  right: -20px;
  background: var(--color-primary);
  color: white;
  padding: 4px 20px;
  font-size: 11px;
  font-weight: 600;
  transform: rotate(45deg);
  width: 80px;
  text-align: center;
}

.tariff-info-note {
  padding: var(--spacing-sm);
  background: var(--color-surface-darker);
  border-radius: var(--border-radius-sm);
  font-size: 14px;
  color: var(--color-text-muted);
}

.tariff-info-note p {
  margin: 4px 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-xs);
  padding: var(--spacing);
  border-top: 1px solid var(--color-border);
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
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border);
  border-top: 2px solid var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: var(--spacing-xxs);
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
  .profile-grid {
    grid-template-columns: 1fr;
  }
  
  .payments-table {
    display: block;
    overflow-x: auto;
  }
  
  .info-row {
    flex-direction: column;
    gap: 4px;
  }
  
  .info-label {
    min-width: auto;
  }
  
  .analyses-left {
    flex-direction: column;
    text-align: center;
  }
  
  .modal-content {
    width: 95%;
  }
  
  .tariffs-grid {
    grid-template-columns: 1fr;
  }
}

.password-toggle-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding: var(--spacing-xs) 0;
  user-select: none;
  transition: var(--transition);
}

.password-toggle-header:hover .subsection-title { color: var(--color-primary); }
.password-toggle-header:hover .accordion-icon { color: var(--color-primary); }

.password-toggle-header .accordion-icon {
  font-size: 13px;
  color: var(--color-text-muted);
  transition: var(--transition);
}

.password-form-wrap {
  animation: slideDown 0.25s ease;
  padding-top: var(--spacing-sm);
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to   { opacity: 1; transform: translateY(0); }
}

</style>