from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SystemHealthSnapshot(Base):
    """
    Periodic snapshots of global system and infrastructure health.

    Tracks infrastructure health score, response latency, uptime percent,
    active models, and active users to optimize administration dashboards.

    TimescaleDB hypertable — partition column: ``recorded_at``.
    Composite PK: (id, recorded_at) to allow stable UUID reference and comply
    with TimescaleDB requirements.
    """

    __tablename__ = "system_health_snapshots"
    __table_args__ = (
        Index("ix_system_health_snapshots_recorded", "recorded_at"),
        CheckConstraint(
            "health_score BETWEEN 0 AND 100",
            name="ck_system_health_snapshot_score_range",
        ),
        CheckConstraint(
            "uptime_pct BETWEEN 0 AND 100",
            name="ck_system_health_snapshot_uptime_range",
        ),
        CheckConstraint(
            "error_rate BETWEEN 0 AND 1",
            name="ck_system_health_snapshot_error_rate_range",
        ),
        {
            "comment": (
                "TimescaleDB hypertable — periodic snapshots of global system/infrastructure health. "
                "Partition: recorded_at / 30-day chunks."
            )
        },
    )

    # ── Composite PK (UUID + recorded_at for TimescaleDB) ────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID identifier for the system health snapshot.",
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="Snapshot recording timestamp (TimescaleDB partition key).",
    )

    # ── Metrics ──────────────────────────────────────────────────────────────
    health_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Global system health score [0.00 - 100.00].",
    )
    latency_ms: Mapped[float] = mapped_column(
        Numeric(8, 2),
        nullable=False,
        comment="Average API response latency in milliseconds.",
    )
    uptime_pct: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Global system uptime percentage [0.00 - 100.00].",
    )
    error_rate: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Proportion of failed API and ingestion requests [0.0 - 1.0].",
    )

    # ── Operational stats ────────────────────────────────────────────────────
    active_users: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Count of active users concurrently on the platform.",
    )
    active_models: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Count of registered AI/ML models currently operational in production.",
    )
    active_alerts_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Count of currently active/unresolved alerts across all farms.",
    )

    def __repr__(self) -> str:
        return (
            f"<SystemHealthSnapshot id={self.id} recorded_at={self.recorded_at} "
            f"health={self.health_score} latency={self.latency_ms}ms>"
        )
