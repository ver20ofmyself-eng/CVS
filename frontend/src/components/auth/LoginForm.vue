<template>
  <div class="login-form">
    <h2 class="form-title">Вход в систему</h2>
    
    <form @submit.prevent="handleSubmit" class="form">
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
            placeholder="••••••••"
            required
            :disabled="loading"
            autocomplete="current-password"
          />
          <button
            type="button"
            class="password-toggle"
            @click="showPassword = !showPassword"
            :aria-label="showPassword ? 'Скрыть пароль' : 'Показать пароль'"
          >
            <span v-if="showPassword">👁️</span>
            <span v-else>👁️‍🗨️</span>
          </button>
        </div>
      </div>

      <!-- Запомнить меня -->
      <div class="form-group checkbox-group">
        <label class="checkbox-label">
          <input
            v-model="form.remember"
            type="checkbox"
            :disabled="loading"
          />
          <span>Запомнить меня</span>
        </label>
      </div>

      <!-- Ошибка -->
      <div v-if="error" class="error-message">
        <span class="error-icon">⚠️</span>
        {{ error }}
      </div>

      <!-- Кнопка входа -->
      <button
        type="submit"
        class="btn btn-primary submit-btn"
        :disabled="loading || !isFormValid"
      >
        <span v-if="loading" class="spinner"></span>
        <span v-else>Войти</span>
      </button>

      <!-- Ссылка на регистрацию -->
      <p class="form-footer">
        Нет аккаунта?
        <router-link to="/register" class="link">Зарегистрироваться</router-link>
      </p>

      <!-- Демо-данные (для разработки) -->
      <div class="demo-info">
        <p class="demo-title">🔐 Демо-доступ:</p>
        <p class="demo-item">Админ: admin@example.com / admin123</p>
        <p class="demo-item">Пользователь: user@example.com / user123</p>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// Состояние формы
const form = reactive({
  email: '',
  password: '',
  remember: false
})

const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

// Валидация
const isFormValid = computed(() => {
  return form.email && form.password && form.password.length >= 6
})

// Обработка отправки
const handleSubmit = async () => {
  if (!isFormValid.value) return

  loading.value = true
  error.value = ''

  try {
    const success = await authStore.login(form.email, form.password)

    if (success) {
      // Если есть redirect, переходим туда, иначе на дашборд
      const redirectPath = route.query.redirect || '/dashboard'
      router.push(redirectPath)
    } else {
      error.value = authStore.error || 'Ошибка входа. Проверьте email и пароль.'
    }
  } catch (err) {
    error.value = 'Произошла ошибка. Попробуйте позже.'
    console.error('Login error:', err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-form {
  max-width: 420px;
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

.checkbox-group {
  flex-direction: row;
  align-items: center;
  gap: var(--spacing-xs);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-xxs);
  cursor: pointer;
  font-size: 14px;
  color: var(--color-text-light);
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--color-primary);
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

.link {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
  margin-left: 4px;
  transition: var(--transition);
}

.link:hover {
  color: var(--color-primary-dark);
  text-decoration: underline;
}

.demo-info {
  margin-top: var(--spacing);
  padding: var(--spacing-xs);
  background: var(--color-surface-darker);
  border-radius: var(--border-radius-sm);
  border: 1px dashed var(--color-border-strong);
  font-size: 13px;
}

.demo-title {
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 4px;
}

.demo-item {
  color: var(--color-text-muted);
  margin: 2px 0;
  font-family: monospace;
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
  .login-form {
    margin: var(--spacing-sm);
    padding: var(--spacing-sm);
  }
}
</style>
