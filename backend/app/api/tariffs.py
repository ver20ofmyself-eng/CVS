from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from app.database import get_db
from app.models.tariff import Tariff  # Было tariffs - исправлено на tariff
from app.models.user import User
from app.api.auth import get_current_user
from app.services.tariff_service import tariff_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def get_tariffs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить список доступных тарифов
    """
    tariffs = db.query(Tariff).filter(Tariff.is_active == True).all()
    return tariffs

@router.get("/my")
async def get_my_tariff(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить информацию о моём текущем тарифе
    """
    info = tariff_service.get_user_tariff_info(db, current_user.id)
    return info

@router.post("/purchase/{tariff_id}")
async def purchase_tariff(
    tariff_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Купить тариф (заглушка для демо)
    В реальном проекте здесь будет интеграция с платежной системой
    """
    # Проверяем существование тарифа
    tariff = db.query(Tariff).filter(
        Tariff.id == tariff_id,
        Tariff.is_active == True
    ).first()
    
    if not tariff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тариф не найден"
        )
    
    # Имитируем покупку
    success = tariff_service.purchase_tariff(
        db=db,
        user_id=current_user.id,
        tariff_id=tariff_id,
        payment_system="demo"
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при покупке тарифа"
        )
    
    return {
        "success": True,
        "message": f"Тариф '{tariff.name}' успешно приобретён",
        "tariff": {
            "id": tariff.id,
            "name": tariff.name,
            "analyses_limit": tariff.analyses_limit
        }
    }
