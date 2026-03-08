from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class SalaryRange(BaseModel):
    min: Optional[int] = None
    max: Optional[int] = None
    currency: str = "RUB"
    
    class Config:
        json_schema_extra = {
            "example": {
                "min": 200000,
                "max": 350000,
                "currency": "RUB"
            }
        }

class VacancyBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Название вакансии")
    location: Optional[str] = Field(None, max_length=255, description="Локация")
    salary_range: Optional[SalaryRange] = Field(None, description="Зарплатный диапазон")
    description_html: Optional[str] = Field(None, description="HTML описание")
    description_text: Optional[str] = Field(None, description="Текстовое описание")
    key_skills: List[str] = Field(default=[], description="Ключевые навыки")
    comment_for_ai: Optional[str] = Field(None, max_length=1000, description="Комментарий для AI")
    templates: Optional[Dict[str, Any]] = Field(default={}, description="Шаблоны сообщений")
    is_active: bool = Field(default=True, description="Активна ли вакансия")

class VacancyCreate(VacancyBase):
    pass

class VacancyUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    salary_range: Optional[SalaryRange] = None
    description_html: Optional[str] = None
    description_text: Optional[str] = None
    key_skills: Optional[List[str]] = None
    comment_for_ai: Optional[str] = Field(None, max_length=1000)
    templates: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class VacancyResponse(VacancyBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "title": "Python Developer",
                "location": "Москва (удаленно)",
                "salary_range": {"min": 200000, "max": 350000, "currency": "RUB"},
                "description_html": "<p>Ищем Python разработчика</p>",
                "description_text": "Ищем Python разработчика",
                "key_skills": ["Python", "FastAPI", "PostgreSQL"],
                "comment_for_ai": "Опыт с микросервисами приветствуется",
                "templates": {
                    "invitation": "Здравствуйте! Приглашаем вас на вакансию...",
                    "interview": "Вопросы для интервью..."
                },
                "is_active": True,
                "created_at": "2026-02-14T14:33:36.327963",
                "updated_at": "2026-02-14T14:33:36.327963"
            }
        }

class VacancyListResponse(BaseModel):
    total: int
    items: List[VacancyResponse]
    