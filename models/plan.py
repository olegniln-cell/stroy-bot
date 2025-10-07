from sqlalchemy import Column, BigInteger, String, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .base import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String, nullable=False)
    monthly_price = Column(Integer, nullable=False)
    period_days = Column(Integer, nullable=False)
    features = Column(JSONB, nullable=True, default=dict)

    subscriptions = relationship(
        "Subscription", back_populates="plan", cascade="all, delete-orphan"
    )
    invoices = relationship(
        "Invoice", back_populates="plan", cascade="all, delete-orphan"
    )
