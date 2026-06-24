from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HarvestPrediction(Base):
    """
    AI-generated harvest readiness forecast for a tank.

    Projects the optimal harvest date and expected biomass based on
    current growth trajectory, feed conversion ratios, and biological
    stress indicators.  Used by the Analytics page harvest timeline
    widget and farm revenue planning dashboards.

    ``predicted_harvest_date`` : DATE — projected optimal harvest window.
    ``projected_biomass``      : expected total biomass (kg) at harvest.
    ``confidence``             : model confidence [0.0000 … 1.0000].

    TimescaleDB hypertable — partition column: ``time``.
    Composite PK: (id, time).

    Alembic note:
        After table creation run:
            SELECT create_hypertable('harvest_predictions', 'time',
                chunk_time_interval => INTERVAL '30 days');
    """

    __tablename__ = "harvest_predictions"
    __table_args__ = (
        Index("ix_harvest_predictions_tank_time", "tank_id", "time"),
        CheckConstraint(
            "projected_biomass > 0",
            name="ck_harvest_biomass_positive",
        ),
        CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name="ck_harvest_confidence_range",
        ),
        CheckConstraint(
            "projected_mean_weight_g > 0",
            name="ck_harvest_mean_weight_positive",
        ),
        CheckConstraint(
            "growth_rate_fcr > 0",
            name="ck_harvest_fcr_positive",
        ),
        {
            "comment": (
                "TimescaleDB hypertable — harvest readiness predictions per tank. "
                "Partition: time / 30-day chunks."
            )
        },
    )

    # ── Composite PK (UUID + time for TimescaleDB) ────────────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID — stable row identifier.",
    )
    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="Prediction generation timestamp (TimescaleDB partition key).",
    )

    # ── FKs ──────────────────────────────────────────────────────────────────
    tank_id: Mapped[UUID] = mapped_column(
        ForeignKey("tanks.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → tanks.id",
    )
    model_version_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("model_versions.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK → model_versions.id — model that generated this forecast.",
    )

    # ── Harvest forecast payload ──────────────────────────────────────────────
    predicted_harvest_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Projected optimal harvest date (calendar date, not timestamp).",
    )
    projected_biomass: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Expected total live weight (kg) at the projected harvest date.",
    )
    projected_mean_weight_g: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Projected mean individual fish weight (g) at harvest.",
    )
    growth_rate_fcr: Mapped[float] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        comment="Feed Conversion Ratio trajectory used in the growth forecast model.",
    )
    confidence: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Model confidence in the harvest forecast [0.0000 … 1.0000].",
    )

    # ── Optional financial projection ─────────────────────────────────────────
    revenue_projection_usd: Mapped[Optional[float]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment=(
            "Estimated gross revenue (USD) at projected biomass and current market price. "
            "Populated when market price data is available."
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<HarvestPrediction id={self.id} tank_id={self.tank_id} "
            f"predicted_harvest_date={self.predicted_harvest_date} "
            f"projected_biomass={self.projected_biomass} confidence={self.confidence}>"
        )
