"""
Модель вакансии.

Статусы (поле status):
  'active'    — Активна (подбор идёт)
  'completed' — Завершена (подбор окончен)
  'archived'  — В архиве (мягкое удаление)

Для обратной совместимости: is_active=True → status='active', is_active=False → status='archived'.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, JSON, ForeignKey, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Vacancy(Base):
    __tablename__ = "vacancies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    location = Column(String)
    salary_range = Column(JSON)
    description_html = Column(Text)
    description_text = Column(Text)
    key_skills = Column(JSON, default=list)
    comment_for_ai = Column(Text)
    templates = Column(JSON, default=dict)

    # ── Новые поля v2.1 ───────────────────────────────────────────────────────
    client = Column(String(255), nullable=True)              # Заказчик
    status = Column(String(20), default="active", index=True)  # 'active' | 'completed' | 'archived'
    recruitment_start_date = Column(Date, nullable=True)     # Дата начала подбора
    recruitment_end_date = Column(Date, nullable=True)       # Дата окончания подбора

    # ── Обратная совместимость ─────────────────────────────────────────────────
    is_active = Column(Boolean, default=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="vacancies")
