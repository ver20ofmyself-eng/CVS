from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, JSON, ForeignKey
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
    key_skills = Column(JSON, default=[])
    comment_for_ai = Column(Text)
    templates = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Связь с User (будет определена после импорта User)
    user = relationship("User", back_populates="vacancies")
    