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
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from './components/common/NavBar.vue'

const route = useRoute()

// Показываем навбар на всех страницах, кроме страниц входа/регистрации
const showNavBar = computed(() => {
  return !['login', 'register'].includes(route.name)
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  /* Цветовая схема (кремовая, как в расширении) */
  --color-bg: #eae2d7;
  --color-surface: #fffcf5;
  --color-surface-lighter: #ffffff;
  --color-surface-darker: #f3eee3;
  
  /* Текст */
  --color-text: #2c4a5e;
  --color-text-light: #5a6e7c;
  --color-text-muted: #8a9aa8;
  --color-text-inverse: #ffffff;
  
  /* Акценты */
  --color-primary: #106ab7;
  --color-primary-dark: #0b5196;
  --color-primary-light: #3b82f6;
  --color-primary-soft: #c3e0f2;
  
  /* Статусы */
  --color-success: #c3e0f2;
  --color-success-text: #0a3142;
  --color-success-border: #0b5196;
  
  --color-warning: #fff5ef;
  --color-warning-text: #8b4a4a;
  --color-warning-border: #d14b4b;
  
  --color-error: #fff5ef;
  --color-error-text: #8b4a4a;
  --color-error-border: #d14b4b;
  
  /* Границы и тени */
  --color-border: rgba(18, 78, 115, 0.1);
  --color-border-strong: rgba(18, 78, 115, 0.2);
  --color-shadow: rgba(18, 78, 115, 0.08);
  --color-shadow-strong: rgba(18, 78, 115, 0.15);
  
  /* Скругления */
  --border-radius: 24px;
  --border-radius-sm: 20px;
  --border-radius-lg: 40px;
  --border-radius-pill: 9999px;
  
  /* Отступы */
  --spacing: 24px;
  --spacing-sm: 16px;
  --spacing-xs: 12px;
  --spacing-xxs: 8px;
  
  /* Анимации */
  --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

body {
  font-family: 'Source Sans 3', sans-serif;
  background: var(--color-bg);
  color: var(--color-text);
  line-height: 1.5;
  min-height: 100vh;
}

.main-content {
  min-height: calc(100vh - 80px);
  padding: var(--spacing);
  max-width: 1200px;
  margin: 0 auto;
}

/* Анимации */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Утилиты */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-sm);
}

.card {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  box-shadow: 0 8px 30px var(--color-shadow);
  border: 1px solid var(--color-border);
  transition: var(--transition);
}

.card:hover {
  box-shadow: 0 12px 40px var(--color-shadow-strong);
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: var(--border-radius-pill);
  font-size: 15px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: var(--transition);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xxs);
  text-decoration: none;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-dark);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px var(--color-shadow-strong);
}

.btn-secondary {
  background: transparent;
  border: 2px solid var(--color-border-strong);
  color: var(--color-text);
}

.btn-secondary:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
  transform: translateY(-2px);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.input, .textarea, .select {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  font-size: 15px;
  font-family: inherit;
  transition: var(--transition);
  background: var(--color-surface-lighter);
  color: var(--color-text);
}

.input:focus, .textarea:focus, .select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-soft);
}

.input::placeholder, .textarea::placeholder {
  color: var(--color-text-muted);
}

/* Адаптивность */
@media (max-width: 768px) {
  .main-content {
    padding: var(--spacing-sm);
  }
  
  :root {
    --spacing: 20px;
    --spacing-sm: 12px;
  }
}
</style>
