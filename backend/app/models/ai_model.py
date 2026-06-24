from __future__ import annotations

from uuid import UUID
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.model_version import ModelVersion


class AiModel(Base, UUIDMixin, TimestampMixin):
    """
    AI/ML model registry entry.

    Each row represents one named model (e.g. 'PSI Predictor',
    'Disease Risk Classifier', 'Harvest Forecast').
    Versioning is handled by the related ModelVersion table.

    MLOps traceability chain:
        AiModel → ModelVersion → Prediction → AiInsight → Recommendation

    ``algorithm`` : ML algorithm family (e.g. 'LSTM', 'XGBoost',
                    'Random Forest', 'Transformer').
    ``status``    : current operational phase of the model.
    ``owner_id``  : FK → users.id — the data scientist / team responsible.
    """

    __tablename__ = "ai_models"
    __table_args__ = (
        Index("ix_ai_models_status",    "status"),
        Index("ix_ai_models_algorithm", "algorithm"),
        CheckConstraint(
            "status IN ("
            "'Development','Staging','Production','Deprecated')",
            name="ck_ai_model_status_valid",
        ),
        {
            "comment": (
                "AI/ML model registry — one row per named model. "
                "Versioning via model_versions. "
                "Anchors the MLOps traceability chain."
            )
        },
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique model name (e.g. 'PSI Predictor v2', 'Sea Lice Classifier').",
    )
    algorithm: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment=(
            "ML algorithm family: "
            "'LSTM' | 'XGBoost' | 'Random Forest' | 'Transformer' | "
            "'CNN' | 'Ensemble' | 'Rule-Based' | 'Other'."
        ),
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Narrative description of the model's purpose, inputs, and outputs.",
    )

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Development",
        comment="'Development' | 'Staging' | 'Production' | 'Deprecated'.",
    )

    # ── Ownership ─────────────────────────────────────────────────────────────
    owner_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="FK → users.id — data scientist or team lead responsible for this model.",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    versions: Mapped[list["ModelVersion"]] = relationship(
        "ModelVersion",
        back_populates="model",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ModelVersion.trained_at.desc()",
    )

    def __repr__(self) -> str:
        return (
            f"<AiModel id={self.id} name={self.name!r} "
            f"algorithm={self.algorithm!r} status={self.status!r}>"
        )
