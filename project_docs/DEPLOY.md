# 🚀 CVS Analyzer — Деплой

**Обновлено:** 2026-03-28

---

## Локальная разработка

```bash
# 1. PostgreSQL
docker-compose up -d postgres

# 2. Backend
cd backend
pip install -r requirements.txt --break-system-packages
python create_superadmin.py    # создаёт таблицы + тарифы + промпт + админа
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Frontend
cd frontend
npm install
npm run dev                    # http://localhost:3004

# 4. Extension
# chrome://extensions → Загрузить распакованное → папка extension/
```

## Продакшен

```bash
# На сервере:
cp .env.example .env
# Отредактировать: SECRET_KEY, AI_MODE=REAL, DEEPSEEK_API_KEY, ALLOWED_ORIGINS

docker-compose up -d

# Frontend build:
cd frontend && npm ci && npm run build
# dist/ → /var/www/cvsanalyzer/

# Nginx: проксировать /api → localhost:8000, остальное → dist/
```

## Требования

- CPU: 2 vCPU, RAM: 2-4 GB, SSD: 20 GB
- PostgreSQL 15, Docker, Nginx
- Домен + SSL (Let's Encrypt)

## Важно при деплое

- Extension: заменить `localhost:8000` → реальный домен в `popup.js` и `api.js`
- Extension: заменить `localhost:3004` → реальный домен в `popup.js` и `content.js`
- `.env`: задать `ALLOWED_ORIGINS` = только реальные домены
