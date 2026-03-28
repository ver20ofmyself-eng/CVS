/**
 * Фоновый сервис-воркер
 */
const API_BASE = 'http://localhost:8000';

// При установке расширения
chrome.runtime.onInstalled.addListener(() => {
    console.log('✅ CVS Analyzer установлен');

    // Очищаем старый кэш
    chrome.storage.local.get(null, (items) => {
        const now = Date.now();
        const toDelete = [];

        for (const [key, value] of Object.entries(items)) {
            if (key.startsWith('cvs_analysis_')) {
                if (now - value.timestamp > 24 * 60 * 60 * 1000) {
                    toDelete.push(key);
                }
            }
        }

        if (toDelete.length > 0) {
            chrome.storage.local.remove(toDelete);
        }
    });
});

// Обработка сообщений от content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'GET_VACANCIES') {
        fetchVacancies(sender.tab?.id);
    } else if (message.type === 'ANALYZE') {
        analyzeCV(message.data, sender.tab?.id);
    }
    return true;
});

// Функция для получения вакансий
async function fetchVacancies(tabId) {
    try {
        const { authToken } = await chrome.storage.local.get(['authToken']);

        const response = await fetch(`${API_BASE}/api/vacancies/`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        const data = await response.json();

        chrome.tabs.sendMessage(tabId, {
            type: 'VACANCIES_LOADED',
            data: data
        });
    } catch (error) {
        console.error('Ошибка загрузки вакансий:', error);
    }
}

// Функция для анализа
async function analyzeCV(data, tabId) {
    try {
        const { authToken } = await chrome.storage.local.get(['authToken']);

        const response = await fetch(`${API_BASE}/api/analyze/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        chrome.tabs.sendMessage(tabId, {
            type: 'ANALYSIS_COMPLETE',
            data: result
        });
    } catch (error) {
        chrome.tabs.sendMessage(tabId, {
            type: 'ANALYSIS_ERROR',
            error: error.message
        });
    }
}
