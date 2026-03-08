from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # База данных
    DATABASE_URL: str = "postgresql://cvs_user:cvs_password@postgres:5432/cvs_analyzer"
    
    # Для локального запуска скриптов
    LOCAL_DATABASE_URL: Optional[str] = "postgresql://cvs_user:cvs_password@localhost:5433/cvs_analyzer"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI Settings - добавляем новые поля
    AI_MODE: str = "MOCK"  # MOCK или REAL
    DEEPSEEK_API_KEY: str = ""  # API ключ для реального режима
    
    # Приложение
    APP_NAME: str = "CVS Analyzer"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Разрешаем дополнительные поля из окружения

settings = Settings()
