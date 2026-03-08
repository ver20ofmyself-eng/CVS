import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'root',
            redirect: () => {
                // Простой редирект без доступа к store
                return '/login'
            }
        },
        {
            path: '/login',
            name: 'login',
            component: () => import('../views/LoginView.vue'),
            meta: { guest: true }
        },
        {
            path: '/register',
            name: 'register',
            component: () => import('../views/RegisterView.vue'),
            meta: { guest: true }
        },
        {
            path: '/vacancies',
            name: 'vacancies',
            component: () => import('../views/VacanciesView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/vacancies/new',
            name: 'new-vacancy',
            component: () => import('../views/VacancyEditView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/vacancies/:id',
            name: 'vacancy-detail',
            component: () => import('../views/VacancyDetailView.vue'),
            meta: { requiresAuth: true },
            props: true
        },
        {
            path: '/vacancies/:id/edit',
            name: 'edit-vacancy',
            component: () => import('../views/VacancyEditView.vue'),
            meta: { requiresAuth: true },
            props: true
        },
        {
            path: '/history',
            name: 'history',
            component: () => import('../views/HistoryView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/history/:id',
            name: 'analysis-detail',
            component: () => import('../views/AnalysisDetailView.vue'),
            meta: { requiresAuth: true },
            props: true
        },
        {
            path: '/profile',
            name: 'profile',
            component: () => import('../views/ProfileView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/admin',
            name: 'admin',
            component: () => import('../views/AdminView.vue'),
            meta: {
                requiresAuth: true,
                requiresAdmin: true
            }
        },
        // Catch-all для несуществующих маршрутов
        {
            path: '/:pathMatch(.*)*',
            name: 'not-found',
            redirect: '/'
        }
    ]
})

// Навигационный гард
router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore()

    // Загружаем пользователя если есть токен, но нет данных
    if (!authStore.user && authStore.token) {
        await authStore.fetchUser()
    }

    const isAuthenticated = authStore.isAuthenticated
    const isAdmin = authStore.isAdmin

    // Маршруты, требующие авторизации
    if (to.meta.requiresAuth && !isAuthenticated) {
        // Не авторизован → на логин
        next({ name: 'login', query: { redirect: to.fullPath } })
        return
    }

    // Маршруты только для гостей (login, register)
    if (to.meta.guest && isAuthenticated) {
        // Уже авторизован → на список вакансий
        next({ name: 'vacancies' })
        return
    }

    // Маршруты только для админов
    if (to.meta.requiresAdmin && !isAdmin) {
        // Не админ → на список вакансий
        next({ name: 'vacancies' })
        return
    }

    // Всё ок, продолжаем
    next()
})

export default router
