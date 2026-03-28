# 🔒 CVS Analyzer — Безопасность

**Обновлено:** 2026-03-28

---

## Реализовано

| Механизм | Реализация |
|---|---|
| Хэширование паролей | Argon2 (argon2-cffi) |
| Аутентификация | JWT HS256, TTL 60 мин |
| SQL Injection | SQLAlchemy ORM (параметризованные запросы) |
| Ownership | Вакансии/анализы видны только владельцу |
| Admin guard | Промпты: CRUD только is_admin=True |
| CORS | ALLOWED_ORIGINS в .env |
| XSS | sanitizeHtml() для v-html на фронтенде |
| SECRET_KEY | Стабильный default для dev, обязателен в prod |

## Чеклист перед продакшеном

- [ ] 🔴 `SECRET_KEY` — уникальная строка ≥ 32 символа в .env
- [ ] 🔴 `ALLOWED_ORIGINS` — только реальные домены (не `*`)
- [ ] 🔴 `DEBUG=false`
- [ ] 🔴 HTTPS (Nginx + Let's Encrypt)
- [ ] 🟡 Rate Limiting (slowapi + Redis)
- [ ] 🟡 Логирование в файл/сервис
- [ ] 🟢 Блэклист токенов при logout
- [ ] 🟢 CSP-заголовки
