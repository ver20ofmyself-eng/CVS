<template>
  <div class="register-form">
    <h2 class="form-title">Регистрация</h2>
    
    <form @submit.prevent="handleSubmit" class="form">
      <!-- Имя (опционально) -->
      <div class="form-group">
        <label for="fullName" class="form-label">Имя (опционально)</label>
        <input
          id="fullName"
          v-model="form.fullName"
          type="text"
          class="input"
          placeholder="Как к вам обращаться?"
          :disabled="loading"
        />
      </div>

      <!-- Email -->
      <div class="form-group">
        <label for="email" class="form-label">Email</label>
        <input
          id="email"
          v-model="form.email"
          type="email"
          class="input"
          placeholder="your@email.com"
          required
          :disabled="loading"
          autocomplete="email"
        />
      </div>

      <!-- Пароль -->
      <div class="form-group">
        <label for="password" class="form-label">Пароль</label>
        <div class="password-input-wrapper">
          <input
            id="password"
            v-model="form.password"
            :type="showPassword ? 'text' : 'password'"
            class="input"
            placeholder="Минимум 6 символов"
            required
            :disabled="loading"
            autocomplete="new-password"
          />
          <button
            type="button"
            class="password-toggle"
            @click="showPassword = !showPassword"
          >
            <span v-if="showPassword">👁️</span>
            <span v-else>👁️‍🗨️</span>
          </button>
        </div>
        <div class="password-strength" v-if="form.password">
          <div class="strength-bar" :class="passwordStrengthClass"></div>
          <span class="strength-text">{{ passwordStrengthText }}</span>
        </div>
      </div>

      <!-- Подтверждение пароля -->
      <div class="form-group">
        <label for="confirmPassword" class="form-label">Подтверждение пароля</label>
        <input
          id="confirmPassword"
          v-model="form.confirmPassword"
          type="password"
          class="input"
          placeholder="Введите пароль ещё раз"
          required
          :disabled="loading"
          autocomplete="new-password"
        />
        <div v-if="form.password && form.confirmPassword" class="password-match">
          <span v-if="passwordsMatch" class="match-success">✅ Пароли совпадают</span>
          <span v-else class="match-error">❌ Пароли не совпадают</span>
        </div>
      </div>

      <!-- Согласие с условиями -->
      <div class="form-group checkbox-group">
        <label class="checkbox-label">
          <input
            v-model="form.agree"
            type="checkbox"
            required
            :disabled="loading"
          />
          <span>
            Я принимаю
            <a href="#" class="link">условия использования</a>
            и
            <a href="#" class="link">политику конфиденциальности</a>
          </span>
        </label>
      </div>

      <!-- Ошибка -->
      <div v-if="error" class="error-message">
        <span class="error-icon">⚠️</span>
        {{ error }}
      </div>

      <!-- Кнопка регистрации -->
      <button
        type="submit"
        class="btn btn-primary submit-btn"
        :disabled="loading || !isFormValid"
      >
        <span v-if="loading" class="spinner"></span>
        <span v-else>Зарегистрироваться</span>
      </button>

      <!-- Ссылка на вход -->
      <p class="form-footer">
        Уже есть аккаунт?
        <router-link to="/login" class="link">Войти</router-link>
      </p>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// Состояние формы
const form = reactive({
  fullName: '',
  email: '',
  password: '',
  confirmPassword: '',
  agree: false
})

const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

// Проверка совпадения паролей
const passwordsMatch = computed(() => {
  return form.password && form.password === form.confirmPassword
})

// Валидация формы
const isFormValid = computed(() => {
  return (
    form.email &&
    form.password &&
    form.password.length >= 6 &&
    passwordsMatch.value &&
    form.agree
  )
})

// Оценка сложности пароля
const passwordStrength = computed(() => {
  const pwd = form.password
  if (!pwd) return 0
  
  let score = 0
  if (pwd.length >= 8) score += 1
  if (/[a-z]/.test(pwd)) score += 1
  if (/[A-Z]/.test(pwd)) score += 1
  if (/[0-9]/.test(pwd)) score += 1
  if (/[^a-zA-Z0-9]/.test(pwd)) score += 1
  
  return score
})

const passwordStrengthClass = computed(() => {
  const score = passwordStrength.value
  if (score <= 2) return 'strength-weak'
  if (score <= 4) return 'strength-medium'
  return 'strength-strong'
})

const passwordStrengthText = computed(() => {
  const score = passwordStrength.value
  if (score <= 2) return 'Слабый'
  if (score <= 4) return 'Средний'
  return 'Сильный'
})

// Обработка отправки
const handleSubmit = async () => {
  if (!isFormValid.value) return

  loading.value = true
  error.value = ''

  try {
    const success = await authStore.register({
      email: form.email,
      password: form.password,
      full_name: form.fullName || undefined
    })

    if (success) {
      router.push('/dashboard')
    } else {
      error.value = authStore.error || 'Ошибка регистрации. Возможно, email уже занят.'
    }
  } catch (err) {
    error.value = 'Произошла ошибка. Попробуйте позже.'
    console.error('Register error:', err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-form {
  max-width: 480px;
  margin: 0 auto;
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  box-shadow: 0 8px 30px var(--color-shadow);
  border: 1px solid var(--color-border);
}

.form-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing);
  text-align: center;
}

.form {
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
  font-weight: 600;
  color: var(--color-text);
  font-size: 14px;
  margin-left: 4px;
}

.password-input-wrapper {
  position: relative;
}

.password-toggle {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  font-size: 20px;
  padding: 4px;
  color: var(--color-text-muted);
  transition: var(--transition);
}

.password-toggle:hover {
  color: var(--color-primary);
}

.password-strength {
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: var(--spacing-xxs);
}

.strength-bar {
  flex: 1;
  height: 4px;
  background: var(--color-border);
  border-radius: 2px;
  transition: var(--transition);
}

.strength-bar.strength-weak {
  background: var(--color-warning-border);
  width: 33%;
}

.strength-bar.strength-medium {
  background: #fbbf24;
  width: 66%;
}

.strength-bar.strength-strong {
  background: #10b981;
  width: 100%;
}

.strength-text {
  font-size: 12px;
  color: var(--color-text-muted);
  min-width: 50px;
}

.password-match {
  font-size: 13px;
  margin-top: 2px;
}

.match-success {
  color: #10b981;
}

.match-error {
  color: var(--color-error-text);
}

.checkbox-group {
  flex-direction: row;
  align-items: flex-start;
  gap: var(--spacing-xs);
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-xxs);
  cursor: pointer;
  font-size: 14px;
  color: var(--color-text-light);
  line-height: 1.4;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--color-primary);
  margin-top: 2px;
}

.link {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
  transition: var(--transition);
}

.link:hover {
  color: var(--color-primary-dark);
  text-decoration: underline;
}

.error-message {
  background: var(--color-error);
  border-left: 6px solid var(--color-error-border);
  color: var(--color-error-text);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: var(--spacing-xxs);
}

.error-icon {
  font-size: 16px;
}

.submit-btn {
  width: 100%;
  margin-top: var(--spacing-xs);
}

.form-footer {
  text-align: center;
  margin-top: var(--spacing-xs);
  font-size: 14px;
  color: var(--color-text-muted);
}

.spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 480px) {
  .register-form {
    margin: var(--spacing-sm);
    padding: var(--spacing-sm);
  }
}
</style>
