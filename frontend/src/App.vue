<template>
  <div id="app">
    <NavBar v-if="showNavBar" />
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <ToastContainer />
    <ConfirmDialog ref="confirmDialog" />
  </div>
</template>

<script setup>
import { computed, ref, provide } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from './components/common/NavBar.vue'
import ToastContainer from './components/common/ToastContainer.vue'
import ConfirmDialog from './components/common/ConfirmDialog.vue'

const route = useRoute()
const confirmDialog = ref(null)

const showNavBar = computed(() => !['login', 'register'].includes(route.name))

// Предоставляем confirm dialog глобально дочерним компонентам
provide('confirm', (options) => confirmDialog.value?.open(options))
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');

*, *::before, *::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  /* ── Фоны ──────────────────────────────────────────────────────────────── */
  --color-bg:              #eae2d7;
  --color-surface:         #fffcf5;
  --color-surface-lighter: #ffffff;
  --color-surface-darker:  #f3eee3;

  /* ── Текст ─────────────────────────────────────────────────────────────── */
  --color-text:        #2c4a5e;
  --color-text-light:  #5a6e7c;
  --color-text-muted:  #8a9aa8;
  --color-text-inverse:#ffffff;

  /* ── Основной цвет ──────────────────────────────────────────────────────── */
  --color-primary:      #106ab7;
  --color-primary-dark: #0b5196;
  --color-primary-light:#3b82f6;
  --color-primary-soft: #deeef9;

  /* ── Статусы ────────────────────────────────────────────────────────────── */
  --color-success:        #ecfdf5;
  --color-success-text:   #065f46;
  --color-success-border: #a7f3d0;

  --color-warning:        #fffbeb;
  --color-warning-text:   #92400e;
  --color-warning-border: #fde68a;

  --color-error:        #fef2f2;
  --color-error-text:   #991b1b;
  --color-error-border: #fecaca;

  /* ── Границы и тени ─────────────────────────────────────────────────────── */
  --color-border:        rgba(18, 78, 115, 0.12);
  --color-border-strong: rgba(18, 78, 115, 0.22);
  --color-shadow:        rgba(18, 78, 115, 0.07);
  --color-shadow-strong: rgba(18, 78, 115, 0.14);

  /* ── Геометрия ──────────────────────────────────────────────────────────── */
  --border-radius:     22px;
  --border-radius-sm:  16px;
  --border-radius-lg:  32px;
  --border-radius-pill:9999px;

  /* ── Отступы ────────────────────────────────────────────────────────────── */
  --spacing:    24px;
  --spacing-sm: 16px;
  --spacing-xs: 12px;
  --spacing-xxs: 8px;

  /* ── Анимации ───────────────────────────────────────────────────────────── */
  --transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

html { scroll-behavior: smooth; }

body {
  font-family: 'Source Sans 3', system-ui, sans-serif;
  background: var(--color-bg);
  color: var(--color-text);
  line-height: 1.55;
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

.main-content {
  min-height: calc(100vh - 64px);
  padding: var(--spacing);
  max-width: 1200px;
  margin: 0 auto;
}

/* ── Анимации роутера ─────────────────────────────────────────────────────── */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* ── Базовые компоненты ─────────────────────────────────────────────────── */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-sm);
}

.card {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  box-shadow: 0 4px 20px var(--color-shadow);
  border: 1px solid var(--color-border);
  transition: var(--transition);
}

.card:hover {
  box-shadow: 0 8px 36px var(--color-shadow-strong);
}

/* ── Кнопки ─────────────────────────────────────────────────────────────── */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 11px 22px;
  border: none;
  border-radius: var(--border-radius-pill);
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: var(--transition);
  text-decoration: none;
  white-space: nowrap;
  user-select: none;
}

.btn-primary {
  background: var(--color-primary);
  color: #fff;
}
.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(16, 106, 183, 0.35);
}

.btn-secondary {
  background: transparent;
  border: 2px solid var(--color-border-strong);
  color: var(--color-text);
}
.btn-secondary:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
  transform: translateY(-1px);
}

.btn-text {
  background: none;
  color: var(--color-text-muted);
}
.btn-text:hover { color: var(--color-text); }

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

/* ── Поля ввода ─────────────────────────────────────────────────────────── */
.input, .textarea, .select {
  width: 100%;
  padding: 11px 15px;
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  font-size: 15px;
  font-family: inherit;
  transition: var(--transition);
  background: var(--color-surface-lighter);
  color: var(--color-text);
  outline: none;
}

.input:focus, .textarea:focus, .select:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-soft);
}

.input.error, .textarea.error { border-color: #ef4444; }
.input::placeholder, .textarea::placeholder { color: var(--color-text-muted); }

.textarea { resize: vertical; min-height: 100px; }
.select { cursor: pointer; }

/* ── Состояния загрузки ─────────────────────────────────────────────────── */
.spinner {
  width: 38px;
  height: 38px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  margin: 0 auto;
}

.spinner-sm {
  width: 20px;
  height: 20px;
  border-width: 2px;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* ── Утилиты ──────────────────────────────────────────────────────────────── */
.text-muted { color: var(--color-text-muted); }
.text-sm { font-size: 13px; }
.mt-1 { margin-top: var(--spacing-xxs); }
.mt-2 { margin-top: var(--spacing-xs); }
.mt-3 { margin-top: var(--spacing-sm); }
.mt-4 { margin-top: var(--spacing); }

/* ── Skeleton loading ──────────────────────────────────────────────────────── */
.skeleton {
  background: linear-gradient(90deg, var(--color-surface-darker) 25%, #e8e0d5 50%, var(--color-surface-darker) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: var(--border-radius-sm);
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Адаптивность ─────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .main-content { padding: var(--spacing-sm); }
  :root { --spacing: 20px; --border-radius: 18px; }
}
</style>
