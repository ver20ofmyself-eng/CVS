# Задача №1 — Исследование ключевых блоков резюме `{key_cv_info}`

> **Подзадачи:** 1.1 (блоки), 1.2 (DB), 1.3 (DeepSeek API), 1.4 (ТЗ)
> **Дата:** 2026-03-28
> **Статус:** Исследование завершено, ожидает утверждения

---

## 1.1 Ключевые блоки информации `{key_cv_info}`

### Итого: 9 блоков

| № | Блок | Ключ в JSON | В AI | В DB | Требует разворачивания |
|---|------|-------------|------|------|------------------------|
| 1 | Личные данные | `personal_info` | ❌ | ✅ | Нет |
| 2 | Контакты | `contacts` | ❌ | ✅ | ✅ Клик «Показать все контакты» |
| 3 | Сопроводительное письмо | `cover_letter` | ✅ | ✅ | ✅ Клик «Развернуть» |
| 4 | Желаемая должность и условия | `desired_position` | ✅ | ✅ | Нет |
| 5 | Опыт работы | `experience` | ✅ | ✅ | Нет |
| 6 | Навыки | `skills` | ✅ | ✅ | Нет |
| 7 | Языки | `languages` | ❌ | ✅ | Нет |
| 8 | О себе | `about` | ✅ | ✅ | Возможно (триггер «Развернуть/Свернуть») |
| 9 | Образование | `education` | ✅ | ✅ | Нет |

### Детальная структура каждого блока

#### Блок 1 — `personal_info`

```json
{
  "full_name": "Зеленский Илья",
  "photo_url": "https://tula.hh.ru/photo/588253680.jpeg?...",
  "gender": "Мужчина",
  "age": 36,
  "birth_date": "9 декабря 1989",
  "location": "Москва",
  "relocation": "готов к переезду",
  "business_trips": "готов к редким командировкам",
  "resume_updated": "28.03.2026",
  "last_online": "Был сегодня в 13:19",
  "job_search_status": "Рассматривает предложения"
}
```

**Селекторы hh.ru:**
- `[data-qa="resume-personal-name"]` → full_name
- `[data-qa="resume-photo"] img` → photo_url (src)
- `[data-qa="resume-personal-gender"]` → gender
- `[data-qa="resume-personal-age"]` → age
- `[data-qa="resume-personal-birthday"]` → birth_date
- `[data-qa="resume-personal-address"]` → location
- `[data-qa="relocation_relocation_possible"]` → relocation
- `[data-qa="resume-update-date"]` → resume_updated
- Статус поиска — тег с классом `magritte-tag_style-positive` внутри блока personal info

#### Блок 2 — `contacts`

```json
{
  "phone": "+7 962 364-84-29",
  "email": "izelenskiy@bk.ru",
  "telegram": "@proxy3d",
  "whatsapp": true,
  "viber": true,
  "preferred_contact": "Telegram"
}
```

**Селекторы hh.ru:**
- `[data-qa="resume-block-contacts"]` → контейнер блока
- `[data-qa="resume-contacts-phone"]` → телефон (скрыт)
- `[data-qa="response-resume_show-phone-number"]` → кнопка «Показать все контакты»
- После клика данные появляются внутри `[data-qa="resume-block-contacts"]`

**⚠️ Требует клика** для раскрытия полной информации.

#### Блок 3 — `cover_letter`

```json
{
  "text": "Добрый день,\n\nВ резюме описано кратко по работе в компаниях..."
}
```

**Селекторы hh.ru:**
- `[data-qa="resume-response-letter-block"]` → контейнер
- `[data-qa="resume-response-letter"]` → текст (может быть обрезан)
- Кнопка «Развернуть» — `[data-qa="trigger-root"]` внутри `[data-qa="resume-response-letter-block"]`

**⚠️ Требует клика** на «Развернуть» для получения полного текста.

**Примечание:** Этот блок может отсутствовать, если кандидат откликнулся без сопроводительного письма, или если резюме открыто не из отклика.

#### Блок 4 — `desired_position`

```json
{
  "titles": ["ML-инженер", "Senior Developer", "Team lead", "Ведущий программист"],
  "specializations": ["Дата-сайентист", "Программист, разработчик"],
  "salary": null,
  "employment_type": "Полная занятость",
  "work_format": ["Удалённо", "Гибрид", "На месте работодателя"]
}
```

**Селекторы hh.ru:**
- `[data-qa="resume-position"] [data-qa="title"]` → titles (заголовок h2)
- `[data-qa="resume-block-salary"]` → salary
- `[data-qa="resume-specialization-professional-role-value"]` → specializations
- `[data-qa="resume-specialization-employment-value"]` → employment_type
- `[data-qa="resume-specialization-work-type-value"]` → work_format

#### Блок 5 — `experience`

```json
{
  "total_years": "17 лет 6 месяцев",
  "relevant_years": "7 лет 3 месяца",
  "positions": [
    {
      "period_from": "Дек 2023",
      "period_to": "сейчас",
      "duration": "2 года 4 мес",
      "company": "МТГ. Бизнес-решения",
      "company_url": "https://tula.hh.ru/employer/679410",
      "company_area": "Москва",
      "company_website": "www.mtg-biz.ru",
      "industry": "Информационные технологии, системная интеграция, интернет",
      "position": "Team Lead / Senior Python Developer",
      "description": "Основные достижения: ..."
    }
  ]
}
```

**Селекторы hh.ru:**
- `[data-qa="resume-experience-block"] [data-qa="title"]` → total_years (в заголовке)
- `[data-qa="relevant-experience-trigger"]` → relevant_years
- Каждая позиция — блок внутри `[data-qa="resume-experience-block"]`, содержащий:
  - `[data-qa="resume-experience-period"]` → period (from + to)
  - `[data-qa="resume-experience-value"]` → duration
  - `[data-qa="resume-experience-company-title"]` → company (текст или ссылка)
  - `[data-qa="resume-experience-company-area"]` → company_area
  - `[data-qa="resume-experience-company-url"]` → company_website
  - `[data-qa="resume-experience-industry-title"]` → industry
  - `[data-qa="resume-block-experience-position"]` → position
  - `[data-qa="resume-block-experience-description"]` → description

#### Блок 6 — `skills`

```json
{
  "advanced": ["Linux", "PyTorch", "TensorFlow", "Keras", "RAG", "ML", "LLM", "NLP", "Numpy"],
  "unspecified": ["PostgreSQL", "ORACLE", "Python", "Docker", "RabbitMQ", "Nginx", "jQuery", "Kafka", "Redis", "Kubernetes", "MongoDB", "Java", "JavaScript", "MS SQL Server", "PHP", "REST", "React", "pandas"]
}
```

**Селекторы hh.ru:**
- `[data-qa="skills-table"]` → контейнер
- `[data-qa="skill-level-title-3"]` → заголовок «Продвинутый уровень»
- `[data-qa="skill-level-title-0"]` → заголовок «Уровень не указан»
- Теги навыков — элементы `.magritte-tag` внутри каждой группы

#### Блок 7 — `languages`

```json
{
  "native": ["Русский"],
  "other": [
    {
      "language": "Английский",
      "level": "B2",
      "level_name": "Средне-продвинутый"
    }
  ]
}
```

**Селекторы hh.ru:**
- `[data-qa="resume-languages-block"]` → контейнер
- `[data-qa="resume-block-language-item"]` → каждый язык (текст содержит название и уровень)

#### Блок 8 — `about`

```json
{
  "text": "Сразу приведу несколько своих разработок:\n\nРазработал архитектуру..."
}
```

**Селекторы hh.ru:**
- `[data-qa="resume-about-block"]` → контейнер
- Текст внутри — элемент с `magritte-text_typography-paragraph-3-regular` внутри блока
- Может быть свёрнут с кнопкой «Развернуть»/«Свернуть» (`[data-qa="trigger-root"]`)

#### Блок 9 — `education`

```json
{
  "level": "Высшее образование",
  "institutions": [
    {
      "name": "Волгоградский государственный университет, Волгоград",
      "faculty": "Информационные технологии и телекоммуникации",
      "specialization": "Инженер-программист",
      "year": 2004,
      "education_level": "Высшее образование"
    }
  ]
}
```

**Селекторы hh.ru:**
- `[data-qa="resume-education-block"]` → контейнер
- Учебные заведения — ячейки `[data-qa="cell"]` внутри блока

---

## 1.2 Как ключевые блоки должны записываться в DB

### Текущее состояние

Сейчас в таблице `analyses` резюме хранится как:
- `cv_text TEXT` — сырой текст (один блок, без структуры)
- `cv_text_preview VARCHAR(500)` — первые 200 символов

**Проблема:** AI получает неструктурированный текст, не может отличить опыт от навыков, теряется контекст блоков.

### Предлагаемые изменения

#### Вариант: добавить поле `cv_structured JSONB` в таблицу `analyses`

```sql
ALTER TABLE analyses ADD COLUMN IF NOT EXISTS cv_structured JSONB;
```

Это поле будет содержать все 9 блоков в структурированном виде:

```json
{
  "personal_info": { ... },
  "contacts": { ... },
  "cover_letter": { ... },
  "desired_position": { ... },
  "experience": { ... },
  "skills": { ... },
  "languages": { ... },
  "about": { ... },
  "education": { ... },
  "source": "hh.ru",
  "parsed_at": "2026-03-28T15:30:00Z",
  "parser_version": "2.0"
}
```

**Почему JSONB, а не отдельные таблицы:**
1. Все данные приходят единым пакетом из расширения — один INSERT вместо 9.
2. Структура блоков может меняться (hh.ru обновляет вёрстку) — JSONB гибче.
3. Для задач 2-3 из бэклога (раздел «Кандидаты», карточка кандидата) позже можно вынести данные в отдельную таблицу `candidates`, а `cv_structured` останется как «снимок» на момент парсинга.
4. Поле `cv_text` сохраняется для обратной совместимости — туда записывается `formatForAI()` результат (текстовое представление).

#### Миграция (в `database.py` → `_migrate_analyses_table()`)

```python
# v2.2: структурированные данные резюме
BEGIN
    ALTER TABLE analyses ADD COLUMN IF NOT EXISTS cv_structured JSONB;
EXCEPTION WHEN duplicate_column THEN END;
```

### Схемы (Pydantic)

**Обновление `AnalysisRequest`:**

```python
class AnalysisRequest(BaseModel):
    vacancy_id: int
    cv_text: str = Field(..., min_length=50)           # сохраняем для совместимости
    cv_structured: Optional[Dict[str, Any]] = None     # НОВОЕ: структурированные данные
    candidate_name: Optional[str] = None
    source_url: Optional[str] = None
    prompt_name: Optional[str] = "default_cv_analyzer"
```

**Логика backend при получении:**
- Если `cv_structured` есть → сохраняем в `cv_structured`, формируем `cv_text` автоматически из блоков
- Если `cv_structured` нет → используем `cv_text` как есть (обратная совместимость)

---

## 1.3 Как ключевые блоки должны передаваться в DeepSeek API

### Текущее состояние

Сейчас в промпте `user_prompt_template` резюме передаётся как `{cv_text}` — одна строка до 4000 символов, без разделения на блоки.

### Предлагаемый формат

Вместо `{cv_text}` (сырой текст) передавать **структурированный текст с явными заголовками блоков**:

```
ТЕКСТ РЕЗЮМЕ:

## Сопроводительное письмо:
{cover_letter}

## Желаемая должность:
Должности: {desired_titles}
Специализации: {specializations}
Зарплата: {salary}
Занятость: {employment_type}
Формат: {work_format}

## Опыт работы ({total_experience}):
Опыт в похожих должностях: {relevant_experience}

### {company_1} ({period_1}, {duration_1})
Должность: {position_1}
Отрасль: {industry_1}
{description_1}

### {company_2} ({period_2}, {duration_2})
...

## Ключевые навыки:
Продвинутый уровень: {advanced_skills}
Остальные: {other_skills}

## О себе:
{about_text}

## Образование:
{education_level}
{institution_1}, {faculty_1}, {specialization_1}, {year_1}
```

### Реализация

**В `ai_service.py` → метод `_real_analysis()`:**

Добавить метод `_format_cv_for_ai(cv_structured)`, который:
1. Принимает `cv_structured` (JSONB из запроса)
2. Форматирует в текст с заголовками блоков (только 6 блоков для AI)
3. Обрезает до лимита токенов (опыт работы — самый длинный блок, можно ограничить последние 3-5 позиций)

```python
def _format_cv_for_ai(self, cv_structured: dict) -> str:
    """Форматирует структурированные данные CV в текст для AI."""
    parts = []

    # Сопроводительное письмо
    cover = cv_structured.get("cover_letter", {})
    if cover and cover.get("text"):
        parts.append(f"## Сопроводительное письмо:\n{cover['text']}")

    # Желаемая должность
    pos = cv_structured.get("desired_position", {})
    if pos:
        pos_lines = []
        if pos.get("titles"):
            pos_lines.append(f"Должности: {', '.join(pos['titles'])}")
        if pos.get("salary"):
            pos_lines.append(f"Зарплата: {pos['salary']}")
        if pos.get("employment_type"):
            pos_lines.append(f"Занятость: {pos['employment_type']}")
        if pos.get("work_format"):
            fmt = pos['work_format'] if isinstance(pos['work_format'], str) else ', '.join(pos['work_format'])
            pos_lines.append(f"Формат: {fmt}")
        if pos_lines:
            parts.append("## Желаемая должность:\n" + "\n".join(pos_lines))

    # Опыт работы (ограничиваем 5 последними позициями)
    exp = cv_structured.get("experience", {})
    if exp:
        exp_header = f"## Опыт работы ({exp.get('total_years', 'не указан')}):"
        if exp.get("relevant_years"):
            exp_header += f"\nОпыт в похожих должностях: {exp['relevant_years']}"
        positions = exp.get("positions", [])[:5]
        pos_texts = []
        for p in positions:
            pos_text = f"### {p.get('company', '?')} ({p.get('period_from', '?')} - {p.get('period_to', '?')}, {p.get('duration', '?')})"
            pos_text += f"\nДолжность: {p.get('position', '?')}"
            if p.get("industry"):
                pos_text += f"\nОтрасль: {p['industry']}"
            if p.get("description"):
                pos_text += f"\n{p['description']}"
            pos_texts.append(pos_text)
        parts.append(exp_header + "\n\n" + "\n\n".join(pos_texts))

    # Навыки
    skills = cv_structured.get("skills", {})
    if skills:
        skill_lines = []
        if skills.get("advanced"):
            skill_lines.append(f"Продвинутый уровень: {', '.join(skills['advanced'])}")
        if skills.get("unspecified"):
            skill_lines.append(f"Остальные: {', '.join(skills['unspecified'])}")
        if skill_lines:
            parts.append("## Ключевые навыки:\n" + "\n".join(skill_lines))

    # О себе
    about = cv_structured.get("about", {})
    if about and about.get("text"):
        parts.append(f"## О себе:\n{about['text']}")

    # Образование
    edu = cv_structured.get("education", {})
    if edu:
        edu_lines = []
        if edu.get("level"):
            edu_lines.append(f"Уровень: {edu['level']}")
        for inst in edu.get("institutions", []):
            line = inst.get("name", "?")
            if inst.get("faculty"):
                line += f", {inst['faculty']}"
            if inst.get("specialization"):
                line += f", {inst['specialization']}"
            if inst.get("year"):
                line += f", {inst['year']}"
            edu_lines.append(line)
        if edu_lines:
            parts.append("## Образование:\n" + "\n".join(edu_lines))

    return "\n\n".join(parts)
```

**В `user_prompt_template` промпта** — `{cv_text}` остаётся как плейсхолдер, но наполнение теперь структурированное.

### Обратная совместимость

Если `cv_structured` не передан (старая версия расширения) — используется `cv_text` как есть. Логика в `analyze.py`:

```python
if request.cv_structured:
    cv_for_ai = ai_service._format_cv_for_ai(request.cv_structured)
    cv_for_db = cv_for_ai  # или request.cv_text если передан
else:
    cv_for_ai = request.cv_text
    cv_for_db = request.cv_text
```

---

## 1.4 Стратегия парсинга (расширение)

### Фазы работы

| Фаза | Время | Действие | Статус для пользователя |
|-------|-------|----------|------------------------|
| 0 | 0-200мс | Инжект виджета-контейнера | ⏳ CVS Analyzer загружается… |
| 1 | 200мс-5с | MutationObserver ждёт `[data-qa="resume-personal-name"]` | 🔍 Определяю резюме… |
| 2 | +0.5-2с | Программно кликаем «Показать контакты», «Развернуть» | 📋 Загружаю данные… |
| 3 | мгновенно | Парсим все 9 блоков | ✅ Готово к анализу |
| Ошибка | 5с таймаут | Если ключевой элемент не найден | ⚠️ Не удалось определить резюме |

### Ключевые решения

1. **MutationObserver вместо таймеров** — работает в неактивных вкладках
2. **Graceful degradation** — каждый блок парсится независимо, `null` при отсутствии
3. **Мгновенная обратная связь** — виджет появляется в первые 200мс
4. **Таймаут 5 секунд** — если страница не загрузилась, показываем ошибку
5. **parser_version** — в `cv_structured` хранится версия парсера для будущих миграций

### Формат данных расширение → backend

```json
POST /api/analyze/
{
  "vacancy_id": 123,
  "cv_text": "форматированный текст для AI (автогенерация из cv_structured)",
  "cv_structured": {
    "personal_info": { ... },
    "contacts": { ... },
    "cover_letter": { ... },
    "desired_position": { ... },
    "experience": { ... },
    "skills": { ... },
    "languages": { ... },
    "about": { ... },
    "education": { ... },
    "source": "hh.ru",
    "parsed_at": "2026-03-28T15:30:00Z",
    "parser_version": "2.0"
  },
  "candidate_name": "Зеленский Илья",
  "source_url": "https://tula.hh.ru/resume/fb73e696...",
  "prompt_name": "default_cv_analyzer"
}
```

---

## Резюме изменений

### Расширение (extension)
- Полная переработка `hh.ru.js` → блочный парсер с 9 блоками
- Новый модуль `resumeExpander.js` — разворачивание скрытых блоков
- `MutationObserver` для ожидания загрузки и работы в неактивных вкладках
- Формирование `cv_structured` JSON и `cv_text` (текстовое представление)

### Backend
- Новая колонка `cv_structured JSONB` в таблице `analyses`
- Обновление `AnalysisRequest` — новое поле `cv_structured`
- Новый метод `_format_cv_for_ai()` в `ai_service.py`
- Обратная совместимость: если `cv_structured` не передан — работает как раньше

### Промпт
- `{cv_text}` теперь получает структурированный текст с заголовками блоков
- Качество анализа должно вырасти за счёт явного разделения информации
