from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PsiPrediction(Base):
    """
    Physiological Stress Index (PSI) prediction for a tank.

    The PSI score is a composite stress indicator computed by the
    AI/ML engine from water-quality and biological features.  Each row
    represents one inference pass.

    PSI score range  : 0.00 (optimal) … 10.00 (critical stress)
    Stress levels    : 'Optimal' | 'Mild Stress' | 'Moderate Stress' |
                       'Severe Stress' | 'Critical Stress'
    Confidence       : 0.0000 … 1.0000

    TimescaleDB hypertable — partition column: ``generated_at``.
    Composite PK: (id, generated_at).

    Alembic note:
        After table creation run:
            SELECT create_hypertable('psi_predictions', 'generated_at',
                chunk_time_interval => INTERVAL '7 days');
    """

    __tablename__ = "psi_predictions"
    __table_args__ = (
        Index("ix_psi_predictions_tank_generated", "tank_id", "generated_at"),
        CheckConstraint(
            "psi_score BETWEEN 0.00 AND 10.00",
            name="ck_psi_score_range",
        ),
        CheckConstraint(
            "stress_level IN ("
            "'Optimal','Mild Stress','Moderate Stress',"
            "'Severe Stress','Critical Stress')",
            name="ck_psi_stress_level_valid",
        ),
        CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name="ck_psi_confidence_range",
        ),
        {
            "comment": (
                "TimescaleDB hypertable — PSI AI inference outputs. "
                "Partition: generated_at / 7-day chunks."
            )
        },
    )

    # ── Composite PK (UUID + time for TimescaleDB) ────────────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID — referenced by psi_factors composite FK.",
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="Inference timestamp (TimescaleDB partition key).",
    )

    # ── FK ──────────────────────────────────────────────────────────────────
    tank_id: Mapped[UUID] = mapped_column(
        ForeignKey("tanks.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → tanks.id",
    )

    # ── AI model provenance ───────────────────────────────────────────────────
    model_version_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("model_versions.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK → model_versions.id — which model version produced this prediction.",
    )

    # ── PSI output ────────────────────────────────────────────────────────────
    psi_score: Mapped[float] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        comment="Composite stress index [0.00 = optimal … 10.00 = critical stress].",
    )
    stress_level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment=(
            "Human-readable stress classification derived from psi_score. "
            "'Optimal' | 'Mild Stress' | 'Moderate Stress' | "
            "'Severe Stress' | 'Critical Stress'."
        ),
    )
    confidence: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Model confidence in this prediction [0.0000 … 1.0000].",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    factors: Mapped[list["PsiFactor"]] = relationship(
        "PsiFactor",
        back_populates="prediction",
        cascade="all, delete-orphan",
        lazy="selectin",
        primaryjoin=(
            "and_(PsiPrediction.id == foreign(PsiFactor.prediction_id),"
            "PsiPrediction.generated_at == foreign(PsiFactor.prediction_time))"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<PsiPrediction id={self.id} tank_id={self.tank_id} "
            f"psi_score={self.psi_score} stress_level={self.stress_level!r} "
            f"confidence={self.confidence}>"
        )
