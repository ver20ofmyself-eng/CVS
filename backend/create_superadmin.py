#!/usr/bin/env python3
"""
Скрипт создания главного администратора CVS Analyzer.

Запуск (из папки backend/):
    python create_superadmin.py

Или с кастомными данными:
    ADMIN_EMAIL=you@example.com ADMIN_PASSWORD=MyPass123 python create_superadmin.py
"""

import os
import sys

# Добавляем корень backend в sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── ВАЖНО: импортируем ВСЕ модели до первого обращения к сессии.
# SQLAlchemy должен знать обо всех классах для разрешения relationship().
import app.models.user          # noqa
import app.models.vacancy       # noqa
import app.models.analyses      # noqa
import app.models.tariff        # noqa
import app.models.user_tariffs  # noqa
import app.models.payments      # noqa
import app.models.prompt        # noqa

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from app.models.user         import User
from app.models.tariff       import Tariff
from app.models.user_tariffs import UserTariff

# ── Конфигурация ───────────────────────────────────────────────────────────────
ADMIN_EMAIL    = os.getenv("ADMIN_EMAIL",    "admin@cvsanalyzer.ru")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@CVS2024!")
ADMIN_NAME     = os.getenv("ADMIN_NAME",     "Главный администратор")
ADMIN_ANALYSES = int(os.getenv("ADMIN_ANALYSES", "10000"))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cvs_user:cvs_password@localhost:5433/cvs_analyzer"
)

# ── Подключение ────────────────────────────────────────────────────────────────
engine  = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")


def create_superadmin():
    db = Session()
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

        # 3. Находим или создаём тариф «Суперадмин»
        tariff_obj = db.query(Tariff).filter(Tariff.name == "Суперадмин").first()
        if not tariff_obj:
            tariff_obj = Tariff(
                name           = "Суперадмин",
                analyses_limit = ADMIN_ANALYSES,
                price          = 0,
                is_active      = True,
            )
            db.add(tariff_obj)
            db.flush()
            print(f"   ✅ Создан тариф 'Суперадмин' ({ADMIN_ANALYSES} анализов).")

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
