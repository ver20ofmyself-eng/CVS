// extension/utils/parser.js
/**
 * Базовые функции парсинга для всех сайтов
 */
class BaseParser {
    constructor() {
        this.siteName = 'unknown';
    }

    /**
     * Определяет тип сайта по URL
     */
    static detectSite(url) {
        if (url.includes('hh.ru')) return 'hh';
        if (url.includes('linkedin.com')) return 'linkedin';
        if (url.includes('habr.com')) return 'habr';
        return 'unknown';
    }

    /**
     * Очищает текст от лишних пробелов
     */
    cleanText(text) {
        if (!text) return '';
        return text.replace(/\s+/g, ' ').trim();
    }

    /**
     * Извлекает числа из строки (для опыта, зарплаты)
     */
    extractNumbers(text) {
        const matches = text.match(/\d+/g);
        return matches ? matches.map(Number) : [];
    }

    /**
     * Форматирует текст для отправки в AI
     */
    formatForAI(data) {
        const parts = [];

        if (data.name) parts.push(`Кандидат: ${data.name}`);
        if (data.title) parts.push(`Желаемая должность: ${data.title}`);
        if (data.salary) parts.push(`Зарплатные ожидания: ${data.salary}`);
        if (data.skills?.length) parts.push(`Ключевые навыки: ${data.skills.join(', ')}`);
        if (data.experience) parts.push(`Опыт работы:\n${data.experience}`);
        if (data.education) parts.push(`Образование:\n${data.education}`);

        return parts.join('\n\n');
    }
}

// Создаём глобальный объект
window.baseParser = new BaseParser();
