from __future__ import annotations

from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDMixin, TimestampMixin


# ─────────────────────────────────────────────────────────────────────────────
# Association table  (Many-to-Many: users ↔ farms)
# ─────────────────────────────────────────────────────────────────────────────
class UserFarmMapping(Base):
    """
    Junction table that grants a User access to a Farm.
    No surrogate key — composite PK is the natural key.
    """

    __tablename__ = "user_farm_mappings"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    farm_id: Mapped[UUID] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        primary_key=True,
    )

    def __repr__(self) -> str:
        return f"<UserFarmMapping user={self.user_id} farm={self.farm_id}>"


# ─────────────────────────────────────────────────────────────────────────────
# Farm
# ─────────────────────────────────────────────────────────────────────────────
class Farm(Base, UUIDMixin, TimestampMixin):
    """
    Top-level geographic entity.
    One deployment supports multiple farms (Scotland, Norway, Chile…).
    """

    __tablename__ = "farms"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Human-readable farm name (e.g. 'Loch Awe — Scotland').",
    )
    latitude: Mapped[float] = mapped_column(
        Numeric(9, 6),
        nullable=False,
        comment="WGS-84 decimal latitude (−90 … +90).",
    )
    longitude: Mapped[float] = mapped_column(
        Numeric(9, 6),
        nullable=False,
        comment="WGS-84 decimal longitude (−180 … +180).",
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UTC",
        comment="IANA timezone string (e.g. 'Europe/Oslo').",
    )
    carrying_capacity_kg: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Maximum licensed biomass capacity in kilograms.",
    )

    __table_args__ = (
        CheckConstraint("latitude  BETWEEN -90  AND  90",  name="ck_farm_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180",  name="ck_farm_longitude"),
        CheckConstraint("carrying_capacity_kg > 0",        name="ck_farm_capacity_positive"),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    zones: Mapped[list["Zone"]] = relationship(
        "Zone",
        back_populates="farm",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_farm_mappings",
        back_populates="farms",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Farm id={self.id} name={self.name!r}>"
