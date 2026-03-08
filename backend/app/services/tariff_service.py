"""
Сервис для работы с тарифами и учётом анализов
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
import logging
from typing import Optional, Dict, Any

from app.models.user import User
from app.models.tariff import Tariff
from app.models.user_tariffs import UserTariff
from app.models.payments import Payment

logger = logging.getLogger(__name__)

class TariffService:
    
    @staticmethod
    def assign_free_tariff(db: Session, user_id: int) -> bool:
        """
        Назначить бесплатный тариф новому пользователю
        """
        try:
            # Находим бесплатный тариф
            free_tariff = db.query(Tariff).filter(
                Tariff.name == "Бесплатный",
                Tariff.is_active == True
            ).first()
            
            if not free_tariff:
                logger.error("Бесплатный тариф не найден в БД")
                return False
            
            # Проверяем, нет ли уже активного тарифа
            existing = db.query(UserTariff).filter(
                UserTariff.user_id == user_id,
                UserTariff.is_active == True
            ).first()
            
            if existing:
                logger.info(f"У пользователя {user_id} уже есть активный тариф")
                return True
            
            # Создаём запись о тарифе
            user_tariff = UserTariff(
                user_id=user_id,
                tariff_id=free_tariff.id,
                analyses_left=free_tariff.analyses_limit,
                purchased_at=datetime.now(),
                expires_at=None,  # Бессрочный
                is_active=True
            )
            
            db.add(user_tariff)
            db.commit()
            
            logger.info(f"✅ Пользователю {user_id} назначен бесплатный тариф ({free_tariff.analyses_limit} анализов)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при назначении бесплатного тарифа: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def get_user_analyses_left(db: Session, user_id: int) -> int:
        """
        Получить количество оставшихся анализов
        """
        try:
            active_tariff = db.query(UserTariff).filter(
                UserTariff.user_id == user_id,
                UserTariff.is_active == True,
                and_(
                    (UserTariff.expires_at > datetime.now()) | 
                    (UserTariff.expires_at == None)
                )
            ).first()
            
            if not active_tariff:
                logger.warning(f"У пользователя {user_id} нет активного тарифа")
                return 0
            
            return active_tariff.analyses_left
            
        except Exception as e:
            logger.error(f"Ошибка при получении остатка анализов: {e}")
            return 0
    
    @staticmethod
    def check_and_decrease_analyses(db: Session, user_id: int) -> bool:
        """
        Проверить наличие анализов и уменьшить счётчик
        Возвращает True если анализ можно провести
        """
        try:
            active_tariff = db.query(UserTariff).filter(
                UserTariff.user_id == user_id,
                UserTariff.is_active == True,
                and_(
                    (UserTariff.expires_at > datetime.now()) | 
                    (UserTariff.expires_at == None)
                )
            ).first()
            
            if not active_tariff:
                logger.warning(f"У пользователя {user_id} нет активного тарифа")
                return False
            
            if active_tariff.analyses_left <= 0:
                logger.warning(f"У пользователя {user_id} закончились анализы")
                return False
            
            # Уменьшаем счётчик
            active_tariff.analyses_left -= 1
            db.commit()
            
            logger.info(f"✅ Анализ проведён. У пользователя {user_id} осталось {active_tariff.analyses_left} анализов")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при уменьшении счётчика анализов: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def get_user_tariff_info(db: Session, user_id: int) -> Dict[str, Any]:
        """
        Получить информацию о текущем тарифе пользователя
        """
        try:
            active_tariff = db.query(UserTariff).filter(
                UserTariff.user_id == user_id,
                UserTariff.is_active == True,
                and_(
                    (UserTariff.expires_at > datetime.now()) | 
                    (UserTariff.expires_at == None)
                )
            ).first()
            
            if not active_tariff:
                return {
                    "has_tariff": False,
                    "analyses_left": 0,
                    "tariff_name": None
                }
            
            tariff = db.query(Tariff).filter(
                Tariff.id == active_tariff.tariff_id
            ).first()
            
            return {
                "has_tariff": True,
                "analyses_left": active_tariff.analyses_left,
                "tariff_name": tariff.name if tariff else "Unknown",
                "tariff_limit": tariff.analyses_limit if tariff else 0,
                "purchased_at": active_tariff.purchased_at.isoformat() if active_tariff.purchased_at else None,
                "expires_at": active_tariff.expires_at.isoformat() if active_tariff.expires_at else None
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении информации о тарифе: {e}")
            return {
                "has_tariff": False,
                "analyses_left": 0,
                "error": str(e)
            }
    
    @staticmethod
    def purchase_tariff(
        db: Session, 
        user_id: int, 
        tariff_id: int,
        payment_system: str = "mock",
        payment_id: Optional[str] = None
    ) -> bool:
        """
        Покупка тарифа (заглушка для интеграции с платежной системой)
        """
        try:
            # Получаем информацию о тарифе
            tariff = db.query(Tariff).filter(
                Tariff.id == tariff_id,
                Tariff.is_active == True
            ).first()
            
            if not tariff:
                logger.error(f"Тариф {tariff_id} не найден")
                return False
            
            # Деактивируем текущий тариф
            db.query(UserTariff).filter(
                UserTariff.user_id == user_id,
                UserTariff.is_active == True
            ).update({"is_active": False})
            
            # Создаём запись о платеже
            payment = Payment(
                user_id=user_id,
                tariff_id=tariff_id,
                payment_system=payment_system,
                payment_id=payment_id or f"mock_{datetime.now().timestamp()}",
                amount=tariff.price,
                currency="RUB",
                status="completed",
                payment_metadata={"tariff_name": tariff.name}
            )
            db.add(payment)
            db.flush()  # Получаем ID платежа
            
            # Создаём новый тариф
            user_tariff = UserTariff(
                user_id=user_id,
                tariff_id=tariff_id,
                analyses_left=tariff.analyses_limit,
                purchased_at=datetime.now(),
                expires_at=None,  # Для пожизненных тарифов
                is_active=True
            )
            db.add(user_tariff)
            
            db.commit()
            
            logger.info(f"✅ Пользователь {user_id} приобрёл тариф {tariff.name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при покупке тарифа: {e}")
            db.rollback()
            return False

# Создаём глобальный экземпляр
tariff_service = TariffService()
