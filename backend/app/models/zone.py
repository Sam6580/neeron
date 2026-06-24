from __future__ import annotations

from uuid import UUID
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDMixin


class Zone(Base, UUIDMixin):
    """
    A named sub-division of a Farm (e.g. 'Zone A — Grow-out', 'Nursery Block').
    Zone names must be unique within a farm.
    """

    __tablename__ = "zones"

    # ── FK ──────────────────────────────────────────────────────────────────
    farm_id: Mapped[UUID] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK → farms.id",
    )

    # ── Descriptors ──────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Zone label, unique within the parent farm.",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Free-text description of the zone's purpose or layout.",
    )

    __table_args__ = (
        UniqueConstraint("farm_id", "name", name="uq_zone_farm_name"),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    farm: Mapped["Farm"] = relationship("Farm", back_populates="zones")

    tanks: Mapped[list["Tank"]] = relationship(
        "Tank",
        back_populates="zone",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Zone id={self.id} name={self.name!r} farm_id={self.farm_id}>"
