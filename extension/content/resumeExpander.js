/**
 * Модуль разворачивания скрытых блоков резюме на hh.ru
 * Программно кликает на «Показать все контакты», «Развернуть» и т.д.
 * 
 * @version 2.0
 */
class ResumeExpander {
    constructor() {
        this.expanded = {
            contacts: false,
            coverLetter: false,
            about: false
        };
        this.CLICK_DELAY = 300;
        this.WAIT_AFTER_CLICK = 800;
    }

    /**
     * Разворачивает все скрытые блоки резюме
     * @returns {Promise<Object>} Статус разворачивания каждого блока
     */
    async expandAll() {
        console.log('📋 ResumeExpander: начинаю разворачивание блоков...');

        await this._expandContacts();
        await this._sleep(this.CLICK_DELAY);

        await this._expandCoverLetter();
        await this._sleep(this.CLICK_DELAY);

        await this._expandAbout();

        console.log('✅ ResumeExpander: разворачивание завершено', this.expanded);
        return { ...this.expanded };
    }

    /**
     * Клик на «Показать все контакты»
     */
    async _expandContacts() {
        try {
            const showContactsBtn = document.querySelector('[data-qa="response-resume_show-phone-number"]');
            if (showContactsBtn) {
                showContactsBtn.click();
                console.log('📋 Клик: «Показать все контакты»');
                await this._waitForElement(
                    '[data-qa="resume-block-contacts"]',
                    () => {
                        const contactsBlock = document.querySelector('[data-qa="resume-block-contacts"]');
                        if (!contactsBlock) return false;
                        const text = contactsBlock.textContent || '';
                        return text.includes('@') || text.includes('Telegram') || text.includes('WhatsApp');
                    },
                    this.WAIT_AFTER_CLICK
                );
                this.expanded.contacts = true;
            } else {
                console.log('⏩ Кнопка «Показать контакты» не найдена');
                const contactsBlock = document.querySelector('[data-qa="resume-block-contacts"]');
                if (contactsBlock) {
                    const text = contactsBlock.textContent || '';
                    this.expanded.contacts = text.includes('@') || text.includes('Telegram');
                }
            }
        } catch (e) {
            console.warn('⚠️ Ошибка разворачивания контактов:', e);
        }
    }

    /**
     * Клик на «Развернуть» в сопроводительном письме
     */
    async _expandCoverLetter() {
        try {
            const letterBlock = document.querySelector('[data-qa="resume-response-letter-block"]');
            if (!letterBlock) {
                console.log('⏩ Сопроводительное письмо отсутствует');
                return;
            }

            const trigger = letterBlock.querySelector('[data-qa="trigger-root"]');
            if (trigger) {
                const labelEl = trigger.querySelector('[class*="magritte-label"]');
                const labelText = labelEl ? labelEl.textContent.trim() : '';
                if (labelText === 'Развернуть') {
                    trigger.click();
                    console.log('📋 Клик: «Развернуть» сопроводительное письмо');
                    await this._sleep(this.WAIT_AFTER_CLICK);
                    this.expanded.coverLetter = true;
                } else {
                    this.expanded.coverLetter = true;
                }
            } else {
                this.expanded.coverLetter = true;
            }
        } catch (e) {
            console.warn('⚠️ Ошибка разворачивания сопроводительного:', e);
        }
    }

    /**
     * Клик на «Развернуть» в блоке «О себе»
     */
    async _expandAbout() {
        try {
            const aboutBlock = document.querySelector('[data-qa="resume-about-block"]');
            if (!aboutBlock) {
                console.log('⏩ Блок «О себе» отсутствует');
                return;
            }

            const trigger = aboutBlock.querySelector('[data-qa="trigger-root"]');
            if (trigger) {
                const labelEl = trigger.querySelector('[class*="magritte-label"]');
                const labelText = labelEl ? labelEl.textContent.trim() : '';
                if (labelText === 'Развернуть') {
                    trigger.click();
                    console.log('📋 Клик: «Развернуть» блок «О себе»');
                    await this._sleep(this.WAIT_AFTER_CLICK);
                    this.expanded.about = true;
                } else {
                    this.expanded.about = true;
                }
            } else {
                this.expanded.about = true;
            }
        } catch (e) {
            console.warn('⚠️ Ошибка разворачивания «О себе»:', e);
        }
    }

    /**
     * Ожидание изменения элемента с таймаутом
     */
    _waitForElement(selector, condition, timeout = 2000) {
        return new Promise((resolve) => {
            if (condition && condition()) {
                resolve(true);
                return;
            }

            const timer = setTimeout(() => {
                if (observer) observer.disconnect();
                resolve(false);
            }, timeout);

            const observer = new MutationObserver(() => {
                if (condition && condition()) {
                    observer.disconnect();
                    clearTimeout(timer);
                    resolve(true);
                }
            });

            const target = document.querySelector(selector) || document.body;
            observer.observe(target, { childList: true, subtree: true, characterData: true });
        });
    }

    /**
     * Утилита задержки
     */
    _sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

window.resumeExpander = new ResumeExpander();
console.log('✅ ResumeExpander загружен');
