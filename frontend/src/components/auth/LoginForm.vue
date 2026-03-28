<template>
  <div class="auth-page">
    <div class="auth-card">
      <!-- Заголовок -->
      <div class="auth-header">
        <span class="auth-logo">🔍</span>
        <h1 class="auth-title">CVS Analyzer</h1>
        <p class="auth-subtitle">Вход в систему</p>
      </div>

      <!-- Форма -->
      <form @submit.prevent="handleSubmit" class="auth-form" novalidate>
        <div class="form-group">
          <label for="email" class="form-label">Email</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            class="input"
            :class="{ error: v.email }"
            placeholder="your@email.com"
            autocomplete="email"
            :disabled="loading"
            @blur="validateEmail"
          />
          <span v-if="v.email" class="field-error">{{ v.email }}</span>
        </div>

        <div class="form-group">
          <label for="password" class="form-label">Пароль</label>
          <div class="input-wrap">
            <input
              id="password"
              v-model="form.password"
              :type="showPwd ? 'text' : 'password'"
              class="input"
              placeholder="••••••••"
              autocomplete="current-password"
              :disabled="loading"
            />
            <button type="button" class="pwd-toggle" @click="showPwd = !showPwd" :title="showPwd ? 'Скрыть' : 'Показать'">
              {{ showPwd ? '🙈' : '👁️' }}
            </button>
          </div>
        </div>

        <div v-if="error" class="alert alert-error">⚠️ {{ error }}</div>

        <button type="submit" class="btn btn-primary submit-btn" :disabled="loading || !canSubmit">
          <span v-if="loading" class="spinner spinner-sm"></span>
          <span v-else>Войти</span>
        </button>

        <p class="form-footer">
          Нет аккаунта?
          <router-link to="/register" class="link">Зарегистрироваться</router-link>
        </p>

        <!-- Демо блок (только в режиме разработки) -->
        <div v-if="isDev" class="demo-block">
          <p class="demo-label">🔐 Демо-данные</p>
          <button type="button" class="demo-btn" @click="fillAdmin">Войти как Админ</button>
          <button type="button" class="demo-btn" @click="fillUser">Войти как Пользователь</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router   = useRouter()
const route    = useRoute()
const authStore = useAuthStore()

const form    = reactive({ email: '', password: '' })
const v       = reactive({ email: '' })
const loading = ref(false)
const error   = ref('')
const showPwd = ref(false)
const isDev   = import.meta.env.DEV

const canSubmit = computed(() => form.email && form.password.length >= 4)

function validateEmail() {
  v.email = form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)
    ? 'Введите корректный email' : ''
}

async function handleSubmit() {
  validateEmail()
  if (v.email || !canSubmit.value) return

  loading.value = true
  error.value   = ''

  const ok = await authStore.login(form.email, form.password)
  loading.value = false

  if (ok) {
    const redirect = route.query.redirect || '/vacancies'
    router.push(redirect)
  } else {
    error.value = authStore.error || 'Неверный email или пароль'
  }
}

function fillAdmin() { form.email = 'admin@example.com'; form.password = 'admin123' }
function fillUser()  { form.email = 'user@example.com';  form.password = 'user123' }
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing);
  background: var(--color-bg);
}

.auth-card {
  width: 100%;
  max-width: 420px;
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: 36px;
  box-shadow: 0 16px 60px var(--color-shadow-strong);
  border: 1px solid var(--color-border);
  animation: slideUp 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(24px) scale(0.97); }
  to   { opacity: 1; transform: none; }
}

.auth-header {
  text-align: center;
  margin-bottom: 28px;
}

.auth-logo { font-size: 40px; display: block; margin-bottom: 8px; }

.auth-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 4px;
}

.auth-subtitle {
  font-size: 15px;
  color: var(--color-text-muted);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-light);
  padding-left: 4px;
}

.input-wrap { position: relative; }
.input-wrap .input { padding-right: 44px; }

.pwd-toggle {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  padding: 2px;
  opacity: 0.6;
  transition: opacity 0.2s;
}
.pwd-toggle:hover { opacity: 1; }

.field-error {
  font-size: 12px;
  color: #ef4444;
  padding-left: 4px;
}

.alert {
  padding: 11px 14px;
  border-radius: var(--border-radius-sm);
  font-size: 14px;
}

.alert-error {
  background: var(--color-error);
  color: var(--color-error-text);
  border: 1px solid var(--color-error-border);
}

.submit-btn {
  width: 100%;
  padding: 13px;
  font-size: 15px;
  margin-top: 4px;
}

.form-footer {
  text-align: center;
  font-size: 14px;
  color: var(--color-text-muted);
}

.link {
  color: var(--color-primary);
  font-weight: 600;
  text-decoration: none;
  margin-left: 4px;
}
.link:hover { text-decoration: underline; }

.demo-block {
  border-top: 1px dashed var(--color-border);
  padding-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.demo-label {
  font-size: 12px;
  color: var(--color-text-muted);
  text-align: center;
}

.demo-btn {
  padding: 7px;
  background: var(--color-surface-darker);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  font-size: 13px;
  cursor: pointer;
  color: var(--color-text-light);
  transition: var(--transition);
  font-family: inherit;
}
.demo-btn:hover { border-color: var(--color-primary); color: var(--color-primary); }
</style>
