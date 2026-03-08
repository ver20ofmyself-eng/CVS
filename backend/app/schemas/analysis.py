from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class AnalysisRequest(BaseModel):
    vacancy_id: int = Field(..., description="ID вакансии для анализа")
    cv_text: str = Field(..., min_length=50, description="Текст резюме для анализа")
    prompt_name: Optional[str] = Field("default_cv_analyzer", description="Имя промпта для анализа")

class AnalysisResponse(BaseModel):
    id: int
    vacancy_id: Optional[int]
    vacancy_title: Optional[str] = None
    cv_text_preview: str
    score: Optional[float]
    recommendation: Optional[str]
    matched_skills: List[str]
    missing_skills: List[str]
    experience_years: Optional[int]
    location_match: Optional[str]
    salary_match: Optional[str]
    mode: str
    prompt_used: Optional[str]
    created_at: datetime
    analysis: Optional[Dict[str, Any]] = None
    analyses_left: Optional[int] = None
    
    class Config:
        from_attributes = True

class AnalysisDetailResponse(BaseModel):
    id: int
    vacancy_id: Optional[int]
    vacancy_title: Optional[str] = None
    cv_text: str
    cv_text_preview: str
    score: Optional[float]
    recommendation: Optional[str]
    matched_skills: List[str]
    missing_skills: List[str]
    experience_years: Optional[int]
    location_match: Optional[str]
    salary_match: Optional[str]
    mode: str
    prompt_used: Optional[str]
    ai_response: Optional[Dict[str, Any]]
    processing_time: Optional[float]
    tokens_used: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class AnalysisFilterParams(BaseModel):
    vacancy_id: Optional[int] = None
    min_score: Optional[float] = Field(None, ge=0, le=10)
    max_score: Optional[float] = Field(None, ge=0, le=10)
    recommendation: Optional[str] = None
    mode: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None

class AnalysisStatsResponse(BaseModel):
    total_analyses: int
    average_score: float
    recommendation_distribution: Dict[str, int]
    mode_distribution: Dict[str, int]
    analyses_by_day: List[Dict[str, Any]]
    top_matched_skills: List[Dict[str, Any]]
    top_missing_skills: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True
        