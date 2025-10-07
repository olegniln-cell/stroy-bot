from sqlalchemy import Column, BigInteger, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Trial(Base):
    __tablename__ = "trials"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(
        BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    starts_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, nullable=False, server_default="true")

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

    company = relationship("Company", back_populates="trials")
