/**
 * Парсер для hh.ru — Блочный парсер резюме v2.0
 * Извлекает 9 структурированных блоков из страницы резюме
 * Формирует cv_structured (JSON) и cv_text (форматированный текст для AI)
 * 
 * @version 2.0
 * @see project_docs/parts/task_1_research.md
 */
class HHParser {
    constructor() {
        this.parserVersion = '2.0';
        this.expander = window.resumeExpander;
        this._expanded = false;
    }

    // ========== ОПРЕДЕЛЕНИЕ СТРАНИЦЫ ==========

    /**
     * Определяет, является ли текущая страница резюме
     */
    isResumePage() {
        const path = window.location.pathname;
        return path.includes('/resume/') ||
            path.includes('/applicant/resumes/') ||
            path.includes('/resumes/');
    }

    // ========== ФАЗА 2: РАЗВОРАЧИВАНИЕ СКРЫТЫХ БЛОКОВ ==========

    /**
     * Разворачивает скрытые блоки (контакты, сопроводительное, «О себе»)
     * Вызывается один раз перед первым парсингом
     */
    async ensureExpanded() {
        if (this._expanded) return;
        if (this.expander) {
            await this.expander.expandAll();
        }
        this._expanded = true;
    }

    // ========== ФАЗА 3: ПАРСИНГ 9 БЛОКОВ ==========

    /**
     * Блок 1 — personal_info
     */
    parsePersonalInfo() {
        try {
            const result = {};

            const nameEl = document.querySelector('[data-qa="resume-personal-name"]');
            result.full_name = nameEl?.textContent?.trim() || null;

            const photoEl = document.querySelector('[data-qa="resume-photo"] img');
            result.photo_url = photoEl?.src || null;

            const genderEl = document.querySelector('[data-qa="resume-personal-gender"]');
            result.gender = genderEl?.textContent?.trim() || null;

            const ageEl = document.querySelector('[data-qa="resume-personal-age"]');
            if (ageEl) {
                const ageMatch = ageEl.textContent.trim().match(/(\d+)/);
                result.age = ageMatch ? parseInt(ageMatch[1]) : null;
            } else {
                result.age = null;
            }

            const bdEl = document.querySelector('[data-qa="resume-personal-birthday"]');
            result.birth_date = bdEl?.textContent?.trim()?.replace(/\u00a0/g, ' ') || null;

            const locEl = document.querySelector('[data-qa="resume-personal-address"]');
            result.location = locEl?.textContent?.trim() || null;

            const relocEl = document.querySelector('[data-qa="relocation_relocation_possible"]');
            result.relocation = relocEl?.textContent?.trim() || null;

            // Командировки
            const areaBlock = document.querySelector('[data-qa="resume-main-info_area-and-relocation"]');
            if (areaBlock) {
                const fullText = areaBlock.textContent;
                const btMatch = fullText.match(/(готов к (?:редким |частым )?командировкам|не готов к командировкам)/i);
                result.business_trips = btMatch ? btMatch[1] : null;
            } else {
                result.business_trips = null;
            }

            const updateEl = document.querySelector('[data-qa="resume-update-date"]');
            result.resume_updated = updateEl?.textContent?.trim() || null;

            // Статус поиска — тег positive
            const personalCard = nameEl?.closest('[class*="magritte-card"]');
            if (personalCard) {
                const statusTag = personalCard.querySelector('[class*="magritte-tag_style-positive"]');
                result.job_search_status = statusTag?.textContent?.trim() || null;
            } else {
                result.job_search_status = null;
            }

            // Последний онлайн
            result.last_online = null;
            const tags = document.querySelectorAll('[class*="tags--"] [class*="magritte-tag_style-neutral"]');
            for (const tag of tags) {
                const text = tag.textContent.trim();
                if (text.includes('Был') || text.includes('Была')) {
                    result.last_online = text;
                    break;
                }
            }

            return result;
        } catch (e) {
            console.warn('⚠️ Ошибка парсинга personal_info:', e);
            return null;
        }
    }

    /**
     * Блок 2 — contacts
     */
    parseContacts() {
        try {
            const contactsBlock = document.querySelector('[data-qa="resume-block-contacts"]');
            if (!contactsBlock) return null;

            const result = {};
            const text = contactsBlock.textContent || '';

            const phoneMatch = text.match(/(\+7[\s\d\-()]+\d)/);
            result.phone = phoneMatch ? phoneMatch[1].trim() : null;

            const emailMatch = text.match(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
            result.email = emailMatch ? emailMatch[1] : null;

            const tgMatch = text.match(/(?:Telegram|@)[\s:]*(@?\w+)/i);
            result.telegram = tgMatch ? tgMatch[1] : null;

            result.whatsapp = text.toLowerCase().includes('whatsapp');
            result.viber = text.toLowerCase().includes('viber');

            const prefMatch = text.match(/Предпочитаемый способ связи[:\s]*([^\n]+)/i);
            result.preferred_contact = prefMatch ? prefMatch[1].trim() : null;

            return result;
        } catch (e) {
            console.warn('⚠️ Ошибка парсинга contacts:', e);
            return null;
        }
    }

    /**
     * Блок 3 — cover_letter
     */
    parseCoverLetter() {
        try {
            const letterBlock = document.querySelector('[data-qa="resume-response-letter-block"]');
            if (!letterBlock) return null;

            const letterEl = letterBlock.querySelector('[data-qa="resume-response-letter"]');
            if (!letterEl) return null;

            const text = letterEl.innerText?.trim();
            return text ? { text } : null;
        } catch (e) {
            console.warn('⚠️ Ошибка парсинга cover_letter:', e);
            return null;
        }
    }

    /**
     * Блок 4 — desired_position
     */
    parseDesiredPosition() {
        try {
            const result = {};

            const titleEl = document.querySelector('[data-qa="resume-position"] [data-qa="title"]');
            if (titleEl) {
                result.titles = titleEl.textContent.trim().split(',').map(t => t.trim()).filter(Boolean);
            } else {
                result.titles = [];
            }

            const salaryEl = document.querySelector('[data-qa="resume-block-salary"]');
            result.salary = salaryEl?.textContent?.trim() || null;

            const specEl = document.querySelector('[data-qa="resume-specialization-professional-role-value"]');
            if (specEl) {
                result.specializations = specEl.textContent.trim().split(',').map(s => s.trim()).filter(Boolean);
            } else {
                result.specializations = [];
            }

            const emplEl = document.querySelector('[data-qa="resume-specialization-employment-value"]');
            result.employment_type = emplEl?.textContent?.trim() || null;

            const workEl = document.querySelector('[data-qa="resume-specialization-work-type-value"]');
            if (workEl) {
                result.work_format = workEl.textContent.trim()
                    .split(',').map(s => s.trim().replace(/\u00a0/g, ' ')).filter(Boolean);
            } else {
                result.work_format = [];
            }

            return result;
        } catch (e) {
            console.warn('⚠️ Ошибка парсинга desired_position:', e);
            return null;
        }
    }

    /**
     * Блок 5 — experience
     */
    parseExperience() {
        try {
            const expBlock = document.querySelector('[data-qa="resume-experience-block"]');
            if (!expBlock) return null;

            const result = {};

            // Общий опыт
            const titleEl = expBlock.querySelector('[data-qa="title"]');
            if (titleEl) {
                const text = titleEl.textContent.replace('Опыт работы:', '').trim().replace(/\u00a0/g, ' ');
                result.total_years = text || null;
            } else {
                result.total_years = null;
            }

            // Релевантный опыт
            const relEl = document.querySelector('[data-qa="relevant-experience-trigger"]');
            if (relEl) {
                const relText = relEl.textContent.trim().replace(/\u00a0/g, ' ');
                const match = relText.match(/(\d+\s*(?:лет|год|года)(?:\s*\d+\s*(?:мес|месяц[а-я]*))?)/);
                result.relevant_years = match ? match[1] : relText;
            } else {
                result.relevant_years = null;
            }

            // Позиции
            result.positions = [];
            const positionContainers = expBlock.querySelectorAll('[class*="magritte-h-spacing-container"]');

            positionContainers.forEach(container => {
                const pos = {};

                const periodFromEl = container.querySelector('[data-qa="resume-experience-period-from"]');
                const periodToEl = container.querySelector('[data-qa="resume-experience-period-to"]');
                pos.period_from = periodFromEl?.textContent?.trim()?.replace(/\u00a0/g, ' ')?.replace(/\s*-\s*$/, '') || null;
                pos.period_to = periodToEl?.textContent?.trim()?.replace(/\u00a0/g, ' ') || null;

                const durationEl = container.querySelector('[data-qa="resume-experience-value"]');
                pos.duration = durationEl?.textContent?.trim()?.replace(/\u00a0/g, ' ') || null;

                const companyEl = container.querySelector('[data-qa="resume-experience-company-title"]');
                if (companyEl) {
                    const linkText = companyEl.querySelector('[data-qa="resume-experience-company-title-text"]');
                    pos.company = (linkText || companyEl).textContent?.trim() || null;
                    if (companyEl.href) pos.company_url = companyEl.href;
                } else {
                    pos.company = null;
                }

                const areaEl = container.querySelector('[data-qa="resume-experience-company-area"]');
                pos.company_area = areaEl?.textContent?.trim() || null;

                const urlEl = container.querySelector('[data-qa="resume-experience-company-url"]');
                pos.company_website = urlEl?.textContent?.trim() || null;

                const industryEl = container.querySelector('[data-qa="resume-experience-industry-title"]');
                pos.industry = industryEl?.textContent?.trim() || null;

                const positionEl = container.querySelector('[data-qa="resume-block-experience-position"]');
                pos.position = positionEl?.textContent?.trim() || null;

                const descEl = container.querySelector('[data-qa="resume-block-experience-description"]');
                pos.description = descEl?.innerText?.trim() || null;

                if (pos.company || pos.position) {
                    result.positions.push(pos);
                }
            });

            return result;
        } catch (e) {
            console.warn('⚠️ Ошибка парсинга experience:', e);
            return null;
        }
    }

    /**
     * Блок 6 — skills
     */
    parseSkills() {
        try {
            const skillsTable = document.querySelector('[data-qa="skills-table"]');
            if (!skillsTable) return null;

            const result = { advanced: [], unspecified: [] };

            const advancedHeader = skillsTable.querySelector('[data-qa="skill-level-title-3"]');
            const unspecifiedHeader = skillsTable.querySelector('[data-qa="skill-level-title-0"]');

            if (advancedHeader) {
                const advancedGroup = advancedHeader.closest('[class*="magritte-v-spacing-container"]');
                if (advancedGroup) {
                    advancedGroup.querySelectorAll('[class*="magritte-tag"] [class*="label--"]').forEach(tag => {
                        const skill = tag.textContent.trim();
                        if (skill) result.advanced.push(skill);
                    });
                }
            }

            if (unspecifiedHeader) {
                const unspecGroup = unspecifiedHeader.closest('[class*="magritte-v-spacing-container"]');
                if (unspecGroup) {
                    unspecGroup.querySelectorAll('[class*="magritte-tag"] [class*="label--"]').forEach(tag => {
                        const skill = tag.textContent.trim();
                        if (skill) result.unspecified.push(skill);
                    });
                }
            }

            // Fallback — собираем все навыки
            if (result.advanced.length === 0 && result.unspecified.length === 0) {
                skillsTable.querySelectorAll('[class*="magritte-tag"] [class*="label--"]').forEach(tag => {
                    const skill = tag.textContent.trim();
                    if (skill) result.unspecified.push(skill);
                });
            }

            return result;
        } catch (e) {
            console.warn('⚠️ Ошибка парсинга skills:', e);
            return null;
        }
    }

    /**
     * Блок 7 — languages
     */
    parseLanguages() {
        try {
            const langBlock = document.querySelector('[data-qa="resume-languages-block"]');
            if (!langBlock) return null;

            const result = { native: [], other: [] };

            const langItems = langBlock.querySelectorAll('[data-qa="resume-block-language-item"]');
            langItems.forEach(item => {
                const text = item.textContent.trim();

                const parent = item.closest('[class*="magritte-v-spacing-container"]');
                const groupTitle = parent?.querySelector('[class*="title--"]');
                const isNative = groupTitle?.textContent?.includes('Родной');

                if (isNative) {
                    result.native.push(text);
                } else {
                    const parts = text.split('—').map(p => p.trim());
                    result.other.push({
                        language: parts[0],
                        level: parts[1] || null,
                        level_name: parts[2] || null
                    });
                }
            });

            return result;
        } catch (e) {
            console.warn('⚠️ Ошибка парсинга languages:', e);
            return null;
        }
    }

    /**
     * Блок 8 — about
     */
    parseAbout() {
        try {
            const aboutBlock = document.querySelector('[data-qa="resume-about-block"]');
            if (!aboutBlock) return null;

            const textEl = aboutBlock.querySelector('[class*="magritte-text_typography-paragraph-3-regular"]');
            if (!textEl) return null;

            const text = textEl.innerText?.trim();
            return text ? { text } : null;
        } catch (e) {
            console.warn('⚠️ Ошибка парсинга about:', e);
            return null;
        }
    }

    /**
     * Блок 9 — education
     */
    parseEducation() {
        try {
            const eduBlock = document.querySelector('[data-qa="resume-education-block"]');
            if (!eduBlock) return null;

            const result = {};

            // Уровень образования
            result.level = null;
            const spacingContainers = eduBlock.querySelectorAll('[class*="magritte-v-spacing-container"]');
            for (const container of spacingContainers) {
                const secondary = container.querySelector('[class*="magritte-text_style-secondary"]');
                if (secondary?.textContent?.includes('Уровень')) {
                    const primary = container.querySelector('[class*="magritte-text_style-primary"]');
                    result.level = primary?.textContent?.trim() || null;
                    break;
                }
            }

            // Учебные заведения
            result.institutions = [];
            const cells = eduBlock.querySelectorAll('[data-qa="cell"]');
            cells.forEach(cell => {
                const inst = {};
                const content = cell.querySelector('[class*="magritte-content"]');
                if (!content) return;

                const primaryEls = content.querySelectorAll('[class*="magritte-text_style-primary"]');
                if (primaryEls.length > 0) {
                    inst.name = primaryEls[0].textContent.trim();
                }

                const secondaryEl = content.querySelector('[class*="magritte-text_style-secondary"]');
                if (secondaryEl) {
                    const parts = secondaryEl.textContent.trim().split('•').map(p => p.trim());
                    if (parts.length >= 1) {
                        const facSpec = parts[0].split(',').map(p => p.trim());
                        inst.faculty = facSpec[0] || null;
                        inst.specialization = facSpec[1] || null;
                    }
                    if (parts.length >= 2) {
                        const yearMatch = parts[1].match(/(\d{4})/);
                        inst.year = yearMatch ? parseInt(yearMatch[1]) : null;
                    }
                    if (parts.length >= 3) {
                        inst.education_level = parts[2] || null;
                    }
                }

                if (inst.name) result.institutions.push(inst);
            });

            return result;
        } catch (e) {
            console.warn('⚠️ Ошибка парсинга education:', e);
            return null;
        }
    }

    // ========== ФОРМАТИРОВАНИЕ cv_text ДЛЯ AI ==========

    /**
     * Форматирует cv_structured в текст с заголовками для AI
     * Только 6 блоков: cover_letter, desired_position, experience, skills, about, education
     */
    formatCvText(structured) {
        const parts = [];

        const cover = structured.cover_letter;
        if (cover?.text) {
            parts.push(`## Сопроводительное письмо:\n${cover.text}`);
        }

        const pos = structured.desired_position;
        if (pos) {
            const posLines = [];
            if (pos.titles?.length) posLines.push(`Должности: ${pos.titles.join(', ')}`);
            if (pos.specializations?.length) posLines.push(`Специализации: ${pos.specializations.join(', ')}`);
            if (pos.salary) posLines.push(`Зарплата: ${pos.salary}`);
            if (pos.employment_type) posLines.push(`Занятость: ${pos.employment_type}`);
            if (pos.work_format?.length) posLines.push(`Формат: ${pos.work_format.join(', ')}`);
            if (posLines.length) parts.push(`## Желаемая должность:\n${posLines.join('\n')}`);
        }

        const exp = structured.experience;
        if (exp) {
            let expHeader = `## Опыт работы (${exp.total_years || 'не указан'}):`;
            if (exp.relevant_years) {
                expHeader += `\nОпыт в похожих должностях: ${exp.relevant_years}`;
            }
            const positions = (exp.positions || []).slice(0, 5);
            const posTexts = positions.map(p => {
                let text = `### ${p.company || '?'} (${p.period_from || '?'} - ${p.period_to || '?'}, ${p.duration || '?'})`;
                text += `\nДолжность: ${p.position || '?'}`;
                if (p.industry) text += `\nОтрасль: ${p.industry}`;
                if (p.description) text += `\n${p.description}`;
                return text;
            });
            parts.push(expHeader + '\n\n' + posTexts.join('\n\n'));
        }

        const skills = structured.skills;
        if (skills) {
            const skillLines = [];
            if (skills.advanced?.length) skillLines.push(`Продвинутый уровень: ${skills.advanced.join(', ')}`);
            if (skills.unspecified?.length) skillLines.push(`Остальные: ${skills.unspecified.join(', ')}`);
            if (skillLines.length) parts.push(`## Ключевые навыки:\n${skillLines.join('\n')}`);
        }

        const about = structured.about;
        if (about?.text) {
            parts.push(`## О себе:\n${about.text}`);
        }

        const edu = structured.education;
        if (edu) {
            const eduLines = [];
            if (edu.level) eduLines.push(`Уровень: ${edu.level}`);
            for (const inst of (edu.institutions || [])) {
                let line = inst.name || '?';
                if (inst.faculty) line += `, ${inst.faculty}`;
                if (inst.specialization) line += `, ${inst.specialization}`;
                if (inst.year) line += `, ${inst.year}`;
                eduLines.push(line);
            }
            if (eduLines.length) parts.push(`## Образование:\n${eduLines.join('\n')}`);
        }

        return parts.join('\n\n');
    }

    // ========== ОБРАТНАЯ СОВМЕСТИМОСТЬ ==========

    /**
     * Извлекает ФИО кандидата (для обратной совместимости)
     */
    extractName() {
        const nameElement = document.querySelector('[data-qa="resume-personal-name"]');
        return nameElement?.textContent?.trim() || 'Неизвестно';
    }

    // ========== ГЛАВНЫЙ МЕТОД ==========

    /**
     * Извлекает все данные резюме: cv_structured + cv_text
     * @returns {Promise<Object>} { name, cvStructured, fullText, url, extractedAt }
     */
    async extractAll() {
        // Фаза 2: разворачиваем скрытые блоки
        await this.ensureExpanded();

        // Фаза 3: парсим все 9 блоков
        const cvStructured = {
            personal_info: this.parsePersonalInfo(),
            contacts: this.parseContacts(),
            cover_letter: this.parseCoverLetter(),
            desired_position: this.parseDesiredPosition(),
            experience: this.parseExperience(),
            skills: this.parseSkills(),
            languages: this.parseLanguages(),
            about: this.parseAbout(),
            education: this.parseEducation(),
            source: 'hh.ru',
            parsed_at: new Date().toISOString(),
            parser_version: this.parserVersion
        };

        const fullText = this.formatCvText(cvStructured);
        const name = cvStructured.personal_info?.full_name || this.extractName();

        console.log('📢 HHParser v2.0: извлечены данные', {
            name,
            blocks: Object.keys(cvStructured).filter(k => !['source', 'parsed_at', 'parser_version'].includes(k) && cvStructured[k] !== null).length,
            textLength: fullText.length
        });

        return {
            name,
            cvStructured,
            fullText,
            url: window.location.href,
            extractedAt: new Date().toISOString()
        };
    }
}

window.hhParser = new HHParser();
console.log('✅ HHParser v2.0 загружен');
