from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import logging

from app.database import get_db
from app.models.vacancy import Vacancy
from app.models.user import User
from app.schemas.vacancy import VacancyCreate, VacancyUpdate, VacancyResponse, VacancyListResponse
from app.api.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=VacancyResponse, status_code=status.HTTP_201_CREATED)
async def create_vacancy(
    vacancy: VacancyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создание новой вакансии
    
    - **title**: обязательное поле, название вакансии
    - **location**: необязательное, место работы
    - **salary_range**: зарплатный диапазон {min, max, currency}
    - **description_html**: HTML описание (для отображения)
    - **description_text**: текстовое описание (для AI)
    - **key_skills**: список ключевых навыков
    - **comment_for_ai**: комментарий для AI-анализа
    - **templates**: шаблоны сообщений
    """
    logger.info(f"Создание вакансии пользователем {current_user.email}")
    
    # Создаём объект вакансии
    db_vacancy = Vacancy(
        user_id=current_user.id,
        **vacancy.model_dump(exclude_unset=True)
    )
    
    db.add(db_vacancy)
    db.commit()
    db.refresh(db_vacancy)
    
    logger.info(f"Вакансия создана: ID {db_vacancy.id}")
    return db_vacancy

@router.get("/", response_model=VacancyListResponse)
async def get_vacancies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Сколько пропустить"),
    limit: int = Query(100, ge=1, le=100, description="Сколько вернуть"),
    active_only: bool = Query(True, description="Только активные"),
    search: Optional[str] = Query(None, description="Поиск по названию")
):
    """
    Получение списка вакансий пользователя
    
    - **skip**: пагинация (сколько пропустить)
    - **limit**: пагинация (сколько вернуть, максимум 100)
    - **active_only**: только активные вакансии
    - **search**: поиск по названию (частичное совпадение)
    """
    logger.info(f"Запрос списка вакансий от {current_user.email}")
    
    # Базовый запрос
    query = db.query(Vacancy).filter(Vacancy.user_id == current_user.id)
    
    # Фильтр по активности
    if active_only:
        query = query.filter(Vacancy.is_active == True)
    
    # Поиск по названию
    if search:
        query = query.filter(Vacancy.title.ilike(f"%{search}%"))
    
    # Сортировка (сначала новые)
    query = query.order_by(desc(Vacancy.created_at))
    
    # Общее количество
    total = query.count()
    
    # Пагинация
    items = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": items
    }

@router.get("/{vacancy_id}", response_model=VacancyResponse)
async def get_vacancy(
    vacancy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получение конкретной вакансии по ID
    """
    logger.info(f"Запрос вакансии ID {vacancy_id} от {current_user.email}")
    
    vacancy = db.query(Vacancy).filter(
        Vacancy.id == vacancy_id,
        Vacancy.user_id == current_user.id
    ).first()
    
    if not vacancy:
        logger.warning(f"Вакансия ID {vacancy_id} не найдена")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена"
        )
    
    return vacancy

@router.put("/{vacancy_id}", response_model=VacancyResponse)
async def update_vacancy(
    vacancy_id: int,
    vacancy_update: VacancyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновление вакансии
    
    Можно обновлять только свои вакансии
    """
    logger.info(f"Обновление вакансии ID {vacancy_id} от {current_user.email}")
    
    # Ищем вакансию
    vacancy = db.query(Vacancy).filter(
        Vacancy.id == vacancy_id,
        Vacancy.user_id == current_user.id
    ).first()
    
    if not vacancy:
        logger.warning(f"Вакансия ID {vacancy_id} не найдена")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена"
        )
    
    # Обновляем только переданные поля
    update_data = vacancy_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vacancy, field, value)
    
    db.commit()
    db.refresh(vacancy)
    
    logger.info(f"Вакансия ID {vacancy_id} обновлена")
    return vacancy

@router.delete("/{vacancy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vacancy(
    vacancy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удаление вакансии (мягкое удаление - помечаем is_active=False)
    """
    logger.info(f"Удаление вакансии ID {vacancy_id} от {current_user.email}")
    
    vacancy = db.query(Vacancy).filter(
        Vacancy.id == vacancy_id,
        Vacancy.user_id == current_user.id
    ).first()
    
    if not vacancy:
        logger.warning(f"Вакансия ID {vacancy_id} не найдена")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена"
        )
    
    # Мягкое удаление (помечаем как неактивную)
    vacancy.is_active = False
    db.commit()
    
    logger.info(f"Вакансия ID {vacancy_id} помечена как удалённая")
    return None

@router.post("/{vacancy_id}/clone", response_model=VacancyResponse)
async def clone_vacancy(
    vacancy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Клонирование существующей вакансии
    Создаёт копию с префиксом "Копия: " в названии
    """
    logger.info(f"Клонирование вакансии ID {vacancy_id} от {current_user.email}")
    
    # Ищем оригинал
    original = db.query(Vacancy).filter(
        Vacancy.id == vacancy_id,
        Vacancy.user_id == current_user.id
    ).first()
    
    if not original:
        logger.warning(f"Вакансия ID {vacancy_id} не найдена")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена"
        )
    
    # Создаём копию
    clone_data = {
        "user_id": current_user.id,
        "title": f"Копия: {original.title}",
        "location": original.location,
        "salary_range": original.salary_range,
        "description_html": original.description_html,
        "description_text": original.description_text,
        "key_skills": original.key_skills,
        "comment_for_ai": original.comment_for_ai,
        "templates": original.templates,
        "is_active": True
    }
    
    clone = Vacancy(**clone_data)
    db.add(clone)
    db.commit()
    db.refresh(clone)
    
    logger.info(f"Вакансия склонирована: новый ID {clone.id}")
    return clone
