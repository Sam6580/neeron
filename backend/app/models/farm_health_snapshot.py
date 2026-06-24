from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FarmHealthSnapshot(Base):
    """
    Periodic snapshots of a farm's aggregate operational health.

    Stores calculated metrics over time to optimize dashboard loading times
    and enable long-term analytics, trend forecasting, and KPI reporting.

    TimescaleDB hypertable — partition column: ``recorded_at``.
    Composite PK: (id, recorded_at) to allow stable UUID reference and comply
    with TimescaleDB requirements.
    """

    __tablename__ = "farm_health_snapshots"
    __table_args__ = (
        Index("ix_farm_health_snapshots_farm_recorded", "farm_id", "recorded_at"),
        CheckConstraint(
            "health_score BETWEEN 0 AND 100",
            name="ck_farm_health_snapshot_score_range",
        ),
        CheckConstraint(
            "psi_average BETWEEN 0 AND 1",
            name="ck_farm_health_snapshot_psi_range",
        ),
        CheckConstraint(
            "risk_score BETWEEN 0 AND 1",
            name="ck_farm_health_snapshot_risk_range",
        ),
        {
            "comment": (
                "TimescaleDB hypertable — periodic snapshots of farm aggregate health metrics. "
                "Partition: recorded_at / 30-day chunks."
            )
        },
    )

    # ── Composite PK (UUID + recorded_at for TimescaleDB) ────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID identifier for the snapshot.",
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="Snapshot recording timestamp (TimescaleDB partition key).",
    )

    # ── FKs ──────────────────────────────────────────────────────────────────
    farm_id: Mapped[UUID] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → farms.id",
    )

    # ── Metrics ──────────────────────────────────────────────────────────────
    health_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Overall calculated health score for the farm [0.00 - 100.00].",
    )
    psi_average: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Weighted average of all tank PSI predictions on the farm [0.0 - 1.0].",
    )
    risk_score: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Calculated biosecurity/disease risk score for the farm [0.0 - 1.0].",
    )

    # ── Count aggregates ─────────────────────────────────────────────────────
    active_alerts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Count of active alerts for the farm at recording time.",
    )
    active_recommendations: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Count of active recommendation actions pending for the farm.",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    farm: Mapped["Farm"] = relationship("Farm", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<FarmHealthSnapshot id={self.id} farm_id={self.farm_id} "
            f"recorded_at={self.recorded_at} health={self.health_score}>"
        )
