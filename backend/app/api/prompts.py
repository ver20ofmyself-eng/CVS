"""
API для управления промптами.

Логика видимости:
  - Системный промпт (owner_id IS NULL, name='default_cv_analyzer') — виден всем,
    нельзя редактировать/удалять.
  - Пользовательские промпты (owner_id = current_user.id) — видны только владельцу.

Права:
  - Читать список и использовать промпты — любой авторизованный пользователь
    (для analyze_cv нужен only промпт своего профиля + системный).
  - Создавать/редактировать/удалять — только пользователи с is_admin=True.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
import logging

from app.database import get_db
from app.models.prompt import Prompt, PromptHistory
from app.models.user import User
from app.schemas.prompt import PromptCreate, PromptUpdate, PromptResponse, PromptHistoryResponse
from app.api.auth import get_current_admin_user, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT_NAME = "default_cv_analyzer"


def _visible_prompts(db: Session, user_id: int):
    """Запрос промптов видимых пользователю: системный + его собственные."""
    return db.query(Prompt).filter(
        or_(Prompt.owner_id == user_id, Prompt.owner_id == None)
    )


def _get_or_404(db: Session, prompt_id: int, user_id: int) -> Prompt:
    prompt = _visible_prompts(db, user_id).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Промпт не найден")
    return prompt


def _is_system(prompt: Prompt) -> bool:
    return prompt.name == SYSTEM_PROMPT_NAME and prompt.owner_id is None


# ── GET /  ─────────────────────────────────────────────────────────────────────
@router.get("/", response_model=List[PromptResponse])
async def get_prompts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """Список промптов текущего пользователя + системный."""
    query = _visible_prompts(db, current_user.id)
    if active_only:
        query = query.filter(Prompt.is_active == True)
    return query.order_by(Prompt.owner_id.is_(None).desc(),  # системный первый
                          Prompt.is_default.desc(),
                          Prompt.created_at.desc()
                          ).offset(skip).limit(limit).all()


# ── GET /default  ──────────────────────────────────────────────────────────────
@router.get("/default", response_model=PromptResponse)
async def get_default_prompt(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Возвращает «основной» промпт текущего пользователя.
    Приоритет: пользовательский is_default=True → системный is_default=True.
    """
    # Сначала ищем пользовательский основной
    prompt = (
        _visible_prompts(db, current_user.id)
        .filter(Prompt.is_default == True, Prompt.is_active == True,
                Prompt.owner_id == current_user.id)
        .first()
    )
    # Если нет — берём системный
    if not prompt:
        prompt = (
            db.query(Prompt)
            .filter(Prompt.name == SYSTEM_PROMPT_NAME, Prompt.is_active == True)
            .first()
        )
    if not prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Ни один промпт не найден")
    return prompt


# ── GET /{id}  ─────────────────────────────────────────────────────────────────
@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Получить промпт по ID (только свой или системный)."""
    return _get_or_404(db, prompt_id, current_user.id)


# ── GET /{id}/history  ─────────────────────────────────────────────────────────
@router.get("/{prompt_id}/history", response_model=List[PromptHistoryResponse])
async def get_prompt_history(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """История изменений промпта."""
    _get_or_404(db, prompt_id, current_user.id)  # Проверка доступа
    return (
        db.query(PromptHistory)
        .filter(PromptHistory.prompt_id == prompt_id)
        .order_by(PromptHistory.changed_at.desc())
        .all()
    )


# ── POST /  ────────────────────────────────────────────────────────────────────
@router.post("/", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    prompt: PromptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Создать новый промпт (только для администраторов)."""
    # Проверяем уникальность имени в рамках профиля
    existing = (
        db.query(Prompt)
        .filter(Prompt.name == prompt.name, Prompt.owner_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Промпт с таким именем уже существует в вашем профиле")

    data = prompt.model_dump()
    data.pop("is_default", None)  # Нельзя создать сразу как основной — только через PUT

    db_prompt = Prompt(
        **data,
        owner_id   = current_user.id,
        created_by = current_user.id,
        version    = 1,
    )
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    logger.info(f"Создан промпт «{prompt.name}» пользователем {current_user.email}")
    return db_prompt


# ── PUT /{id}  ─────────────────────────────────────────────────────────────────
@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: int,
    prompt_update: PromptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Обновить промпт. Системный нельзя изменить."""
    prompt = _get_or_404(db, prompt_id, current_user.id)

    if _is_system(prompt):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Системный промпт нельзя редактировать")

    update_data = prompt_update.model_dump(exclude_unset=True)

    # Если делаем этот промпт основным — снимаем флаг с предыдущего основного
    if update_data.get("is_default") is True:
        db.query(Prompt).filter(
            Prompt.owner_id == current_user.id,
            Prompt.is_default == True,
            Prompt.id != prompt_id,
        ).update({"is_default": False})

    # Сохраняем в историю перед изменением (только если меняется содержимое)
    content_fields = {"system_prompt", "user_prompt_template", "parameters", "name"}
    if content_fields & set(update_data.keys()):
        db.add(PromptHistory(
            prompt_id            = prompt.id,
            name                 = prompt.name,
            system_prompt        = prompt.system_prompt,
            user_prompt_template = prompt.user_prompt_template,
            parameters           = prompt.parameters,
            version              = prompt.version,
            changed_by           = current_user.id,
            change_comment       = "Обновление содержимого",
        ))

    for field, value in update_data.items():
        setattr(prompt, field, value)

    if content_fields & set(update_data.keys()):
        prompt.version += 1

    db.commit()
    db.refresh(prompt)
    logger.info(f"Обновлён промпт ID {prompt_id} пользователем {current_user.email}")
    return prompt


# ── DELETE /{id}  ──────────────────────────────────────────────────────────────
@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: int,
    hard: bool = Query(False, description="True = физическое удаление, False = архивирование"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Архивировать (мягкое удаление) или удалить промпт.
    Системный нельзя удалить вовсе.
    Если удаляется основной — основным автоматически становится системный.
    """
    prompt = _get_or_404(db, prompt_id, current_user.id)

    if _is_system(prompt):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Системный промпт нельзя удалить")

    was_default = prompt.is_default

    if hard:
        db.delete(prompt)
    else:
        prompt.is_active  = False
        prompt.is_default = False

    db.commit()

    # Если удалили основной — системный автоматически становится основным
    # (это только маркер для UI; ai_service сам его выбирает при отсутствии пользовательского)
    if was_default:
        logger.info(f"Основной промпт удалён — fallback на системный для user {current_user.id}")

    return None


# ── POST /{id}/clone  ─────────────────────────────────────────────────────────
@router.post("/{prompt_id}/clone", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def clone_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Клонировать промпт (включая системный).
    Копия всегда создаётся как пользовательский промпт.
    """
    # Получаем оригинал (можно клонировать и системный)
    original = _visible_prompts(db, current_user.id).filter(Prompt.id == prompt_id).first()
    if not original:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Промпт не найден")

    # Генерируем уникальное имя
    base_name = f"copy_{original.name}"
    counter = 1
    new_name = base_name
    while db.query(Prompt).filter(Prompt.name == new_name, Prompt.owner_id == current_user.id).first():
        counter += 1
        new_name = f"{base_name}_{counter}"

    clone = Prompt(
        name=new_name,
        description=f"Копия: {original.description or original.name}",
        system_prompt=original.system_prompt,
        user_prompt_template=original.user_prompt_template,
        response_format=original.response_format or {},
        parameters=original.parameters or {},
        is_active=True,
        is_default=False,
        version=1,
        owner_id=current_user.id,
        created_by=current_user.id,
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)

    logger.info("Промпт ID %d клонирован → ID %d пользователем %s", prompt_id, clone.id, current_user.email)
    return clone
