# CVS Analyzer

> AI-ассистент для рекрутёра: анализирует резюме с hh.ru на соответствие вакансии

## Архитектура

```
┌──────────────────┐      REST API      ┌──────────────────┐
│  Расширение      │ ◄────────────────► │  Backend         │
│  Chrome/Yandex   │                    │  FastAPI + PG    │
│  Парсит hh.ru    │                    │  DeepSeek AI     │
└──────────────────┘                    └────────┬─────────┘
                                                 │
                                        ┌────────▼─────────┐
                                        │  Frontend        │
                                        │  Vue 3           │
                                        │  Управление      │
                                        └──────────────────┘
```

## Быстрый старт (Docker)

```bash
# 1. Скопировать и заполнить .env
cp .env.example .env

# 2. Запустить
docker-compose up -d

# 3. Backend доступен на: http://localhost:8000
#    API-документация:   http://localhost:8000/api/docs
```

## Фронтенд (локально)

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

## Расширение

1. Открыть в Yandex/Chrome: `chrome://extensions/`
2. Включить **Режим разработчика**
3. **Загрузить распакованное** → выбрать папку `extension/`

## Структура проекта

```
├── backend/
│   ├── app/
│   │   ├── api/         # FastAPI роутеры
│   │   ├── core/        # Конфиг, безопасность
│   │   ├── models/      # SQLAlchemy модели
│   │   ├── schemas/     # Pydantic схемы
│   │   └── services/    # AI сервис, тарифы
│   ├── init.sql         # Инициализация БД
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/  # Компоненты UI
│       ├── views/       # Страницы
│       ├── stores/      # Pinia store
│       └── services/    # API клиент
├── extension/
│   ├── content/         # Внедряется на hh.ru
│   ├── popup/           # Попап расширения
│   └── utils/           # Утилиты
└── docker-compose.yml
```

## Конфигурация (.env)

| Переменная | Описание | По умолчанию |
|---|---|---|
| `SECRET_KEY` | JWT секрет (сгенерировать!) | random |
| `AI_MODE` | `MOCK` или `REAL` | `MOCK` |
| `DEEPSEEK_API_KEY` | Ключ DeepSeek API | пусто |
| `DEBUG` | Отладочный режим | `False` |

## Тарифы (дефолтные)

| Название | Анализов | Цена |
|---|---|---|
| Бесплатный | 50 | 0 ₽ |
| Частичный | 100 | 500 ₽ |
| Полный | 300 | 1200 ₽ |

## API Документация

После запуска: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
