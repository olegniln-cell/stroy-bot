from sqlalchemy import Column, BigInteger, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class File(Base, TimestampMixin):
    __tablename__ = "files"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    task_id = Column(
        BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    company_id = Column(
        BigInteger,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploader_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    s3_key = Column(String, unique=True, nullable=False)
    original_name = Column(String, nullable=False)
    size = Column(BigInteger, nullable=False)
    mime_type = Column(String, nullable=False)

    # Связи
    task = relationship("Task", back_populates="files")
    uploader = relationship("User", back_populates="files")
    company = relationship("Company", back_populates="files")
