# 🤖 CVS Analyzer — Инструкции для AI-разработчика

> **Этот файл — первый, что должен прочитать AI при начале работы с проектом.**
> Он определяет КАК работать с проектом, а не ЧТО в нём есть.

**Обновлено:** 2026-03-28 | **Версия проекта:** 2.1.0

---

## 1. КОНТЕКСТ И ОПТИМИЗАЦИЯ ТОКЕНОВ

### 1.1 Приоритеты чтения файлов

При начале нового чата AI **обязан** прочитать файлы в следующем порядке:

| Шаг | Файл | Зачем | Когда обновлять |
|---|---|---|---|
| 1 | `project_docs/AI_DEV_GUIDE.md` | Правила работы | При изменении процессов |
| 2 | `project_docs/INDEX.md` | Реестр всех доков | При добавлении доки |
| 3 | `project_docs/BACKLOG.md` | Что делать дальше | После каждой задачи |
| 4 | Доки по конкретной задаче | Контекст задачи | По необходимости |

### 1.2 Принцип минимального контекста

**НЕ ЗАГРУЖАЙ ВСЕ ФАЙЛЫ.** Каждый файл в контексте тратит токены и размывает фокус.

Алгоритм:
1. Прочитай `AI_DEV_GUIDE.md` + `INDEX.md` + `BACKLOG.md`
2. Определи задачу → найди связанные компоненты
3. Загружай ТОЛЬКО файлы, необходимые для текущей задачи
4. При работе с backend — НЕ загружай frontend и наоборот
5. При работе с extension — НЕ загружай backend/frontend

### 1.3 .claudeignore (для Claude Code)

В корне проекта должен быть файл `.claudeignore`:
```
node_modules/
dist/
build/
.git/
__pycache__/
*.pyc
*.lock
poetry.lock
package-lock.json
frontend/package-lock.json
*.png
*.ico
*.jpg
*.jpeg
```

### 1.4 Фокусированный контекст (для Claude Code CLI)

```bash
# Работа с авторизацией
claude "fix auth bug" --include backend/app/api/auth.py backend/app/models/user.py

# Работа с вакансиями
claude "add field" --include backend/app/models/vacancy.py backend/app/schemas/vacancy.py backend/app/api/vacancies.py

# Работа с расширением
claude "fix widget" --include extension/content/** extension/utils/**
```

### 1.5 Когда создавать новый чат

Создавай **НОВЫЙ ЧАТ** когда:
- Переключаешься между компонентами (backend → frontend → extension)
- Контекст текущего чата > 60% использован
- Задача логически завершена и начинается другая
- Чат стал длинным (>15 сообщений с кодом)

При создании нового чата:
- Приложи актуальный zip-архив проекта
- Начни с: «Изучи `project_docs/AI_DEV_GUIDE.md`, затем `project_docs/BACKLOG.md`. Задача: [описание]»

---

## 2. АРХИТЕКТУРА ПРОЕКТА (КРАТКАЯ)

```
CVS-Analyzer-v2.1/
├── project_docs/          # 📚 Документация (ты здесь)
├── backend/               # 🐍 FastAPI + PostgreSQL + SQLAlchemy
│   ├── app/api/           #    API роутеры (auth, vacancies, analyze, prompts, tariffs, profile)
│   ├── app/models/        #    SQLAlchemy модели (user, vacancy, analysis, prompt, tariff...)
│   ├── app/schemas/       #    Pydantic схемы (request/response validation)
│   ├── app/services/      #    Бизнес-логика (ai_service, tariff_service)
│   └── app/core/          #    Конфигурация (.env, settings)
├── frontend/              # 🟢 Vue 3 + Pinia + Vite
│   └── src/
│       ├── views/         #    Страницы (VacancyDetailView, HistoryView...)
│       ├── components/    #    Компоненты (VacancyCard, NavBar, ToastContainer...)
│       ├── stores/        #    Pinia stores (auth, vacancies)
│       ├── composables/   #    Хуки (useToast)
│       ├── services/      #    API клиент (axios)
│       └── router/        #    Vue Router
├── extension/             # 🔌 Chrome Extension (Manifest V3)
│   ├── popup/             #    Popup окно (авторизация, выбор вакансии)
│   ├── content/           #    Content script (виджет на hh.ru)
│   ├── background/        #    Service worker
│   └── utils/             #    API клиент, кэш, парсер
├── .env                   # Переменные окружения
├── docker-compose.yml     # PostgreSQL + backend
└── .gitignore
```

### Ключевые зависимости между компонентами

```
Extension → [POST /api/analyze/] → Backend → AI (DeepSeek/MOCK)
Extension → [GET /api/vacancies/] → Backend → PostgreSQL
Frontend  → [all API endpoints]  → Backend → PostgreSQL
Frontend  ← [shared auth token]  → Extension (через chrome.storage)
```

---

## 3. NAMING CONVENTIONS

### 3.1 Backend (Python)

| Категория | Паттерн | Пример |
|---|---|---|
| Модели | `PascalCase`, единственное число | `User`, `Vacancy`, `Analysis` |
| Схемы | `{Model}{Action}` | `VacancyCreate`, `VacancyUpdate`, `VacancyResponse` |
| API функции | `snake_case`, глагол + существительное | `create_vacancy`, `get_analysis_history` |
| Роутеры | `router = APIRouter()` | — |
| Конфиг | `UPPER_SNAKE_CASE` | `DATABASE_URL`, `AI_MODE` |

### 3.2 Frontend (Vue 3 / JS)

| Категория | Паттерн | Пример |
|---|---|---|
| Компоненты (Views) | `PascalCase` + `View` | `VacancyDetailView.vue` |
| Компоненты (UI) | `PascalCase` | `VacancyCard.vue`, `NavBar.vue` |
| Stores | `use{Name}Store` | `useVacanciesStore`, `useAuthStore` |
| Composables | `use{Name}` | `useToast` |
| CSS классы | `kebab-case` с BEM-like prefix | `.vd-header`, `.vc-status-bar` |
| Events (emit) | `kebab-case` глагол | `@view`, `@edit`, `@clone`, `@archive` |

### 3.3 Extension

| Категория | Паттерн | Пример |
|---|---|---|
| CSS классы | `cvs-` prefix | `.cvs-analyzer-container`, `.cvs-score-high` |
| Storage keys | `cvs_` prefix | `cvs_last_vacancy`, `cvs_remember_me` |
| Messages | `UPPER_SNAKE_CASE` | `TOKEN_UPDATED`, `VACANCY_SELECTED` |

### 3.4 Базы данных

| Категория | Паттерн | Пример |
|---|---|---|
| Таблицы | `snake_case`, множественное число | `users`, `vacancies`, `analyses` |
| Колонки | `snake_case` | `user_id`, `created_at`, `is_active` |
| Индексы | `idx_{table}_{column}` | `idx_analyses_user_id` |
| FK | `{column} REFERENCES {table}(id)` | `user_id REFERENCES users(id)` |

---

## 4. WORKFLOW РАЗРАБОТКИ

### 4.1 Перед началом работы

```
1. Прочитать AI_DEV_GUIDE.md (этот файл)
2. Прочитать BACKLOG.md — понять текущие задачи
3. Определить scope задачи — какие файлы затронуты
4. Загрузить ТОЛЬКО необходимые файлы
```

### 4.2 Во время работы

```
1. Создавать файлы через полную замену (не патчи) для больших изменений
2. Проверять Python синтаксис: py_compile
3. Проверять Vue template integrity: парные <template>/<script>/<style>
4. Все List/Dict поля в Pydantic → Optional с default (во избежание ValidationError)
5. Все новые колонки БД → добавлять в _migrate_analyses_table()
```

### 4.3 После завершения

```
1. Обновить CHANGELOG.md
2. Обновить BACKLOG.md (закрыть задачу, добавить новые)
3. Собрать архив БЕЗ node_modules, .git, __pycache__, lock-файлов
4. Проверить размер архива (должен быть ~150-200 КБ)
```

---

## 5. ИЗВЕСТНЫЕ ПАТТЕРНЫ И ЛОВУШКИ

### 5.1 Pydantic v2 + SQLAlchemy JSON

**Проблема:** JSON-поля в БД могут быть `NULL`, но Pydantic ожидает `List[str]`.
**Решение:** Всегда `Optional[List[str]] = []` в схемах.
**Файлы:** `backend/app/schemas/analysis.py`, `backend/app/schemas/vacancy.py`

### 5.2 date-fns `format` конфликт

**Проблема:** Импорт `format` из date-fns конфликтует с переменными `format`.
**Решение:** Импорт как `dateFmt` или `format as dateFmt`.
**Файл:** `frontend/src/views/HistoryView.vue`

### 5.3 SQLAlchemy `create_all` не добавляет колонки

**Проблема:** `Base.metadata.create_all()` создаёт таблицы, но НЕ добавляет колонки в существующие.
**Решение:** Функция `_migrate_analyses_table()` в `database.py` с `ALTER TABLE ADD COLUMN IF NOT EXISTS`.

### 5.4 Extension — Docker vs localhost

**Проблема:** Extension всегда обращается к `localhost:8000`, а не к Docker-hostname.
**Решение:** `APP_BASE_URL` в popup.js и content.js — менять при деплое.

### 5.5 Шкала оценки

**Текущая:** 1-100% (не 1-10!)
**Пороги:** 85+ = high (зелёный), 50-84 = medium (жёлтый), <50 = low (красный)
**Рекомендации:** 5 уровней (Пригласить / Рекомендуется / С оговорками / Не рекомендуется / Не подходит)

---

## 6. ЦЕЛЕВАЯ АУДИТОРИЯ И КОНТЕКСТ ПРОДУКТА

- **Пользователи:** IT-рекрутёры РФ, фрилансеры, рекрутинговые агентства
- **Браузер:** преимущественно Yandex Browser (+ Chrome)
- **Язык интерфейса:** русский
- **Язык AI-ответов:** русский, ключевые навыки на оригинальном языке
- **Источник резюме:** hh.ru (приоритет), LinkedIn (в планах)
- **AI-провайдер:** DeepSeek (текущий), возможна замена
