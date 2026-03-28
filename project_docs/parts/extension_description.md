# 🔌 Расширение CVS Analyzer — Описание функционала и архитектуры

> **Задача:** 1.6
> **Дата:** 2026-03-28
> **Версия расширения:** 2.0.0

---

## 1. Общее описание

Chrome-расширение (Manifest V3) для парсинга резюме кандидатов на hh.ru и отправки структурированных данных на анализ в CVS Analyzer. Работает в Chrome и Yandex Browser.

**Что делает:**
- Определяет страницу резюме на hh.ru
- Автоматически разворачивает скрытые блоки (контакты, сопроводительное, «О себе»)
- Парсит 9 структурированных блоков данных из DOM
- Формирует `cv_structured` (JSON) и `cv_text` (текст с заголовками для AI)
- Отправляет данные на backend через `POST /api/analyze/`
- Отображает результат анализа во встроенном виджете на странице

---

## 2. Структура файлов

```
extension/
├── manifest.json              # Конфигурация Manifest V3
├── background/
│   └── service-worker.js      # Фоновый процесс (обработка сообщений)
├── content/
│   ├── resumeExpander.js      # Модуль разворачивания скрытых блоков
│   ├── hh.ru.js               # Блочный парсер резюме (9 блоков)
│   ├── content.js             # Основной content-script (виджет, UI, анализ)
│   └── content.css            # Стили виджета
├── popup/
│   ├── popup.html             # HTML popup-окна
│   ├── popup.js               # Логика popup (авторизация, выбор вакансии)
│   └── popup.css              # Стили popup
├── utils/
│   ├── api.js                 # HTTP-клиент для backend API
│   ├── cache.js               # Кэш результатов анализов
│   ├── parser.js              # Базовый парсер (общие утилиты)
│   └── storage.js             # Обёртка над chrome.storage
└── icons/
    ├── icon16.png
    ├── icon32.png
    ├── icon48.png
    └── icon128.png
```

### Порядок загрузки content-scripts

```
storage.js → cache.js → api.js → parser.js → resumeExpander.js → hh.ru.js → content.js
```

Все модули создают глобальные объекты на `window`, которые `content.js` использует через ссылки в конструкторе.

---

## 3. Фазы работы на странице резюме

| Фаза | Время | Действие | Статус пользователю |
|-------|-------|----------|---------------------|
| 0 | 0–200мс | Инжект виджета-контейнера | ⏳ CVS Analyzer загружается… |
| 1 | 200мс–5с | `MutationObserver` ждёт `[data-qa="resume-personal-name"]` | 🔍 Определяю резюме… |
| 2 | +0.5–2с | `ResumeExpander` кликает «Показать контакты», «Развернуть» | 📋 Загружаю данные… |
| 3 | мгновенно | `HHParser.buildStructured()` парсит все 9 блоков | ✅ Готово к анализу |
| Ошибка | 5с таймаут | Ключевой элемент не найден | ⚠️ Не удалось определить резюме |

---

## 4. Модуль `resumeExpander.js`

**Класс:** `ResumeExpander` → `window.resumeExpander`

Автоматически разворачивает скрытые блоки на странице резюме hh.ru программными кликами.

### Методы

| Метод | Что делает | Селектор клика |
|-------|-----------|----------------|
| `expandAll()` | Параллельно вызывает все три метода | — |
| `expandContacts()` | Клик «Показать все контакты» | `[data-qa="response-resume_show-phone-number"]` |
| `expandCoverLetter()` | Клик «Развернуть» в сопроводительном | `[data-qa="trigger-root"]` внутри `[data-qa="resume-response-letter-block"]` |
| `expandAbout()` | Клик «Развернуть» в «О себе» | `[data-qa="trigger-root"]` внутри `[data-qa="resume-about-block-title-right"]` |

**Особенности:**
- Каждый блок разворачивается независимо — ошибка в одном не блокирует остальные
- Проверяет, не развёрнут ли блок уже (label = «Свернуть»)
- `MutationObserver` для ожидания появления данных после клика (до 3с)
- Возвращает `{contacts: bool, coverLetter: bool, about: bool}`

---

## 5. Модуль `hh.ru.js` — Блочный парсер

**Класс:** `HHParser` → `window.hhParser`
**Версия парсера:** 2.0

### 9 блоков данных

| № | Блок | Метод | В AI | В DB | Ключ |
|---|------|-------|------|------|------|
| 1 | Личные данные | `parsePersonalInfo()` | ❌ | ✅ | `personal_info` |
| 2 | Контакты | `parseContacts()` | ❌ | ✅ | `contacts` |
| 3 | Сопроводительное | `parseCoverLetter()` | ✅ | ✅ | `cover_letter` |
| 4 | Желаемая должность | `parseDesiredPosition()` | ✅ | ✅ | `desired_position` |
| 5 | Опыт работы | `parseExperience()` | ✅ | ✅ | `experience` |
| 6 | Навыки | `parseSkills()` | ✅ | ✅ | `skills` |
| 7 | Языки | `parseLanguages()` | ❌ | ✅ | `languages` |
| 8 | О себе | `parseAbout()` | ✅ | ✅ | `about` |
| 9 | Образование | `parseEducation()` | ✅ | ✅ | `education` |

### Ключевые методы

**`buildStructured()`** — собирает все 9 блоков + метаданные:
```json
{
  "personal_info": { "full_name": "...", "age": 36, ... },
  "contacts": { "phone": "...", "email": "...", ... },
  "cover_letter": { "text": "..." },
  "desired_position": { "titles": [...], "salary": null, ... },
  "experience": { "total_years": "...", "positions": [...] },
  "skills": { "advanced": [...], "unspecified": [...] },
  "languages": { "native": [...], "other": [...] },
  "about": { "text": "..." },
  "education": { "level": "...", "institutions": [...] },
  "source": "hh.ru",
  "parsed_at": "2026-03-28T15:30:00Z",
  "parser_version": "2.0"
}
```

**`formatForAI(structured)`** — формирует текст для AI из 6 блоков:
```
## Сопроводительное письмо:
...

## Желаемая должность:
Должности: ML-инженер, Senior Developer
Занятость: Полная занятость
...

## Опыт работы (17 лет 6 месяцев):
Опыт в похожих должностях: 7 лет 3 месяца

### МТГ. Бизнес-решения (Дек 2023 - сейчас, 2 года 4 мес)
Должность: Team Lead / Senior Python Developer
...

## Ключевые навыки:
Продвинутый уровень: Linux, PyTorch, TensorFlow, ...
Остальные: PostgreSQL, Python, Docker, ...

## О себе:
...

## Образование:
Уровень: Высшее образование
...
```

**`extractAll()`** — совместимость со старым интерфейсом + `cvStructured`:
```javascript
{
  name: "Зеленский Илья",        // обратная совместимость
  title: "ML-инженер, ...",       // обратная совместимость
  salary: null,                    // обратная совместимость
  skills: ["Linux", "PyTorch"],   // обратная совместимость
  fullText: "## Сопроводительное...",  // форматированный текст для AI
  url: "https://tula.hh.ru/resume/...",
  extractedAt: "2026-03-28T...",
  cvStructured: { ... }           // НОВОЕ: структурированные данные
}
```

### Селекторы hh.ru (полная карта)

Все селекторы используют `data-qa` атрибуты hh.ru, верифицированы на реальной странице (март 2026).

**personal_info:**
- `[data-qa="resume-personal-name"]` → `full_name`
- `[data-qa="resume-photo"] img` → `photo_url`
- `[data-qa="resume-personal-gender"]` → `gender`
- `[data-qa="resume-personal-age"]` → `age`
- `[data-qa="resume-personal-birthday"]` → `birth_date`
- `[data-qa="resume-personal-address"]` → `location`
- `[data-qa="relocation_relocation_possible"]` → `relocation`
- `[data-qa="resume-update-date"]` → `resume_updated`
- `.magritte-tag_style-positive` → `job_search_status`

**contacts:**
- `[data-qa="resume-block-contacts"]` → контейнер (парсинг по regex из textContent)

**cover_letter:**
- `[data-qa="resume-response-letter-block"]` → контейнер
- `[data-qa="resume-response-letter"]` → текст

**desired_position:**
- `[data-qa="resume-position"] [data-qa="title"]` → `titles`
- `[data-qa="resume-block-salary"]` → `salary`
- `[data-qa="resume-specialization-professional-role-value"]` → `specializations`
- `[data-qa="resume-specialization-employment-value"]` → `employment_type`
- `[data-qa="resume-specialization-work-type-value"]` → `work_format`

**experience:**
- `[data-qa="resume-experience-block"]` → контейнер
- `[data-qa="resume-experience-block-title"] [data-qa="title"]` → `total_years`
- `[data-qa="relevant-experience-trigger"]` → `relevant_years`
- Позиции: `.magritte-h-spacing-container` внутри experience-block
  - `[data-qa="resume-experience-period-from/to"]` → период
  - `[data-qa="resume-experience-value"]` → длительность
  - `[data-qa="resume-experience-company-title"]` → компания
  - `[data-qa="resume-experience-company-area"]` → город
  - `[data-qa="resume-experience-company-url"]` → сайт
  - `[data-qa="resume-experience-industry-title"]` → отрасль
  - `[data-qa="resume-block-experience-position"]` → должность
  - `[data-qa="resume-block-experience-description"]` → описание

**skills:**
- `[data-qa="skills-table"]` → контейнер
- `[data-qa="skill-level-title-3"]` → группа «Продвинутый»
- `[data-qa="skill-level-title-0"]` → группа «Не указан»
- `.magritte-tag__label` → теги навыков

**languages:**
- `[data-qa="resume-languages-block"]` → контейнер
- `[data-qa="resume-block-language-item"]` → каждый язык

**about:**
- `[data-qa="resume-about-block"]` → контейнер
- `.magritte-text_typography-paragraph-3-regular` → текст

**education:**
- `[data-qa="resume-education-block"]` → контейнер
- `[data-qa="cell"]` → учебные заведения

---

## 6. Модуль `content.js` — Виджет и UI

**Класс:** `ContentInjector`

### Жизненный цикл

```
DOMContentLoaded → init() → startInjectionProcess()
  → tryInject() (интервал 300мс + MutationObserver)
    → injectAnalysisBlock()
      → resumeExpander.expandAll()  ← НОВОЕ: разворачиваем блоки
      → initializeAfterInjection()
        → loadVacancies()
        → checkCache()
```

### Основной поток анализа

```
Пользователь кликает «Анализировать»
  → analyze()
    → parser.extractAll()           ← возвращает {fullText, cvStructured, ...}
    → cache.get()                   ← проверка кэша
    → api.analyze(vacancyId, fullText, name, url, cvStructured)
      → POST /api/analyze/ с cv_text + cv_structured
    → displayResult()
    → cache.save()
```

### Виджет

Встраивается после блока personal_info на странице резюме. Содержит:
- Селектор вакансии + кнопка «Обновить»
- Кнопка «Анализировать»
- Блок результатов: score, рекомендация, навыки, сильные/слабые стороны
- Прогресс-бар (3 шага: загрузка → AI → результат)
- Индикатор кэша, режима (MOCK/REAL), timestamp

---

## 7. Модуль `api.js` — HTTP-клиент

**Класс:** `ApiClient` → `window.apiClient`

### Методы

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `login(email, password)` | `POST /api/auth/login` | Авторизация, сохранение токена |
| `getVacancies()` | `GET /api/vacancies/` | Список вакансий пользователя |
| `analyze(vacancyId, cvText, name, url, cvStructured)` | `POST /api/analyze/` | Анализ резюме |
| `getAnalysis(id)` | `GET /api/analyze/history/{id}` | Детали анализа |
| `getPrompts()` | `GET /api/analyze/prompts` | Список промптов |

### Формат запроса анализа

```json
POST /api/analyze/
{
  "vacancy_id": 123,
  "cv_text": "## Сопроводительное письмо:\n...",
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

## 8. Обратная совместимость

- Если `cv_structured` не передан (старая версия расширения) — backend использует `cv_text` как есть
- `extractAll()` возвращает все старые поля (`name`, `title`, `salary`, `skills`, `fullText`) + новый `cvStructured`
- Backend метод `format_cv_for_ai()` дублирует логику `formatForAI()` из расширения — для случаев когда текст нужно пересобрать на сервере

---

## 9. Кэширование

Модуль `cache.js` хранит результаты анализов в `chrome.storage.local`:
- Ключ кэша: hash от `vacancyId + cvText + url`
- TTL: текущая сессия (очищается при закрытии браузера)
- При смене вакансии — проверяется кэш для текущей комбинации

---

## 10. Popup

Popup-окно расширения предоставляет:
- Авторизацию (email/password) с опцией «Запомнить меня»
- Выбор вакансии из списка (без опции «любая»)
- Последние 5 анализов
- Ссылку на сайт CVS Analyzer
- Индикатор авторизации (зелёная/красная точка)
