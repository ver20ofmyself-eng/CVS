from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from app.database import Base

class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id"), nullable=True)
    
    # Исходные данные
    cv_text = Column(Text, nullable=False)
    cv_text_preview = Column(String(500))
    
    # Результаты анализа
    ai_response = Column(JSON, nullable=True)
    score = Column(Float, nullable=True)
    recommendation = Column(String(50), nullable=True)
    
    # Детали для фильтрации
    matched_skills = Column(JSON, default=[])
    missing_skills = Column(JSON, default=[])
    experience_years = Column(Integer, nullable=True)
    location_match = Column(String(20), nullable=True)
    salary_match = Column(String(20), nullable=True)
    
    # Метаданные
    mode = Column(String(50), default="MOCK")
    prompt_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, default=0)
    processing_time = Column(Float, nullable=True)
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    