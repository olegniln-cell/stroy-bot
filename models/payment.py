from sqlalchemy import Column, BigInteger, String, Numeric, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
from .invoice import InvoiceStatus


class Payment(Base):
    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id = Column(
        BigInteger,
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, server_default="USD")
    status = Column(
        Enum(InvoiceStatus, name="payment_status", native_enum=True),
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
    invoice = relationship("Invoice", back_populates="payments")
