"""
Pydantic-схемы для анализов.

ВАЖНО: все JSON-поля (matched_skills, missing_skills) должны иметь
Optional + default, иначе Pydantic v2 выбрасывает ValidationError
когда в БД значение NULL.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ── Запрос ─────────────────────────────────────────────────────────────────────
class AnalysisRequest(BaseModel):
    vacancy_id: int = Field(..., description="ID вакансии для анализа")
    cv_text: str = Field(..., min_length=50, description="Текст резюме для анализа")
    cv_structured: Optional[Dict[str, Any]] = Field(None, description="Структурированные данные резюме (9 блоков)")
    candidate_name: Optional[str] = Field(None, description="ФИО кандидата (Фамилия Имя)")
    source_url: Optional[str] = Field(None, description="URL страницы резюме")
    prompt_name: Optional[str] = Field("default_cv_analyzer", description="Имя промпта для анализа")


# ── Ответ при создании анализа ─────────────────────────────────────────────────
class AnalysisResponse(BaseModel):
    id: int
    vacancy_id: Optional[int] = None
    vacancy_title: Optional[str] = None
    candidate_name: Optional[str] = None
    source_url: Optional[str] = None
    analysis_number: Optional[int] = None
    analysis_title: Optional[str] = None
    cv_text_preview: Optional[str] = None
    score: Optional[float] = None
    recommendation: Optional[str] = None
    matched_skills: Optional[List[str]] = []
    missing_skills: Optional[List[str]] = []
    experience_years: Optional[int] = None
    location_match: Optional[str] = None
    salary_match: Optional[str] = None
    mode: Optional[str] = "MOCK"
    prompt_used: Optional[str] = None
    created_at: Optional[datetime] = None
    analysis: Optional[Dict[str, Any]] = None
    analyses_left: Optional[int] = None

    class Config:
        from_attributes = True


# ── Ответ для списка (история) ─────────────────────────────────────────────────
class AnalysisHistoryResponse(BaseModel):
    id: int
    vacancy_id: Optional[int] = None
    vacancy_title: Optional[str] = None
    candidate_name: Optional[str] = None
    source_url: Optional[str] = None
    analysis_number: Optional[int] = None
    analysis_title: Optional[str] = None
    cv_text_preview: Optional[str] = None
    score: Optional[float] = None
    recommendation: Optional[str] = None
    matched_skills: Optional[List[str]] = []
    missing_skills: Optional[List[str]] = []
    experience_years: Optional[int] = None
    location_match: Optional[str] = None
    salary_match: Optional[str] = None
    mode: Optional[str] = "MOCK"
    prompt_used: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Детальный ответ ────────────────────────────────────────────────────────────
class AnalysisDetailResponse(BaseModel):
    id: int
    vacancy_id: Optional[int] = None
    vacancy_title: Optional[str] = None
    candidate_name: Optional[str] = None
    source_url: Optional[str] = None
    analysis_number: Optional[int] = None
    analysis_title: Optional[str] = None
    cv_text: Optional[str] = None
    cv_text_preview: Optional[str] = None
    score: Optional[float] = None
    recommendation: Optional[str] = None
    matched_skills: Optional[List[str]] = []
    missing_skills: Optional[List[str]] = []
    experience_years: Optional[int] = None
    location_match: Optional[str] = None
    salary_match: Optional[str] = None
    mode: Optional[str] = "MOCK"
    prompt_used: Optional[str] = None
    ai_response: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None
    tokens_used: Optional[int] = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Фильтры ───────────────────────────────────────────────────────────────────
class AnalysisFilterParams(BaseModel):
    vacancy_id: Optional[int] = None
    min_score: Optional[float] = Field(None, ge=0, le=10)
    max_score: Optional[float] = Field(None, ge=0, le=10)
    recommendation: Optional[str] = None
    mode: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None


# ── Статистика ─────────────────────────────────────────────────────────────────
class AnalysisStatsResponse(BaseModel):
    total_analyses: int = 0
    average_score: float = 0
    recommendation_distribution: Optional[Dict[str, int]] = {}
    mode_distribution: Optional[Dict[str, int]] = {}
    analyses_by_day: Optional[List[Dict[str, Any]]] = []
    top_matched_skills: Optional[List[Dict[str, Any]]] = []
    top_missing_skills: Optional[List[Dict[str, Any]]] = []

    class Config:
        from_attributes = True
