/**
 * Управление кэшированием результатов анализа
 * Ключ: хэш (vacancy_id + URL_страницы + текст_резюме)
 */
class AnalysisCache {
    constructor(storage = chrome.storage.local) {
        this.storage = storage;
        this.cachePrefix = 'cvs_analysis_';
        this.ttl = 24 * 60 * 60 * 1000; // 24 часа
    }

    /**
     * Создаёт хэш из вакансии, URL страницы и текста резюме
     */
    createHash(vacancyId, cvText, pageUrl) {
        // Берём только путь без параметров (чтобы ?utm_source=... не ломал кэш)
        const urlPath = pageUrl ? new URL(pageUrl).pathname : '';
        const str = `${vacancyId}_${urlPath}_${cvText.substring(0, 200)}`;

        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return Math.abs(hash).toString(36);
    }

    /**
     * Сохраняет результат анализа
     */
    async save(vacancyId, cvText, result, pageUrl) {
        const hash = this.createHash(vacancyId, cvText, pageUrl);
        const key = this.cachePrefix + hash;

        const data = {
            result: result,
            timestamp: Date.now(),
            vacancyId: vacancyId,
            pageUrl: pageUrl,
            cvPreview: cvText.substring(0, 200)
        };

        return new Promise(resolve => {
            this.storage.set({ [key]: data }, () => {
                console.log('✅ Результат сохранён в кэш', {
                    hash,
                    vacancyId,
                    url: pageUrl.split('/').pop()
                });

                // Очищаем старые записи для этой вакансии (необязательно)
                this._cleanOldForVacancy(vacancyId);

                // Сохраняем также в список последних анализов
                this._addToRecentList(hash, vacancyId, result?.analysis?.score, pageUrl);
                resolve(hash);
            });
        });
    }

    /**
     * Получает результат из кэша
     */
    async get(vacancyId, cvText, pageUrl) {
        const hash = this.createHash(vacancyId, cvText, pageUrl);
        const key = this.cachePrefix + hash;

        console.log('📢 Поиск в кэше:', {
            vacancyId,
            urlPath: pageUrl ? new URL(pageUrl).pathname : 'unknown',
            hash
        });

        return new Promise(resolve => {
            this.storage.get([key], (items) => {
                const cached = items[key];

                if (!cached) {
                    console.log('⏳ Кэш пуст');
                    resolve(null);
                    return;
                }

                // Проверяем срок действия
                const age = Date.now() - cached.timestamp;
                if (age > this.ttl) {
                    console.log('⌛ Кэш устарел', { age, maxAge: this.ttl });
                    this.storage.remove([key]);
                    resolve(null);
                    return;
                }

                // Дополнительная проверка: совпадает ли URL (на всякий случай)
                if (cached.pageUrl && pageUrl) {
                    const cachedPath = new URL(cached.pageUrl).pathname;
                    const currentPath = new URL(pageUrl).pathname;

                    if (cachedPath !== currentPath) {
                        console.log('⚠️ URL не совпадает, игнорируем кэш', {
                            cached: cachedPath,
                            current: currentPath
                        });
                        resolve(null);
                        return;
                    }
                }

                console.log('✅ Найден в кэше', { age, hash });
                resolve(cached.result);
            });
        });
    }

    /**
     * Очищает старые записи для конкретной вакансии (держит только последние 5)
     */
    _cleanOldForVacancy(vacancyId) {
        this.storage.get(null, (items) => {
            const entries = [];

            for (const [key, value] of Object.entries(items)) {
                if (key.startsWith(this.cachePrefix) && value.vacancyId == vacancyId) {
                    entries.push({ key, ...value });
                }
            }

            // Сортируем по времени (новые первые)
            entries.sort((a, b) => b.timestamp - a.timestamp);

            // Оставляем только последние 5
            if (entries.length > 5) {
                const toDelete = entries.slice(5).map(e => e.key);
                this.storage.remove(toDelete, () => {
                    console.log(`🧹 Очищено ${toDelete.length} старых записей для вакансии ${vacancyId}`);
                });
            }
        });
    }

    /**
     * Добавляет анализ в список последних
     */
    _addToRecentList(hash, vacancyId, score, pageUrl) {
        this.storage.get(['recent_analyses'], (items) => {
            let recent = items.recent_analyses || [];

            recent.unshift({
                hash: hash,
                vacancyId: vacancyId,
                score: score,
                timestamp: Date.now(),
                pageUrl: pageUrl
            });

            // Оставляем только последние 20
            recent = recent.slice(0, 20);
            this.storage.set({ recent_analyses: recent });
        });
    }

    /**
     * Удаляет конкретную запись из кэша
     */
    async remove(vacancyId, cvText, pageUrl) {
        const hash = this.createHash(vacancyId, cvText, pageUrl);
        const key = this.cachePrefix + hash;
        return new Promise(resolve => {
            this.storage.remove([key], () => {
                console.log(`🗑️ Удалена запись из кэша: ${hash}`);
                resolve();
            });
        });
    }

    /**
     * Очищает весь кэш для текущей страницы (полезно для тестирования)
     */
    async clearForCurrentPage(pageUrl) {
        return new Promise(resolve => {
            this.storage.get(null, (items) => {
                const toDelete = [];
                const currentPath = new URL(pageUrl).pathname;

                for (const [key, value] of Object.entries(items)) {
                    if (key.startsWith(this.cachePrefix) && value.pageUrl) {
                        const cachedPath = new URL(value.pageUrl).pathname;
                        if (cachedPath === currentPath) {
                            toDelete.push(key);
                        }
                    }
                }

                if (toDelete.length > 0) {
                    this.storage.remove(toDelete, () => {
                        console.log(`🧹 Очищено ${toDelete.length} записей для текущей страницы`);
                        resolve(toDelete.length);
                    });
                } else {
                    resolve(0);
                }
            });
        });
    }
}

// Создаём глобальный экземпляр
window.analysisCache = new AnalysisCache();
