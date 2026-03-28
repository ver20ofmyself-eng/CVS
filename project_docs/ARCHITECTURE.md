# 🏗️ CVS Analyzer — Архитектура

**Обновлено:** 2026-03-28

---

## Трёхзвенная архитектура

```
┌─────────────────────────────────────────────────┐
│                CVS ANALYZER                      │
├─────────────────────────────────────────────────┤
│                                                   │
│  Extension          Backend           AI          │
│  Chrome/Yandex  ←→  FastAPI      ←→  DeepSeek    │
│  Парсит hh.ru       PostgreSQL       (или MOCK)  │
│                        ↕                          │
│                    Frontend                       │
│                     Vue 3                         │
└─────────────────────────────────────────────────┘
```

## Стек технологий

| Слой | Технологии |
|---|---|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2, PostgreSQL 15, JWT (HS256), Argon2 |
| **Frontend** | Vue 3 (Composition API), Pinia, Vite 5, Axios, Chart.js, date-fns |
| **Extension** | Chrome Manifest V3, vanilla JS, Chrome Storage API |
| **AI** | DeepSeek API (deepseek-chat) / MOCK-режим |
| **DevOps** | Docker Compose, Nginx (prod) |

## Структура БД (9 таблиц)

```
users ──────────► user_tariffs ◄── tariffs
  │
  ├──► vacancies (+ client, status, dates)
  │       │
  │       └──► analyses (+ candidate_name, source_url, analysis_number)
  │
  ├──► payments ◄── tariffs
  │
  └──► prompts ──► prompt_history
```

### Ключевые поля (v2.1)

**vacancies:** `status` (active|completed|archived), `client`, `recruitment_start_date`, `recruitment_end_date`

**analyses:** `candidate_name`, `source_url`, `analysis_number` → автогенерация `analysis_title`, `cv_structured` (JSONB, 9 блоков)

**prompts:** `owner_id=NULL` = системный, `is_default`, `version` с историей

## Статусы вакансий

```
active ──► completed ──► archived
  ↑                         │
  └─────── reopen ──────────┘
```

## Шкала оценки AI

- **1-100%** (не 1-10)
- 5 уровней рекомендаций: Пригласить / Рекомендуется / С оговорками / Не рекомендуется / Не подходит
- Пороги: 85+ high, 50-84 medium, <50 low
