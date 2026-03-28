"""
Профиль пользователя — просмотр и редактирование
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.tariff_service import tariff_service

logger = logging.getLogger(__name__)
router = APIRouter()


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None


@router.get("/")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Полный профиль: данные пользователя + информация о тарифе."""
    tariff_info = tariff_service.get_user_tariff_info(db, current_user.id)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login,
        "tariff": tariff_info,
    }


@router.put("/")
async def update_profile(
    data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Обновление имени пользователя."""
    if data.full_name is not None:
        current_user.full_name = data.full_name.strip() or None
    db.commit()
    db.refresh(current_user)
    logger.info("Профиль обновлён: %s", current_user.email)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
    }
