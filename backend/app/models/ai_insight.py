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
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.historical_case import HistoricalCase


class AiInsight(Base):
    """
    Persisted AI-generated insight for display on dashboards and as input
    to the recommendation engine.

    An AiInsight is the structured intermediate step between a prediction
    (or case match) and a final Recommendation.  It captures the AI's
    synthesised interpretation in human-readable form, together with
    provenance metadata for auditability.

    Recommendation engine chain:
        Prediction → CaseMatch → HistoricalCase → AiInsight → Recommendation

    ``source_model_id`` : FK → model_versions.id — which model version
                          generated this insight (MLOps traceability).
    ``historical_case_id``: optional FK → historical_cases.id — if this
                            insight was surfaced by the CBR engine from a
                            matched historical case.
    ``priority``        : 'Info' | 'Medium' | 'High' | 'Critical'.
    ``confidence``      : model confidence [0.0000 … 1.0000].
    ``expires_at``      : if set, the insight is suppressed after this timestamp.

    TimescaleDB hypertable — partition column: ``generated_at``.
    Composite PK: (id, generated_at).

    Alembic note:
        After table creation run:
            SELECT create_hypertable('ai_insights', 'generated_at',
                chunk_time_interval => INTERVAL '30 days');
    """

    __tablename__ = "ai_insights"
    __table_args__ = (
        Index("ix_ai_insights_tank_generated",   "tank_id", "generated_at"),
        Index("ix_ai_insights_priority_active",  "priority", "generated_at"),
        # Partial index for permanently-active insights. The predicate must be
        # IMMUTABLE for Postgres, so the time-based check (expires_at > now())
        # is applied at query time rather than in the index predicate.
        Index(
            "ix_ai_insights_active",
            "tank_id",
            "generated_at",
            postgresql_where="expires_at IS NULL",
        ),
        CheckConstraint(
            "priority IN ('Info','Medium','High','Critical')",
            name="ck_ai_insight_priority_valid",
        ),
        CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name="ck_ai_insight_confidence_range",
        ),
        {
            "comment": (
                "TimescaleDB hypertable — AI-synthesised insights for dashboards "
                "and the recommendation engine. "
                "Partition: generated_at / 30-day chunks."
            )
        },
    )

    # ── Composite PK (UUID + time for TimescaleDB) ────────────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID — referenced by Recommendation.insight_id.",
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        server_default=func.now(),
        comment="Insight generation timestamp (TimescaleDB partition key).",
    )

    # ── Scope FKs ────────────────────────────────────────────────────────────
    tank_id: Mapped[UUID] = mapped_column(
        ForeignKey("tanks.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → tanks.id — the tank this insight pertains to.",
    )

    # ── Provenance — MLOps traceability ──────────────────────────────────────
    source_model_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("model_versions.id", ondelete="SET NULL"),
        nullable=True,
        comment=(
            "FK → model_versions.id — the specific model version that generated "
            "this insight. Enables MLOps auditability and model performance tracking."
        ),
    )

    # ── CBR linkage (optional) ────────────────────────────────────────────────
    historical_case_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("historical_cases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment=(
            "FK → historical_cases.id — if this insight was derived from a "
            "CBR case match, links back to the source historical case."
        ),
    )

    # ── Content ───────────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Short, actionable insight headline shown in the UI.",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full narrative explanation of the insight and its supporting evidence.",
    )

    # ── Classification ────────────────────────────────────────────────────────
    priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="'Info' | 'Medium' | 'High' | 'Critical'",
    )
    confidence: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Model confidence in this insight [0.0000 … 1.0000].",
    )

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment=(
            "Optional expiry timestamp. "
            "Insight is suppressed in the UI after this time. "
            "NULL = permanently active."
        ),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    historical_case: Mapped[Optional["HistoricalCase"]] = relationship(
        "HistoricalCase",
        back_populates="ai_insights",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<AiInsight id={self.id} tank_id={self.tank_id} "
            f"priority={self.priority!r} confidence={self.confidence} "
            f"expires_at={self.expires_at}>"
        )
