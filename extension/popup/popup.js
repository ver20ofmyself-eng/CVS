let api;
const KEYS = {
  LAST_VACANCY: 'cvs_last_vacancy',
  REMEMBER_ME: 'cvs_remember_me',
  SAVED_EMAIL: 'cvs_saved_email',
};
// Base URL — поменять при деплое на сервер
const APP_BASE_URL = 'http://localhost:3004';

document.addEventListener('DOMContentLoaded', async () => {
  if (typeof ApiClient === 'undefined') {
    document.body.innerHTML = '<div style="padding:20px;color:#991b1b;">Ошибка: API не загружен</div>';
    return;
  }

  api = new ApiClient('http://localhost:8000');

  const $ = (id) => document.getElementById(id);
  const authSection = $('auth-section');
  const mainSection = $('main-section');
  const loadingDiv  = $('loading');
  const loginBtn    = $('login-btn');
  const logoutBtn   = $('logout-btn');
  const emailInput  = $('email');
  const passwordInput = $('password');
  const rememberMe  = $('remember-me');
  const loginError  = $('login-error');
  const vacSelect   = $('vacancy-select');
  const refreshBtn  = $('refresh-btn');
  const analyzeBtn  = $('analyze-btn');

  // Восстанавливаем "Запомнить меня"
  const saved = await chrome.storage.local.get([KEYS.REMEMBER_ME, KEYS.SAVED_EMAIL]);
  if (saved[KEYS.REMEMBER_ME]) {
    rememberMe.checked = true;
    if (saved[KEYS.SAVED_EMAIL]) emailInput.value = saved[KEYS.SAVED_EMAIL];
  }

  await api.loadToken();
  if (api.token) {
    showMain();
  } else {
    showAuth();
  }

  // === Login ===
  loginBtn.addEventListener('click', async () => {
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    if (!email || !password) { loginError.textContent = 'Введите email и пароль'; return; }

    try {
      showLoading();
      loginError.textContent = '';
      const data = await api.login(email, password);
      await chrome.storage.local.set({ authToken: data.access_token, userEmail: email });

      // Запомнить меня
      if (rememberMe.checked) {
        await chrome.storage.local.set({ [KEYS.REMEMBER_ME]: true, [KEYS.SAVED_EMAIL]: email });
      } else {
        await chrome.storage.local.remove([KEYS.REMEMBER_ME, KEYS.SAVED_EMAIL]);
      }

      showMain();
      notifyContentScript('TOKEN_UPDATED');
    } catch {
      loginError.textContent = 'Ошибка входа. Проверьте данные.';
    } finally { hideLoading(); }
  });

  // Enter to login
  passwordInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') loginBtn.click(); });

  // === Logout ===
  logoutBtn.addEventListener('click', async () => {
    await chrome.storage.local.remove(['authToken', 'userEmail', KEYS.LAST_VACANCY]);
    api.token = null;
    showAuth();
    notifyContentScript('TOKEN_UPDATED');
  });

  // === Vacancy select ===
  vacSelect.addEventListener('change', async () => {
    analyzeBtn.disabled = !vacSelect.value;
    if (vacSelect.value) {
      await chrome.storage.local.set({ [KEYS.LAST_VACANCY]: vacSelect.value });
      notifyContentScript('VACANCY_SELECTED', { vacancyId: vacSelect.value });
    }
  });

  refreshBtn.addEventListener('click', () => loadVacancies());

  // === Analyze ===
  analyzeBtn.addEventListener('click', async () => {
    if (!vacSelect.value) return;
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      chrome.tabs.sendMessage(tab.id, { type: 'ANALYZE', vacancyId: vacSelect.value });
      window.close();
    }
  });

  // === Helpers ===
  function showAuth() { authSection.style.display = 'block'; mainSection.style.display = 'none'; }

  async function showMain() {
    authSection.style.display = 'none';
    mainSection.style.display = 'block';
    await Promise.all([loadUserInfo(), loadVacancies(), loadRecentAnalyses()]);
  }

  function showLoading() { loadingDiv.style.display = 'flex'; loginBtn.disabled = true; }
  function hideLoading() { loadingDiv.style.display = 'none'; loginBtn.disabled = false; }

  async function loadUserInfo() {
    try {
      const data = await api.request('/api/tariffs/my');
      $('analyses-badge').textContent = `⚡ ${data.analyses_left || 0}`;
      await chrome.storage.local.set({ analyses_left: data.analyses_left || 0 });
      const st = await chrome.storage.local.get(['userEmail']);
      if (st.userEmail) $('user-email').textContent = st.userEmail;
    } catch { $('analyses-badge').textContent = '⚡ ?'; }
  }

  async function loadVacancies() {
    try {
      vacSelect.innerHTML = '<option value="">Загрузка...</option>';
      vacSelect.disabled = true;
      const data = await api.getVacancies();
      vacSelect.innerHTML = '<option value="">Выберите вакансию...</option>';
      if (data.items?.length) {
        data.items.forEach(v => {
          const opt = document.createElement('option');
          opt.value = v.id;
          // Без "(любая)" — только название + локация если есть
          opt.textContent = v.location ? `${v.title} · ${v.location}` : v.title;
          vacSelect.appendChild(opt);
        });
        const saved = await chrome.storage.local.get([KEYS.LAST_VACANCY]);
        if (saved[KEYS.LAST_VACANCY]) vacSelect.value = saved[KEYS.LAST_VACANCY];
        vacSelect.disabled = false;
        analyzeBtn.disabled = !vacSelect.value;
      } else {
        vacSelect.innerHTML = '<option value="">Нет вакансий</option>';
      }
    } catch {
      vacSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
    }
  }

  async function loadRecentAnalyses() {
    try {
      const data = await api.request('/api/analyze/history?limit=5');
      const section = $('recent-section');
      const list = $('recent-list');
      if (!data?.length) { section.style.display = 'none'; return; }
      section.style.display = 'block';
      list.innerHTML = '';
      data.slice(0, 5).forEach(a => {
        const item = document.createElement('a');
        item.className = 'recent-item';
        item.href = `${APP_BASE_URL}/history/${a.id}`;
        item.target = '_blank';
        item.innerHTML = `
          <span class="recent-name">${a.analysis_title || ('Анализ #' + a.id)}</span>
          <span class="recent-score ${a.score >= 85 ? 'sc-high' : a.score >= 50 ? 'sc-mid' : 'sc-low'}">${a.score || 0}%</span>
        `;
        list.appendChild(item);
      });
    } catch { /* silent */ }
  }

  async function notifyContentScript(type, extra = {}) {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab) chrome.tabs.sendMessage(tab.id, { type, ...extra }).catch(() => {});
    } catch {}
  }
});
