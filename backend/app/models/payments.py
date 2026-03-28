from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, TIMESTAMP, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tariff_id = Column(Integer, ForeignKey("tariffs.id"), nullable=False)
    payment_system = Column(String(50))
    payment_id = Column(String(255))
    amount = Column(DECIMAL(10, 2))
    currency = Column(String(3), default="RUB")
    status = Column(String(50))
    payment_metadata = Column(JSON, default={})
    created_at = Column(TIMESTAMP, server_default=func.now())
