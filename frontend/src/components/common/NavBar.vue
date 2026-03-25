<template>
  <header class="navbar">
    <div class="container">
      <div class="navbar-content">
        <!-- Логотип -->
        <router-link to="/" class="logo">
          <span class="logo-icon">🔍</span>
          <span class="logo-text">CVS Analyzer</span>
        </router-link>

        <!-- Навигация (десктоп) -->
        <nav v-if="authStore.isAuthenticated" class="nav-links">
          <router-link to="/vacancies" class="nav-link" active-class="active">
            📋 Вакансии
          </router-link>
          <router-link to="/history" class="nav-link" active-class="active">
            📜 История
          </router-link>
        </nav>

        <!-- Правый блок -->
        <div class="navbar-right">
          <!-- Индикатор анализов -->
          <div v-if="authStore.isAuthenticated && analysesLeft !== null" class="analyses-indicator">
            <span class="analyses-icon">⚡</span>
            <span class="analyses-count">{{ analysesLeft }}</span>
          </div>

          <!-- Меню пользователя -->
          <div v-if="authStore.isAuthenticated" class="user-menu" ref="menuRef">
            <button @click="showUserMenu = !showUserMenu" class="user-button">
              <span class="user-avatar">👤</span>
              <span class="user-name">{{ authStore.userName }}</span>
              <span class="chevron" :class="{ rotated: showUserMenu }">▼</span>
            </button>

            <Transition name="dropdown">
              <div v-if="showUserMenu" class="user-dropdown">
                <router-link to="/profile" class="dropdown-item" @click="closeUserMenu">
                  👤 Мой профиль
                </router-link>
                <router-link
                  v-if="authStore.isAdmin"
                  to="/prompts"
                  class="dropdown-item admin-item"
                  @click="closeUserMenu"
                >
                  ⚙️ Промпты
                </router-link>
                <div class="dropdown-divider"></div>
                <button @click="logout" class="dropdown-item logout">
                  🚪 Выйти
                </button>
              </div>
            </Transition>
          </div>

          <!-- Кнопки для неавторизованных -->
          <div v-else class="auth-buttons">
            <router-link to="/login" class="btn btn-secondary btn-small">Войти</router-link>
            <router-link to="/register" class="btn btn-primary btn-small">Регистрация</router-link>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const router     = useRouter()
const authStore  = useAuthStore()
const showUserMenu = ref(false)
const analysesLeft = ref(null)
const menuRef      = ref(null)

const loadAnalysesLeft = async () => {
  try {
    const { data } = await api.get('/tariffs/my')
    analysesLeft.value = data.analyses_left
  } catch { /* silent */ }
}

const logout = async () => {
  await authStore.logout()
  closeUserMenu()
  router.push('/login')
}

const closeUserMenu = () => { showUserMenu.value = false }

const handleClickOutside = e => {
  if (menuRef.value && !menuRef.value.contains(e.target)) closeUserMenu()
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  if (authStore.isAuthenticated) loadAnalysesLeft()
})
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
</script>

<style scoped>
.navbar {
  position: sticky; top: 0; z-index: 100;
  background: rgba(255, 252, 245, 0.95);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-border);
  padding: var(--spacing-xs) 0;
}
.navbar-content { display: flex; align-items: center; justify-content: space-between; gap: var(--spacing); }
.logo { display: flex; align-items: center; gap: 8px; text-decoration: none; color: var(--color-text); font-weight: 700; font-size: 18px; transition: var(--transition); }
.logo:hover { color: var(--color-primary); }
.logo-icon { font-size: 22px; }
.nav-links { display: flex; gap: 4px; flex: 1; justify-content: center; }
.nav-link { padding: 8px 16px; color: var(--color-text-light); text-decoration: none; font-weight: 500; font-size: 14px; border-radius: var(--border-radius-pill); transition: var(--transition); white-space: nowrap; }
.nav-link:hover { color: var(--color-primary); background: var(--color-primary-soft); }
.nav-link.active { color: var(--color-primary); background: var(--color-primary-soft); font-weight: 600; }
.navbar-right { display: flex; align-items: center; gap: var(--spacing-sm); }
.analyses-indicator { display: flex; align-items: center; gap: 5px; padding: 6px 12px; background: var(--color-primary-soft); border-radius: var(--border-radius-pill); border: 1px solid rgba(16, 106, 183, 0.3); color: var(--color-primary-dark); font-weight: 700; font-size: 13px; }
.user-menu { position: relative; }
.user-button { display: flex; align-items: center; gap: 6px; padding: 6px 12px; background: transparent; border: 2px solid var(--color-border); border-radius: var(--border-radius-pill); cursor: pointer; transition: var(--transition); color: var(--color-text); font-size: 14px; font-family: inherit; }
.user-button:hover { border-color: var(--color-primary); background: var(--color-primary-soft); }
.user-avatar { font-size: 16px; }
.user-name { font-weight: 500; max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chevron { font-size: 10px; transition: transform 0.2s ease; }
.chevron.rotated { transform: rotate(180deg); }
.user-dropdown { position: absolute; top: calc(100% + 8px); right: 0; min-width: 190px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--border-radius-sm); box-shadow: 0 12px 40px var(--color-shadow-strong); overflow: hidden; }
.dropdown-item { display: block; padding: 10px 16px; color: var(--color-text); text-decoration: none; transition: var(--transition); text-align: left; width: 100%; border: none; background: none; font-size: 14px; cursor: pointer; font-family: inherit; }
.dropdown-item:hover { background: var(--color-primary-soft); color: var(--color-primary-dark); }
.dropdown-item.logout:hover { background: #fef2f2; color: #991b1b; }
.admin-item { color: #6d28d9; }
.admin-item:hover { background: #ede9fe !important; color: #5b21b6 !important; }
.dropdown-divider { height: 1px; background: var(--color-border); margin: 2px 0; }
.auth-buttons { display: flex; gap: 8px; }
.btn-small { padding: 8px 16px; font-size: 14px; }
.dropdown-enter-active, .dropdown-leave-active { transition: all 0.15s ease; }
.dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(-8px); }
@media (max-width: 768px) { .nav-links { display: none; } .user-name { display: none; } .analyses-indicator { display: none; } }
</style>
