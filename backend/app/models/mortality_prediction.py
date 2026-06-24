from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MortalityPrediction(Base):
    """
    AI-generated mortality probability forecast for a tank.

    Projects the probability of elevated mortality events within a
    defined forecast horizon.  Used by the Biosecurity & Health page
    and the Analytics dashboard to surface early-warning risk.

    ``mortality_probability`` : 0.0000 … 1.0000 (fractional probability).
    ``confidence``            : model confidence [0.0000 … 1.0000].
    ``forecast_days``         : horizon in days (7 | 14 | 30).

    TimescaleDB hypertable — partition column: ``time``.
    Composite PK: (id, time).

    Alembic note:
        After table creation run:
            SELECT create_hypertable('mortality_predictions', 'time',
                chunk_time_interval => INTERVAL '14 days');
    """

    __tablename__ = "mortality_predictions"
    __table_args__ = (
        Index("ix_mortality_predictions_tank_time", "tank_id", "time"),
        CheckConstraint(
            "mortality_probability BETWEEN 0 AND 1",
            name="ck_mortality_probability_range",
        ),
        CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name="ck_mortality_confidence_range",
        ),
        CheckConstraint(
            "forecast_days IN (7, 14, 30)",
            name="ck_mortality_forecast_days_valid",
        ),
        {
            "comment": (
                "TimescaleDB hypertable — mortality risk probability forecasts per tank. "
                "Partition: time / 14-day chunks."
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

    # ── Prediction payload ────────────────────────────────────────────────────
    mortality_probability: Mapped[float] = mapped_column(
        Numeric(6, 4),
        nullable=False,
        comment="Predicted probability of elevated mortality in the forecast window [0.0 … 1.0].",
    )
    confidence: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Model confidence in this forecast [0.0000 … 1.0000].",
    )
    forecast_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Forecast horizon in days: 7 | 14 | 30.",
    )

    # ── Confidence interval ───────────────────────────────────────────────────
    confidence_low: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 4),
        nullable=True,
        comment="Lower bound of the 90% CI for mortality_probability.",
    )
    confidence_high: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 4),
        nullable=True,
        comment="Upper bound of the 90% CI for mortality_probability.",
    )

    def __repr__(self) -> str:
        return (
            f"<MortalityPrediction id={self.id} tank_id={self.tank_id} "
            f"mortality_probability={self.mortality_probability} "
            f"forecast_days={self.forecast_days} confidence={self.confidence}>"
        )
