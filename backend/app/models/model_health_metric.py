from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.model_version import ModelVersion


class ModelHealthMetric(Base):
    """
    Periodic MLOps performance snapshot for a deployed model version.

    Powers the Settings & Operations Control page AI Operations Monitor
    (accuracy bars, F1 trend charts, data quality and agreement scores).

    MLOps traceability chain:
        AiModel → ModelVersion → ModelHealthMetric
                               → Prediction → AiInsight → Recommendation

    All scores are in [0.0000 … 1.0000] where 1.0 = perfect.

    ``data_quality_score`` : fraction of valid, in-range inputs during
                             the evaluation window.
    ``agreement_score``    : inter-model agreement coefficient when
                             multiple ensemble members are used.

    TimescaleDB hypertable — partition column: ``recorded_at``.
    Composite PK: (id, recorded_at).

    Alembic note:
        After table creation run:
            SELECT create_hypertable('model_health_metrics', 'recorded_at',
                chunk_time_interval => INTERVAL '90 days');
    """

    __tablename__ = "model_health_metrics"
    __table_args__ = (
        Index("ix_model_health_metrics_version_time", "model_version_id", "recorded_at"),
        CheckConstraint("accuracy        IS NULL OR accuracy        BETWEEN 0 AND 1", name="ck_mhm_accuracy_range"),
        CheckConstraint("precision       IS NULL OR precision       BETWEEN 0 AND 1", name="ck_mhm_precision_range"),
        CheckConstraint("recall          IS NULL OR recall          BETWEEN 0 AND 1", name="ck_mhm_recall_range"),
        CheckConstraint("f1_score        IS NULL OR f1_score        BETWEEN 0 AND 1", name="ck_mhm_f1_range"),
        CheckConstraint("data_quality_score IS NULL OR data_quality_score BETWEEN 0 AND 1", name="ck_mhm_dq_range"),
        CheckConstraint("agreement_score IS NULL OR agreement_score BETWEEN 0 AND 1", name="ck_mhm_agreement_range"),
        {
            "comment": (
                "TimescaleDB hypertable — MLOps performance snapshots per model version. "
                "Partition: recorded_at / 90-day chunks. "
                "Powers the Settings page AI Operations Monitor."
            )
        },
    )

    # ── Composite PK (UUID + time for TimescaleDB) ────────────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID — stable row identifier.",
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="Evaluation timestamp (TimescaleDB partition key).",
    )

    # ── FK — MLOps traceability ───────────────────────────────────────────────
    model_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("model_versions.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → model_versions.id — which version these metrics were evaluated against.",
    )

    # ── Classification metrics ────────────────────────────────────────────────
    accuracy: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="Classification accuracy [0.0 … 1.0].",
    )
    precision: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="Precision (positive predictive value) [0.0 … 1.0].",
    )
    recall: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="Recall (sensitivity / true positive rate) [0.0 … 1.0].",
    )
    f1_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment="Harmonic mean of precision and recall [0.0 … 1.0].",
    )

    # ── Operational quality metrics ───────────────────────────────────────────
    data_quality_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment=(
            "Fraction of model inputs that passed data quality checks "
            "in this evaluation window [0.0 … 1.0]. "
            "Low scores indicate upstream sensor/pipeline issues."
        ),
    )
    agreement_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        comment=(
            "Inter-model agreement coefficient for ensemble models [0.0 … 1.0]. "
            "Measures consistency between sub-model predictions."
        ),
    )

    # ── Relationship ──────────────────────────────────────────────────────────
    model_version: Mapped["ModelVersion"] = relationship(
        "ModelVersion",
        back_populates="health_metrics",
    )

    def __repr__(self) -> str:
        return (
            f"<ModelHealthMetric id={self.id} "
            f"model_version_id={self.model_version_id} "
            f"recorded_at={self.recorded_at} "
            f"accuracy={self.accuracy} f1={self.f1_score}>"
        )
