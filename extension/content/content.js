/**
 * Основной content-скрипт
 * Внедряет интерфейс анализа на страницу
 */
// ========== ДИАГНОСТИКА ЗАГРУЗКИ ==========
console.log('🔥 content.js загружен');
console.log('URL:', window.location.href);
console.log('Pathname:', window.location.pathname);

// Проверяем глобальные объекты
setTimeout(() => {
    console.log('📊 Диагностика после загрузки:');
    console.log('  window.apiClient:', window.apiClient ? '✅' : '❌');
    console.log('  window.hhParser:', window.hhParser ? '✅' : '❌');
    console.log('  window.analysisCache:', window.analysisCache ? '✅' : '❌');

    if (window.apiClient) {
        console.log('  apiClient методы:', Object.keys(window.apiClient));
    }
}, 1000);
// ========== КОНЕЦ ДИАГНОСТИКИ ==========

/**
 * Основной content-скрипт
 * Внедряет интерфейс анализа на страницу
 */
class ContentInjector {
    constructor() {
        this.parser = window.hhParser;
        this.api = window.apiClient;
        this.cache = window.analysisCache;
        this.resultBlock = null;
        this.isAnalyzing = false;

        // Параметры для повторных попыток внедрения
        this.injectionAttempts = 0;
        this.maxInjectionAttempts = 20;
        this.injectionInterval = 300;
        this.observer = null;
        this.injectionTimer = null;

        // Флаги
        this.isInjected = false;
        this.injectionStarted = false;
        this.isDestroyed = false; // Флаг для очистки

        // Кэш для последней активности
        this.lastActivity = Date.now();

        // Параметры для адаптивности
        this.lastWindowWidth = window.innerWidth;
        this.resizeTimeout = null;
        this.visibilityCheckInterval = null;

        // Привязываем методы
        this.handleResize = this.handleResize.bind(this);
        this.handleMessage = this.handleMessage.bind(this);
        this.handleTokenChange = this.handleTokenChange.bind(this);

        // Оптимизированные версии
        this.optimizedResize = this.debounce(this.handleResize, 250);
        this.optimizedScroll = this.throttle(() => {
            this.lastActivity = Date.now();
        }, 1000);

        // Слушаем изменения в хранилище
        chrome.storage.onChanged.addListener((changes, area) => {
            if (area === 'local' && changes.authToken) {
                this.handleTokenChange(changes.authToken.newValue);
            }
        });

        // Слушаем изменение размера окна (оптимизировано)
        window.addEventListener('resize', this.optimizedResize);

        // Слушаем скролл для определения активности (оптимизировано)
        window.addEventListener('scroll', this.optimizedScroll, { passive: true });

        // Единственный обработчик сообщений
        chrome.runtime.onMessage.addListener(this.handleMessage);
    }

    /**
     * Дебаунс функция для ограничения частоты вызовов
     */
    debounce(func, wait) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    /**
     * Троттлинг функция для ограничения частоты вызовов
     */
    throttle(func, limit) {
        let inThrottle;
        return (...args) => {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * Обработка сообщений от background/popup
     */
    handleMessage(message) {
        console.log('📢 Сообщение получено в content.js:', message.type);

        switch (message.type) {
            case 'TOKEN_UPDATED':
                this.handleTokenUpdate();
                break;
            case 'VACANCY_SELECTED':
                this.handleVacancySelected(message.vacancyId);
                break;
            case 'REFRESH_VACANCIES':
                this.loadVacancies();
                break;
            case 'ANALYZE':
                this.analyze();
                break;
        }
    }

    /**
     * Обработка изменения токена
     */
    handleTokenChange(newToken) {
        console.log('📢 Токен изменился:', newToken ? 'установлен' : 'удалён');

        if (this.api) {
            this.api.token = newToken;

            if (newToken && this.vacancySelect) {
                this.loadVacancies();
                if (this.vacancySelect.value) {
                    this.analyzeBtn.disabled = false;
                }
            } else if (!newToken && this.vacancySelect) {
                this.showAuthRequired();
            }
        }
    }

    /**
     * Обработка обновления токена
     */
    async handleTokenUpdate() {
        console.log('📢 Обновляем данные после логина');
        await this.api.loadToken();

        if (this.vacancySelect) {
            this.loadVacancies();
        }
    }

    /**
     * Обработка выбора вакансии из popup
     */
    handleVacancySelected(vacancyId) {
        console.log('📢 Выбрана вакансия из popup:', vacancyId);

        if (this.vacancySelect) {
            this.vacancySelect.value = vacancyId;
            this.analyzeBtn.disabled = false;
            this.checkCache();
        }
    }

    /**
     * Показывает сообщение о необходимости авторизации
     */
    showAuthRequired() {
        if (this.vacancySelect) {
            this.vacancySelect.innerHTML = '<option value="">Войдите для загрузки вакансий</option>';
            this.vacancySelect.disabled = true;
        }
        if (this.analyzeBtn) {
            this.analyzeBtn.disabled = true;
        }
    }

    /**
     * Инициализация
     */
    async init() {
        console.log('📢 CVS Analyzer: init() вызван', {
            url: window.location.href,
            readyState: document.readyState
        });

        // Проверяем парсер
        if (!this.parser) {
            console.error('❌ Парсер не загружен');
            return;
        }

        // Проверяем, что это страница резюме
        if (!this.parser.isResumePage || !this.parser.isResumePage()) {
            console.log('⏩ Не страница резюме, выходим');
            return;
        }

        console.log('✅ Это страница резюме, начинаем попытки внедрения');

        // Загружаем токен
        if (this.api && this.api.loadToken) {
            await this.api.loadToken();
            console.log('📢 Токен загружен:', this.api.token ? 'есть' : 'нет');
        }

        // Запускаем процесс внедрения
        this.startInjectionProcess();
    }

    /**
     * Запуск процесса внедрения
     */
    startInjectionProcess() {
        if (this.injectionStarted) return;
        this.injectionStarted = true;

        // Сначала пробуем немедленно
        setTimeout(() => {
            if (this.tryInject()) {
                return;
            }

            console.log('⏳ Контент ещё не загружен, начинаем наблюдение...');

            // Запускаем интервал для периодических проверок
            this.startInjectionInterval();

            // Также запускаем MutationObserver для более точного отслеживания
            this.startMutationObserver();
        }, 100);
    }

    /**
     * Запускает интервал для периодических проверок
     */
    startInjectionInterval() {
        if (this.injectionTimer) {
            clearInterval(this.injectionTimer);
        }

        this.injectionTimer = setInterval(() => {
            this.injectionAttempts++;

            console.log(`⏳ Попытка внедрения #${this.injectionAttempts}`);

            if (this.tryInject() || this.injectionAttempts >= this.maxInjectionAttempts) {
                clearInterval(this.injectionTimer);
                this.injectionTimer = null;

                if (this.injectionAttempts >= this.maxInjectionAttempts) {
                    console.warn('⚠️ Достигнут лимит попыток внедрения');
                }
            }
        }, this.injectionInterval);
    }

    /**
     * Запускает MutationObserver для отслеживания изменений DOM
     */
    startMutationObserver() {
        if (this.observer) {
            this.observer.disconnect();
        }

        this.observer = new MutationObserver((mutations) => {
            // Проверяем, появились ли нужные элементы
            const mainContent = this.findMainContent();

            if (mainContent && !this.isInjected) {
                console.log('✅ MutationObserver: найден контент, внедряем');
                this.tryInject();

                // Если внедрение успешно, отключаем наблюдатель
                if (this.isInjected) {
                    this.observer.disconnect();
                    this.observer = null;

                    if (this.injectionTimer) {
                        clearInterval(this.injectionTimer);
                        this.injectionTimer = null;
                    }
                }
            }
        });

        // Наблюдаем за изменениями во всём документе
        this.observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: false,
            characterData: false
        });

        console.log('👀 MutationObserver запущен');
    }

    /**
     * Пытается найти основной контент страницы
     */
    findMainContent() {
        // Пробуем разные селекторы для определения загрузки страницы
        const selectors = [
            '[data-qa="resume-personal-name"]',
            '.resume-wrapper',
            '[data-qa="resume"]',
            '.magritte-card___bhGKz_8-3-0',
            '.content-wrapper--S2N8DTJvpz43RS4t',
            'main'
        ];

        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element) {
                return element;
            }
        }

        return null;
    }

    /**
     * Проверяет, полностью ли загружено резюме
     */
    isResumeFullyLoaded() {
        // Проверяем наличие имени кандидата
        const nameElement = document.querySelector('[data-qa="resume-personal-name"]');
        if (!nameElement || !nameElement.textContent.trim()) {
            return false;
        }

        // Проверяем наличие хотя бы одного блока с опытом или навыками
        const hasContent =
            document.querySelector('[data-qa="resume-block-experience"]') ||
            document.querySelector('[data-qa="skills-table"]') ||
            document.querySelector('[data-qa="resume-block-education"]');

        return !!hasContent;
    }

    /**
     * Пытается внедрить интерфейс
     */
    tryInject() {
        // Если уже внедрён, не делаем повторно
        if (this.isInjected) {
            return true;
        }

        // Проверяем, загрузилась ли страница достаточно
        const mainContent = this.findMainContent();

        if (!mainContent) {
            console.log('⏳ Основной контент ещё не загружен');
            return false;
        }

        // Дополнительная проверка: полностью ли загружено резюме
        if (!this.isResumeFullyLoaded()) {
            console.log('⏳ Резюме ещё не полностью загружено');
            return false;
        }

        console.log('✅ Контент найден, внедряем интерфейс');
        this.injectAnalysisBlock();

        this.isInjected = true;
        return true;
    }

    /**
     * Внедряет блок анализа на страницу
     */
    injectAnalysisBlock() {
        console.log('📢 injectAnalysisBlock: ищем место для вставки');

        // Проверяем, не внедрён ли уже блок
        if (document.getElementById('cvs-analyzer-container')) {
            console.log('⚠️ Блок уже существует, обновляем ссылки');
            this.updateElementReferences();
            this.isInjected = true;
            return;
        }

        // Создаём контейнер для нашего интерфейса
        const container = document.createElement('div');
        container.id = 'cvs-analyzer-container';
        container.innerHTML = this.getHTML();

        // Ищем идеальное место для вставки
        const insertAfterElement = this.findInsertPosition();

        if (insertAfterElement && insertAfterElement.parentNode) {
            insertAfterElement.parentNode.insertBefore(container, insertAfterElement.nextSibling);
            console.log('✅ Интерфейс внедрён после найденного элемента');
        } else {
            // Запасной вариант - вставляем в начало body
            document.body.insertBefore(container, document.body.firstChild);
            console.log('⚠️ Использован запасной вариант вставки');
        }

        // Сохраняем ссылки на элементы
        this.updateElementReferences();

        // Проверяем авторизацию и загружаем вакансии
        setTimeout(() => this.initializeAfterInjection(), 100);
    }

    /**
     * Находит позицию для вставки
     */
    findInsertPosition() {
        // Приоритетные цели для вставки
        const targets = [
            document.querySelector('.tags--ps9ZeYs98SQzTcNn'),
            document.querySelector('[data-qa="resume-personal-name"]')?.closest('.magritte-card___bhGKz_8-3-0'),
            document.querySelector('.resume-wrapper'),
            document.querySelector('[data-qa="resume"]'),
            document.querySelector('main')
        ];

        for (const target of targets) {
            if (target) {
                return target;
            }
        }

        return null;
    }

    /**
     * Обновляет ссылки на элементы интерфейса
     */
    updateElementReferences() {
        this.resultBlock = document.getElementById('cvs-result');
        this.analyzeBtn = document.getElementById('cvs-analyze-btn');
        this.vacancySelect = document.getElementById('cvs-vacancy-select');
        this.refreshBtn = document.getElementById('cvs-refresh-vacancies');

        // Добавляем обработчики событий
        this.attachEventListeners();
    }

    /**
     * Добавляет обработчики событий
     */
    attachEventListeners() {
        if (this.analyzeBtn) {
            // Удаляем старый обработчик, если был
            const newAnalyzeBtn = this.analyzeBtn.cloneNode(true);
            this.analyzeBtn.parentNode.replaceChild(newAnalyzeBtn, this.analyzeBtn);
            this.analyzeBtn = newAnalyzeBtn;

            this.analyzeBtn.addEventListener('click', () => this.analyze());
        }

        if (this.refreshBtn) {
            const newRefreshBtn = this.refreshBtn.cloneNode(true);
            this.refreshBtn.parentNode.replaceChild(newRefreshBtn, this.refreshBtn);
            this.refreshBtn = newRefreshBtn;

            this.refreshBtn.addEventListener('click', () => this.loadVacancies());
        }

        // Добавляем обработчик изменения select
        if (this.vacancySelect) {
            const newSelect = this.vacancySelect.cloneNode(true);
            this.vacancySelect.parentNode.replaceChild(newSelect, this.vacancySelect);
            this.vacancySelect = newSelect;

            this.vacancySelect.addEventListener('change', (e) => this.handleVacancyChange(e));
        }

        // Добавляем обработчик горячих клавиш
        document.addEventListener('keydown', (e) => this.handleHotkeys(e));
    }

    /**
     * Обработка изменения выбранной вакансии
     */
    async handleVacancyChange(e) {
        try {
            this.analyzeBtn.disabled = true;

            if (e.target.value) {
                this.showLoading('Проверка кэша...');
                await this.checkCache();
                await chrome.storage.local.set({ cvs_last_vacancy: e.target.value });
                this.analyzeBtn.disabled = false;
            }
        } catch (error) {
            console.error('❌ Ошибка при выборе вакансии:', error);
            this.showError('Ошибка при выборе вакансии');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Обработка горячих клавиш
     */
    handleHotkeys(e) {
        // Ctrl/Cmd + Enter - запуск анализа
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            if (this.vacancySelect?.value && this.analyzeBtn && !this.analyzeBtn.disabled) {
                e.preventDefault();
                console.log('📢 Запуск анализа по горячей клавише');
                this.analyze();
            }
        }

        // Ctrl/Cmd + R - обновить список вакансий (без перезагрузки страницы)
        if ((e.ctrlKey || e.metaKey) && e.key === 'r' && !e.shiftKey) {
            // Только если фокус не на поле ввода
            if (!['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
                e.preventDefault();
                console.log('📢 Обновление списка вакансий');
                this.loadVacancies();
            }
        }

        // Ctrl/Cmd + Shift + C - очистить кэш для текущей страницы
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'C') {
            e.preventDefault();
            console.log('📢 Очистка кэша для текущей страницы');
            this.cache.clearForCurrentPage(window.location.href);
            this.clearResult();
            this.showNotification('🧹 Кэш очищен');
        }

        // Escape - скрыть результат (если показан)
        if (e.key === 'Escape' && this.resultBlock?.style.display === 'block') {
            this.clearResult();
        }

        // Ctrl+Shift+D - диагностика
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
            e.preventDefault();
            this.showDiagnostics();
        }
    }

    /**
 * Показывает уведомление (временное)
 */
    showNotification(message, type = 'info') {
        // Удаляем старое уведомление если есть
        const oldNotification = document.querySelector('.cvs-notification');
        if (oldNotification) oldNotification.remove();

        const notification = document.createElement('div');
        notification.className = `cvs-notification cvs-notification-${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    /**
     * Инициализация после внедрения с полным восстановлением состояния
     */
    async initializeAfterInjection() {
        console.log('📢 Инициализация после внедрения');

        // Обновляем индикатор авторизации
        const authDot = document.getElementById('cvs-auth-dot');
        if (authDot) {
            authDot.className = `cvs-auth-dot ${this.api?.token ? 'online' : 'offline'}`;
        }

        if (this.api && this.api.token) {
            console.log('📢 Пользователь авторизован, загружаем вакансии');
            await this.loadVacancies();

            // Восстанавливаем все сохранённые состояния
            await this.restoreAllState();

            // Запускаем периодическую проверку видимости
            this.startVisibilityChecks();
        } else {
            console.log('⏳ Пользователь не авторизован');
            this.showAuthRequired();
        }

        // Применяем адаптивные стили
        this.applyResponsiveStyles();
    }

    /**
     * Восстановление всего состояния
     */
    async restoreAllState() {
        try {
            // Загружаем все сохранённые данные
            const storage = await chrome.storage.local.get([
                'cvs_last_vacancy',
                'cvs_last_result_hash',
                'cvs_settings'
            ]);

            // Восстанавливаем настройки
            if (storage.cvs_settings) {
                console.log('📢 Настройки восстановлены:', storage.cvs_settings);
            }

            // Восстанавливаем последнюю вакансию
            if (storage.cvs_last_vacancy && this.vacancySelect) {
                await this.restoreLastVacancy();
            }

            // Пробуем восстановить результат из sessionStorage
            if (!this.restoreFromSession()) {
                // Если не получилось, пробуем из кэша по сохранённому хэшу
                if (storage.cvs_last_result_hash && this.vacancySelect?.value) {
                    const cached = await this.cache.getByHash(storage.cvs_last_result_hash);
                    if (cached) {
                        console.log('📢 Восстанавливаем результат по хэшу');
                        this.displayResult(cached.result, true);
                    }
                } else {
                    // Обычная проверка кэша
                    setTimeout(() => this.checkCache(), 500);
                }
            }

            // Если включён автоанализ, запускаем
            setTimeout(() => this.tryAutoAnalyze(), 1000);

        } catch (error) {
            console.warn('⚠️ Ошибка восстановления состояния:', error);
        }
    }

    /**
     * Сохранение состояния после анализа
     */
    async saveStateAfterAnalysis(result, isCached) {
        try {
            const analysis = result.analysis || result;

            // Сохраняем хэш последнего результата
            if (analysis._hash) {
                await chrome.storage.local.set({
                    cvs_last_result_hash: analysis._hash
                });
            }

            // Сохраняем результат в sessionStorage
            sessionStorage.setItem('cvs_last_result', JSON.stringify({
                result: result,
                isCached: isCached,
                vacancyId: this.vacancySelect?.value,
                url: window.location.href,
                timestamp: Date.now(),
                hash: analysis._hash
            }));

            // Обновляем статистику
            this.updateStats();

        } catch (e) {
            console.warn('⚠️ Не удалось сохранить состояние:', e);
        }
    }

    /**
     * Обновление статистики использования
     */
    updateStats() {
        const stats = {
            lastUsed: Date.now(),
            totalAnalyses: (parseInt(localStorage.getItem('cvs_total_analyses') || '0')) + 1,
            lastUrl: window.location.href
        };

        localStorage.setItem('cvs_total_analyses', stats.totalAnalyses.toString());
        localStorage.setItem('cvs_last_used', stats.lastUsed.toString());

        console.log('📊 Статистика обновлена:', stats);
    }

    /**
     * Восстанавливает последнюю выбранную вакансию
     */
    async restoreLastVacancy() {
        try {
            const storage = await chrome.storage.local.get(['cvs_last_vacancy']);

            if (storage.cvs_last_vacancy && this.vacancySelect) {
                // Проверяем, существует ли такая вакансия в списке
                const exists = Array.from(this.vacancySelect.options)
                    .some(opt => opt.value === storage.cvs_last_vacancy);

                if (exists) {
                    console.log('📢 Восстанавливаем последнюю вакансию:', storage.cvs_last_vacancy);
                    this.vacancySelect.value = storage.cvs_last_vacancy;
                    this.analyzeBtn.disabled = false;

                    // Проверяем кэш для этой вакансии
                    setTimeout(() => this.checkCache(), 100);
                }
            }
        } catch (error) {
            console.warn('⚠️ Ошибка при восстановлении вакансии:', error);
        }
    }

    /**
     * HTML для внедряемого блока
     */
    getHTML() {
        return `
      <div class="cvs-analyzer-widget">
        <div class="cvs-header">
          <div class="cvs-title">
            <span class="cvs-icon">🔍</span>
            <h3>CVS Analyzer</h3>
          </div>
          <div class="cvs-status" id="cvs-auth-status">
            <span class="cvs-auth-dot" id="cvs-auth-dot"></span>
          </div>
        </div>
        
        <div class="cvs-controls-panel">
          <div class="cvs-select-wrapper">
            <select id="cvs-vacancy-select" class="cvs-select">
              <option value="">Выберите вакансию...</option>
            </select>
            <button id="cvs-refresh-vacancies" class="cvs-icon-btn" title="Обновить список">🔄</button>
          </div>

          <button id="cvs-analyze-btn" class="cvs-analyze-btn" disabled>
            <span class="btn-icon">⚡</span>
            <span class="btn-text">Анализировать резюме</span>
          </button>
        </div>

        <!-- Улучшенный индикатор загрузки с прогрессом -->
        <div id="cvs-loading" class="cvs-loading" style="display: none;">
          <div class="cvs-progress-container">
            <div class="cvs-progress-bar" id="cvs-progress-bar"></div>
          </div>
          <div class="cvs-loading-content">
            <div class="cvs-spinner"></div>
            <span id="cvs-loading-message">Анализируем резюме...</span>
          </div>
          <div class="cvs-progress-steps">
            <span class="cvs-step" data-step="1">📄 Загрузка</span>
            <span class="cvs-step" data-step="2">🤖 Анализ AI</span>
            <span class="cvs-step" data-step="3">📊 Обработка</span>
          </div>
        </div>

        <div id="cvs-result" class="cvs-result" style="display: none;">
          <div class="cvs-result-header">
            <div class="cvs-score-container">
              <span class="cvs-score-label">Оценка</span>
              <span class="cvs-score-badge"></span>
            </div>
            <span class="cvs-recommendation"></span>
          </div>
          
          <div class="cvs-skills-section">
            <div class="cvs-matched-skills">
              <div class="section-title">
                <span class="title-icon">✅</span>
                <h4>Совпавшие навыки</h4>
              </div>
              <div class="cvs-skills-list"></div>
            </div>
            
            <div class="cvs-missing-skills">
              <div class="section-title">
                <span class="title-icon">⚠️</span>
                <h4>Отсутствуют</h4>
              </div>
              <div class="cvs-skills-list"></div>
            </div>
          </div>

          <div class="cvs-details">
            <div class="cvs-strengths">
              <div class="section-title">
                <span class="title-icon">💪</span>
                <h4>Сильные стороны</h4>
              </div>
              <ul class="cvs-strengths-list"></ul>
            </div>
            
            <div class="cvs-weaknesses">
              <div class="section-title">
                <span class="title-icon">📉</span>
                <h4>Риски</h4>
              </div>
              <ul class="cvs-weaknesses-list"></ul>
            </div>
          </div>

          <div class="cvs-footer">
            <div class="cvs-metadata">
              <span class="cvs-mode"></span>
              <span class="cvs-timestamp"></span>
            </div>
            <div class="cvs-actions">
              <button id="cvs-update-btn" class="cvs-update-btn" title="Запустить новый анализ">🔄 Новый анализ</button>
              <a id="cvs-site-link" class="cvs-site-link" href="#" target="_blank" title="Открыть на сайте">🔗 На сайте</a>
            </div>
          </div>
        </div>

        <div id="cvs-error" class="cvs-error" style="display: none;"></div>
      </div>
    `;
    }

    /**
     * Загружает список вакансий пользователя
     */
    async loadVacancies() {
        try {
            // ПРОВЕРКА: убеждаемся что элементы существуют
            if (!this.vacancySelect || !this.analyzeBtn) {
                console.error('❌ Элементы интерфейса не найдены (select или кнопка анализа)');
                // Пробуем найти элементы заново
                this.vacancySelect = document.getElementById('cvs-vacancy-select');
                this.analyzeBtn = document.getElementById('cvs-analyze-btn');

                if (!this.vacancySelect || !this.analyzeBtn) {
                    console.error('❌ Не удалось восстановить элементы интерфейса');
                    this.showError('Ошибка интерфейса. Обновите страницу.');
                    return;
                }
            }

            this.showLoading('Загрузка вакансий...', 1);

            // ПРОВЕРКА: наличие API и токена
            if (!this.api) {
                console.error('❌ API клиент не инициализирован');
                this.showError('Ошибка подключения к API');
                this.finishLoading(false);
                return;
            }

            if (!this.api.token) {
                console.log('⏳ Нет токена, загружаем...');
                await this.api.loadToken();
            }

            // ФИНАЛЬНАЯ ПРОВЕРКА токена
            if (!this.api.token) {
                console.log('⏳ Токен не загружен, показываем сообщение');
                this.showAuthRequiredMessage();
                this.finishLoading(false);
                return;
            }

            // ОСНОВНОЙ ЗАПРОС к API с retry-логикой
            console.log('📢 Запрос списка вакансий...');

            let data;
            try {
                data = await this.retry(() => this.api.getVacancies(), 3, 1000);
            } catch (retryError) {
                console.error('❌ Все попытки загрузки вакансий не удались:', retryError);
                this.showError('Не удалось загрузить вакансии после нескольких попыток. Проверьте подключение к серверу.');
                this.finishLoading(false);
                return;
            }

            const select = this.vacancySelect;

            // Очищаем и заполняем select
            select.innerHTML = '<option value="">Выберите вакансию...</option>';
            select.disabled = false;

            if (data.items && data.items.length > 0) {
                // Добавляем вакансии в выпадающий список
                data.items.forEach(vacancy => {
                    const option = document.createElement('option');
                    option.value = vacancy.id;
                    option.textContent = vacancy.location ? `${vacancy.title} · ${vacancy.location}` : vacancy.title;
                    select.appendChild(option);
                });

                // Восстанавливаем последнюю выбранную вакансию из хранилища
                await this.restoreLastVacancyFromList(select);

                // Загружаем информацию о тарифе (остаток анализов)
                await this.loadTariffInfo();

            } else {
                // Нет вакансий
                select.innerHTML = '<option value="">Нет доступных вакансий</option>';
                this.analyzeBtn.disabled = true;

                // Показываем подсказку
                this.showNotification('Создайте вакансию на сайте cvs-analyzer.ru', 'info');
            }

            // Обновляем обработчик изменения выбора вакансии
            this.setupVacancySelectHandler(select);

            this.finishLoading(true);
            console.log('✅ Вакансии успешно загружены');

        } catch (error) {
            console.error('❌ Ошибка загрузки вакансий:', error);
            this.handleLoadError(error);
        }
    }

    /**
     * Показывает сообщение о необходимости авторизации
     */
    showAuthRequiredMessage() {
        if (this.vacancySelect) {
            this.vacancySelect.innerHTML = '<option value="">🔐 Войдите в систему</option>';
            this.vacancySelect.disabled = true;
        }
        if (this.analyzeBtn) {
            this.analyzeBtn.disabled = true;
        }
        this.showError('Необходима авторизация. Откройте popup расширения и войдите.');
    }

    /**
     * Восстанавливает последнюю выбранную вакансию из списка
     */
    async restoreLastVacancyFromList(select) {
        try {
            const storage = await chrome.storage.local.get(['cvs_last_vacancy']);
            if (storage.cvs_last_vacancy) {
                const exists = Array.from(select.options).some(opt => opt.value === storage.cvs_last_vacancy);
                if (exists) {
                    select.value = storage.cvs_last_vacancy;
                    this.analyzeBtn.disabled = false;
                    console.log('📢 Восстановлена последняя вакансия:', storage.cvs_last_vacancy);

                    // Проверяем кэш для восстановленной вакансии
                    setTimeout(() => this.checkCache(), 100);
                } else {
                    console.log('⚠️ Последняя вакансия больше не доступна');
                }
            }
        } catch (storageError) {
            console.warn('⚠️ Ошибка доступа к хранилищу:', storageError);
        }
    }

    /**
     * Загружает информацию о тарифе
     */
    async loadTariffInfo() {
        try {
            const tariffInfo = await this.retry(() => this.api.request('/api/tariffs/my'), 2, 500);
            if (tariffInfo && tariffInfo.analyses_left !== undefined) {
                this.updateAnalysesLeft(tariffInfo.analyses_left);

                // Сохраняем в storage для popup
                await chrome.storage.local.set({
                    analyses_left: tariffInfo.analyses_left,
                    tariff_name: tariffInfo.tariff_name || 'Бесплатный'
                }).catch(() => { });

                // Если анализов мало, показываем предупреждение
                if (tariffInfo.analyses_left <= 5) {
                    this.showNotification(`⚠️ Осталось всего ${tariffInfo.analyses_left} анализов`, 'warning');
                }
            }
        } catch (tariffError) {
            console.log('⚠️ Не удалось загрузить информацию о тарифе:', tariffError.message);
            // Не показываем ошибку пользователю, это не критично
        }
    }

    /**
     * Настраивает обработчик выбора вакансии
     */
    setupVacancySelectHandler(select) {
        // Удаляем старый обработчик если он был
        if (this.selectChangeHandler) {
            select.removeEventListener('change', this.selectChangeHandler);
        }

        // Создаём новый обработчик
        this.selectChangeHandler = async (e) => {
            try {
                // Блокируем кнопку на время проверки
                this.analyzeBtn.disabled = true;

                if (e.target.value) {
                    this.showLoading('Проверка кэша...', 1);

                    // Проверяем кэш
                    await this.checkCache();

                    // Сохраняем выбор
                    await chrome.storage.local.set({ cvs_last_vacancy: e.target.value });

                    // Активируем кнопку
                    this.analyzeBtn.disabled = false;

                    console.log('📢 Выбрана вакансия:', e.target.value);

                    // Если включён автоанализ, запускаем
                    if (await this.shouldAutoAnalyze()) {
                        setTimeout(() => this.analyze(), 300);
                    }
                }
            } catch (error) {
                console.error('❌ Ошибка при выборе вакансии:', error);
                this.showError('Ошибка при выборе вакансии');
            } finally {
                this.finishLoading(false);
            }
        };

        // Добавляем новый обработчик
        select.addEventListener('change', this.selectChangeHandler);

        // Если вакансия уже выбрана, проверяем кэш
        if (select.value) {
            setTimeout(() => {
                if (select.value) {
                    this.checkCache().catch(e => console.log('⚠️ Ошибка проверки кэша:', e));
                }
            }, 100);
        }
    }

    /**
     * Обработка ошибок загрузки
     */
    handleLoadError(error) {
        // Обработка различных типов ошибок
        if (error.message.includes('401')) {
            this.showError('Сессия истекла. Войдите снова.');
            if (this.vacancySelect) {
                this.vacancySelect.innerHTML = '<option value="">Требуется авторизация</option>';
                this.vacancySelect.disabled = true;
            }
            if (this.analyzeBtn) {
                this.analyzeBtn.disabled = true;
            }

            // Очищаем токен
            if (this.api) {
                this.api.token = null;
            }
            chrome.storage.local.remove(['authToken', 'analyses_left']).catch(() => { });

        } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            this.showError('Сервер недоступен. Проверьте подключение к localhost:8000');

            if (this.vacancySelect) {
                this.vacancySelect.innerHTML = '<option value="">Ошибка подключения</option>';
                this.vacancySelect.disabled = true;
            }
            if (this.analyzeBtn) {
                this.analyzeBtn.disabled = true;
            }

        } else if (error.message.includes('500')) {
            this.showError('Ошибка сервера. Попробуйте позже.');

            if (this.vacancySelect) {
                this.vacancySelect.innerHTML = '<option value="">Ошибка сервера</option>';
                this.vacancySelect.disabled = true;
            }

        } else {
            this.showError('Ошибка загрузки вакансий');

            if (this.vacancySelect) {
                this.vacancySelect.innerHTML = '<option value="">Ошибка загрузки</option>';
                this.vacancySelect.disabled = true;
            }
        }

        this.hideLoading();
    }

    /**
     * Обновляет отображение остатка анализов
     */
    updateAnalysesLeft(count) {
        let analysesLeftSpan = document.getElementById('cvs-analyses-left');

        if (!analysesLeftSpan) {
            analysesLeftSpan = document.createElement('span');
            analysesLeftSpan.id = 'cvs-analyses-left';
            analysesLeftSpan.className = 'cvs-analyses-left';

            const header = document.querySelector('.cvs-header');
            if (header) {
                header.appendChild(analysesLeftSpan);
            }
        }

        analysesLeftSpan.textContent = `Осталось анализов: ${count}`;

        if (count <= 10) {
            analysesLeftSpan.style.color = 'var(--color-error)';
        } else if (count <= 30) {
            analysesLeftSpan.style.color = 'var(--color-warning)';
        } else {
            analysesLeftSpan.style.color = 'var(--color-success)';
        }
    }

    /**
     * Обработка изменения размера окна
     */
    handleResize() {
        // Используем debounce чтобы не дёргать слишком часто
        clearTimeout(this.resizeTimeout);
        this.resizeTimeout = setTimeout(() => {
            const newWidth = window.innerWidth;
            console.log('📢 Изменение размера окна:', {
                oldWidth: this.lastWindowWidth,
                newWidth: newWidth,
                diff: Math.abs(newWidth - this.lastWindowWidth)
            });

            // Если ширина изменилась значительно (>100px), проверяем видимость блока
            if (Math.abs(newWidth - this.lastWindowWidth) > 100) {
                this.checkBlockVisibility();
            }

            // Всегда применяем адаптивные стили
            this.applyResponsiveStyles();

            this.lastWindowWidth = newWidth;
        }, 250);
    }

    /**
     * Проверка видимости и корректности блока
     */
    checkBlockVisibility() {
        const container = document.getElementById('cvs-analyzer-container');

        if (!container) {
            console.log('📢 Блок отсутствует, пробуем внедрить');
            this.startInjectionProcess();
            return;
        }

        // Проверяем, видим ли блок
        const rect = container.getBoundingClientRect();
        const style = window.getComputedStyle(container);

        const isVisible = (
            rect.width > 0 &&
            rect.height > 0 &&
            style.display !== 'none' &&
            style.visibility !== 'hidden' &&
            style.opacity !== '0'
        );

        console.log('📢 Проверка видимости блока:', {
            exists: true,
            visible: isVisible,
            width: rect.width,
            height: rect.height,
            display: style.display,
            opacity: style.opacity
        });

        // Если блок невидим, пробуем пересоздать
        if (!isVisible) {
            console.log('⚠️ Блок невидим, пересоздаём');
            this.recreateBlock();
        } else {
            // Если блок видим, но результат должен быть, проверяем
            this.checkResultVisibility();
        }
    }

    /**
     * Проверка видимости результата внутри блока
     */
    checkResultVisibility() {
        const resultBlock = document.getElementById('cvs-result');
        if (!resultBlock) return;

        const style = window.getComputedStyle(resultBlock);
        const isResultVisible = style.display !== 'none' && style.opacity !== '0';

        // Если результат скрыт, но должен быть (по кэшу), показываем
        if (!isResultVisible) {
            const vacancyId = this.vacancySelect?.value;
            if (vacancyId) {
                console.log('📢 Результат скрыт, проверяем кэш');
                this.checkCache(true);
            }
        }
    }

    /**
     * Пересоздание блока
     */
    recreateBlock() {
        const oldContainer = document.getElementById('cvs-analyzer-container');
        if (oldContainer) {
            oldContainer.remove();
        }

        this.isInjected = false;
        this.injectionStarted = false;
        this.injectionAttempts = 0;
        this.startInjectionProcess();
    }

    /**
     * Проверка кэша с возможностью принудительного показа
     */
    async checkCache(forceShow = false) {
        console.log('📢 checkCache:', { forceShow });

        const cvData = this.parser.extractAll();
        const select = this.vacancySelect;
        const currentUrl = window.location.href;

        if (!select || !select.value || !this.api?.token) {
            console.log('⏩ Пропускаем проверку кэша');
            return;
        }

        const cached = await this.cache.get(select.value, cvData.fullText, currentUrl);

        if (cached) {
            console.log('✅ Найден результат в кэше');
            this.displayResult(cached, true);
        } else if (forceShow) {
            // Если запрошен принудительный показ, но кэша нет - скрываем результат
            if (this.resultBlock) {
                this.resultBlock.style.display = 'none';
            }
        }
    }

    async analyze(forceNew = false) {
        if (this.isAnalyzing) return;

        const vacancyId = this.vacancySelect.value;
        if (!vacancyId) {
            this.showError('Выберите вакансию');
            return;
        }

        // Проверяем авторизацию
        if (!this.api || !this.api.token) {
            await this.api.loadToken();
            if (!this.api.token) {
                this.showError('Необходима авторизация');
                return;
            }
        }

        const cvData = this.parser.extractAll();
        const currentUrl = window.location.href;
        const candidateName = cvData.name && cvData.name !== 'Неизвестно' ? cvData.name : null;

        // Проверяем кэш (если не forceNew)
        if (!forceNew) {
            const cached = await this.cache.get(vacancyId, cvData.fullText, currentUrl);
            if (cached) {
                console.log('✅ Найден результат в кэше');
                this.displayResult(cached, true);
                return;
            }
        }

        try {
            this.isAnalyzing = true;
            this.showLoading('Загрузка резюме...', 1);

            // Шаг 2: анализ AI (через небольшую задержку для эффекта прогресса)
            setTimeout(() => {
                this.updateProgress(2, 'Анализ AI...');
            }, 300);

            const result = await this.api.analyze(vacancyId, cvData.fullText, candidateName, currentUrl);

            // Шаг 3: обработка результатов
            this.updateProgress(3, 'Обработка результатов...');

            setTimeout(() => {
                // Сохраняем в кэш
                this.cache.save(vacancyId, cvData.fullText, result, currentUrl);

                // Обновляем остаток анализов
                if (result.analyses_left !== undefined) {
                    this.updateAnalysesLeft(result.analyses_left);
                    chrome.storage.local.set({ analyses_left: result.analyses_left });
                }

                this.finishLoading(true);
                this.displayResult(result, false);
            }, 300);

        } catch (error) {
            console.error('❌ Ошибка анализа:', error);
            this.finishLoading(false);
            this.handleAnalysisError(error);
        } finally {
            this.isAnalyzing = false;
        }
    }

    /**
     * Отображает результат анализа
     */
    displayResult(result, isCached = false) {
        const analysis = result.analysis || result;

        // Добавляем хэш к результату для сохранения
        if (!analysis._hash && this.vacancySelect?.value) {
            const cvData = this.parser.extractAll();
            analysis._hash = this.cache.createHash(
                this.vacancySelect.value,
                cvData.fullText,
                window.location.href
            );
        }

        // Проверяем существование resultBlock
        if (!this.resultBlock) {
            console.log('⚠️ resultBlock не найден, пробуем обновить ссылки');
            this.updateElementReferences();
            if (!this.resultBlock) {
                console.error('❌ Не удалось найти resultBlock');

                // Пробуем создать блок заново
                if (!document.getElementById('cvs-analyzer-container')) {
                    this.injectAnalysisBlock();
                    setTimeout(() => this.displayResult(result, isCached), 100);
                }
                return;
            }
        }

        // Сохраняем результат для быстрого доступа
        this.lastResult = {
            result: result,
            isCached: isCached,
            timestamp: Date.now(),
            hash: analysis._hash
        };

        // Если результат из кэша, показываем индикатор
        if (isCached) {
            console.log('⚡ Результат из кэша');
        }

        // Плавно показываем результат
        this.resultBlock.style.opacity = '0';
        this.resultBlock.style.display = 'block';

        // Принудительно применяем стили для текущего размера окна
        this.applyResponsiveStyles();

        // Небольшая задержка для плавности
        setTimeout(() => {
            this.resultBlock.style.transition = 'opacity 0.3s ease';
            this.resultBlock.style.opacity = '1';

            // Обновляем содержимое
            this.updateResultContent(analysis, isCached);

            // Добавляем класс для анимации
            this.resultBlock.classList.add('cvs-result-new');
            setTimeout(() => {
                this.resultBlock.classList.remove('cvs-result-new');
            }, 1000);

            // Прокручиваем к результату (опционально)
            if (!isCached) {
                this.resultBlock.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }

        }, 50);

        // Сохраняем результат во все хранилища
        this.saveResultToStorages(result, isCached, analysis._hash);
    }

    /**
     * Сохраняет результат во все хранилища
     */
    saveResultToStorages(result, isCached, hash) {
        // Сохраняем в sessionStorage для восстановления после ресайза
        try {
            sessionStorage.setItem('cvs_last_result', JSON.stringify({
                result: result,
                isCached: isCached,
                vacancyId: this.vacancySelect?.value,
                url: window.location.href,
                timestamp: Date.now(),
                hash: hash
            }));
        } catch (e) {
            console.warn('⚠️ Не удалось сохранить результат в sessionStorage:', e);
        }

        // Сохраняем хэш в chrome.storage для восстановления после перезапуска
        if (hash) {
            chrome.storage.local.set({
                cvs_last_result_hash: hash,
                cvs_last_result_time: Date.now()
            }).catch(() => { });
        }

        // Обновляем статистику
        this.updateStats();
    }

    /**
     * Обновление содержимого результата
     */
    updateResultContent(analysis, isCached) {
        // Оценка
        const score = analysis.score || 0;
        const scoreBadge = this.resultBlock.querySelector('.cvs-score-badge');
        if (scoreBadge) {
            scoreBadge.textContent = `${score}%`;

            let scoreClass = 'cvs-score-low';
            if (score >= 85) scoreClass = 'cvs-score-high';
            else if (score >= 50) scoreClass = 'cvs-score-medium';

            scoreBadge.className = `cvs-score-badge ${scoreClass}`;
        }

        // Рекомендация
        const recommendation = this.resultBlock.querySelector('.cvs-recommendation');
        if (recommendation) {
            recommendation.textContent = analysis.recommendation || 'Не определено';
        }

        // Индикатор кэша
        let cacheIndicator = this.resultBlock.querySelector('.cvs-cache-indicator');
        if (!cacheIndicator) {
            cacheIndicator = document.createElement('div');
            cacheIndicator.className = 'cvs-cache-indicator';
            const metadata = this.resultBlock.querySelector('.cvs-metadata');
            if (metadata) metadata.appendChild(cacheIndicator);
        }

        if (cacheIndicator) {
            cacheIndicator.textContent = isCached ? '⚡ из кэша' : '🆕 новый анализ';
        }

        // Совпавшие навыки
        const matchedList = this.resultBlock.querySelector('.cvs-matched-skills .cvs-skills-list');
        if (matchedList) {
            const matchedSkills = analysis.matched_skills || [];
            matchedList.innerHTML = matchedSkills
                .map(skill => `<span class="cvs-skill-tag cvs-skill-matched">${skill}</span>`)
                .join('');
        }

        // Отсутствующие навыки
        const missingList = this.resultBlock.querySelector('.cvs-missing-skills .cvs-skills-list');
        if (missingList) {
            const missingSkills = analysis.missing_skills || [];
            missingList.innerHTML = missingSkills
                .map(skill => `<span class="cvs-skill-tag cvs-skill-missing">${skill}</span>`)
                .join('');
        }

        // Сильные стороны
        const strengthsList = this.resultBlock.querySelector('.cvs-strengths-list');
        if (strengthsList) {
            const strengths = analysis.strengths || analysis.pros || [];
            strengthsList.innerHTML = strengths.map(item => `<li>${item}</li>`).join('');
        }

        // Слабые стороны
        const weaknessesList = this.resultBlock.querySelector('.cvs-weaknesses-list');
        if (weaknessesList) {
            const weaknesses = analysis.weaknesses || analysis.cons || [];
            weaknessesList.innerHTML = weaknesses.map(item => `<li>${item}</li>`).join('');
        }

        // Метаданные
        const modeSpan = this.resultBlock.querySelector('.cvs-mode');
        if (modeSpan) {
            modeSpan.textContent = analysis.mode ? `Режим: ${analysis.mode}` : '';
        }

        const timestampSpan = this.resultBlock.querySelector('.cvs-timestamp');
        if (timestampSpan) {
            timestampSpan.textContent = new Date().toLocaleString();
        }

        // Индикатор страницы
        let pageIndicator = this.resultBlock.querySelector('.cvs-page-indicator');
        if (!pageIndicator) {
            pageIndicator = document.createElement('span');
            pageIndicator.className = 'cvs-page-indicator';
            const metadata = this.resultBlock.querySelector('.cvs-metadata');
            if (metadata) metadata.appendChild(pageIndicator);
        }

        if (pageIndicator) {
            const urlPath = window.location.pathname;
            const resumeId = urlPath.split('/').pop() || 'unknown';
            pageIndicator.textContent = `📄 ${resumeId.substring(0, 8)}...`;
            pageIndicator.title = window.location.href;
        }

        // Кнопка "Новый анализ" с подтверждением
        const updateBtn = document.getElementById('cvs-update-btn');
        if (updateBtn) {
            updateBtn.onclick = async () => {
                if (!confirm('Запустить новый анализ? Предыдущий результат будет заменён.')) return;
                const vacancyId = this.vacancySelect.value;
                const cvData = this.parser.extractAll();
                const currentUrl = window.location.href;
                await this.cache.remove(vacancyId, cvData.fullText, currentUrl);
                this.analyze(true);
            };
        }

        // Ссылка на результат на сайте
        const siteLink = document.getElementById('cvs-site-link');
        if (siteLink && result?.id) {
            // APP_BASE_URL — поменять при деплое
            const appBase = 'http://localhost:3004';
            siteLink.href = `${appBase}/history/${result.id}`;
            siteLink.style.display = 'inline-flex';
        }
    }

    /**
     * Применение адаптивных стилей
     */
    applyResponsiveStyles() {
        const container = document.getElementById('cvs-analyzer-container');
        if (!container) return;

        const width = window.innerWidth;

        if (width < 768) {
            container.classList.add('cvs-mobile');
            container.classList.remove('cvs-tablet', 'cvs-desktop');
        } else if (width < 1024) {
            container.classList.add('cvs-tablet');
            container.classList.remove('cvs-mobile', 'cvs-desktop');
        } else {
            container.classList.add('cvs-desktop');
            container.classList.remove('cvs-mobile', 'cvs-tablet');
        }
    }

    /**
     * Восстановление результата из sessionStorage
     */
    restoreFromSession() {
        try {
            const saved = sessionStorage.getItem('cvs_last_result');
            if (!saved) return false;

            const data = JSON.parse(saved);

            // Проверяем, что результат для текущей страницы
            if (data.url !== window.location.href) {
                sessionStorage.removeItem('cvs_last_result');
                return false;
            }

            // Проверяем, что результат свежий (< 1 часа)
            if (Date.now() - data.timestamp > 3600000) {
                sessionStorage.removeItem('cvs_last_result');
                return false;
            }

            console.log('📢 Восстанавливаем результат из sessionStorage');

            // Если вакансия уже выбрана, показываем результат
            if (this.vacancySelect && this.vacancySelect.value === data.vacancyId) {
                this.displayResult(data.result, data.isCached);
                return true;
            }

        } catch (e) {
            console.warn('⚠️ Ошибка восстановления из sessionStorage:', e);
        }

        return false;
    }

    /**
     * Запуск периодической проверки видимости
     */
    startVisibilityChecks() {
        if (this.visibilityCheckInterval) {
            clearInterval(this.visibilityCheckInterval);
        }

        this.visibilityCheckInterval = setInterval(() => {
            // Проверяем только если страница видима
            if (document.visibilityState === 'visible') {
                this.checkBlockVisibility();
            }
        }, 2000);
    }

    /**
     * Очистка ресурсов
     */
    cleanup() {
        if (this.visibilityCheckInterval) {
            clearInterval(this.visibilityCheckInterval);
            this.visibilityCheckInterval = null;
        }

        if (this.resizeTimeout) {
            clearTimeout(this.resizeTimeout);
            this.resizeTimeout = null;
        }

        if (this.injectionTimer) {
            clearInterval(this.injectionTimer);
            this.injectionTimer = null;
        }

        if (this.observer) {
            this.observer.disconnect();
            this.observer = null;
        }
    }

    /**
     * Обработка ошибок анализа с понятными сообщениями
     */
    handleAnalysisError(error) {
        console.error('❌ Детали ошибки:', {
            message: error.message,
            stack: error.stack,
            name: error.name
        });

        // Определяем тип ошибки и показываем понятное сообщение
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            this.showError('🔌 Сервер недоступен. Проверьте: \n• Запущен ли бэкенд (localhost:8000)\n• Подключение к интернету');

        } else if (error.message.includes('402')) {
            this.showError('💰 Недостаточно анализов. Пополните баланс в личном кабинете.');
            this.updateAnalysesLeft(0);

        } else if (error.message.includes('401')) {
            this.showError('🔐 Сессия истекла. Пожалуйста, войдите снова.');
            if (this.api) {
                this.api.token = null;
            }
            chrome.storage.local.remove(['authToken']);

            // Показываем форму входа
            this.showAuthRequired();

        } else if (error.message.includes('422')) {
            this.showError('⚠️ Ошибка валидации. Возможно, резюме слишком короткое (нужно минимум 50 символов).');

        } else if (error.message.includes('429')) {
            this.showError('⏳ Слишком много запросов. Подождите минуту и попробуйте снова.');

        } else if (error.message.includes('500')) {
            this.showError('🔧 Ошибка на сервере. Наши разработчики уже работают над этим.');

        } else if (error.message.includes('503')) {
            this.showError('🔄 Сервер временно недоступен. Попробуйте через несколько минут.');

        } else {
            this.showError(`❌ Неизвестная ошибка: ${error.message.substring(0, 100)}`);
        }

        // Логируем для отладки (но не показываем пользователю)
        this.logError(error);
    }

    /**
     * Логирование ошибок (для отладки)
     */
    logError(error) {
        const errorLog = {
            timestamp: new Date().toISOString(),
            url: window.location.href,
            userAgent: navigator.userAgent,
            error: {
                message: error.message,
                stack: error.stack,
                name: error.name
            },
            state: {
                isAnalyzing: this.isAnalyzing,
                isInjected: this.isInjected,
                hasToken: !!this.api?.token,
                vacancySelected: this.vacancySelect?.value
            }
        };

        console.log('📋 Лог ошибки:', errorLog);

        // Сохраняем последние 10 ошибок в localStorage для диагностики
        try {
            const errors = JSON.parse(localStorage.getItem('cvs_errors') || '[]');
            errors.unshift(errorLog);
            if (errors.length > 10) errors.pop();
            localStorage.setItem('cvs_errors', JSON.stringify(errors));
        } catch (e) {
            // Игнорируем ошибки localStorage
        }
    }

    /**
 * Повторная попытка с задержкой
 */
    async retry(fn, maxAttempts = 3, delay = 1000) {
        let lastError;

        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return await fn();
            } catch (error) {
                lastError = error;
                console.log(`⏳ Попытка ${attempt}/${maxAttempts} не удалась, повтор через ${delay}ms`);

                if (attempt < maxAttempts) {
                    await new Promise(resolve => setTimeout(resolve, delay));
                    delay *= 2; // Экспоненциальная задержка
                }
            }
        }

        throw lastError;
    }

    /**
     * Показывает загрузку с прогрессом
     */
    showLoading(message, step = 1) {
        const loading = document.getElementById('cvs-loading');
        const progressBar = document.getElementById('cvs-progress-bar');
        const messageSpan = document.getElementById('cvs-loading-message');
        const steps = document.querySelectorAll('.cvs-step');

        if (loading) {
            loading.style.display = 'block';
            messageSpan.textContent = message;

            // Обновляем прогресс-бар
            if (progressBar) {
                const progress = step * 33; // 3 шага ~ 33% каждый
                progressBar.style.width = `${Math.min(progress, 99)}%`;
            }

            // Обновляем активный шаг
            steps.forEach(s => {
                s.classList.remove('active', 'completed');
                const stepNum = parseInt(s.dataset.step);
                if (stepNum === step) {
                    s.classList.add('active');
                } else if (stepNum < step) {
                    s.classList.add('completed');
                }
            });
        }

        if (this.analyzeBtn) {
            this.analyzeBtn.disabled = true;
        }
    }

    /**
     * Завершает загрузку (успех)
     */
    finishLoading(success = true) {
        const loading = document.getElementById('cvs-loading');
        const progressBar = document.getElementById('cvs-progress-bar');
        const steps = document.querySelectorAll('.cvs-step');

        if (success && progressBar) {
            // Заполняем прогресс-бар до конца
            progressBar.style.width = '100%';

            // Отмечаем все шаги как выполненные
            steps.forEach(s => {
                s.classList.remove('active');
                s.classList.add('completed');
            });

            // Даём увидеть завершение
            setTimeout(() => {
                loading.style.display = 'none';
                progressBar.style.width = '0%';
                steps.forEach(s => s.classList.remove('completed'));
            }, 500);
        } else {
            loading.style.display = 'none';
            if (progressBar) progressBar.style.width = '0%';
        }

        if (this.analyzeBtn && this.vacancySelect?.value) {
            this.analyzeBtn.disabled = false;
        }
    }

    /**
     * Скрывает загрузку (псевдоним для совместимости)
     */
    hideLoading() {
        this.finishLoading(false);
    }

    /**
 * Обновляет прогресс
 */
    updateProgress(step, message) {
        const progressBar = document.getElementById('cvs-progress-bar');
        const messageSpan = document.getElementById('cvs-loading-message');
        const steps = document.querySelectorAll('.cvs-step');

        if (progressBar) {
            const progress = step * 33;
            progressBar.style.width = `${Math.min(progress, 99)}%`;
        }

        if (messageSpan) {
            messageSpan.textContent = message;
        }

        steps.forEach(s => {
            s.classList.remove('active', 'completed');
            const stepNum = parseInt(s.dataset.step);
            if (stepNum === step) {
                s.classList.add('active');
            } else if (stepNum < step) {
                s.classList.add('completed');
            }
        });
    }

    /**
     * Показывает ошибку
     */
    showError(message) {
        const error = document.getElementById('cvs-error');

        // Проверяем что элемент существует
        if (!error) {
            console.error('❌ Элемент ошибки не найден:', message);
            return;
        }

        error.textContent = message;
        error.style.display = 'block';

        // Автоматически скрываем через 5 секунд
        setTimeout(() => {
            if (error) error.style.display = 'none';
        }, 5000);
    }

    /**
     * Очищает результат анализа
     */
    clearResult(animate = true) {
        console.log('📢 Очистка результата');

        if (!this.resultBlock) {
            console.log('⚠️ resultBlock не найден');
            return;
        }

        const clearFields = () => {
            // Очищаем основные поля
            const scoreBadge = this.resultBlock.querySelector('.cvs-score-badge');
            if (scoreBadge) scoreBadge.textContent = '';

            const recommendation = this.resultBlock.querySelector('.cvs-recommendation');
            if (recommendation) recommendation.textContent = '';

            // Очищаем списки навыков
            const matchedList = this.resultBlock.querySelector('.cvs-matched-skills .cvs-skills-list');
            if (matchedList) matchedList.innerHTML = '';

            const missingList = this.resultBlock.querySelector('.cvs-missing-skills .cvs-skills-list');
            if (missingList) missingList.innerHTML = '';

            // Очищаем списки сильных и слабых сторон
            const strengthsList = this.resultBlock.querySelector('.cvs-strengths-list');
            if (strengthsList) strengthsList.innerHTML = '';

            const weaknessesList = this.resultBlock.querySelector('.cvs-weaknesses-list');
            if (weaknessesList) weaknessesList.innerHTML = '';

            // Очищаем индикаторы
            const pageIndicator = this.resultBlock.querySelector('.cvs-page-indicator');
            if (pageIndicator) pageIndicator.textContent = '';

            const cacheIndicator = this.resultBlock.querySelector('.cvs-cache-indicator');
            if (cacheIndicator) cacheIndicator.textContent = '';

            const modeSpan = this.resultBlock.querySelector('.cvs-mode');
            if (modeSpan) modeSpan.textContent = '';

            const timestampSpan = this.resultBlock.querySelector('.cvs-timestamp');
            if (timestampSpan) timestampSpan.textContent = '';
        };

        if (animate) {
            // Плавно скрываем
            this.resultBlock.style.transition = 'opacity 0.3s ease';
            this.resultBlock.style.opacity = '0';

            setTimeout(() => {
                this.resultBlock.style.display = 'none';
                clearFields();
                this.resultBlock.style.opacity = '1';
            }, 300);
        } else {
            // Мгновенно скрываем
            this.resultBlock.style.display = 'none';
            clearFields();
        }
    }

    /**
 * Проверяет, нужно ли запустить автоанализ
 */
    async shouldAutoAnalyze() {
        try {
            const settings = await chrome.storage.local.get(['cvs_auto_analyze']);
            return settings.cvs_auto_analyze === true;
        } catch (e) {
            console.warn('⚠️ Ошибка проверки настроек автоанализа:', e);
            return false;
        }
    }

    /**
     * Запускает анализ если выполнены условия
     */
    async tryAutoAnalyze() {
        // Проверяем, включён ли автоанализ
        if (!await this.shouldAutoAnalyze()) {
            console.log('⏩ Автоанализ отключён в настройках');
            return;
        }

        // Проверяем, выбрана ли вакансия
        if (!this.vacancySelect || !this.vacancySelect.value) {
            console.log('⏩ Вакансия не выбрана, автоанализ отложен');
            return;
        }

        // Проверяем, не было ли уже анализа для этого резюме
        const cvData = this.parser.extractAll();
        const currentUrl = window.location.href;
        const cached = await this.cache.get(this.vacancySelect.value, cvData.fullText, currentUrl);

        if (cached) {
            console.log('📢 Результат уже есть в кэше, показываем');
            this.displayResult(cached, true);
            return;
        }

        // Даём небольшую задержку для полной загрузки страницы
        setTimeout(() => {
            console.log('🤖 Запуск автоанализа');
            this.analyze();
        }, 500);
    }

    /**
 * Показывает меню быстрого переключения между последними анализами
 */
    showQuickSwitch() {
        chrome.storage.local.get(['recent_analyses'], (items) => {
            const recent = items.recent_analyses || [];

            if (recent.length < 2) {
                this.showNotification('Нет других анализов для сравнения');
                return;
            }

            // Создаём временное меню
            let menu = document.getElementById('cvs-quick-switch');
            if (menu) menu.remove();

            menu = document.createElement('div');
            menu.id = 'cvs-quick-switch';
            menu.className = 'cvs-quick-switch';

            const title = document.createElement('div');
            title.className = 'cvs-quick-switch-title';
            title.textContent = 'Последние анализы';
            menu.appendChild(title);

            recent.slice(0, 5).forEach((item, index) => {
                if (item.hash === this.lastResultHash) return; // Пропускаем текущий

                const option = document.createElement('div');
                option.className = 'cvs-quick-switch-item';
                option.innerHTML = `
                <span class="cvs-quick-switch-score">${item.score || '?'}%</span>
                <span class="cvs-quick-switch-date">${new Date(item.timestamp).toLocaleTimeString()}</span>
            `;

                option.onclick = async () => {
                    // Загружаем результат из кэша
                    const data = await this.cache.getByHash(item.hash);
                    if (data) {
                        this.displayResult(data.result, true);
                        this.showNotification('Загружен предыдущий результат');
                    }
                    menu.remove();
                };

                menu.appendChild(option);
            });

            document.body.appendChild(menu);

            // Закрытие по клику вне меню
            setTimeout(() => {
                document.addEventListener('click', function closeMenu(e) {
                    if (!menu.contains(e.target)) {
                        menu.remove();
                        document.removeEventListener('click', closeMenu);
                    }
                });
            }, 100);
        });
    }

    /**
 * Полная очистка ресурсов
 */
    destroy() {
        console.log('📢 Destroy: очистка ресурсов');
        this.isDestroyed = true;

        // Очищаем интервалы
        if (this.visibilityCheckInterval) {
            clearInterval(this.visibilityCheckInterval);
            this.visibilityCheckInterval = null;
        }

        if (this.resizeTimeout) {
            clearTimeout(this.resizeTimeout);
            this.resizeTimeout = null;
        }

        if (this.injectionTimer) {
            clearInterval(this.injectionTimer);
            this.injectionTimer = null;
        }

        // Отключаем observer
        if (this.observer) {
            this.observer.disconnect();
            this.observer = null;
        }

        // Удаляем слушатели событий
        window.removeEventListener('resize', this.optimizedResize);
        window.removeEventListener('scroll', this.optimizedScroll);

        // Удаляем обработчик клавиш
        document.removeEventListener('keydown', this.handleHotkeys);

        console.log('✅ Ресурсы очищены');
    }

    /**
     * Показать диагностическую информацию (для отладки)
     */
    showDiagnostics() {
        const diagnostics = {
            version: '1.0.0',
            injected: this.isInjected,
            analyzing: this.isAnalyzing,
            token: !!this.api?.token,
            vacancySelected: this.vacancySelect?.value,
            resultVisible: this.resultBlock?.style.display === 'block',
            url: window.location.href,
            parser: {
                exists: !!this.parser,
                isResumePage: this.parser?.isResumePage?.()
            },
            cache: {
                exists: !!this.cache,
                recentCount: 0
            },
            errors: JSON.parse(localStorage.getItem('cvs_errors') || '[]').length,
            memory: performance?.memory ? {
                usedJSHeapSize: Math.round(performance.memory.usedJSHeapSize / 1048576) + 'MB',
                totalJSHeapSize: Math.round(performance.memory.totalJSHeapSize / 1048576) + 'MB'
            } : 'Недоступно'
        };

        console.table(diagnostics);

        // Показываем в уведомлении
        const message = `
        📊 Диагностика:
        • Версия: ${diagnostics.version}
        • Статус: ${diagnostics.injected ? '✅ Внедрён' : '❌ Не внедрён'}
        • Токен: ${diagnostics.token ? '✅' : '❌'}
        • Вакансия: ${diagnostics.vacancySelected || 'не выбрана'}
        • Ошибок в логе: ${diagnostics.errors}
    `;

        this.showNotification(message, 'info');
    }
}

// Запускаем при загрузке страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new ContentInjector().init();
    });
} else {
    new ContentInjector().init();
}
