/**
 * Клиент для работы с бэкендом CVS Analyzer
 */
class ApiClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.token = null;
    }

    setToken(token) {
        this.token = token;
        chrome.storage.local.set({ authToken: token });
    }

    async loadToken() {
        return new Promise(resolve => {
            chrome.storage.local.get(['authToken'], (items) => {
                this.token = items.authToken;
                resolve(this.token);
            });
        });
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, { ...options, headers });

            if (!response.ok) {
                const error = await response.text();
                console.error('❌ API Error:', response.status, error);
                throw new Error(`API Error: ${response.status} - ${error}`);
            }

            return await response.json();
        } catch (error) {
            console.error('❌ API Request failed:', error);
            throw error;
        }
    }

    async login(email, password) {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await fetch(`${this.baseUrl}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        if (!response.ok) {
            const error = await response.text();
            console.error('❌ Login error:', error);
            throw new Error('Login failed');
        }

        const data = await response.json();
        this.setToken(data.access_token);
        return data;
    }

    async getVacancies() {
        return this.request('/api/vacancies/');
    }

    /**
     * Анализ резюме.
     * @param {number|string} vacancyId
     * @param {string} cvText
     * @param {string|null} candidateName — "Фамилия Имя" кандидата
     * @param {string|null} sourceUrl — URL страницы резюме
     * @param {string} promptName
     */
    async analyze(vacancyId, cvText, candidateName = null, sourceUrl = null, promptName = 'default_cv_analyzer') {
        console.log('📢 Анализ CV:', { vacancyId, candidateName, sourceUrl, promptName });

        const body = {
            vacancy_id: parseInt(vacancyId),
            cv_text: cvText,
            prompt_name: promptName,
        };

        // Добавляем опциональные поля только если они есть
        if (candidateName && candidateName.trim()) {
            body.candidate_name = candidateName.trim();
        }
        if (sourceUrl && sourceUrl.trim()) {
            body.source_url = sourceUrl.trim();
        }

        return this.request('/api/analyze/', {
            method: 'POST',
            body: JSON.stringify(body),
        });
    }

    async getAnalysis(analysisId) {
        return this.request(`/api/analyze/history/${analysisId}`);
    }

    async getPrompts() {
        return this.request('/api/analyze/prompts');
    }
}

// Глобальный экземпляр
window.apiClient = new ApiClient();
console.log('✅ ApiClient загружен');
