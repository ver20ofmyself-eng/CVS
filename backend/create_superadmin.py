#!/usr/bin/env python3
"""
Скрипт создания главного администратора CVS Analyzer.

Запуск (из корня проекта или из папки backend/):
    python backend/create_superadmin.py
    cd backend && python create_superadmin.py

Или с кастомными данными:
    ADMIN_EMAIL=you@example.com ADMIN_PASSWORD=MyPass123 python backend/create_superadmin.py
"""

import os
import sys

# Добавляем корень backend в sys.path (работает и из корня проекта, и из backend/)
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from datetime import datetime
from passlib.context import CryptContext

# Импортируем конфигурацию и БД (автоматически определит Docker/локальный режим)
from app.database import init_db, SessionLocal
from app.models.user import User
from app.models.tariff import Tariff
from app.models.user_tariffs import UserTariff

# ── Конфигурация ───────────────────────────────────────────────────────────────
ADMIN_EMAIL    = os.getenv("ADMIN_EMAIL",    "admin@cvsanalyzer.ru")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@CVS2024!")
ADMIN_NAME     = os.getenv("ADMIN_NAME",     "Главный администратор")
ADMIN_ANALYSES = int(os.getenv("ADMIN_ANALYSES", "10000"))

pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")


def create_superadmin():
    # Сначала создаём таблицы и начальные данные (если их нет)
    print("📦 Проверяем/создаём таблицы...")
    init_db()

    db = SessionLocal()
    try:
        # 1. Проверяем, существует ли уже
        existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if existing:
            print(f"⚠️  Пользователь {ADMIN_EMAIL} уже существует.")
            if not existing.is_admin:
                existing.is_admin = True
                print("   ✅ Выданы права администратора.")

            tariff = db.query(UserTariff).filter(
                UserTariff.user_id == existing.id,
                UserTariff.is_active == True
            ).first()
            if tariff:
                old_val = tariff.analyses_left
                tariff.analyses_left = ADMIN_ANALYSES
                print(f"   ✅ Анализов обновлено: {old_val} → {ADMIN_ANALYSES}")
            db.commit()
            return

        # 2. Создаём пользователя
        user = User(
            email         = ADMIN_EMAIL,
            password_hash = pwd_ctx.hash(ADMIN_PASSWORD),
            full_name     = ADMIN_NAME,
            is_admin      = True,
            is_active     = True,
        )
        db.add(user)
        db.flush()

        # 3. Находим тариф «Безлимитный» или создаём спецтариф
        tariff_obj = db.query(Tariff).filter(Tariff.name == "Безлимитный").first()
        if not tariff_obj:
            tariff_obj = Tariff(
                name           = "Безлимитный",
                analyses_limit = ADMIN_ANALYSES,
                price          = 0,
                is_active      = True,
            )
            db.add(tariff_obj)
            db.flush()
            print(f"   ✅ Создан тариф 'Безлимитный' ({ADMIN_ANALYSES} анализов).")

        # 4. Назначаем тариф
        db.add(UserTariff(
            user_id       = user.id,
            tariff_id     = tariff_obj.id,
            analyses_left = ADMIN_ANALYSES,
            purchased_at  = datetime.now(),
            expires_at    = None,
            is_active     = True,
        ))
        db.commit()

        print(f"""
╔══════════════════════════════════════════════════════╗
║         ✅ Суперадмин успешно создан!                ║
╠══════════════════════════════════════════════════════╣
║  Email:    {ADMIN_EMAIL:<42}║
║  Пароль:   {ADMIN_PASSWORD:<42}║
║  Имя:      {ADMIN_NAME:<42}║
║  Анализов: {str(ADMIN_ANALYSES):<42}║
╚══════════════════════════════════════════════════════╝
⚠️  Сохраните пароль — он нигде больше не отображается!
        """)

    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Создание главного администратора CVS Analyzer...")
    create_superadmin()
