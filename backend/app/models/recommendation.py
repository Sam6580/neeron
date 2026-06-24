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
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Recommendation(Base):
    """
    AI-generated operational recommendation for a tank operator.

    Priority levels  : 'Low' | 'Medium' | 'High' | 'Critical'
    Status lifecycle : 'Pending' → 'Accepted' | 'Dismissed' | 'Completed'

    ``generated_by_model`` stores the model_version_id (as UUID string)
    from the AI model that produced this recommendation, enabling
    traceability back to a specific model version.

    ``confidence`` ∈ [0.0, 1.0] — prediction confidence score.

    TimescaleDB hypertable — partition column: ``time``.
    Composite PK: (id, time) provides stable UUID reference while
    satisfying the TimescaleDB partition-key-in-PK requirement.

    Alembic note:
        After table creation run:
            SELECT create_hypertable('recommendations', 'time',
                chunk_time_interval => INTERVAL '30 days');
    """

    __tablename__ = "recommendations"
    __table_args__ = (
        Index("ix_recommendations_tank_time",    "tank_id", "time"),
        Index("ix_recommendations_status_priority", "status", "priority"),
        CheckConstraint(
            "priority IN ('Low','Medium','High','Critical')",
            name="ck_recommendation_priority_valid",
        ),
        CheckConstraint(
            "status IN ('Pending','Accepted','Dismissed','Completed')",
            name="ck_recommendation_status_valid",
        ),
        CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name="ck_recommendation_confidence_range",
        ),
        {
            "comment": (
                "TimescaleDB hypertable — AI-generated operational recommendations. "
                "Partition: time / 30-day chunks."
            )
        },
    )

    # ── Composite PK (UUID + time for TimescaleDB) ────────────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID — referenced by recommendation_feedback.",
    )
    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="Recommendation generation timestamp (TimescaleDB partition key).",
    )

    # ── FKs ──────────────────────────────────────────────────────────────────
    tank_id: Mapped[UUID] = mapped_column(
        ForeignKey("tanks.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → tanks.id",
    )

    # ── AI provenance ─────────────────────────────────────────────────────────
    generated_by_model: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("model_versions.id", ondelete="SET NULL"),
        nullable=True,
        comment=(
            "FK → model_versions.id — the model version that generated "
            "this recommendation. Enables MLOps traceability."
        ),
    )

    # ── Content ───────────────────────────────────────────────────────────────
    action: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Short imperative action title shown in the UI (e.g. 'Increase aeration').",
    )
    expected_outcome: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Narrative description of what the action will achieve.",
    )
    confidence: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Model confidence score for this recommendation [0.0 … 1.0].",
    )

    # ── Classification ────────────────────────────────────────────────────────
    priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="'Low' | 'Medium' | 'High' | 'Critical'",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Pending",
        comment="'Pending' | 'Accepted' | 'Dismissed' | 'Completed'",
    )

    # ── Resolution ────────────────────────────────────────────────────────────
    resolved_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK → users.id  (operator who acted on the recommendation).",
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the recommendation was actioned or dismissed.",
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Free-text operator notes on the resolution.",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    feedback: Mapped[Optional["RecommendationFeedback"]] = relationship(
        "RecommendationFeedback",
        back_populates="recommendation",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
        primaryjoin=(
            "and_(Recommendation.id == foreign(RecommendationFeedback.recommendation_id),"
            "Recommendation.time == foreign(RecommendationFeedback.recommendation_time))"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Recommendation id={self.id} tank_id={self.tank_id} "
            f"priority={self.priority!r} status={self.status!r} "
            f"confidence={self.confidence}>"
        )
