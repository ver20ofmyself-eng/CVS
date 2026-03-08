<template>
  <header class="navbar">
    <div class="container">
      <div class="navbar-content">
        <!-- Логотип -->
        <router-link to="/" class="logo">
          <span class="logo-icon">🔍</span>
          <span class="logo-text">CVS Analyzer</span>
        </router-link>

        <!-- Навигация (для авторизованных) -->
        <nav v-if="authStore.isAuthenticated" class="nav-links">
          <router-link to="/dashboard" class="nav-link" active-class="active">
            📊 Дашборд
          </router-link>
          <router-link to="/vacancies" class="nav-link" active-class="active">
            📋 Вакансии
          </router-link>
          <router-link to="/history" class="nav-link" active-class="active">
            📜 История
          </router-link>
          
          <!-- Админ-ссылка (только для админов) -->
          <router-link 
            v-if="authStore.isAdmin" 
            to="/admin" 
            class="nav-link admin-link" 
            active-class="active"
          >
            ⚙️ Админ
          </router-link>
        </nav>

        <!-- Правый блок -->
        <div class="navbar-right">
          <!-- Индикатор анализов (для авторизованных) -->
          <div v-if="authStore.isAuthenticated" class="analyses-indicator">
            <span class="analyses-icon">📊</span>
            <span class="analyses-count">{{ analysesLeft || '...' }}</span>
          </div>

          <!-- Меню пользователя -->
          <div v-if="authStore.isAuthenticated" class="user-menu">
            <button @click="showUserMenu = !showUserMenu" class="user-button">
              <span class="user-avatar">👤</span>
              <span class="user-name">{{ authStore.userName }}</span>
              <span class="chevron">▼</span>
            </button>
            
            <div v-if="showUserMenu" class="user-dropdown" v-click-outside="closeUserMenu">
              <router-link to="/profile" class="dropdown-item" @click="closeUserMenu">
                👤 Профиль
              </router-link>
              <router-link to="/profile" class="dropdown-item" @click="closeUserMenu">
                👤 Мой профиль
              </router-link>
              <div class="dropdown-divider"></div>
              <button @click="logout" class="dropdown-item logout">
                🚪 Выйти
              </button>
            </div>
          </div>

          <!-- Кнопки для неавторизованных -->
          <div v-else class="auth-buttons">
            <router-link to="/login" class="btn btn-secondary btn-small">
              Войти
            </router-link>
            <router-link to="/register" class="btn btn-primary btn-small">
              Регистрация
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const router = useRouter()
const authStore = useAuthStore()
const showUserMenu = ref(false)
const analysesLeft = ref(null)

// Директива для клика вне меню
const vClickOutside = {
  mounted: (el, binding) => {
    el.clickOutsideEvent = (event) => {
      if (!(el === event.target || el.contains(event.target))) {
        binding.value()
      }
    }
    document.addEventListener('click', el.clickOutsideEvent)
  },
  unmounted: (el) => {
    document.removeEventListener('click', el.clickOutsideEvent)
  }
}

// Загружаем остаток анализов
const loadAnalysesLeft = async () => {
  try {
    const response = await api.get('/tariffs/my')
    analysesLeft.value = response.data.analyses_left
  } catch (error) {
    console.error('Ошибка загрузки анализов:', error)
  }
}

// Выход
const logout = () => {
  authStore.logout()
  closeUserMenu()
  router.push('/')
}

const closeUserMenu = () => {
  showUserMenu.value = false
}

onMounted(() => {
  if (authStore.isAuthenticated) {
    loadAnalysesLeft()
  }
})
</script>

<style scoped>
.navbar {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  padding: var(--spacing-xs) 0;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
  background: rgba(255, 252, 245, 0.95);
}

.navbar-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  text-decoration: none;
  color: var(--color-text);
  font-weight: 600;
  font-size: 20px;
  transition: var(--transition);
}

.logo:hover {
  color: var(--color-primary);
}

.logo-icon {
  font-size: 24px;
}

.nav-links {
  display: flex;
  gap: var(--spacing-xs);
  flex: 1;
  justify-content: center;
}

.nav-link {
  padding: var(--spacing-xs) var(--spacing-sm);
  color: var(--color-text-light);
  text-decoration: none;
  font-weight: 500;
  border-radius: var(--border-radius-pill);
  transition: var(--transition);
  white-space: nowrap;
}

.nav-link:hover {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.nav-link.active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
  font-weight: 600;
}

.admin-link {
  color: #8b5cf6;
}

.admin-link:hover,
.admin-link.active {
  color: #7c3aed;
  background: #ede9fe;
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.analyses-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: var(--color-primary-soft);
  border-radius: var(--border-radius-pill);
  border: 1px solid var(--color-primary);
  color: var(--color-primary-dark);
  font-weight: 600;
  font-size: 14px;
}

.analyses-icon {
  font-size: 16px;
}

.user-menu {
  position: relative;
}

.user-button {
  display: flex;
  align-items: center;
  gap: var(--spacing-xxs);
  padding: 6px 12px;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius-pill);
  cursor: pointer;
  transition: var(--transition);
  color: var(--color-text);
}

.user-button:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.user-avatar {
  font-size: 18px;
}

.user-name {
  font-weight: 500;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chevron {
  font-size: 12px;
  transition: var(--transition);
}

.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 200px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  box-shadow: 0 8px 30px var(--color-shadow-strong);
  overflow: hidden;
  animation: dropdownAppear 0.2s ease;
  z-index: 1000;
}

@keyframes dropdownAppear {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dropdown-item {
  display: block;
  padding: var(--spacing-xs) var(--spacing-sm);
  color: var(--color-text);
  text-decoration: none;
  transition: var(--transition);
  text-align: left;
  width: 100%;
  border: none;
  background: none;
  font-size: 14px;
  cursor: pointer;
}

.dropdown-item:hover {
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.dropdown-item.logout:hover {
  background: var(--color-error);
  color: var(--color-error-text);
}

.dropdown-divider {
  height: 1px;
  background: var(--color-border);
  margin: 4px 0;
}

.auth-buttons {
  display: flex;
  gap: var(--spacing-xxs);
}

.btn-small {
  padding: 8px 16px;
  font-size: 14px;
}

@media (max-width: 768px) {
  .nav-links {
    display: none;
  }
  
  .user-name {
    display: none;
  }
  
  .analyses-indicator {
    display: none;
  }
}
</style>
