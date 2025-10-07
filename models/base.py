# models/base.py
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, DateTime, func


class TimestampMixin:
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


Base = declarative_base()
