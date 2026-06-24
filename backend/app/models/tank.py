from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDMixin, TimestampMixin


# ─────────────────────────────────────────────────────────────────────────────
# Tank
# ─────────────────────────────────────────────────────────────────────────────
class Tank(Base, UUIDMixin, TimestampMixin):
    """
    A physical tank or sea-cage within a Zone.
    Supports RAS Tank, Sea Cage, and Nursery types.
    digital_twin_config stores optional Digital Twin configuration parameters.
    """

    __tablename__ = "tanks"

    # ── FK ──────────────────────────────────────────────────────────────────
    zone_id: Mapped[UUID] = mapped_column(
        ForeignKey("zones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK → zones.id",
    )

    # ── Identifiers ───────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Human-readable tank label (e.g. 'TNK-01'). Unique per zone.",
    )
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Structural type: 'RAS Tank' | 'Sea Cage' | 'Nursery'.",
    )

    # ── Physical parameters ───────────────────────────────────────────────────
    volume_m3: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Tank volume in cubic metres.",
    )
    max_biomass_kg: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Maximum safe stocking biomass in kilograms.",
    )
    species: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Atlantic Salmon",
        comment="Primary species stocked (default: 'Atlantic Salmon').",
    )

    # ── Digital twin ──────────────────────────────────────────────────────────
    digital_twin_config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Optional Digital Twin model parameters (JSON).",
    )

    __table_args__ = (
        UniqueConstraint("zone_id", "name", name="uq_tank_zone_name"),
        CheckConstraint("volume_m3 > 0",      name="ck_tank_volume_positive"),
        CheckConstraint("max_biomass_kg > 0",  name="ck_tank_biomass_positive"),
        CheckConstraint(
            "type IN ('RAS Tank', 'Sea Cage', 'Nursery')",
            name="ck_tank_type_valid",
        ),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    zone: Mapped["Zone"] = relationship("Zone", back_populates="tanks")

    sensors: Mapped[list["Sensor"]] = relationship(
        "Sensor",
        back_populates="tank",
        lazy="selectin",
    )

    quarantine_events: Mapped[list["QuarantineEvent"]] = relationship(
        "QuarantineEvent",
        back_populates="tank",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    inspections: Mapped[list["Inspection"]] = relationship(
        "Inspection",
        back_populates="tank",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Tank id={self.id} name={self.name!r} zone_id={self.zone_id}>"


# ─────────────────────────────────────────────────────────────────────────────
# QuarantineEvent  (owned by Tank)
# ─────────────────────────────────────────────────────────────────────────────
class QuarantineEvent(Base, UUIDMixin):
    """
    Records an active or resolved quarantine event on a tank.
    Cleared quarantines retain a historical record for audit purposes.
    """

    __tablename__ = "quarantine_events"

    # ── FK ──────────────────────────────────────────────────────────────────
    tank_id: Mapped[UUID] = mapped_column(
        ForeignKey("tanks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK → tanks.id",
    )

    # ── Details ───────────────────────────────────────────────────────────────
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Severity level: 'Low' | 'Medium' | 'High' | 'Critical'.",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When the quarantine event began.",
    )
    cleared_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the quarantine was lifted; NULL if still active.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "severity IN ('Low', 'Medium', 'High', 'Critical')",
            name="ck_quarantine_severity_valid",
        ),
    )

    tank: Mapped["Tank"] = relationship("Tank", back_populates="quarantine_events")

    def __repr__(self) -> str:
        return f"<QuarantineEvent id={self.id} tank_id={self.tank_id} severity={self.severity!r}>"


# ─────────────────────────────────────────────────────────────────────────────
# Inspection  (owned by Tank)
# ─────────────────────────────────────────────────────────────────────────────
class Inspection(Base, UUIDMixin):
    """
    Manual inspection record created by a certified biologist or operator.
    Inspector FK enforces RESTRICT to prevent accidental user deletion.
    """

    __tablename__ = "inspections"

    # ── FKs ──────────────────────────────────────────────────────────────────
    tank_id: Mapped[UUID] = mapped_column(
        ForeignKey("tanks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK → tanks.id",
    )
    inspector_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="FK → users.id  (RESTRICT prevents losing the audit trail).",
    )

    # ── Content ───────────────────────────────────────────────────────────────
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    tank: Mapped["Tank"] = relationship("Tank", back_populates="inspections")
    inspector: Mapped["User"] = relationship("User", foreign_keys=[inspector_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<Inspection id={self.id} tank_id={self.tank_id}>"
