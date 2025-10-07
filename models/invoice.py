from sqlalchemy import Column, BigInteger, String, Numeric, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import enum


class InvoiceStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(
        BigInteger,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id = Column(
        BigInteger,
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, server_default="USD")
    status = Column(
        Enum(InvoiceStatus, name="invoice_status", native_enum=True),
        nullable=False,
        server_default=InvoiceStatus.pending.value,
    )

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Связи
    company = relationship("Company", backref="invoices")
    plan = relationship("Plan", back_populates="invoices")
    payments = relationship(
        "Payment", back_populates="invoice", cascade="all, delete-orphan"
    )
