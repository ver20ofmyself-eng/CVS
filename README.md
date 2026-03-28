# 🔍 CVS Analyzer

**AI-анализ резюме кандидатов на соответствие вакансии.**

Расширение для браузера Chrome/Yandex + веб-приложение для рекрутёров.

## Быстрый старт

```bash
# 1. Клонируйте репозиторий
git clone <repo-url> && cd cvs-analyzer

# 2. Скопируйте конфигурацию
cp .env.example .env   # отредактируйте при необходимости

# 3. Запустите через Docker
docker-compose up -d

# 4. Запустите фронтенд (dev)
cd frontend && npm install && npm run dev

# 5. Откройте http://localhost:3004
```

## Архитектура

| Компонент | Технологии | Описание |
|-----------|-----------|----------|
| **Backend** | FastAPI, PostgreSQL 15, SQLAlchemy 2 | 25 API-эндпоинтов, JWT auth, AI-анализ |
| **Frontend** | Vue 3, Pinia, Vite 5, Chart.js | 10 страниц: вакансии, история, профиль, промпты |
| **Extension** | Chrome Manifest V3 | Парсинг hh.ru, виджет анализа, кэширование |

## Версия 2.1.0

Полный список изменений — см. [CVS-Analyzer-docs-v2.1.md](./CVS-Analyzer-docs-v2.1.md)
