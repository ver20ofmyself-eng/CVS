"""
Конфигурация приложения CVS Analyzer
Все параметры читаются из переменных окружения / .env файла
"""
from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    # ── База данных ────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://cvs_user:cvs_password@postgres:5432/cvs_analyzer"
    LOCAL_DATABASE_URL: Optional[str] = "postgresql://cvs_user:cvs_password@localhost:5433/cvs_analyzer"

    # ── JWT / безопасность ─────────────────────────────────────────────────────
    # ВАЖНО: в продакшене задать через переменную окружения SECRET_KEY
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # увеличен с 30 до 60 мин

    # ── AI настройки ───────────────────────────────────────────────────────────
    AI_MODE: str = "MOCK"          # "MOCK" или "REAL"
    DEEPSEEK_API_KEY: str = ""     # заполнить при переходе в REAL режим
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1/chat/completions"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_TIMEOUT: int = 30     # секунд

    # ── CORS ───────────────────────────────────────────────────────────────────
    # В продакшене заменить "*" на конкретные домены
    ALLOWED_ORIGINS: list[str] = ["*"]

    # ── Приложение ─────────────────────────────────────────────────────────────
    APP_NAME: str = "CVS Analyzer"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # ── Тарифы ────────────────────────────────────────────────────────────────
    FREE_TIER_ANALYSES: int = 50   # анализов при регистрации

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
