"""
API вакансий — CRUD + фильтрация + статусы.

Статусы: active → completed → archived
Обратная совместимость: is_active синхронизируется со status.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import date
import logging

from app.database import get_db
from app.models.vacancy import Vacancy
from app.models.user import User
from app.schemas.vacancy import VacancyCreate, VacancyUpdate, VacancyResponse, VacancyListResponse
from app.api.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

VALID_STATUSES = {"active", "completed", "archived"}


def _sync_status(vacancy):
    """Синхронизирует is_active ↔ status."""
    if vacancy.status == "archived":
        vacancy.is_active = False
    elif vacancy.status in ("active", "completed"):
        vacancy.is_active = True
    # Обратная совместимость: если is_active изменился без status
    if not vacancy.is_active and vacancy.status == "active":
        vacancy.status = "archived"


@router.post("/", response_model=VacancyResponse, status_code=status.HTTP_201_CREATED)
async def create_vacancy(
    vacancy: VacancyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создание новой вакансии."""
    logger.info("Создание вакансии пользователем %s", current_user.email)

    data = vacancy.model_dump(exclude_unset=True)
    # Гарантируем корректный статус
    if data.get("status") not in VALID_STATUSES:
        data["status"] = "active"

    db_vacancy = Vacancy(user_id=current_user.id, **data)
    _sync_status(db_vacancy)

    db.add(db_vacancy)
    db.commit()
    db.refresh(db_vacancy)

    logger.info("Вакансия создана: ID %d", db_vacancy.id)
    return db_vacancy


@router.get("/", response_model=VacancyListResponse)
async def get_vacancies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status", description="active|completed|archived"),
    active_only: bool = Query(False, description="Только активные (обратная совместимость)"),
    search: Optional[str] = Query(None),
    client: Optional[str] = Query(None, description="Фильтр по заказчику"),
):
    """Список вакансий пользователя с фильтрацией."""
    query = db.query(Vacancy).filter(Vacancy.user_id == current_user.id)

    # Фильтр по статусу
    if status_filter and status_filter in VALID_STATUSES:
        query = query.filter(Vacancy.status == status_filter)
    elif active_only:
        query = query.filter(Vacancy.status.in_(["active", "completed"]))

    if search:
        query = query.filter(Vacancy.title.ilike(f"%{search}%"))

    if client:
        query = query.filter(Vacancy.client.ilike(f"%{client}%"))

    # Сортировка: active → completed → archived, внутри — по дате (новые первые)
    status_order = desc(
        Vacancy.status == "active"
    )
    query = query.order_by(
        desc(Vacancy.status == "active"),
        desc(Vacancy.status == "completed"),
        desc(Vacancy.created_at),
    )

    total = query.count()
    items = query.offset(skip).limit(limit).all()

    return {"total": total, "items": items}


@router.get("/{vacancy_id}", response_model=VacancyResponse)
async def get_vacancy(
    vacancy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    vacancy = db.query(Vacancy).filter(
        Vacancy.id == vacancy_id, Vacancy.user_id == current_user.id,
    ).first()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")
    return vacancy


@router.put("/{vacancy_id}", response_model=VacancyResponse)
async def update_vacancy(
    vacancy_id: int,
    vacancy_update: VacancyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновление вакансии."""
    vacancy = db.query(Vacancy).filter(
        Vacancy.id == vacancy_id, Vacancy.user_id == current_user.id,
    ).first()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")

    update_data = vacancy_update.model_dump(exclude_unset=True)

    # Валидируем статус
    if "status" in update_data and update_data["status"] not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"Недопустимый статус: {update_data['status']}")

    for field, value in update_data.items():
        setattr(vacancy, field, value)

    _sync_status(vacancy)
    db.commit()
    db.refresh(vacancy)

    logger.info("Вакансия ID %d обновлена (статус: %s)", vacancy_id, vacancy.status)
    return vacancy


@router.delete("/{vacancy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vacancy(
    vacancy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Мягкое удаление — переводит в статус archived."""
    vacancy = db.query(Vacancy).filter(
        Vacancy.id == vacancy_id, Vacancy.user_id == current_user.id,
    ).first()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")

    vacancy.status = "archived"
    vacancy.is_active = False
    db.commit()

    logger.info("Вакансия ID %d → archived", vacancy_id)
    return None


@router.post("/{vacancy_id}/clone", response_model=VacancyResponse)
async def clone_vacancy(
    vacancy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Клонирование вакансии."""
    original = db.query(Vacancy).filter(
        Vacancy.id == vacancy_id, Vacancy.user_id == current_user.id,
    ).first()
    if not original:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")

    clone = Vacancy(
        user_id=current_user.id,
        title=f"Копия: {original.title}",
        location=original.location,
        salary_range=original.salary_range,
        description_html=original.description_html,
        description_text=original.description_text,
        key_skills=original.key_skills,
        comment_for_ai=original.comment_for_ai,
        templates=original.templates,
        client=original.client,
        status="active",
        is_active=True,
        recruitment_start_date=None,
        recruitment_end_date=None,
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)

    logger.info("Вакансия ID %d → клонирована → ID %d", vacancy_id, clone.id)
    return clone


@router.post("/{vacancy_id}/complete", response_model=VacancyResponse)
async def complete_vacancy(
    vacancy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Перевод вакансии в статус 'Завершена'."""
    vacancy = db.query(Vacancy).filter(
        Vacancy.id == vacancy_id, Vacancy.user_id == current_user.id,
    ).first()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")

    vacancy.status = "completed"
    vacancy.is_active = True  # completed ≠ archived
    db.commit()
    db.refresh(vacancy)

    logger.info("Вакансия ID %d → completed", vacancy_id)
    return vacancy


@router.post("/{vacancy_id}/reopen", response_model=VacancyResponse)
async def reopen_vacancy(
    vacancy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Возобновить вакансию (из completed или archived → active)."""
    vacancy = db.query(Vacancy).filter(
        Vacancy.id == vacancy_id, Vacancy.user_id == current_user.id,
    ).first()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")

    vacancy.status = "active"
    vacancy.is_active = True
    db.commit()
    db.refresh(vacancy)

    logger.info("Вакансия ID %d → active (reopened)", vacancy_id)
    return vacancy
