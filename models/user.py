from sqlalchemy import Column, BigInteger, ForeignKey, DateTime, Enum, Boolean, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base
from utils.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, unique=True, nullable=False)
    role = Column(Enum(UserRole, name="user_role", native_enum=True), nullable=False)

    company_id = Column(
        BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True
    )
    phone_number = Column(BigInteger, nullable=True)

    is_active = Column(Boolean, server_default=text("true"), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

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
    company = relationship("Company", back_populates="users")
    tasks = relationship("Task", back_populates="user")
    files = relationship("File", back_populates="uploader")
    sessions = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
