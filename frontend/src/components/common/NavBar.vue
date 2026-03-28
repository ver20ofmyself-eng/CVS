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

        <!-- Бургер-меню (мобильное) -->
        <button
          v-if="authStore.isAuthenticated"
          class="burger-btn"
          @click="showMobileMenu = !showMobileMenu"
          :class="{ open: showMobileMenu }"
        >
          <span></span><span></span><span></span>
        </button>

        <!-- Правый блок -->
        <div class="navbar-right">
          <!-- Индикатор анализов -->
          <div v-if="authStore.isAuthenticated && analysesLeft !== null" class="analyses-indicator" :class="analysesClass">
            <span class="analyses-icon">⚡</span>
            <span class="analyses-count">{{ analysesLeft }}</span>
            <span class="analyses-label">анализов</span>
          </div>

          <!-- Кнопка темы/фона -->
          <div v-if="authStore.isAuthenticated" class="theme-menu" ref="themeRef">
            <button class="theme-btn" @click="showThemeMenu = !showThemeMenu" title="Оформление">
              🎨
            </button>
            <Transition name="dropdown">
              <div v-if="showThemeMenu" class="theme-dropdown">
                <label class="theme-upload-btn">
                  🖼️ Загрузить фон
                  <input type="file" accept="image/*" @change="handleBgUpload" class="theme-file-input" />
                </label>
                <button v-if="hasBgImage" class="theme-clear-btn" @click="clearBgImage">
                  ✕ Убрать фон
                </button>
              </div>
            </Transition>
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

    <!-- Мобильное меню -->
    <Transition name="mobile-menu">
      <div v-if="showMobileMenu && authStore.isAuthenticated" class="mobile-menu-overlay" @click.self="showMobileMenu = false">
        <nav class="mobile-nav">
          <router-link to="/vacancies" class="mobile-nav-link" @click="showMobileMenu = false">📋 Вакансии</router-link>
          <router-link to="/history" class="mobile-nav-link" @click="showMobileMenu = false">📜 История</router-link>
          <router-link to="/profile" class="mobile-nav-link" @click="showMobileMenu = false">👤 Профиль</router-link>
          <router-link v-if="authStore.isAdmin" to="/prompts" class="mobile-nav-link" @click="showMobileMenu = false">⚙️ Промпты</router-link>
          <div class="mobile-nav-divider"></div>
          <div v-if="analysesLeft !== null" class="mobile-analyses">⚡ Осталось анализов: {{ analysesLeft }}</div>
          <button class="mobile-nav-link mobile-logout" @click="logout; showMobileMenu = false">🚪 Выйти</button>
        </nav>
      </div>
    </Transition>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const router     = useRouter()
const authStore  = useAuthStore()
const showUserMenu = ref(false)
const showMobileMenu = ref(false)
const showThemeMenu = ref(false)
const analysesLeft = ref(null)
const menuRef      = ref(null)
const themeRef     = ref(null)
const hasBgImage   = ref(!!localStorage.getItem('cvs_bg_image'))

const analysesClass = computed(() => {
  const v = analysesLeft.value
  if (v === null) return ''
  if (v <= 5)  return 'analyses--critical'
  if (v <= 20) return 'analyses--warning'
  return ''
})

// ── Background image ──────────────────────────────────────────────────────────
const applyBgImage = () => {
  const img = localStorage.getItem('cvs_bg_image')
  const app = document.getElementById('app')
  if (!app) return
  if (img) {
    app.style.backgroundImage = `url(${img})`
    app.style.backgroundSize = 'cover'
    app.style.backgroundPosition = 'center'
    app.style.backgroundAttachment = 'fixed'
    app.classList.add('has-bg-image')
    hasBgImage.value = true
  } else {
    app.style.backgroundImage = ''
    app.classList.remove('has-bg-image')
    hasBgImage.value = false
  }
}

const handleBgUpload = (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  // Limit to 5MB
  if (file.size > 5 * 1024 * 1024) { alert('Максимум 5 МБ'); return }
  const reader = new FileReader()
  reader.onload = () => {
    localStorage.setItem('cvs_bg_image', reader.result)
    applyBgImage()
    showThemeMenu.value = false
  }
  reader.readAsDataURL(file)
}

const clearBgImage = () => {
  localStorage.removeItem('cvs_bg_image')
  applyBgImage()
  showThemeMenu.value = false
}

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
  if (themeRef.value && !themeRef.value.contains(e.target)) showThemeMenu.value = false
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  if (authStore.isAuthenticated) loadAnalysesLeft()
  applyBgImage() // Восстанавливаем фон при загрузке
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
.analyses-indicator { display: flex; align-items: center; gap: 5px; padding: 6px 14px; background: var(--color-primary-soft); border-radius: var(--border-radius-pill); border: 1px solid rgba(16, 106, 183, 0.3); color: var(--color-primary-dark); font-weight: 700; font-size: 13px; transition: var(--transition); }
.analyses-indicator .analyses-label { font-weight: 500; font-size: 12px; opacity: 0.8; }
.analyses--warning { background: #fffbeb; border-color: #f59e0b; color: #92400e; }
.analyses--critical { background: #fef2f2; border-color: #ef4444; color: #991b1b; animation: pulse-critical 2s infinite; }
@keyframes pulse-critical { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
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

/* Бургер-кнопка */
.burger-btn {
  display: none; width: 36px; height: 36px; border: none; background: none;
  cursor: pointer; flex-direction: column; justify-content: center; align-items: center; gap: 5px;
  padding: 6px; border-radius: 8px; transition: background 0.2s;
}
.burger-btn:hover { background: var(--color-primary-soft); }
.burger-btn span {
  display: block; width: 20px; height: 2px; background: var(--color-text);
  border-radius: 2px; transition: all 0.25s ease;
}
.burger-btn.open span:nth-child(1) { transform: rotate(45deg) translate(5px, 5px); }
.burger-btn.open span:nth-child(2) { opacity: 0; }
.burger-btn.open span:nth-child(3) { transform: rotate(-45deg) translate(5px, -5px); }
@media (max-width: 768px) { .burger-btn { display: flex; } }

/* Мобильное меню */
.mobile-menu-overlay {
  position: fixed; top: 56px; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.3); backdrop-filter: blur(4px); z-index: 99;
}
.mobile-nav {
  background: var(--color-surface); border-bottom: 1px solid var(--color-border);
  padding: 12px 16px; display: flex; flex-direction: column; gap: 4px;
  box-shadow: 0 12px 40px var(--color-shadow-strong);
  animation: mobileSlide 0.2s ease;
}
@keyframes mobileSlide { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
.mobile-nav-link {
  display: block; padding: 12px 16px; border-radius: var(--border-radius-sm);
  text-decoration: none; color: var(--color-text); font-size: 15px; font-weight: 500;
  transition: var(--transition); border: none; background: none; text-align: left;
  cursor: pointer; font-family: inherit; width: 100%;
}
.mobile-nav-link:hover { background: var(--color-primary-soft); color: var(--color-primary); }
.mobile-nav-link.router-link-active { background: var(--color-primary-soft); color: var(--color-primary); font-weight: 600; }
.mobile-logout:hover { background: #fef2f2; color: #991b1b; }
.mobile-nav-divider { height: 1px; background: var(--color-border); margin: 4px 0; }
.mobile-analyses { padding: 8px 16px; font-size: 13px; color: var(--color-primary-dark); font-weight: 600; }
.mobile-menu-enter-active, .mobile-menu-leave-active { transition: opacity 0.2s ease; }
.mobile-menu-enter-from, .mobile-menu-leave-to { opacity: 0; }

/* Theme button */
.theme-menu { position: relative; }
.theme-btn {
  width: 36px; height: 36px; border: 2px solid var(--color-border); border-radius: 50%;
  background: var(--color-surface); cursor: pointer; font-size: 16px;
  display: flex; align-items: center; justify-content: center; transition: var(--transition);
}
.theme-btn:hover { border-color: var(--color-primary); background: var(--color-primary-soft); transform: scale(1.05); }
.theme-dropdown {
  position: absolute; top: calc(100% + 8px); right: 0; min-width: 180px;
  background: var(--color-surface); border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm); box-shadow: 0 12px 40px var(--color-shadow-strong);
  overflow: hidden; padding: 6px;
}
.theme-upload-btn {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px; border-radius: 8px;
  cursor: pointer; font-size: 14px; color: var(--color-text); transition: var(--transition); width: 100%;
}
.theme-upload-btn:hover { background: var(--color-primary-soft); color: var(--color-primary-dark); }
.theme-file-input { display: none; }
.theme-clear-btn {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px; border-radius: 8px;
  cursor: pointer; font-size: 14px; color: #991b1b; border: none; background: none;
  transition: var(--transition); width: 100%; font-family: inherit; text-align: left;
}
.theme-clear-btn:hover { background: #fef2f2; }
</style>
