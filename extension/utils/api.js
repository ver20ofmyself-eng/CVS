/**
 * Клиент для работы с бэкендом
 */
class ApiClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.token = null;
    }

    /**
     * Устанавливает токен авторизации
     */
    setToken(token) {
        console.log('📢 Установка токена:', token ? 'есть' : 'нет');
        this.token = token;
        chrome.storage.local.set({ authToken: token });
    }

    /**
     * Загружает токен из хранилища
     */
    async loadToken() {
        console.log('📢 Загрузка токена из хранилища...');
        return new Promise(resolve => {
            chrome.storage.local.get(['authToken'], (items) => {
                this.token = items.authToken;
                console.log('📢 Токен загружен:', this.token ? 'есть' : 'нет');
                resolve(this.token);
            });
        });
    }

    /**
     * Выполняет запрос к API
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
            console.log('📢 Добавлен заголовок Authorization');
        } else {
            console.warn('⚠️ Токен отсутствует, запрос без авторизации');
        }

        console.log('📢 Запрос к API:', url, options.method || 'GET');

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            console.log('📢 Ответ API:', response.status);

            if (!response.ok) {
                const error = await response.text();
                console.error('❌ Ошибка API:', response.status, error);
                throw new Error(`API Error: ${response.status} - ${error}`);
            }

            return await response.json();
        } catch (error) {
            console.error('❌ API Request failed:', error);
            throw error;
        }
    }

    /**
     * Логин пользователя
     */
    async login(email, password) {
        console.log('📢 Попытка входа:', email);

        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await fetch(`${this.baseUrl}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        });

        console.log('📢 Ответ на логин:', response.status);

        if (!response.ok) {
            const error = await response.text();
            console.error('❌ Ошибка логина:', error);
            throw new Error('Login failed');
        }

        const data = await response.json();
        console.log('📢 Токен получен, сохраняем...');

        this.setToken(data.access_token);

        return data;
    }

    /**
     * Получает список вакансий пользователя
     */
    async getVacancies() {
        console.log('📢 Запрос списка вакансий...');
        return this.request('/api/vacancies/');
    }

    /**
     * АНАЛИЗИРУЕТ РЕЗЮМЕ
     */
    async analyze(vacancyId, cvText, promptName = 'default_cv_analyzer') {
        console.log('📢 Запрос на анализ CV...', { vacancyId, promptName });

        return this.request('/api/analyze/', {
            method: 'POST',
            body: JSON.stringify({
                vacancy_id: vacancyId,
                cv_text: cvText,
                prompt_name: promptName
            })
        });
    }

    /**
     * Получает результат анализа по ID
     */
    async getAnalysis(analysisId) {
        return this.request(`/api/analyze/history/${analysisId}`);
    }

    /**
     * Получает список доступных промптов
     */
    async getPrompts() {
        return this.request('/api/analyze/prompts');
    }
}

// Создаём глобальный экземпляр
window.apiClient = new ApiClient();
console.log('✅ ApiClient загружен, методы:', Object.getOwnPropertyNames(ApiClient.prototype));
