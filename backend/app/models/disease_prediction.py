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
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DiseasePrediction(Base):
    """
    AI-generated disease risk forecast for a tank.

    Each row represents one inference run for a specific disease/pathogen.
    Multiple rows may exist per tank per timestamp if the model evaluates
    several diseases in a single pass (e.g. Amoebic Gill Disease, IHN,
    Sea Lice infestation).

    ``disease_name``  : free-form pathogen or syndrome label.
    ``risk_score``    : 0.00 (negligible) … 10.00 (critical outbreak risk).
    ``confidence``    : model confidence [0.0000 … 1.0000].
    ``forecast_days`` : prediction horizon in days (typically 7, 14, or 30).

    TimescaleDB hypertable — partition column: ``time``.
    Composite PK: (id, time).

    Alembic note:
        After table creation run:
            SELECT create_hypertable('disease_predictions', 'time',
                chunk_time_interval => INTERVAL '14 days');
    """

    __tablename__ = "disease_predictions"
    __table_args__ = (
        Index("ix_disease_predictions_tank_time",  "tank_id", "time"),
        Index("ix_disease_predictions_disease",    "disease_name", "time"),
        CheckConstraint(
            "risk_score BETWEEN 0.00 AND 10.00",
            name="ck_disease_risk_score_range",
        ),
        CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name="ck_disease_confidence_range",
        ),
        CheckConstraint(
            "forecast_days > 0",
            name="ck_disease_forecast_days_positive",
        ),
        {
            "comment": (
                "TimescaleDB hypertable — disease risk predictions per tank. "
                "Partition: time / 14-day chunks."
            )
        },
    )

    # ── Composite PK (UUID + time for TimescaleDB) ────────────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID — stable row identifier for case-match references.",
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
    disease_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment=(
            "Pathogen or syndrome name "
            "(e.g. 'Amoebic Gill Disease', 'Infectious Haematopoietic Necrosis', "
            "'Sea Lice Infestation')."
        ),
    )
    risk_score: Mapped[float] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        comment="Disease outbreak risk score [0.00 = negligible … 10.00 = critical].",
    )
    confidence: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Model confidence in this disease prediction [0.0000 … 1.0000].",
    )
    forecast_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Prediction horizon in days (e.g. 7, 14, 30).",
    )

    # ── Confidence interval ───────────────────────────────────────────────────
    confidence_low: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="Lower bound of the 90% confidence interval for risk_score.",
    )
    confidence_high: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="Upper bound of the 90% confidence interval for risk_score.",
    )

    def __repr__(self) -> str:
        return (
            f"<DiseasePrediction id={self.id} tank_id={self.tank_id} "
            f"disease={self.disease_name!r} risk_score={self.risk_score} "
            f"forecast_days={self.forecast_days}>"
        )
