from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RecommendationAction(Base):
    """
    Operator action on an AI recommendation.

    Tracks direct operator responses (Accepted, Rejected, Ignored) in the UI.
    This feedback loop helps downstream ML algorithms learn decision preferences
    and associate recommendations with farm/tank production outcome improvements.

    TimescaleDB hypertable — partition column: ``executed_at``.
    Composite PK: (id, executed_at) to allow stable UUID reference and comply
    with TimescaleDB requirements.
    """

    __tablename__ = "recommendation_actions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["recommendation_id", "recommendation_time"],
            ["recommendations.id", "recommendations.time"],
            ondelete="CASCADE",
            name="fk_rec_actions_recommendation",
        ),
        CheckConstraint(
            "action IN ('Accepted', 'Rejected', 'Ignored')",
            name="ck_rec_action_valid",
        ),
        Index("ix_rec_actions_rec_composite", "recommendation_id", "recommendation_time"),
        {
            "comment": (
                "TimescaleDB hypertable — operator UI actions (accept/reject/ignore) on recommendations. "
                "Partition: executed_at / 30-day chunks."
            )
        },
    )

    # ── Composite PK (UUID + executed_at for TimescaleDB) ────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID identifier for the UI action.",
    )
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="Action execution timestamp (TimescaleDB partition key).",
    )

    # ── FKs ──────────────────────────────────────────────────────────────────
    recommendation_id: Mapped[UUID] = mapped_column(
        comment="FK → recommendations.id (part of composite FK).",
    )
    recommendation_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        comment="FK → recommendations.time (part of composite FK).",
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="FK → users.id (operator who took the action).",
    )

    # ── Action details ───────────────────────────────────────────────────────
    action: Mapped[str] = mapped_column(
        comment="Action taken: 'Accepted' | 'Rejected' | 'Ignored'",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    recommendation: Mapped["Recommendation"] = relationship(
        "Recommendation",
        foreign_keys=[recommendation_id, recommendation_time],
    )
    user: Mapped["User"] = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<RecommendationAction id={self.id} recommendation_id={self.recommendation_id} "
            f"user_id={self.user_id} action={self.action!r} executed_at={self.executed_at}>"
        )
