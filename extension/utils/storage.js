// extension/utils/storage.js
/**
 * Работа с хранилищем
 */
class StorageManager {
    constructor(storage = chrome.storage.local) {
        this.storage = storage;
    }

    /**
     * Сохранить данные
     */
    async set(key, value) {
        return new Promise(resolve => {
            this.storage.set({ [key]: value }, resolve);
        });
    }

    /**
     * Получить данные
     */
    async get(key) {
        return new Promise(resolve => {
            this.storage.get([key], (items) => {
                resolve(items[key]);
            });
        });
    }

    /**
     * Удалить данные
     */
    async remove(key) {
        return new Promise(resolve => {
            this.storage.remove([key], resolve);
        });
    }

    /**
     * Очистить всё
     */
    async clear() {
        return new Promise(resolve => {
            this.storage.clear(resolve);
        });
    }
}

window.storageManager = new StorageManager();
