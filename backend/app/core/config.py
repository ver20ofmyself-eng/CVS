"""
Конфигурация приложения CVS Analyzer.
Все параметры читаются из переменных окружения / .env файла.

Порядок поиска .env:
  1. .env  (текущая директория — для Docker или запуска из корня)
  2. ../.env  (если запуск из backend/)
  3. backend/.env.example  (fallback для локальной разработки)
"""
import os
import socket
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


def _find_env_file() -> str:
    """Ищет .env файл в нескольких возможных локациях."""
    candidates = [
        Path(".env"),
        Path("../.env"),
        Path("backend/.env.example"),
        Path("../.env.example"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return ".env"  # fallback


def _is_docker() -> bool:
    """Определяет, работаем ли мы внутри Docker-контейнера."""
    # Метод 1: проверяем /.dockerenv
    if os.path.exists("/.dockerenv"):
        return True
    # Метод 2: проверяем hostname — резолвится ли 'postgres'
    try:
        socket.getaddrinfo("postgres", 5432)
        return True
    except socket.gaierror:
        return False


class Settings(BaseSettings):
    # ── База данных ────────────────────────────────────────────────────────────
    DATABASE_URL:       str           = "postgresql://cvs_user:cvs_password@postgres:5432/cvs_analyzer"
    LOCAL_DATABASE_URL: Optional[str] = "postgresql://cvs_user:cvs_password@localhost:5433/cvs_analyzer"

    # ── JWT / безопасность ─────────────────────────────────────────────────────
    SECRET_KEY:                  str = "dev-only-change-me-in-production-minimum-32-chars!!"
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
    APP_VERSION: str  = "2.1.0"
    DEBUG:       bool = False

    # ── Тарифы ────────────────────────────────────────────────────────────────
    FREE_TIER_ANALYSES: int = 50

    class Config:
        env_file          = _find_env_file()
        env_file_encoding = "utf-8"
        extra             = "ignore"


settings = Settings()

# Автоопределение: если не внутри Docker → переключаемся на LOCAL_DATABASE_URL
if not _is_docker() and settings.LOCAL_DATABASE_URL:
    import logging
    _logger = logging.getLogger(__name__)
    _logger.info(
        "🖥️  Обнаружен локальный запуск (не Docker) → используем LOCAL_DATABASE_URL: %s",
        settings.LOCAL_DATABASE_URL.split("@")[-1]  # логируем только хост, без пароля
    )
    settings.DATABASE_URL = settings.LOCAL_DATABASE_URL
