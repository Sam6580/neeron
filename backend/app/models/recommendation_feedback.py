from __future__ import annotations

from uuid import UUID
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RecommendationFeedback(Base):
    """
    Operator feedback on a completed or dismissed recommendation.

    Closes the AI feedback loop: effectiveness scores are aggregated
    during model retraining to improve future recommendation quality.

    ``action_taken``       : what the operator actually did.
    ``effectiveness_score``: 1 (not effective) … 5 (highly effective).
    ``comments``           : optional free-text narrative.

    TimescaleDB hypertable — partition column: ``recommendation_time``.
    Composite PK: (recommendation_id, recommendation_time) mirrors the
    parent ``recommendations`` composite PK for the FK constraint,
    satisfying TimescaleDB's requirement.

    Alembic note:
        After table creation run:
            SELECT create_hypertable('recommendation_feedback',
                'recommendation_time',
                chunk_time_interval => INTERVAL '30 days');
    """

    __tablename__ = "recommendation_feedback"
    __table_args__ = (
        ForeignKeyConstraint(
            ["recommendation_id", "recommendation_time"],
            ["recommendations.id",  "recommendations.time"],
            ondelete="CASCADE",
            name="fk_rec_feedback_recommendation",
        ),
        CheckConstraint(
            "effectiveness_score BETWEEN 1 AND 5",
            name="ck_rec_feedback_effectiveness_range",
        ),
        CheckConstraint(
            "action_taken IN ("
            "'Applied Remediation',"
            "'Alternative Action Taken',"
            "'Ignored - False Alarm',"
            "'Ignored - Operational Constraints')",
            name="ck_rec_feedback_action_valid",
        ),
        Index("ix_rec_feedback_recommendation", "recommendation_id", "recommendation_time"),
        {
            "comment": (
                "TimescaleDB hypertable — operator feedback on AI recommendations. "
                "Partition: recommendation_time / 30-day chunks."
            )
        },
    )

    # ── Composite PK mirrors parent recommendation PK ─────────────────────────
    recommendation_id: Mapped[UUID] = mapped_column(
        primary_key=True,
        comment="FK → recommendations.id  (part of composite PK).",
    )
    recommendation_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="FK → recommendations.time  (TimescaleDB partition key).",
    )

    # ── FK — who provided feedback ────────────────────────────────────────────
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="FK → users.id  (RESTRICT preserves feedback authorship).",
    )

    # ── Feedback payload ──────────────────────────────────────────────────────
    action_taken: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment=(
            "What the operator did: "
            "'Applied Remediation' | 'Alternative Action Taken' | "
            "'Ignored - False Alarm' | 'Ignored - Operational Constraints'."
        ),
    )
    effectiveness_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Operator rating of recommendation effectiveness: 1 (poor) … 5 (excellent).",
    )
    comments: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional free-text operator commentary on the recommendation outcome.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Feedback submission timestamp.",
    )

    # ── Relationship ──────────────────────────────────────────────────────────
    recommendation: Mapped["Recommendation"] = relationship(
        "Recommendation",
        back_populates="feedback",
        foreign_keys=[recommendation_id, recommendation_time],
    )

    def __repr__(self) -> str:
        return (
            f"<RecommendationFeedback "
            f"recommendation_id={self.recommendation_id} "
            f"score={self.effectiveness_score} "
            f"action={self.action_taken!r}>"
        )
