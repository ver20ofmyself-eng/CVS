"""
Тарифы и платежи
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.tariff import Tariff
from app.models.payments import Payment
from app.models.user import User
from app.services.tariff_service import tariff_service

logger = logging.getLogger(__name__)
router = APIRouter()


class TariffResponse(BaseModel):
    id: int
    name: str
    analyses_limit: int
    price: float
    description: str = ""

    class Config:
        from_attributes = True


class PaymentHistoryItem(BaseModel):
    id: int
    tariff_name: str | None
    amount: float
    currency: str
    status: str
    created_at: str
    receipt_url: str | None = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[TariffResponse])
async def get_tariffs(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Список всех активных тарифов."""
    return db.query(Tariff).filter(Tariff.is_active == True).order_by(Tariff.price).all()


@router.get("/my")
async def get_my_tariff(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Информация о текущем тарифе авторизованного пользователя."""
    info = tariff_service.get_user_tariff_info(db, current_user.id)
    if not info.get("has_tariff"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Активный тариф не найден",
        )
    return info


@router.post("/purchase/{tariff_id}")
async def purchase_tariff(
    tariff_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Покупка тарифа (демо-режим).
    В продакшене здесь будет редирект на страницу оплаты ЮKassa / CloudPayments.
    """
    tariff = db.query(Tariff).filter(
        Tariff.id == tariff_id, Tariff.is_active == True
    ).first()
    if not tariff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тариф не найден")

    success = tariff_service.purchase_tariff(db, current_user.id, tariff_id, payment_system="mock")
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось активировать тариф",
        )

    new_info = tariff_service.get_user_tariff_info(db, current_user.id)
    logger.info("Пользователь %s купил тариф '%s'", current_user.email, tariff.name)
    return {
        "success": True,
        "message": f"Тариф «{tariff.name}» успешно активирован (демо-режим)",
        "tariff": new_info,
    }


@router.get("/payments/history")
async def get_payment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """История платежей текущего пользователя."""
    payments = (
        db.query(Payment)
        .filter(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .limit(50)
        .all()
    )

    result = []
    for p in payments:
        tariff = db.query(Tariff).filter(Tariff.id == p.tariff_id).first()
        result.append({
            "id": p.id,
            "tariff_name": tariff.name if tariff else None,
            "amount": p.amount,
            "currency": p.currency,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "receipt_url": None,  # TODO: добавить при интеграции с платёжной системой
        })
    return result
