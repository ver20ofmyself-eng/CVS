from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from typing import List, Optional, Dict, Any
import logging
import csv
from io import StringIO

from pydantic import BaseModel, Field

from app.database import get_db
from app.models.user import User
from app.models.vacancy import Vacancy
from app.models.analyses import Analysis
from app.models.prompt import Prompt
from app.api.auth import get_current_user
from app.services.ai_service import ai_service, AIServiceError
from app.services.tariff_service import tariff_service
from app.schemas.analysis import (
    AnalysisResponse,
    AnalysisDetailResponse,
    AnalysisStatsResponse
)
from fastapi.responses import Response

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic схемы
# ============================================================================
class AnalysisRequest(BaseModel):
    """Запрос на анализ CV"""
    vacancy_id: int = Field(..., description="ID вакансии для анализа")
    cv_text: str = Field(..., min_length=50, description="Текст резюме для анализа")
    prompt_name: Optional[str] = Field("default_cv_analyzer", description="Имя промпта для анализа")


class AnalysisHistoryResponse(BaseModel):
    """Ответ для списка анализов"""
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

    class Config:
        from_attributes = True


# ============================================================================
# Эндпоинты
# ============================================================================

@router.post(
    "/",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    operation_id="analyze_cv",
    summary="Анализ резюме",
    description="Анализирует резюме на соответствие вакансии и сохраняет результат в историю"
)
async def analyze_cv(
    request: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Анализ CV на соответствие вакансии

    - **vacancy_id**: ID вакансии
    - **cv_text**: текст резюме (минимум 50 символов)
    - **prompt_name**: имя промпта для анализа (опционально)
    """
    start_time = datetime.now()
    logger.info(f"Анализ CV пользователем {current_user.email} для вакансии {request.vacancy_id}")

    # 1. Проверяем существование вакансии
    vacancy = db.query(Vacancy).filter(
        Vacancy.id == request.vacancy_id,
        Vacancy.user_id == current_user.id
    ).first()

    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена"
        )

    # 2. Проверяем наличие анализов
    analyses_left = tariff_service.get_user_analyses_left(db, current_user.id)

    if analyses_left <= 0:
        logger.warning(f"У пользователя {current_user.email} закончились анализы")
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Недостаточно анализов. Пополните баланс."
        )

    # 3. Проверяем промпт
    if request.prompt_name:
        prompt = db.query(Prompt).filter(
            Prompt.name == request.prompt_name,
            Prompt.is_active == True
        ).first()

        if not prompt:
            logger.warning(f"Промпт {request.prompt_name} не найден, использую дефолтный")
            request.prompt_name = "default_cv_analyzer"

    # 4. Конвертируем вакансию в словарь
    vacancy_dict = {
        "id": vacancy.id,
        "title": vacancy.title,
        "location": vacancy.location,
        "salary_range": vacancy.salary_range,
        "description_html": vacancy.description_html,
        "description_text": vacancy.description_text,
        "key_skills": vacancy.key_skills,
        "comment_for_ai": vacancy.comment_for_ai
    }

    # 5. Вызываем AI сервис
    try:
        analysis_result = await ai_service.analyze_cv(
            vacancy_dict,
            request.cv_text,
            db=db,
            user_id=current_user.id,
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        # 6. Уменьшаем счётчик анализов
        tariff_service.check_and_decrease_analyses(db, current_user.id)

        # 7. Сохраняем детальную информацию
        cv_preview = request.cv_text[:200] + ("..." if len(request.cv_text) > 200 else "")

        db_analysis = Analysis(
            user_id=current_user.id,
            vacancy_id=vacancy.id,
            cv_text=request.cv_text,
            cv_text_preview=cv_preview,
            ai_response=analysis_result,
            score=analysis_result.get('score'),
            recommendation=analysis_result.get('recommendation'),
            matched_skills=analysis_result.get('matched_skills', []),
            missing_skills=analysis_result.get('missing_skills', []),
            experience_years=analysis_result.get('experience_years'),
            location_match=str(analysis_result.get('location_match')) if analysis_result.get('location_match') is not None else None,
            salary_match=analysis_result.get('salary_match'),
            mode=analysis_result.get('mode', ai_service.mode),
            prompt_used=analysis_result.get('prompt_used', request.prompt_name),
            tokens_used=analysis_result.get('tokens_used', 0),
            processing_time=processing_time
        )
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)

        # 8. Получаем актуальный остаток
        new_analyses_left = tariff_service.get_user_analyses_left(db, current_user.id)

        logger.info(f"✅ Анализ завершён. Оценка: {analysis_result.get('score', 'N/A')}")

        # Формируем ответ
        response = {
            "id": db_analysis.id,
            "vacancy_id": vacancy.id,
            "vacancy_title": vacancy.title,
            "cv_text_preview": cv_preview,
            "score": analysis_result.get('score'),
            "recommendation": analysis_result.get('recommendation'),
            "matched_skills": analysis_result.get('matched_skills', []),
            "missing_skills": analysis_result.get('missing_skills', []),
            "experience_years": analysis_result.get('experience_years'),
            "location_match": str(analysis_result.get('location_match')) if analysis_result.get('location_match') is not None else None,
            "salary_match": analysis_result.get('salary_match'),
            "mode": analysis_result.get('mode', ai_service.mode),
            "prompt_used": analysis_result.get('prompt_used', request.prompt_name),
            "created_at": db_analysis.created_at,
            "analysis": analysis_result,
            "analyses_left": new_analyses_left
        }

        return response

    except AIServiceError as e:
        logger.error(f"❌ Ошибка AI-сервиса: {e.technical}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=e.user_message,
        )
    except Exception as e:
        logger.error(f"❌ Ошибка при анализе: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при анализе: {str(e)}"
        )


@router.get(
    "/prompts",
    operation_id="get_available_prompts",
    summary="Список доступных промптов"
)
async def get_available_prompts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить список доступных промптов"""
    prompts = db.query(Prompt).filter(Prompt.is_active == True).all()
    return [
        {
            "name": p.name,
            "description": p.description,
            "is_default": p.is_default,
            "version": p.version
        }
        for p in prompts
    ]


@router.get(
    "/history",
    response_model=List[AnalysisHistoryResponse],
    operation_id="get_analysis_history",
    summary="История анализов с фильтрацией"
)
async def get_analysis_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Сколько пропустить"),
    limit: int = Query(20, ge=1, le=100, description="Сколько вернуть"),
    vacancy_id: Optional[int] = Query(None, description="Фильтр по вакансии"),
    min_score: Optional[float] = Query(None, ge=0, le=10, description="Минимальная оценка"),
    recommendation: Optional[str] = Query(None, description="Фильтр по рекомендации"),
    date_from: Optional[datetime] = Query(None, description="С даты"),
    date_to: Optional[datetime] = Query(None, description="По дату"),
    search: Optional[str] = Query(None, description="Поиск по тексту CV")
):
    """
    Получение истории анализов с фильтрацией

    Параметры:
    - **skip**: пагинация (сколько пропустить)
    - **limit**: пагинация (сколько вернуть)
    - **vacancy_id**: фильтр по вакансии
    - **min_score**: минимальная оценка
    - **recommendation**: фильтр по рекомендации
    - **date_from**: с даты
    - **date_to**: по дату
    - **search**: поиск по тексту CV
    """
    query = db.query(Analysis).filter(Analysis.user_id == current_user.id)

    # Применяем фильтры
    if vacancy_id:
        query = query.filter(Analysis.vacancy_id == vacancy_id)

    if min_score is not None:
        query = query.filter(Analysis.score >= min_score)

    if recommendation:
        query = query.filter(Analysis.recommendation == recommendation)

    if date_from:
        query = query.filter(Analysis.created_at >= date_from)

    if date_to:
        query = query.filter(Analysis.created_at <= date_to)

    if search:
        query = query.filter(Analysis.cv_text.ilike(f"%{search}%"))

    # Сортировка по дате (сначала новые)
    query = query.order_by(Analysis.created_at.desc())

    # Пагинация
    analyses = query.offset(skip).limit(limit).all()

    # Добавляем название вакансии к каждому анализу
    result = []
    for analysis in analyses:
        analysis_dict = {
            "id": analysis.id,
            "vacancy_id": analysis.vacancy_id,
            "vacancy_title": None,
            "cv_text_preview": analysis.cv_text_preview,
            "score": analysis.score,
            "recommendation": analysis.recommendation,
            "matched_skills": analysis.matched_skills,
            "missing_skills": analysis.missing_skills,
            "experience_years": analysis.experience_years,
            "location_match": analysis.location_match,
            "salary_match": analysis.salary_match,
            "mode": analysis.mode,
            "prompt_used": analysis.prompt_used,
            "created_at": analysis.created_at
        }

        # Получаем название вакансии
        if analysis.vacancy_id:
            vacancy = db.query(Vacancy).filter(Vacancy.id == analysis.vacancy_id).first()
            if vacancy:
                analysis_dict["vacancy_title"] = vacancy.title

        result.append(analysis_dict)

    return result


@router.get(
    "/history/{analysis_id}",
    response_model=AnalysisDetailResponse,
    operation_id="get_analysis_detail",
    summary="Детальная информация об анализе"
)
async def get_analysis_detail(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получение детальной информации об анализе
    """
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Анализ не найден"
        )

    # Получаем название вакансии
    vacancy_title = None
    if analysis.vacancy_id:
        vacancy = db.query(Vacancy).filter(Vacancy.id == analysis.vacancy_id).first()
        if vacancy:
            vacancy_title = vacancy.title

    return {
        "id": analysis.id,
        "vacancy_id": analysis.vacancy_id,
        "vacancy_title": vacancy_title,
        "cv_text": analysis.cv_text,
        "cv_text_preview": analysis.cv_text_preview,
        "score": analysis.score,
        "recommendation": analysis.recommendation,
        "matched_skills": analysis.matched_skills,
        "missing_skills": analysis.missing_skills,
        "experience_years": analysis.experience_years,
        "location_match": analysis.location_match,
        "salary_match": analysis.salary_match,
        "mode": analysis.mode,
        "prompt_used": analysis.prompt_used,
        "ai_response": analysis.ai_response,
        "processing_time": analysis.processing_time,
        "tokens_used": analysis.tokens_used,
        "created_at": analysis.created_at
    }


@router.get(
    "/stats",
    response_model=AnalysisStatsResponse,
    operation_id="get_analysis_stats",
    summary="Статистика по анализам"
)
async def get_analysis_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365, description="Количество дней для статистики")
):
    """
    Получение статистики по анализам за последние N дней
    """
    date_from = datetime.now() - timedelta(days=days)

    # Базовый запрос
    query = db.query(Analysis).filter(
        Analysis.user_id == current_user.id,
        Analysis.created_at >= date_from
    )

    # Общее количество
    total_analyses = query.count()

    # Средняя оценка
    avg_score = db.query(func.avg(Analysis.score)).filter(
        Analysis.user_id == current_user.id,
        Analysis.created_at >= date_from,
        Analysis.score.isnot(None)
    ).scalar() or 0

    # Распределение по рекомендациям
    rec_dist = db.query(
        Analysis.recommendation,
        func.count(Analysis.id)
    ).filter(
        Analysis.user_id == current_user.id,
        Analysis.created_at >= date_from,
        Analysis.recommendation.isnot(None)
    ).group_by(Analysis.recommendation).all()

    recommendation_distribution = {r: c for r, c in rec_dist if r}

    # Распределение по режимам
    mode_dist = db.query(
        Analysis.mode,
        func.count(Analysis.id)
    ).filter(
        Analysis.user_id == current_user.id,
        Analysis.created_at >= date_from
    ).group_by(Analysis.mode).all()

    mode_distribution = {m: c for m, c in mode_dist}

    # Анализы по дням
    daily = db.query(
        cast(Analysis.created_at, Date).label('date'),
        func.count(Analysis.id).label('count')
    ).filter(
        Analysis.user_id == current_user.id,
        Analysis.created_at >= date_from
    ).group_by(cast(Analysis.created_at, Date)).order_by('date').all()

    analyses_by_day = [{"date": d.date.isoformat(), "count": d.count} for d in daily]

    # Топ совпавших навыков (заглушка - в реальности нужно парсить JSON)
    top_matched_skills = []
    top_missing_skills = []

    return {
        "total_analyses": total_analyses,
        "average_score": round(avg_score, 2),
        "recommendation_distribution": recommendation_distribution,
        "mode_distribution": mode_distribution,
        "analyses_by_day": analyses_by_day,
        "top_matched_skills": top_matched_skills,
        "top_missing_skills": top_missing_skills
    }


@router.delete(
    "/history/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_analysis",
    summary="Удаление анализа из истории"
)
async def delete_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удаление анализа из истории
    """
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Анализ не найден"
        )

    db.delete(analysis)
    db.commit()

    return None


@router.get(
    "/export",
    operation_id="export_analyses",
    summary="Экспорт истории анализов"
)
async def export_analyses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    format: str = Query("csv", regex="^(csv|json)$", description="Формат экспорта (csv или json)")
):
    """
    Экспорт истории анализов в CSV или JSON
    """
    analyses = db.query(Analysis).filter(
        Analysis.user_id == current_user.id
    ).order_by(Analysis.created_at.desc()).all()

    if format == "json":
        # Возвращаем JSON
        return analyses

    else:
        # Формируем CSV
        output = StringIO()
        writer = csv.writer(output)

        # Заголовки
        writer.writerow([
            "ID", "Дата", "Вакансия", "Оценка", "Рекомендация",
            "Совпавшие навыки", "Отсутствующие навыки", "Опыт (лет)",
            "Локация", "Зарплата", "Режим", "Промпт"
        ])

        # Данные
        for a in analyses:
            vacancy_title = "Не указана"
            if a.vacancy_id:
                vacancy = db.query(Vacancy).filter(Vacancy.id == a.vacancy_id).first()
                if vacancy:
                    vacancy_title = vacancy.title

            writer.writerow([
                a.id,
                a.created_at.strftime("%Y-%m-%d %H:%M"),
                vacancy_title,
                a.score or "",
                a.recommendation or "",
                ", ".join(a.matched_skills or []),
                ", ".join(a.missing_skills or []),
                a.experience_years or "",
                a.location_match or "",
                a.salary_match or "",
                a.mode,
                a.prompt_used or ""
            ])

        # Возвращаем CSV файл
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=analyses_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )
    