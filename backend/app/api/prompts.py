from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import get_db
from app.models.prompt import Prompt, PromptHistory
from app.models.user import User
from app.schemas.prompt import PromptCreate, PromptUpdate, PromptResponse, PromptHistoryResponse
from app.api.auth import get_current_admin_user, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[PromptResponse])
async def get_prompts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),  # Только админы могут видеть все промпты
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """Получить список доступных промптов"""
    query = db.query(Prompt)
    
    if active_only:
        query = query.filter(Prompt.is_active == True)
    
    prompts = query.offset(skip).limit(limit).all()
    return prompts

@router.get("/default", response_model=PromptResponse)
async def get_default_prompt(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)  # Только админы могут видеть дефолтный промпт
):
    """Получить промпт по умолчанию"""
    prompt = db.query(Prompt).filter(Prompt.is_default == True, Prompt.is_active == True).first()
    
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Промпт по умолчанию не найден"
        )
    
    return prompt

@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)  # Только админы могут видеть конкретный промпт
):
    """Получить конкретный промпт"""
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Промпт не найден"
        )
    
    return prompt

@router.get("/{prompt_id}/history", response_model=List[PromptHistoryResponse])
async def get_prompt_history(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить историю изменений промпта"""
    history = db.query(PromptHistory).filter(
        PromptHistory.prompt_id == prompt_id
    ).order_by(PromptHistory.changed_at.desc()).all()
    
    return history

# Админские эндпоинты (только для пользователей с правами)
@router.post("/", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    prompt: PromptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)  # Специальная зависимость для админов
):
    """Создать новый промпт (только для админов)"""
    # Проверяем уникальность имени
    existing = db.query(Prompt).filter(Prompt.name == prompt.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Промпт с таким именем уже существует"
        )
    
    db_prompt = Prompt(
        **prompt.model_dump(),
        created_by=current_user.id,
        version=1
    )
    
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    
    logger.info(f"Создан новый промпт: {prompt.name} (ID: {db_prompt.id})")
    return db_prompt

@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: int,
    prompt_update: PromptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Обновить промпт (только для админов)"""
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Промпт не найден"
        )
    
    # Сохраняем историю
    history = PromptHistory(
        prompt_id=prompt.id,
        name=prompt.name,
        system_prompt=prompt.system_prompt,
        user_prompt_template=prompt.user_prompt_template,
        parameters=prompt.parameters,
        version=prompt.version,
        changed_by=current_user.id,
        change_comment="Обновление промпта"
    )
    db.add(history)
    
    # Обновляем поля
    update_data = prompt_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prompt, field, value)
    
    prompt.version += 1
    db.commit()
    db.refresh(prompt)
    
    logger.info(f"Обновлён промпт ID {prompt_id}, новая версия: {prompt.version}")
    return prompt

@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Мягкое удаление промпта (только для админов)"""
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Промпт не найден"
        )
    
    prompt.is_active = False
    db.commit()
    
    logger.info(f"Промпт ID {prompt_id} деактивирован")
    return None
