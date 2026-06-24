from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Alert(Base):
    """
    Real-time alert triggered by the AI engine or sensor threshold breach.

    Severity levels   : 'Info' | 'Warning' | 'Critical'
    Status lifecycle  : 'Active' → 'Acknowledged' → 'Resolved'

    TimescaleDB hypertable — partition column: ``time``.
    Composite PK: (id, time) provides a stable UUID reference while
    satisfying the TimescaleDB partition-key-in-PK requirement.

    Alembic note:
        After table creation run:
            SELECT create_hypertable('alerts', 'time',
                chunk_time_interval => INTERVAL '7 days');
    """

    __tablename__ = "alerts"
    __table_args__ = (
        # Most common query: unresolved alerts for a specific tank, newest first
        Index("ix_alerts_tank_time", "tank_id", "time"),
        # Support filtering by severity across all tanks
        Index("ix_alerts_severity_status", "severity", "status"),
        CheckConstraint(
            "severity IN ('Info','Warning','Critical')",
            name="ck_alert_severity_valid",
        ),
        CheckConstraint(
            "status IN ('Active','Acknowledged','Resolved')",
            name="ck_alert_status_valid",
        ),
        {
            "comment": (
                "TimescaleDB hypertable — AI and threshold-breach alerts. "
                "Partition: time / 7-day chunks."
            )
        },
    )

    # ── Composite PK (UUID + time for TimescaleDB) ────────────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID — stable reference for notifications and audit.",
    )
    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="Alert creation timestamp (TimescaleDB partition key).",
    )

    # ── FKs ──────────────────────────────────────────────────────────────────
    tank_id: Mapped[UUID] = mapped_column(
        ForeignKey("tanks.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → tanks.id",
    )
    sensor_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("sensors.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK → sensors.id  (nullable: alert may originate from AI, not a sensor).",
    )

    # ── Classification ────────────────────────────────────────────────────────
    type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Alert category (e.g. 'DO_DEPLETION', 'HIGH_AMMONIA', 'PSI_CRITICAL').",
    )
    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="'Info' | 'Warning' | 'Critical'",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Active",
        comment="'Active' | 'Acknowledged' | 'Resolved'",
    )

    # ── Content ───────────────────────────────────────────────────────────────
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Human-readable alert description rendered in the UI.",
    )

    # ── Resolution ────────────────────────────────────────────────────────────
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when an operator acknowledged the alert.",
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the alert was resolved / cleared.",
    )
    resolved_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK → users.id  (operator who resolved the alert).",
    )

    def __repr__(self) -> str:
        return (
            f"<Alert id={self.id} tank_id={self.tank_id} "
            f"severity={self.severity!r} status={self.status!r}>"
        )
