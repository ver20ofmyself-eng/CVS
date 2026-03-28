"""
API анализа резюме.

Исправления v2.1:
  - Все List/Dict поля в response_model имеют Optional + default → нет ValidationError при NULL в БД
  - Новые поля: candidate_name, source_url, analysis_number, analysis_title
  - analysis_title формируется автоматически: "{Фамилия} {Имя} [{МесДень}: {Номер}]"
  - export_format вместо format (конфликт с date-fns)
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from typing import List, Optional, Dict, Any
import logging
import csv
import re
from io import StringIO

from app.database import get_db
from app.models.user import User
from app.models.vacancy import Vacancy
from app.models.analyses import Analysis
from app.models.prompt import Prompt
from app.api.auth import get_current_user
from app.services.ai_service import ai_service, AIServiceError
from app.services.tariff_service import tariff_service
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisHistoryResponse,
    AnalysisDetailResponse,
    AnalysisStatsResponse,
)
from fastapi.responses import Response

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Русские месяцы для analysis_title ──────────────────────────────────────────
_MONTHS_RU = {
    1: "Янв", 2: "Фев", 3: "Мар", 4: "Апр", 5: "Май", 6: "Июн",
    7: "Июл", 8: "Авг", 9: "Сен", 10: "Окт", 11: "Ноя", 12: "Дек",
}


def _build_analysis_title(
    candidate_name: Optional[str],
    created_at: datetime,
    analysis_number: int,
) -> str:
    """
    Формирует название анализа:
      "{Фамилия} {Имя} [МесДД: №N]"
    Если имя не указано → "Кандидат [МесДД: №N]"
    """
    month_str = _MONTHS_RU.get(created_at.month, str(created_at.month))
    day_str = f"{created_at.day:02d}"
    tag = f"[{month_str}{day_str}: №{analysis_number}]"

    if candidate_name and candidate_name.strip():
        return f"{candidate_name.strip()} {tag}"
    return f"Кандидат {tag}"


def _compute_analysis_number(db: Session, user_id: int, source_url: Optional[str]) -> int:
    """
    Вычисляет порядковый номер анализа по данному source_url для пользователя.
    Если source_url не задан — считает по user_id глобально за текущие сутки.
    """
    if source_url and source_url.strip():
        # Нормализуем URL — убираем query params и fragment
        clean_url = source_url.split("?")[0].split("#")[0].rstrip("/")
        count = db.query(func.count(Analysis.id)).filter(
            Analysis.user_id == user_id,
            Analysis.source_url.ilike(f"{clean_url}%"),
        ).scalar() or 0
        return count + 1

    # Fallback: номер за текущие сутки
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    count = db.query(func.count(Analysis.id)).filter(
        Analysis.user_id == user_id,
        Analysis.created_at >= today_start,
    ).scalar() or 0
    return count + 1


def _safe_list(val) -> list:
    """Гарантирует, что значение — список (не None)."""
    if val is None:
        return []
    if isinstance(val, list):
        return val
    return []


# ============================================================================
# POST /  — Анализ резюме
# ============================================================================
@router.post(
    "/",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Анализ резюме",
)
async def analyze_cv(
    request: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_time = datetime.now()
    logger.info("Анализ CV пользователем %s для вакансии %s", current_user.email, request.vacancy_id)

    # 1. Проверяем вакансию
    vacancy = db.query(Vacancy).filter(
        Vacancy.id == request.vacancy_id,
        Vacancy.user_id == current_user.id,
    ).first()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")

    # 2. Проверяем остаток анализов
    analyses_left = tariff_service.get_user_analyses_left(db, current_user.id)
    if analyses_left <= 0:
        raise HTTPException(status_code=402, detail="Недостаточно анализов. Пополните баланс.")

    # 3. Проверяем промпт
    if request.prompt_name:
        prompt = db.query(Prompt).filter(Prompt.name == request.prompt_name, Prompt.is_active == True).first()
        if not prompt:
            request.prompt_name = "default_cv_analyzer"

    # 4. Вакансия → словарь
    vacancy_dict = {
        "id": vacancy.id, "title": vacancy.title, "location": vacancy.location,
        "salary_range": vacancy.salary_range,
        "description_html": vacancy.description_html, "description_text": vacancy.description_text,
        "key_skills": vacancy.key_skills or [], "comment_for_ai": vacancy.comment_for_ai,
    }

    # 5. AI-анализ
    try:
        analysis_result = await ai_service.analyze_cv(vacancy_dict, request.cv_text, db=db, user_id=current_user.id)
        processing_time = (datetime.now() - start_time).total_seconds()

        # 6. Списываем анализ
        tariff_service.check_and_decrease_analyses(db, current_user.id)

        # 7. Вычисляем номер анализа и название
        analysis_number = _compute_analysis_number(db, current_user.id, request.source_url)
        now = datetime.now()
        candidate_name = request.candidate_name or None
        analysis_title = _build_analysis_title(candidate_name, now, analysis_number)

        # 8. Сохраняем
        cv_preview = request.cv_text[:200] + ("..." if len(request.cv_text) > 200 else "")
        db_analysis = Analysis(
            user_id=current_user.id,
            vacancy_id=vacancy.id,
            candidate_name=candidate_name,
            source_url=request.source_url,
            analysis_number=analysis_number,
            cv_text=request.cv_text,
            cv_text_preview=cv_preview,
            ai_response=analysis_result,
            score=analysis_result.get("score"),
            recommendation=analysis_result.get("recommendation"),
            matched_skills=_safe_list(analysis_result.get("matched_skills")),
            missing_skills=_safe_list(analysis_result.get("missing_skills")),
            experience_years=analysis_result.get("experience_years"),
            location_match=str(analysis_result.get("location_match")) if analysis_result.get("location_match") is not None else None,
            salary_match=analysis_result.get("salary_match"),
            mode=analysis_result.get("mode", ai_service.mode),
            prompt_used=analysis_result.get("prompt_used", request.prompt_name),
            tokens_used=analysis_result.get("tokens_used", 0),
            processing_time=processing_time,
        )
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)

        new_analyses_left = tariff_service.get_user_analyses_left(db, current_user.id)
        logger.info("✅ Анализ #%d завершён. Оценка: %s, Название: %s", db_analysis.id, analysis_result.get("score"), analysis_title)

        return {
            "id": db_analysis.id,
            "vacancy_id": vacancy.id,
            "vacancy_title": vacancy.title,
            "candidate_name": candidate_name,
            "source_url": request.source_url,
            "analysis_number": analysis_number,
            "analysis_title": analysis_title,
            "cv_text_preview": cv_preview,
            "score": analysis_result.get("score"),
            "recommendation": analysis_result.get("recommendation"),
            "matched_skills": _safe_list(analysis_result.get("matched_skills")),
            "missing_skills": _safe_list(analysis_result.get("missing_skills")),
            "experience_years": analysis_result.get("experience_years"),
            "location_match": str(analysis_result.get("location_match")) if analysis_result.get("location_match") is not None else None,
            "salary_match": analysis_result.get("salary_match"),
            "mode": analysis_result.get("mode", ai_service.mode),
            "prompt_used": analysis_result.get("prompt_used", request.prompt_name),
            "created_at": db_analysis.created_at,
            "analysis": analysis_result,
            "analyses_left": new_analyses_left,
        }

    except AIServiceError as e:
        logger.error("❌ AI-сервис: %s", e.technical)
        raise HTTPException(status_code=503, detail=e.user_message)
    except Exception as e:
        logger.error("❌ Ошибка анализа: %s", e)
        raise HTTPException(status_code=500, detail=f"Ошибка при анализе: {str(e)}")


# ============================================================================
# GET /prompts — доступные промпты
# ============================================================================
@router.get("/prompts", summary="Список доступных промптов")
async def get_available_prompts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prompts = db.query(Prompt).filter(Prompt.is_active == True).all()
    return [{"name": p.name, "description": p.description, "is_default": p.is_default, "version": p.version} for p in prompts]


# ============================================================================
# GET /history — история с фильтрацией
# ============================================================================
@router.get("/history", response_model=List[AnalysisHistoryResponse], summary="История анализов")
async def get_analysis_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    vacancy_id: Optional[int] = Query(None),
    min_score: Optional[float] = Query(None, ge=0, le=10),
    recommendation: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
):
    query = db.query(Analysis).filter(Analysis.user_id == current_user.id)

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

    analyses = query.order_by(Analysis.created_at.desc()).offset(skip).limit(limit).all()

    # Подгружаем vacancy titles одним запросом
    vacancy_ids = {a.vacancy_id for a in analyses if a.vacancy_id}
    vacancies_map = {}
    if vacancy_ids:
        vacs = db.query(Vacancy.id, Vacancy.title).filter(Vacancy.id.in_(vacancy_ids)).all()
        vacancies_map = {v.id: v.title for v in vacs}

    result = []
    for a in analyses:
        vacancy_title = vacancies_map.get(a.vacancy_id)
        analysis_title = _build_analysis_title(
            a.candidate_name,
            a.created_at or datetime.now(),
            a.analysis_number or a.id,
        )
        result.append({
            "id": a.id,
            "vacancy_id": a.vacancy_id,
            "vacancy_title": vacancy_title,
            "candidate_name": a.candidate_name,
            "source_url": a.source_url,
            "analysis_number": a.analysis_number,
            "analysis_title": analysis_title,
            "cv_text_preview": a.cv_text_preview or "",
            "score": a.score,
            "recommendation": a.recommendation,
            "matched_skills": _safe_list(a.matched_skills),
            "missing_skills": _safe_list(a.missing_skills),
            "experience_years": a.experience_years,
            "location_match": a.location_match,
            "salary_match": a.salary_match,
            "mode": a.mode or "MOCK",
            "prompt_used": a.prompt_used,
            "created_at": a.created_at,
        })

    return result


# ============================================================================
# GET /history/{id} — детали анализа
# ============================================================================
@router.get("/history/{analysis_id}", response_model=AnalysisDetailResponse, summary="Детали анализа")
async def get_analysis_detail(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id,
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Анализ не найден")

    vacancy_title = None
    if analysis.vacancy_id:
        vacancy = db.query(Vacancy).filter(Vacancy.id == analysis.vacancy_id).first()
        if vacancy:
            vacancy_title = vacancy.title

    analysis_title = _build_analysis_title(
        analysis.candidate_name,
        analysis.created_at or datetime.now(),
        analysis.analysis_number or analysis.id,
    )

    return {
        "id": analysis.id,
        "vacancy_id": analysis.vacancy_id,
        "vacancy_title": vacancy_title,
        "candidate_name": analysis.candidate_name,
        "source_url": analysis.source_url,
        "analysis_number": analysis.analysis_number,
        "analysis_title": analysis_title,
        "cv_text": analysis.cv_text or "",
        "cv_text_preview": analysis.cv_text_preview or "",
        "score": analysis.score,
        "recommendation": analysis.recommendation,
        "matched_skills": _safe_list(analysis.matched_skills),
        "missing_skills": _safe_list(analysis.missing_skills),
        "experience_years": analysis.experience_years,
        "location_match": analysis.location_match,
        "salary_match": analysis.salary_match,
        "mode": analysis.mode or "MOCK",
        "prompt_used": analysis.prompt_used,
        "ai_response": analysis.ai_response,
        "processing_time": analysis.processing_time,
        "tokens_used": analysis.tokens_used or 0,
        "created_at": analysis.created_at,
    }


# ============================================================================
# GET /stats — статистика
# ============================================================================
@router.get("/stats", response_model=AnalysisStatsResponse, summary="Статистика")
async def get_analysis_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365),
):
    date_from = datetime.now() - timedelta(days=days)
    base = db.query(Analysis).filter(Analysis.user_id == current_user.id, Analysis.created_at >= date_from)

    total = base.count()
    avg_score = db.query(func.avg(Analysis.score)).filter(
        Analysis.user_id == current_user.id, Analysis.created_at >= date_from, Analysis.score.isnot(None),
    ).scalar() or 0

    rec_dist = dict(db.query(Analysis.recommendation, func.count(Analysis.id)).filter(
        Analysis.user_id == current_user.id, Analysis.created_at >= date_from, Analysis.recommendation.isnot(None),
    ).group_by(Analysis.recommendation).all())

    mode_dist = dict(db.query(Analysis.mode, func.count(Analysis.id)).filter(
        Analysis.user_id == current_user.id, Analysis.created_at >= date_from,
    ).group_by(Analysis.mode).all())

    daily = db.query(
        cast(Analysis.created_at, Date).label("date"), func.count(Analysis.id).label("count"),
    ).filter(
        Analysis.user_id == current_user.id, Analysis.created_at >= date_from,
    ).group_by(cast(Analysis.created_at, Date)).order_by("date").all()

    return {
        "total_analyses": total,
        "average_score": round(avg_score, 2),
        "recommendation_distribution": rec_dist,
        "mode_distribution": mode_dist,
        "analyses_by_day": [{"date": d.date.isoformat(), "count": d.count} for d in daily],
        "top_matched_skills": [],
        "top_missing_skills": [],
    }


# ============================================================================
# DELETE /history/{id}
# ============================================================================
@router.delete("/history/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить анализ")
async def delete_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Анализ не найден")
    db.delete(analysis)
    db.commit()
    return None


# ============================================================================
# GET /export — экспорт CSV/JSON
# ============================================================================
@router.get("/export", summary="Экспорт истории анализов")
async def export_analyses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    export_format: str = Query("csv", pattern="^(csv|json)$"),
):
    analyses = db.query(Analysis).filter(Analysis.user_id == current_user.id).order_by(Analysis.created_at.desc()).all()

    if export_format == "json":
        return analyses

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Название", "Дата", "Вакансия", "Кандидат", "Оценка", "Рекомендация",
        "Совпавшие навыки", "Отсутствующие навыки", "Опыт (лет)", "Режим", "URL резюме",
    ])

    vacancy_ids = {a.vacancy_id for a in analyses if a.vacancy_id}
    vmap = {}
    if vacancy_ids:
        vmap = {v.id: v.title for v in db.query(Vacancy.id, Vacancy.title).filter(Vacancy.id.in_(vacancy_ids)).all()}

    for a in analyses:
        title = _build_analysis_title(a.candidate_name, a.created_at or datetime.now(), a.analysis_number or a.id)
        writer.writerow([
            a.id, title,
            a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else "",
            vmap.get(a.vacancy_id, "—"),
            a.candidate_name or "—",
            a.score or "", a.recommendation or "",
            ", ".join(_safe_list(a.matched_skills)),
            ", ".join(_safe_list(a.missing_skills)),
            a.experience_years or "", a.mode or "",
            a.source_url or "",
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=analyses_{datetime.now().strftime('%Y%m%d')}.csv"},
    )
