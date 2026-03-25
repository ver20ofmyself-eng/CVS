"""Модели промптов."""
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Prompt(Base):
    __tablename__ = "prompts"

    id                   = Column(Integer, primary_key=True, index=True)
    name                 = Column(String(100), nullable=False, index=True)
    description          = Column(String(255))
    system_prompt        = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=False)
    response_format      = Column(JSON, default={})
    parameters           = Column(JSON, default={})
    is_active            = Column(Boolean, default=True)
    is_default           = Column(Boolean, default=False)   # Основной в рамках профиля
    version              = Column(Integer, default=1)

    # owner_id = NULL → системный промпт (глобальный, виден всем)
    # owner_id = <user_id> → пользовательский, виден только владельцу
    owner_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"),                     nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    owner      = relationship("User", foreign_keys=[owner_id])
    creator    = relationship("User", foreign_keys=[created_by])


class PromptHistory(Base):
    """История изменений промпта."""
    __tablename__ = "prompt_history"

    id                   = Column(Integer, primary_key=True, index=True)
    prompt_id            = Column(Integer, ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    name                 = Column(String(100))
    system_prompt        = Column(Text)
    user_prompt_template = Column(Text)
    parameters           = Column(JSON)
    version              = Column(Integer)
    changed_by           = Column(Integer, ForeignKey("users.id"), nullable=True)
    changed_at           = Column(TIMESTAMP, server_default=func.now())
    change_comment       = Column(String(255))
