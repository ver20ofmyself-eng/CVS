from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date


class SalaryRange(BaseModel):
    min: Optional[int] = None
    max: Optional[int] = None
    currency: str = "RUB"


class VacancyBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Название вакансии")
    location: Optional[str] = Field(None, max_length=255)
    salary_range: Optional[SalaryRange] = None
    description_html: Optional[str] = None
    description_text: Optional[str] = None
    key_skills: Optional[List[str]] = Field(default=[])
    comment_for_ai: Optional[str] = Field(None, max_length=2000)
    templates: Optional[Dict[str, Any]] = Field(default={})
    client: Optional[str] = Field(None, max_length=255, description="Заказчик")
    status: Optional[str] = Field("active", description="active | completed | archived")
    is_active: Optional[bool] = True
    recruitment_start_date: Optional[date] = Field(None, description="Дата начала подбора")
    recruitment_end_date: Optional[date] = Field(None, description="Дата окончания подбора")


class VacancyCreate(VacancyBase):
    pass


class VacancyUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    salary_range: Optional[SalaryRange] = None
    description_html: Optional[str] = None
    description_text: Optional[str] = None
    key_skills: Optional[List[str]] = None
    comment_for_ai: Optional[str] = Field(None, max_length=2000)
    templates: Optional[Dict[str, Any]] = None
    client: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = None
    is_active: Optional[bool] = None
    recruitment_start_date: Optional[date] = None
    recruitment_end_date: Optional[date] = None


class VacancyResponse(BaseModel):
    id: int
    user_id: int
    title: str
    location: Optional[str] = None
    salary_range: Optional[Dict[str, Any]] = None
    description_html: Optional[str] = None
    description_text: Optional[str] = None
    key_skills: Optional[List[str]] = []
    comment_for_ai: Optional[str] = None
    templates: Optional[Dict[str, Any]] = {}
    client: Optional[str] = None
    status: Optional[str] = "active"
    is_active: Optional[bool] = True
    recruitment_start_date: Optional[date] = None
    recruitment_end_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VacancyListResponse(BaseModel):
    total: int
    items: List[VacancyResponse]
