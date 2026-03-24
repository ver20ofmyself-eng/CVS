"""
Управление соединением с базой данных (SQLAlchemy)
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,       # автоматически проверяет соединение
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency для FastAPI — предоставляет сессию БД."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
