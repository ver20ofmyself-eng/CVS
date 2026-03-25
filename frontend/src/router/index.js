import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/', redirect: '/vacancies' },

    // ── Гостевые маршруты ──────────────────────────────────────────────────
    { path: '/login',    name: 'login',    component: () => import('@/views/LoginView.vue'),    meta: { guest: true } },
    { path: '/register', name: 'register', component: () => import('@/views/RegisterView.vue'), meta: { guest: true } },

    // ── Защищённые маршруты ────────────────────────────────────────────────
    { path: '/vacancies',          name: 'vacancies',      component: () => import('@/views/VacanciesView.vue'),     meta: { requiresAuth: true } },
    { path: '/vacancies/new',      name: 'new-vacancy',    component: () => import('@/views/VacancyEditView.vue'),   meta: { requiresAuth: true } },
    { path: '/vacancies/:id',      name: 'vacancy-detail', component: () => import('@/views/VacancyDetailView.vue'), meta: { requiresAuth: true }, props: true },
    { path: '/vacancies/:id/edit', name: 'edit-vacancy',   component: () => import('@/views/VacancyEditView.vue'),   meta: { requiresAuth: true }, props: true },

    { path: '/history',     name: 'history',         component: () => import('@/views/HistoryView.vue'),        meta: { requiresAuth: true } },
    { path: '/history/:id', name: 'analysis-detail', component: () => import('@/views/AnalysisDetailView.vue'), meta: { requiresAuth: true }, props: true },

    { path: '/profile', name: 'profile', component: () => import('@/views/ProfileView.vue'), meta: { requiresAuth: true } },

    // ── Только для администраторов ─────────────────────────────────────────
    { path: '/prompts', name: 'prompts', component: () => import('@/views/PromptsView.vue'), meta: { requiresAuth: true, requiresAdmin: true } },

    // ── Catch-all ──────────────────────────────────────────────────────────
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  if (!authStore.user && authStore.token) {
    await authStore.fetchUser()
  }

  const isAuth  = authStore.isAuthenticated
  const isAdmin = authStore.isAdmin

  if (to.meta.requiresAuth && !isAuth)  return { name: 'login', query: { redirect: to.fullPath } }
  if (to.meta.guest      && isAuth)     return { name: 'vacancies' }
  if (to.meta.requiresAdmin && !isAdmin) return { name: 'vacancies' }
})

export default router
