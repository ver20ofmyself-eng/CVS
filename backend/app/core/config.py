"""
Конфигурация приложения CVS Analyzer.
Все параметры читаются из переменных окружения / backend/.env
"""
from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    # ── База данных ────────────────────────────────────────────────────────────
    DATABASE_URL:       str           = "postgresql://cvs_user:cvs_password@postgres:5432/cvs_analyzer"
    LOCAL_DATABASE_URL: Optional[str] = "postgresql://cvs_user:cvs_password@localhost:5433/cvs_analyzer"

    # ── JWT / безопасность ─────────────────────────────────────────────────────
    SECRET_KEY:                  str = secrets.token_urlsafe(48)  # всегда переопределять в .env
    ALGORITHM:                   str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── AI ─────────────────────────────────────────────────────────────────────
    AI_MODE:           str = "MOCK"   # "MOCK" или "REAL"
    DEEPSEEK_API_KEY:  str = ""
    DEEPSEEK_API_URL:  str = "https://api.deepseek.com/v1/chat/completions"
    DEEPSEEK_MODEL:    str = "deepseek-chat"
    DEEPSEEK_TIMEOUT:  int = 45       # секунд
    DEEPSEEK_RETRIES:  int = 2        # повторных попыток при ошибке сети

    # ── CORS ───────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = ["*"]

    # ── Приложение ─────────────────────────────────────────────────────────────
    APP_NAME:    str  = "CVS Analyzer"
    APP_VERSION: str  = "2.0.0"
    DEBUG:       bool = False

    # ── Тарифы ────────────────────────────────────────────────────────────────
    FREE_TIER_ANALYSES: int = 50

    class Config:
        env_file          = ".env"
        env_file_encoding = "utf-8"
        extra             = "ignore"


settings = Settings()
