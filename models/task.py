from sqlalchemy import Column, BigInteger, String, ForeignKey, Enum, Text, DateTime
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
from utils.enums import TaskStatus


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    status = Column(
        Enum(TaskStatus, name="taskstatus", native_enum=True),
        nullable=False,
        server_default=TaskStatus.todo.value,
    )

    project_id = Column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    company_id = Column(
        BigInteger,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Связи
    files = relationship("File", back_populates="task", cascade="all, delete-orphan")
    project = relationship(
        "Project", back_populates="tasks", passive_deletes=True
    )  # ✅ добавлено passive_deletes=True
    user = relationship(
        "User", back_populates="tasks", passive_deletes=True
    )  # ✅ добавлено passive_deletes=True
    company = relationship("Company", back_populates="tasks", passive_deletes=True)
