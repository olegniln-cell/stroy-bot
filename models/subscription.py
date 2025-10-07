from sqlalchemy import Column, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
from utils.enums import SubscriptionStatus


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(
        BigInteger,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id = Column(
        BigInteger, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False
    )

    status = Column(
        ENUM(SubscriptionStatus, name="subscription_status", native_enum=True),
        nullable=False,
        server_default=SubscriptionStatus.trial.value,
    )
    starts_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    created_by = Column(BigInteger, nullable=True)
    updated_by = Column(BigInteger, nullable=True)

    # Связи
    company = relationship("Company", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")

    creator = relationship(
        "User", primaryjoin="Subscription.created_by==foreign(User.id)", viewonly=True
    )
    updater = relationship(
        "User", primaryjoin="Subscription.updated_by==foreign(User.id)", viewonly=True
    )
