<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-header">
        <span class="auth-logo">🔍</span>
        <h1 class="auth-title">CVS Analyzer</h1>
        <p class="auth-subtitle">Создать аккаунт</p>
      </div>

      <form @submit.prevent="handleSubmit" class="auth-form" novalidate>
        <div class="form-group">
          <label for="fullName" class="form-label">Имя <span class="optional">(необязательно)</span></label>
          <input id="fullName" v-model="form.fullName" type="text" class="input" placeholder="Как к вам обращаться?" :disabled="loading" />
        </div>

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
              placeholder="Минимум 6 символов"
              autocomplete="new-password"
              :disabled="loading"
            />
            <button type="button" class="pwd-toggle" @click="showPwd = !showPwd">
              {{ showPwd ? '🙈' : '👁️' }}
            </button>
          </div>
          <div v-if="form.password" class="strength-bar-wrap">
            <div class="strength-bar" :class="`strength-${strength.level}`"></div>
            <span class="strength-label" :class="`text-${strength.level}`">{{ strength.text }}</span>
          </div>
        </div>

        <div class="form-group">
          <label for="confirm" class="form-label">Подтверждение пароля</label>
          <input
            id="confirm"
            v-model="form.confirm"
            type="password"
            class="input"
            :class="{ error: form.confirm && !pwdMatch }"
            placeholder="Повторите пароль"
            :disabled="loading"
          />
          <span v-if="form.confirm && !pwdMatch" class="field-error">Пароли не совпадают</span>
        </div>

        <div v-if="error" class="alert alert-error">⚠️ {{ error }}</div>

        <button type="submit" class="btn btn-primary submit-btn" :disabled="loading || !canSubmit">
          <span v-if="loading" class="spinner spinner-sm"></span>
          <span v-else>Создать аккаунт</span>
        </button>

        <p class="form-footer">
          Уже есть аккаунт?
          <router-link to="/login" class="link">Войти</router-link>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router    = useRouter()
const authStore = useAuthStore()

const form    = reactive({ fullName: '', email: '', password: '', confirm: '' })
const v       = reactive({ email: '' })
const loading = ref(false)
const error   = ref('')
const showPwd = ref(false)

const pwdMatch  = computed(() => form.password === form.confirm)
const canSubmit = computed(() => form.email && form.password.length >= 6 && pwdMatch.value)

const strength = computed(() => {
  const p = form.password
  let s = 0
  if (p.length >= 8) s++
  if (/[a-z]/.test(p)) s++
  if (/[A-Z]/.test(p)) s++
  if (/[0-9]/.test(p)) s++
  if (/[^a-zA-Z0-9]/.test(p)) s++
  if (s <= 2) return { level: 'weak', text: 'Слабый' }
  if (s <= 3) return { level: 'medium', text: 'Средний' }
  return { level: 'strong', text: 'Сильный' }
})

function validateEmail() {
  v.email = form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)
    ? 'Введите корректный email' : ''
}

async function handleSubmit() {
  validateEmail()
  if (v.email || !canSubmit.value) return

  loading.value = true
  error.value   = ''

  const ok = await authStore.register({
    email:     form.email,
    password:  form.password,
    full_name: form.fullName || undefined,
  })

  loading.value = false

  if (ok) router.push('/vacancies')
  else error.value = authStore.error || 'Ошибка регистрации'
}
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
  max-width: 440px;
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

.auth-header { text-align: center; margin-bottom: 28px; }
.auth-logo { font-size: 40px; display: block; margin-bottom: 8px; }
.auth-title { font-size: 26px; font-weight: 700; color: var(--color-text); margin-bottom: 4px; }
.auth-subtitle { font-size: 15px; color: var(--color-text-muted); }

.auth-form { display: flex; flex-direction: column; gap: 14px; }

.form-group { display: flex; flex-direction: column; gap: 5px; }
.form-label { font-size: 13px; font-weight: 600; color: var(--color-text-light); padding-left: 4px; }
.optional { font-weight: 400; color: var(--color-text-muted); }

.input-wrap { position: relative; }
.input-wrap .input { padding-right: 44px; }

.pwd-toggle {
  position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
  background: none; border: none; cursor: pointer; font-size: 18px;
  padding: 2px; opacity: 0.6; transition: opacity 0.2s;
}
.pwd-toggle:hover { opacity: 1; }

.field-error { font-size: 12px; color: #ef4444; padding-left: 4px; }

.strength-bar-wrap {
  display: flex; align-items: center; gap: 8px; margin-top: 4px;
}

.strength-bar {
  flex: 1; height: 4px; border-radius: 2px; transition: all 0.3s;
}
.strength-weak   { background: #ef4444; width: 33%; }
.strength-medium { background: #f59e0b; width: 66%; }
.strength-strong { background: #10b981; width: 100%; }

.strength-label { font-size: 12px; font-weight: 500; white-space: nowrap; }
.text-weak   { color: #ef4444; }
.text-medium { color: #f59e0b; }
.text-strong { color: #10b981; }

.alert { padding: 11px 14px; border-radius: var(--border-radius-sm); font-size: 14px; }
.alert-error { background: var(--color-error); color: var(--color-error-text); border: 1px solid var(--color-error-border); }

.submit-btn { width: 100%; padding: 13px; font-size: 15px; margin-top: 4px; }

.form-footer { text-align: center; font-size: 14px; color: var(--color-text-muted); }
.link { color: var(--color-primary); font-weight: 600; text-decoration: none; margin-left: 4px; }
.link:hover { text-decoration: underline; }
</style>
