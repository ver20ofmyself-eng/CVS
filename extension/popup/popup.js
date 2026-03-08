// Глобальная переменная для API
let api;
const STORAGE_KEYS = {
    AUTO_ANALYZE: 'cvs_auto_analyze',
    SHOW_NOTIFICATIONS: 'cvs_show_notifications',
    LAST_VACANCY: 'cvs_last_vacancy'
};

document.addEventListener('DOMContentLoaded', async () => {
    console.log('📢 Popup загружен');

    if (typeof ApiClient === 'undefined') {
        console.error('❌ ApiClient не загружен!');
        document.body.innerHTML = '<div style="padding: 20px; color: #e8cfcf;">Ошибка: API не загружен</div>';
        return;
    }

    api = new ApiClient('http://localhost:8000');

    // Элементы DOM
    const unauthorizedDiv = document.getElementById('unauthorized');
    const authorizedDiv = document.getElementById('authorized');
    const loadingDiv = document.getElementById('loading');
    const loginBtn = document.getElementById('login-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const loginError = document.getElementById('login-error');
    const vacancySelect = document.getElementById('vacancy-select');
    const autoAnalyzeCheck = document.getElementById('auto-analyze');
    const showNotificationsCheck = document.getElementById('show-notifications');
    const analyzeBtn = document.getElementById('analyze-current');

    // Загружаем сохранённые настройки
    await loadSettings();

    // Загружаем токен
    await api.loadToken();

    if (api.token) {
        console.log('✅ Токен есть, показываем авторизованный интерфейс');
        unauthorizedDiv.style.display = 'none';
        authorizedDiv.style.display = 'block';
        await loadUserInfo();
        await loadVacancies();
        await updateStats();
    } else {
        console.log('⏳ Токена нет, показываем форму входа');
        unauthorizedDiv.style.display = 'block';
        authorizedDiv.style.display = 'none';
    }

    // Загрузка настроек
    async function loadSettings() {
        const items = await chrome.storage.local.get([STORAGE_KEYS.AUTO_ANALYZE, STORAGE_KEYS.SHOW_NOTIFICATIONS]);
        if (autoAnalyzeCheck) autoAnalyzeCheck.checked = items[STORAGE_KEYS.AUTO_ANALYZE] || false;
        if (showNotificationsCheck) showNotificationsCheck.checked = items[STORAGE_KEYS.SHOW_NOTIFICATIONS] || false;
    }

    // Сохранение настроек
    async function saveSettings() {
        await chrome.storage.local.set({
            [STORAGE_KEYS.AUTO_ANALYZE]: autoAnalyzeCheck?.checked || false,
            [STORAGE_KEYS.SHOW_NOTIFICATIONS]: showNotificationsCheck?.checked || false
        });
    }

    // Обработчики изменения настроек
    if (autoAnalyzeCheck) autoAnalyzeCheck.addEventListener('change', saveSettings);
    if (showNotificationsCheck) showNotificationsCheck.addEventListener('change', saveSettings);

    // Сохранение выбранной вакансии
    vacancySelect.addEventListener('change', async () => {
        const selectedId = vacancySelect.value;
        if (selectedId) {
            await chrome.storage.local.set({ [STORAGE_KEYS.LAST_VACANCY]: selectedId });

            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tab) {
                chrome.tabs.sendMessage(tab.id, {
                    type: 'VACANCY_SELECTED',
                    vacancyId: selectedId
                }).catch(() => { });
            }
        }
    });

    // Обработчик входа
    loginBtn.addEventListener('click', async () => {
        const email = emailInput.value;
        const password = passwordInput.value;

        if (!email || !password) {
            loginError.textContent = 'Введите email и пароль';
            return;
        }

        try {
            showLoading();
            loginError.textContent = '';

            const data = await api.login(email, password);

            await chrome.storage.local.set({
                authToken: data.access_token,
                userEmail: email
            });

            unauthorizedDiv.style.display = 'none';
            authorizedDiv.style.display = 'block';

            document.getElementById('user-email').textContent = email;
            await loadUserInfo();
            await loadVacancies();
            await updateStats();

            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tab) {
                chrome.tabs.sendMessage(tab.id, { type: 'TOKEN_UPDATED' }).catch(() => { });
            }

        } catch (error) {
            console.error('❌ Ошибка входа:', error);
            loginError.textContent = 'Ошибка входа. Проверьте данные.';
        } finally {
            hideLoading();
        }
    });

    // Выход
    logoutBtn.addEventListener('click', async () => {
        await chrome.storage.local.remove(['authToken', 'userEmail', STORAGE_KEYS.LAST_VACANCY]);
        api.token = null;
        unauthorizedDiv.style.display = 'block';
        authorizedDiv.style.display = 'none';

        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tab) {
            chrome.tabs.sendMessage(tab.id, { type: 'TOKEN_UPDATED' }).catch(() => { });
        }
    });

    // Анализ текущей страницы
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', async () => {
            const vacancyId = vacancySelect.value;
            if (!vacancyId) {
                alert('Выберите вакансию');
                return;
            }

            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tab) {
                chrome.tabs.sendMessage(tab.id, {
                    type: 'ANALYZE',
                    vacancyId: vacancyId
                });
                window.close();
            }
        });
    }

    async function loadUserInfo() {
        try {
            if (!api.token) return;

            const data = await api.request('/api/tariffs/my');
            const analysesLeft = data.analyses_left || 0;

            document.getElementById('analyses-left').textContent = `осталось: ${analysesLeft}`;

            // Сохраняем в storage для доступа из content script
            await chrome.storage.local.set({ analyses_left: analysesLeft });

            const storage = await chrome.storage.local.get(['userEmail']);
            if (storage.userEmail) {
                document.getElementById('user-email').textContent = storage.userEmail;
            }
        } catch (error) {
            console.error('❌ Ошибка загрузки информации:', error);
            document.getElementById('analyses-left').textContent = 'осталось: ?';
        }
    }

    async function loadVacancies() {
        try {
            vacancySelect.innerHTML = '<option value="">Загрузка...</option>';
            vacancySelect.disabled = true;

            const data = await api.getVacancies();

            vacancySelect.innerHTML = '<option value="">Выберите вакансию...</option>';

            if (data.items && data.items.length > 0) {
                data.items.forEach(vacancy => {
                    const option = document.createElement('option');
                    option.value = vacancy.id;
                    option.textContent = `${vacancy.title} (${vacancy.location || 'любая'})`;
                    vacancySelect.appendChild(option);
                });

                const storage = await chrome.storage.local.get([STORAGE_KEYS.LAST_VACANCY]);
                if (storage[STORAGE_KEYS.LAST_VACANCY]) {
                    vacancySelect.value = storage[STORAGE_KEYS.LAST_VACANCY];
                }

                vacancySelect.disabled = false;
            } else {
                vacancySelect.innerHTML = '<option value="">Нет вакансий</option>';
            }

        } catch (error) {
            console.error('❌ Ошибка загрузки вакансий:', error);
            vacancySelect.innerHTML = '<option value="">Ошибка загрузки</option>';
        }
    }

    async function updateStats() {
        try {
            if (!api.token) {
                document.getElementById('today-analyses').textContent = '0';
                document.getElementById('cached-analyses').textContent = '0';
                return;
            }

            const history = await api.request('/api/analyze/history?limit=100');

            const today = new Date().toDateString();
            const todayAnalyses = history.filter(a =>
                new Date(a.created_at).toDateString() === today
            ).length;

            document.getElementById('today-analyses').textContent = todayAnalyses;

            const items = await chrome.storage.local.get(null);
            const cachedCount = Object.keys(items).filter(key =>
                key.startsWith('cvs_analysis_')
            ).length;

            document.getElementById('cached-analyses').textContent = cachedCount;

        } catch (error) {
            console.error('Ошибка загрузки статистики:', error);
            document.getElementById('today-analyses').textContent = '?';
            document.getElementById('cached-analyses').textContent = '?';
        }
    }

    function showLoading() {
        loadingDiv.style.display = 'flex';
        if (loginBtn) loginBtn.disabled = true;
    }

    function hideLoading() {
        loadingDiv.style.display = 'none';
        if (loginBtn) loginBtn.disabled = false;
    }
});
