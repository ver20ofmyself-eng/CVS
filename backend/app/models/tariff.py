from sqlalchemy import Column, Integer, String, Boolean, DECIMAL
from app.database import Base

class Tariff(Base):
    __tablename__ = "tariffs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    analyses_limit = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    