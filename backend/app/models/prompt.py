from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Prompt(Base):
    __tablename__ = "prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(String(255))
    system_prompt = Column(Text, nullable=False)  # Системный промпт (роль AI)
    user_prompt_template = Column(Text, nullable=False)  # Шаблон промпта с переменными
    response_format = Column(JSON, default={})  # Ожидаемый формат ответа
    parameters = Column(JSON, default={})  # Параметры (temperature, max_tokens, etc)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # Используется по умолчанию
    version = Column(Integer, default=1)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Связь с пользователем (кто создал/редактировал)
    user = relationship("User", foreign_keys=[created_by])

class PromptHistory(Base):
    """История изменений промптов"""
    __tablename__ = "prompt_history"
    
    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=False)
    name = Column(String(100))
    system_prompt = Column(Text)
    user_prompt_template = Column(Text)
    parameters = Column(JSON)
    version = Column(Integer)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    changed_at = Column(TIMESTAMP, server_default=func.now())
    change_comment = Column(String(255))
    