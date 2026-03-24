/**
 * Парсер для hh.ru
 * Извлекает текст резюме со страницы
 */
class HHParser {
    /**
     * Определяет, является ли текущая страница резюме
     */
    isResumePage() {
        const path = window.location.pathname;
        return path.includes('/resume/') ||
            path.includes('/applicant/resumes/') ||
            path.includes('/resumes/');
    }

    /**
     * Извлекает ФИО кандидата
     */
    extractName() {
        const nameElement = document.querySelector('[data-qa="resume-personal-name"]');
        return nameElement?.textContent?.trim() || 'Неизвестно';
    }

    /**
     * Извлекает заголовок (желаемую должность)
     */
    extractTitle() {
        const titleElement = document.querySelector('[data-qa="resume-block-title"]');
        return titleElement?.textContent?.trim() || '';
    }

    /**
     * Извлекает зарплатные ожидания
     */
    extractSalary() {
        const salaryElement = document.querySelector('[data-qa="resume-block-salary"]');
        return salaryElement?.textContent?.trim() || null;
    }

    /**
     * Извлекает опыт работы
     */
    extractExperience() {
        const experienceSections = document.querySelectorAll('[data-qa="resume-block-experience"]');
        let experience = [];

        experienceSections.forEach(section => {
            const period = section.querySelector('[data-qa="resume-block-experience-position"]')?.textContent?.trim() || '';
            const description = section.querySelector('[data-qa="resume-block-experience-description"]')?.textContent?.trim() || '';
            if (period || description) {
                experience.push(`${period}\n${description}`);
            }
        });

        return experience.join('\n\n');
    }

    /**
     * Извлекает образование
     */
    extractEducation() {
        const educationSections = document.querySelectorAll('[data-qa="resume-block-education"]');
        let education = [];

        educationSections.forEach(section => {
            const text = section.textContent?.trim();
            if (text) education.push(text);
        });

        return education.join('\n');
    }

    /**
     * Извлекает ключевые навыки
     */
    extractSkills() {
        const skillsElements = document.querySelectorAll('[data-qa="skills-table"] td');
        return Array.from(skillsElements)
            .map(el => el.textContent?.trim())
            .filter(skill => skill && skill.length > 0);
    }

    /**
     * Извлекает текст "Обо мне"
     */
    extractAbout() {
        const aboutElement = document.querySelector('[data-qa="resume-block-about"]');
        return aboutElement?.textContent?.trim() || '';
    }

    /**
     * Извлекает полный текст резюме для AI
     */
    extractFullText() {
        const parts = [];

        // Заголовок
        const title = this.extractTitle();
        if (title) parts.push(`Желаемая должность: ${title}`);

        // Зарплата
        const salary = this.extractSalary();
        if (salary) parts.push(`Зарплатные ожидания: ${salary}`);

        // Опыт работы
        const experience = this.extractExperience();
        if (experience) parts.push(`Опыт работы:\n${experience}`);

        // Образование
        const education = this.extractEducation();
        if (education) parts.push(`Образование:\n${education}`);

        // Навыки
        const skills = this.extractSkills();
        if (skills.length > 0) parts.push(`Ключевые навыки: ${skills.join(', ')}`);

        // О себе
        const about = this.extractAbout();
        if (about) parts.push(`О себе:\n${about}`);

        // Если ничего не нашли - пробуем собрать весь текст страницы
        if (parts.length === 0) {
            console.log('⚠️ Не удалось найти структурированные данные, собираем весь текст');

            // Пробуем найти основной контент
            const mainContent = document.querySelector('.resume-wrapper') ||
                document.querySelector('[data-qa="resume"]') ||
                document.querySelector('main');

            if (mainContent) {
                parts.push(mainContent.innerText);
            } else {
                parts.push(document.body.innerText);
            }
        }

        const fullText = parts.join('\n\n');
        console.log('📢 Извлечён текст длиной:', fullText.length);
        return fullText;
    }

    /**
     * Извлекает все данные резюме
     */
    extractAll() {
        const fullText = this.extractFullText();

        return {
            name: this.extractName(),
            title: this.extractTitle(),
            salary: this.extractSalary(),
            skills: this.extractSkills(),
            fullText: fullText,
            url: window.location.href,
            extractedAt: new Date().toISOString()
        };
    }
}

window.hhParser = new HHParser();
console.log('✅ HHParser загружен');
