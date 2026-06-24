from __future__ import annotations

from uuid import UUID
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDMixin

if TYPE_CHECKING:
    from app.models.ai_model import AiModel
    from app.models.model_health_metric import ModelHealthMetric


class ModelVersion(Base, UUIDMixin):
    """
    A specific trained and versioned artefact of an AI model.

    MLOps traceability chain (this is the critical link):
        AiModel → ModelVersion → Prediction → AiInsight → Recommendation

    Every prediction table (psi_predictions, disease_predictions,
    mortality_predictions, harvest_predictions) and ai_insights carry a
    ``model_version_id`` FK → this table, enabling full backward
    traceability: given any insight or recommendation, you can trace
    exactly which model version produced it.

    ``artifact_uri`` : storage URI of the serialised model artefact
                       (e.g. MLflow / S3 path: 's3://neeron-models/psi/v2.1.0.pkl').
    ``version_tag``  : human-readable version string (e.g. 'v2.1.0').
    ``is_active``    : True for the single currently-deployed version.
                       Enforced at application layer (not DB unique constraint)
                       to allow graceful rollover without downtime.
    ``deployed_at``  : NULL until the version is promoted to production.
    ``status``       : 'Active' | 'Testing' | 'Archived'.
    """

    __tablename__ = "model_versions"
    __table_args__ = (
        UniqueConstraint("model_id", "version_tag", name="uq_model_version_tag"),
        Index("ix_model_versions_model_status", "model_id", "status"),
        Index("ix_model_versions_is_active",    "model_id", "is_active"),
        CheckConstraint(
            "status IN ('Active','Testing','Archived')",
            name="ck_model_version_status_valid",
        ),
        {
            "comment": (
                "Model version registry — one row per trained artefact. "
                "Critical FK target for prediction tables and ai_insights "
                "to support full MLOps traceability."
            )
        },
    )

    # ── FK ──────────────────────────────────────────────────────────────────
    model_id: Mapped[UUID] = mapped_column(
        ForeignKey("ai_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK → ai_models.id",
    )

    # ── Version identity ──────────────────────────────────────────────────────
    version_tag: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Semantic version string (e.g. 'v2.1.0'). Unique per model.",
    )
    artifact_uri: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment=(
            "URI of the serialised model artefact. "
            "e.g. 's3://neeron-models/psi-predictor/v2.1.0/model.pkl' "
            "or 'mlflow://experiments/42/runs/abc123/artifacts/model'."
        ),
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional release notes or changelog for this version.",
    )

    # ── ML metadata ───────────────────────────────────────────────────────────
    hyperparameters: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Training hyperparameters (JSON) — stored for reproducibility.",
    )
    metrics: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Final evaluation metrics from training/validation (JSON).",
    )

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Testing",
        comment="'Active' | 'Testing' | 'Archived'.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment=(
            "True for the currently deployed (production) version. "
            "Only one version per model should be active at a time "
            "(enforced at application layer)."
        ),
    )
    trained_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Timestamp when training completed.",
    )
    deployed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when this version was promoted to production. NULL = not yet deployed.",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    model: Mapped["AiModel"] = relationship(
        "AiModel",
        back_populates="versions",
    )
    health_metrics: Mapped[list["ModelHealthMetric"]] = relationship(
        "ModelHealthMetric",
        back_populates="model_version",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return (
            f"<ModelVersion id={self.id} model_id={self.model_id} "
            f"version_tag={self.version_tag!r} status={self.status!r} "
            f"is_active={self.is_active}>"
        )
