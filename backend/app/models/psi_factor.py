from __future__ import annotations

from uuid import UUID
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PsiFactor(Base):
    """
    Explainable-AI (XAI) factor breakdown for a single PSI prediction.

    Each row records how much one environmental or biological variable
    contributed to the parent PSI score.  A full prediction has one
    PsiFactor row per active factor (typically 5–6 rows).

    Supported factor names:
        'temperature' | 'dissolved_oxygen' | 'pH' | 'ammonia' |
        'salinity'    | 'stocking_density'

    ``contribution``    : signed SHAP-style value (positive = raises stress).
    ``importance_score``: absolute importance [0.0000 … 1.0000].

    TimescaleDB hypertable — partition column: ``prediction_time``.
    Composite PK: (prediction_id, prediction_time, factor_name) mirrors
    the parent psi_predictions composite PK and uniquely identifies
    each factor within a prediction.

    Alembic note:
        After table creation run:
            SELECT create_hypertable('psi_factors', 'prediction_time',
                chunk_time_interval => INTERVAL '7 days');
    """

    __tablename__ = "psi_factors"
    __table_args__ = (
        # Composite FK → psi_predictions(id, generated_at)
        ForeignKeyConstraint(
            ["prediction_id", "prediction_time"],
            ["psi_predictions.id", "psi_predictions.generated_at"],
            ondelete="CASCADE",
            name="fk_psi_factors_prediction",
        ),
        CheckConstraint(
            "factor_name IN ("
            "'temperature','dissolved_oxygen','pH','ammonia',"
            "'salinity','stocking_density')",
            name="ck_psi_factor_name_valid",
        ),
        CheckConstraint(
            "importance_score >= 0",
            name="ck_psi_factor_importance_non_negative",
        ),
        Index("ix_psi_factors_prediction", "prediction_id", "prediction_time"),
        {
            "comment": (
                "TimescaleDB hypertable — XAI factor breakdown per PSI prediction. "
                "Partition: prediction_time / 7-day chunks."
            )
        },
    )

    # ── Composite PK ──────────────────────────────────────────────────────────
    prediction_id: Mapped[UUID] = mapped_column(
        primary_key=True,
        comment="FK → psi_predictions.id  (part of composite PK and composite FK).",
    )
    prediction_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="FK → psi_predictions.generated_at  (TimescaleDB partition key).",
    )
    factor_name: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        comment=(
            "Name of the environmental/biological factor. "
            "One of: 'temperature' | 'dissolved_oxygen' | 'pH' | "
            "'ammonia' | 'salinity' | 'stocking_density'."
        ),
    )

    # ── XAI values ────────────────────────────────────────────────────────────
    contribution: Mapped[float] = mapped_column(
        Numeric(6, 4),
        nullable=False,
        comment=(
            "Signed SHAP-style contribution to the PSI score. "
            "Positive = increases stress; negative = reduces stress."
        ),
    )
    importance_score: Mapped[float] = mapped_column(
        Numeric(6, 4),
        nullable=False,
        comment="Absolute feature importance weight [≥ 0.0000].",
    )

    # ── Relationship ──────────────────────────────────────────────────────────
    prediction: Mapped["PsiPrediction"] = relationship(
        "PsiPrediction",
        back_populates="factors",
        foreign_keys=[prediction_id, prediction_time],
    )

    def __repr__(self) -> str:
        return (
            f"<PsiFactor prediction_id={self.prediction_id} "
            f"factor={self.factor_name!r} "
            f"contribution={self.contribution} importance={self.importance_score}>"
        )
