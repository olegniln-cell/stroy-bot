from sqlalchemy import Column, BigInteger, String
from sqlalchemy.orm import relationship
from .base import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    created_by = Column(BigInteger, nullable=True)

    # Связи
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    projects = relationship(
        "Project", back_populates="company", cascade="all, delete-orphan"
    )
    files = relationship("File", back_populates="company", cascade="all, delete-orphan")
    trials = relationship(
        "Trial", back_populates="company", cascade="all, delete-orphan"
    )
    subscriptions = relationship(
        "Subscription", back_populates="company", cascade="all, delete-orphan"
    )
    tasks = relationship("Task", back_populates="company", cascade="all, delete-orphan")
