from datetime import datetime
from uuid import uuid4, UUID
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

class UUIDMixin:
    """Mixin to add a UUID primary key to tables."""
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, sort_order=-10)

class TimestampMixin:
    """Mixin to add timezone-aware creation and update timestamps."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), sort_order=90)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), sort_order=91)

class SoftDeleteMixin:
    """Mixin to add soft deletion capability."""
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, default=None, sort_order=92)
