<template>
  <div class="vd">
    <div class="container">
      <!-- Хлебные крошки -->
      <div class="vd-breadcrumb">
        <router-link to="/vacancies" class="vd-back">← К списку вакансий</router-link>
      </div>

      <!-- Загрузка -->
      <div v-if="loading" class="vd-state"><div class="spinner"></div><p>Загрузка вакансии...</p></div>

      <!-- Ошибка -->
      <div v-else-if="error" class="vd-state">
        <span class="vd-state-icon">❌</span><p>{{ error }}</p>
        <button class="btn btn-primary" @click="retryLoad">Повторить</button>
      </div>

      <!-- Контент -->
      <template v-else-if="vacancy">
        <!-- ═══ ШАПКА ═══ -->
        <div class="vd-header">
          <div class="vd-header-info">
            <div class="vd-title-row">
              <h1 class="vd-title">{{ vacancy.title }}</h1>
              <span class="vd-status-tag" :class="`st--${vacancy.status || 'active'}`">{{ statusLabel }}</span>
            </div>
            <div class="vd-meta-row">
              <span v-if="vacancy.location">📍 {{ vacancy.location }}</span>
              <span v-if="vacancy.client">👤 {{ vacancy.client }}</span>
              <span v-if="hasSalary">💰 {{ formatSalary }}</span>
              <span v-if="vacancy.recruitment_start_date">📅 {{ vacancy.recruitment_start_date }}</span>
            </div>
          </div>
          <!-- Кнопки: опасные слева, активные справа -->
          <div class="vd-header-actions">
            <div class="vd-actions-left">
              <button v-if="vacancy.status !== 'archived'" class="vd-act vd-act--warn" @click="confirmArchive" title="В архив">📦</button>
            </div>
            <div class="vd-actions-right">
              <button v-if="vacancy.status === 'active'" class="vd-act vd-act--success" @click="confirmComplete" title="Завершить">✅</button>
              <button v-if="vacancy.status !== 'active'" class="vd-act vd-act--success" @click="confirmReopen" title="Возобновить">▶️</button>
              <button class="vd-act vd-act--neutral" @click="confirmClone" title="Клонировать">📋</button>
              <router-link :to="`/vacancies/${vacancy.id}/edit`" class="vd-act vd-act--primary" title="Редактировать">✏️</router-link>
            </div>
          </div>
        </div>

        <!-- ═══ ТАБЫ ═══ -->
        <div class="vd-tabs">
          <button
            v-for="tab in tabs" :key="tab.key"
            class="vd-tab"
            :class="{ 'vd-tab--active': activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            {{ tab.icon }} {{ tab.label }}
            <span v-if="tab.count !== undefined" class="vd-tab-count">{{ tab.count }}</span>
          </button>
        </div>

        <!-- ═══ ОБЗОР ═══ -->
        <div v-if="activeTab === 'overview'" class="vd-tab-content">
          <!-- Статистика -->
          <div class="vd-stats-grid">
            <div class="vd-stat"><span class="vd-stat-val">{{ stats.totalAnalyses }}</span><span class="vd-stat-lbl">Анализов</span></div>
            <div class="vd-stat"><span class="vd-stat-val">{{ stats.averageScore > 0 ? stats.averageScore.toFixed(0) + '%' : '—' }}</span><span class="vd-stat-lbl">Ср. оценка</span></div>
            <div class="vd-stat"><span class="vd-stat-val">{{ stats.invitationRate }}%</span><span class="vd-stat-lbl">Приглашений</span></div>
            <div class="vd-stat"><span class="vd-stat-val">{{ stats.uniqueCandidates }}</span><span class="vd-stat-lbl">Кандидатов</span></div>
          </div>

          <!-- Ключевые навыки -->
          <div class="vd-card" v-if="vacancy.key_skills?.length">
            <h3 class="vd-card-title">🔧 Ключевые навыки</h3>
            <div class="vd-skills">
              <span v-for="s in vacancy.key_skills" :key="s" class="vd-skill">{{ s }}</span>
            </div>
          </div>

          <!-- Описание -->
          <div class="vd-card">
            <h3 class="vd-card-title">📝 Описание вакансии</h3>
            <div class="vd-description" v-html="sanitizeHtml(vacancy.description_html || vacancy.description_text || '<em>Описание отсутствует</em>')"></div>
          </div>

          <!-- Комментарий для AI -->
          <div class="vd-card" v-if="vacancy.comment_for_ai">
            <h3 class="vd-card-title">🤖 Комментарий для AI</h3>
            <div class="vd-comment">{{ vacancy.comment_for_ai }}</div>
          </div>

          <!-- Распределение оценок -->
          <div class="vd-card" v-if="stats.totalAnalyses > 0">
            <h3 class="vd-card-title">📊 Распределение оценок</h3>
            <div class="vd-bars">
              <div class="vd-bar-row">
                <span class="vd-bar-label">85-100%</span>
                <div class="vd-bar-track"><div class="vd-bar-fill vd-bar--high" :style="{ width: stats.highScorePercent + '%' }"></div></div>
                <span class="vd-bar-val">{{ stats.highScoreCount }}</span>
              </div>
              <div class="vd-bar-row">
                <span class="vd-bar-label">50-84%</span>
                <div class="vd-bar-track"><div class="vd-bar-fill vd-bar--mid" :style="{ width: stats.mediumScorePercent + '%' }"></div></div>
                <span class="vd-bar-val">{{ stats.mediumScoreCount }}</span>
              </div>
              <div class="vd-bar-row">
                <span class="vd-bar-label">0-49%</span>
                <div class="vd-bar-track"><div class="vd-bar-fill vd-bar--low" :style="{ width: stats.lowScorePercent + '%' }"></div></div>
                <span class="vd-bar-val">{{ stats.lowScoreCount }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- ═══ КАНДИДАТЫ ═══ -->
        <div v-if="activeTab === 'candidates'" class="vd-tab-content">
          <div v-if="history.loading" class="vd-mini-state"><div class="spinner spinner-sm"></div> Загрузка...</div>
          <div v-else-if="!history.items.length" class="vd-mini-state">
            <p>По этой вакансии ещё нет анализов</p>
            <p class="text-muted text-sm">💡 Откройте расширение на hh.ru и выберите эту вакансию для анализа</p>
          </div>
          <div v-else class="vd-candidates-list">
            <div
              v-for="a in history.items" :key="a.id"
              class="vd-cand-card"
              @click="$router.push(`/history/${a.id}`)"
            >
              <div class="vd-cand-header">
                <span class="vd-cand-title">{{ a.analysis_title || ('Анализ #' + a.id) }}</span>
                <span class="vd-cand-score" :class="scoreClass(a.score)">{{ a.score }}%</span>
              </div>
              <p class="vd-cand-preview">{{ a.cv_text_preview }}</p>
              <div class="vd-cand-footer">
                <span class="vd-cand-rec" :class="recClass(a.recommendation)">{{ a.recommendation }}</span>
                <span class="vd-cand-date">{{ formatDate(a.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- ═══ ШАБЛОНЫ ═══ -->
        <div v-if="activeTab === 'templates'" class="vd-tab-content">
          <div v-if="!hasTemplates" class="vd-mini-state">
            <p>Шаблоны пока не заполнены</p>
            <router-link :to="`/vacancies/${vacancy.id}/edit`" class="btn btn-secondary">✏️ Редактировать вакансию</router-link>
          </div>
          <div v-else class="vd-templates-grid">
            <div v-for="(tpl, key) in templatesList" :key="key" class="vd-tpl-card">
              <h4 class="vd-tpl-title">{{ tpl.icon }} {{ tpl.label }}</h4>
              <p class="vd-tpl-text">{{ tpl.text }}</p>
              <button class="vd-tpl-copy" @click="copyText(tpl.text)">📋 Копировать</button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Confirm -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="confirm.show" class="vd-overlay" @click.self="confirm.show = false">
          <div class="vd-confirm">
            <div class="vd-confirm-icon">{{ confirm.icon }}</div>
            <h3>{{ confirm.title }}</h3>
            <p>{{ confirm.message }}</p>
            <div class="vd-confirm-btns">
              <button class="btn btn-secondary" @click="confirm.show = false">Отмена</button>
              <button class="btn" :class="confirm.danger ? 'btn-danger' : 'btn-primary'" @click="confirm.action">{{ confirm.btnText }}</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useVacanciesStore } from '@/stores/vacancies'
import { useToast } from '@/composables/useToast'
import api from '@/services/api'
import { formatDistance } from 'date-fns'
import { ru } from 'date-fns/locale'

const route = useRoute()
const router = useRouter()
const store = useVacanciesStore()
const toast = useToast()

const vacancy = ref(null)
const loading = ref(true)
const error = ref(null)
const activeTab = ref('overview')
const history = reactive({ items: [], loading: false })
const confirm = reactive({ show: false, title: '', message: '', icon: '⚠️', btnText: 'OK', danger: false, action: null })

// Stats
const stats = ref({
  totalAnalyses: 0, averageScore: 0, invitationRate: 0, uniqueCandidates: 0,
  highScoreCount: 0, mediumScoreCount: 0, lowScoreCount: 0,
  highScorePercent: 0, mediumScorePercent: 0, lowScorePercent: 0,
})

const statusLabel = computed(() => {
  const m = { active: 'Активна', completed: 'Завершена', archived: 'В архиве' }
  return m[vacancy.value?.status] || 'Активна'
})

const hasSalary = computed(() => {
  const sr = vacancy.value?.salary_range
  return sr && (sr.min || sr.max)
})

const formatSalary = computed(() => {
  const sr = vacancy.value?.salary_range
  if (!sr) return ''
  const fmt = (v) => new Intl.NumberFormat('ru-RU').format(v)
  const p = []
  if (sr.min) p.push(`от ${fmt(sr.min)}`)
  if (sr.max) p.push(`до ${fmt(sr.max)}`)
  return `${p.join(' ')} ${sr.currency || 'RUB'}`
})

const tabs = computed(() => [
  { key: 'overview', icon: '📊', label: 'Обзор' },
  { key: 'candidates', icon: '👥', label: 'Кандидаты', count: history.items.length },
  { key: 'templates', icon: '📋', label: 'Шаблоны' },
])

const hasTemplates = computed(() => {
  const t = vacancy.value?.templates
  return t && Object.values(t).some(v => v && v.trim())
})

const templateConfig = {
  hh_invitation:        { label: 'Приглашение на hh.ru', icon: '📧' },
  messenger_invitation: { label: 'Приглашение в мессенджер', icon: '💬' },
  interview_questions:  { label: 'Вопросы для интервью', icon: '❓' },
  rejection:            { label: 'Шаблон отказа', icon: '📨' },
}

const templatesList = computed(() => {
  const t = vacancy.value?.templates || {}
  return Object.entries(t)
    .filter(([, v]) => v && v.trim())
    .map(([key, text]) => ({
      key,
      text,
      label: templateConfig[key]?.label || key,
      icon: templateConfig[key]?.icon || '📄',
    }))
})

const sanitizeHtml = (html) => {
  if (!html) return ''
  const tmp = document.createElement('div')
  tmp.innerHTML = html
  tmp.querySelectorAll('script, iframe, object, embed, link, style').forEach(el => el.remove())
  tmp.querySelectorAll('*').forEach(el => {
    Array.from(el.attributes).forEach(attr => {
      if (attr.name.startsWith('on') || attr.value.includes('javascript:')) el.removeAttribute(attr.name)
    })
  })
  return tmp.innerHTML
}

const formatDate = (d) => d ? formatDistance(new Date(d), new Date(), { addSuffix: true, locale: ru }) : ''

const scoreClass = (s) => {
  if (s >= 85) return 'sc--high'
  if (s >= 50) return 'sc--mid'
  return 'sc--low'
}

const recClass = (r) => {
  if (!r) return ''
  if (r.includes('Пригласить')) return 'rc--invite'
  if (r.includes('Рекомендуется') || r.includes('Рассмотреть')) return 'rc--consider'
  return 'rc--reject'
}

// Load
const loadData = async () => {
  const id = parseInt(route.params.id)
  if (isNaN(id)) { error.value = 'Неверный ID'; loading.value = false; return }
  try {
    vacancy.value = await store.fetchVacancy(id)
    await loadHistory(id)
  } catch { error.value = 'Не удалось загрузить вакансию' }
  finally { loading.value = false }
}

const loadHistory = async (vacancyId) => {
  history.loading = true
  try {
    const { data } = await api.get('/analyze/history', { params: { vacancy_id: vacancyId, limit: 200 } })
    history.items = data
    calcStats(data)
  } catch { /* silent */ }
  finally { history.loading = false }
}

const calcStats = (analyses) => {
  if (!analyses.length) return
  const t = analyses.length
  const avg = analyses.reduce((s, a) => s + (a.score || 0), 0) / t
  const inv = analyses.filter(a => a.recommendation?.includes('Пригласить')).length
  const high = analyses.filter(a => a.score >= 85).length
  const med = analyses.filter(a => a.score >= 50 && a.score < 85).length
  const low = analyses.filter(a => a.score < 50).length
  stats.value = {
    totalAnalyses: t, averageScore: avg,
    invitationRate: Math.round((inv / t) * 100),
    uniqueCandidates: new Set(analyses.map(a => a.candidate_name || a.cv_text_preview)).size,
    highScoreCount: high, mediumScoreCount: med, lowScoreCount: low,
    highScorePercent: Math.round((high / t) * 100),
    mediumScorePercent: Math.round((med / t) * 100),
    lowScorePercent: Math.round((low / t) * 100),
  }
}

const retryLoad = () => { error.value = null; loading.value = true; loadData() }

const copyText = async (text) => {
  try { await navigator.clipboard.writeText(text); toast.success('Скопировано') }
  catch { toast.error('Не удалось скопировать') }
}

// Confirm actions
const showConfirm = (opts) => Object.assign(confirm, { show: true, ...opts })

const confirmComplete = () => showConfirm({
  title: 'Завершить вакансию?', message: `«${vacancy.value.title}» будет отмечена как завершённая.`,
  icon: '✅', btnText: 'Завершить', danger: false,
  action: async () => { confirm.show = false; try { await store.completeVacancy(vacancy.value.id); vacancy.value.status = 'completed'; toast.success('Вакансия завершена') } catch { toast.error('Ошибка') } }
})

const confirmReopen = () => showConfirm({
  title: 'Возобновить вакансию?', message: `«${vacancy.value.title}» снова станет активной.`,
  icon: '▶️', btnText: 'Возобновить', danger: false,
  action: async () => { confirm.show = false; try { await store.reopenVacancy(vacancy.value.id); vacancy.value.status = 'active'; toast.success('Вакансия активирована') } catch { toast.error('Ошибка') } }
})

const confirmArchive = () => showConfirm({
  title: 'Перевести в архив?', message: `«${vacancy.value.title}» будет перемещена в архив.`,
  icon: '📦', btnText: 'В архив', danger: true,
  action: async () => { confirm.show = false; try { await store.deleteVacancy(vacancy.value.id); toast.success('Вакансия в архиве'); router.push('/vacancies') } catch { toast.error('Ошибка') } }
})

const confirmClone = () => showConfirm({
  title: 'Создать копию?', message: `Будет создана копия «${vacancy.value.title}».`,
  icon: '📋', btnText: 'Создать', danger: false,
  action: async () => { confirm.show = false; try { await store.cloneVacancy(vacancy.value.id); toast.success('Вакансия клонирована'); router.push('/vacancies') } catch { toast.error('Ошибка') } }
})

onMounted(loadData)
</script>

<style scoped>
.vd { padding: var(--spacing) 0; min-height: calc(100vh - 140px); }
.vd-breadcrumb { margin-bottom: var(--spacing); }
.vd-back { color: var(--color-text-muted); text-decoration: none; font-size: 14px; transition: var(--transition); }
.vd-back:hover { color: var(--color-primary); }

/* Header */
.vd-header { display: flex; justify-content: space-between; align-items: flex-start; gap: var(--spacing); margin-bottom: var(--spacing); flex-wrap: wrap; }
.vd-header-info { flex: 1; }
.vd-title-row { display: flex; align-items: center; gap: var(--spacing-xs); flex-wrap: wrap; margin-bottom: 6px; }
.vd-title { font-size: 28px; font-weight: 700; color: var(--color-text); margin: 0; }
.vd-status-tag { font-size: 12px; font-weight: 600; padding: 3px 12px; border-radius: var(--border-radius-pill); }
.st--active { background: #ecfdf5; color: #065f46; }
.st--completed { background: #fffbeb; color: #92400e; }
.st--archived { background: #f3f4f6; color: #6b7280; }
.vd-meta-row { display: flex; gap: var(--spacing-sm); font-size: 14px; color: var(--color-text-light); flex-wrap: wrap; }

.vd-header-actions { display: flex; gap: var(--spacing-xs); }
.vd-actions-left, .vd-actions-right { display: flex; gap: 6px; }
.vd-actions-left { margin-right: var(--spacing-xs); }

.vd-act {
  width: 40px; height: 40px; border: 2px solid var(--color-border); border-radius: 50%;
  background: var(--color-surface); cursor: pointer; transition: var(--transition); font-size: 18px;
  display: flex; align-items: center; justify-content: center; text-decoration: none; color: var(--color-text);
}
.vd-act:hover { transform: translateY(-2px); }
.vd-act--primary:hover { border-color: var(--color-primary); background: var(--color-primary-soft); }
.vd-act--neutral:hover { border-color: #0ea5e9; background: #e0f2fe; }
.vd-act--success:hover { border-color: #10b981; background: #ecfdf5; }
.vd-act--warn:hover    { border-color: #ef4444; background: #fef2f2; }

/* Tabs */
.vd-tabs { display: flex; gap: 4px; margin-bottom: var(--spacing); border-bottom: 2px solid var(--color-border); padding-bottom: 0; }
.vd-tab {
  padding: 10px 20px; border: none; background: none; cursor: pointer; font-size: 14px; font-weight: 500;
  color: var(--color-text-muted); border-bottom: 3px solid transparent; margin-bottom: -2px;
  transition: var(--transition); font-family: inherit; display: flex; align-items: center; gap: 6px;
}
.vd-tab:hover { color: var(--color-text); }
.vd-tab--active { color: var(--color-primary); border-bottom-color: var(--color-primary); font-weight: 600; }
.vd-tab-count { font-size: 11px; background: var(--color-surface-darker); padding: 1px 7px; border-radius: var(--border-radius-pill); color: var(--color-text-muted); }

.vd-tab-content { animation: fadeIn 0.2s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

/* Stats */
.vd-stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--spacing-sm); margin-bottom: var(--spacing); }
.vd-stat { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--border-radius); padding: var(--spacing-sm); text-align: center; transition: var(--transition); }
.vd-stat:hover { box-shadow: 0 6px 20px var(--color-shadow); }
.vd-stat-val { display: block; font-size: 28px; font-weight: 700; color: var(--color-primary); line-height: 1.2; }
.vd-stat-lbl { font-size: 12px; color: var(--color-text-muted); }

/* Cards */
.vd-card { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--border-radius); padding: var(--spacing); margin-bottom: var(--spacing-sm); transition: var(--transition); }
.vd-card:hover { box-shadow: 0 6px 20px var(--color-shadow); }
.vd-card-title { font-size: 16px; font-weight: 600; color: var(--color-text); margin: 0 0 var(--spacing-sm); }

.vd-skills { display: flex; flex-wrap: wrap; gap: 6px; }
.vd-skill { padding: 5px 14px; background: var(--color-primary-soft); border: 1px solid rgba(16,106,183,0.2); border-radius: var(--border-radius-pill); font-size: 13px; color: var(--color-primary-dark); }

.vd-description { font-size: 14px; line-height: 1.7; color: var(--color-text); }
.vd-description :deep(ul), .vd-description :deep(ol) { padding-left: 20px; }
.vd-comment { font-size: 14px; line-height: 1.6; background: var(--color-surface-darker); border-left: 4px solid var(--color-primary); padding: var(--spacing-sm); border-radius: var(--border-radius-sm); }

/* Bars */
.vd-bars { display: flex; flex-direction: column; gap: var(--spacing-xs); }
.vd-bar-row { display: flex; align-items: center; gap: var(--spacing-xs); }
.vd-bar-label { font-size: 12px; color: var(--color-text-muted); min-width: 60px; }
.vd-bar-track { flex: 1; height: 8px; background: var(--color-border); border-radius: 4px; overflow: hidden; }
.vd-bar-fill { height: 100%; transition: width 0.3s ease; border-radius: 4px; }
.vd-bar--high { background: #10b981; }
.vd-bar--mid  { background: #f59e0b; }
.vd-bar--low  { background: #ef4444; }
.vd-bar-val { font-size: 12px; color: var(--color-text-muted); min-width: 30px; text-align: right; }

/* Candidates */
.vd-candidates-list { display: flex; flex-direction: column; gap: var(--spacing-xs); }
.vd-cand-card { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--border-radius-sm); padding: var(--spacing-sm); cursor: pointer; transition: var(--transition); }
.vd-cand-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px var(--color-shadow); border-color: var(--color-primary); }
.vd-cand-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.vd-cand-title { font-size: 15px; font-weight: 600; color: var(--color-text); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-right: var(--spacing-xs); }
.vd-cand-score { font-size: 16px; font-weight: 700; padding: 2px 10px; border-radius: var(--border-radius-pill); color: white; flex-shrink: 0; }
.sc--high { background: #10b981; }
.sc--mid  { background: #f59e0b; color: #1e293b; }
.sc--low  { background: #ef4444; }
.vd-cand-preview { font-size: 13px; color: var(--color-text-light); line-height: 1.4; margin-bottom: 6px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.vd-cand-footer { display: flex; justify-content: space-between; align-items: center; }
.vd-cand-rec { font-size: 12px; font-weight: 600; padding: 2px 10px; border-radius: var(--border-radius-pill); }
.rc--invite  { background: #ecfdf5; color: #065f46; }
.rc--consider { background: #fffbeb; color: #92400e; }
.rc--reject  { background: #fef2f2; color: #991b1b; }
.vd-cand-date { font-size: 11px; color: var(--color-text-muted); }

/* Templates */
.vd-templates-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--spacing-sm); }
.vd-tpl-card { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--border-radius-sm); padding: var(--spacing-sm); transition: var(--transition); }
.vd-tpl-card:hover { box-shadow: 0 4px 12px var(--color-shadow); }
.vd-tpl-title { font-size: 15px; font-weight: 600; margin: 0 0 var(--spacing-xs); }
.vd-tpl-text { font-size: 13px; color: var(--color-text-light); line-height: 1.5; margin-bottom: var(--spacing-xs); max-height: 120px; overflow: hidden; }
.vd-tpl-copy { padding: 5px 12px; background: var(--color-surface-darker); border: 1px solid var(--color-border); border-radius: var(--border-radius-pill); font-size: 12px; cursor: pointer; transition: var(--transition); color: var(--color-text); font-family: inherit; }
.vd-tpl-copy:hover { background: var(--color-primary-soft); border-color: var(--color-primary); }

/* States */
.vd-state { text-align: center; padding: 48px; background: var(--color-surface); border-radius: var(--border-radius); border: 1px solid var(--color-border); }
.vd-state-icon { font-size: 48px; display: block; margin-bottom: var(--spacing-sm); }
.vd-mini-state { text-align: center; padding: var(--spacing); color: var(--color-text-muted); }

/* Confirm */
.vd-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 9000; }
.vd-confirm { background: var(--color-surface); border-radius: var(--border-radius); max-width: 420px; width: 90%; padding: var(--spacing); text-align: center; box-shadow: 0 24px 60px rgba(18,78,115,.2); }
.vd-confirm-icon { font-size: 40px; margin-bottom: 12px; }
.vd-confirm h3 { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
.vd-confirm p { color: var(--color-text-light); font-size: 14px; margin-bottom: var(--spacing); }
.vd-confirm-btns { display: flex; gap: 12px; justify-content: center; }
.btn-danger { background: #ef4444; color: white; }

.fade-enter-active, .fade-leave-active { transition: opacity .2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@media (max-width: 768px) {
  .vd-stats-grid { grid-template-columns: repeat(2, 1fr); }
  .vd-header { flex-direction: column; }
  .vd-tabs { overflow-x: auto; }
  .vd-templates-grid { grid-template-columns: 1fr; }
}
</style>
