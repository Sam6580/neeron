from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.historical_case import HistoricalCase


class CaseMatch(Base):
    """
    Links an active prediction to a historically similar case.

    This is the core join table of the Case-Based Reasoning (CBR) engine.
    The recommendation engine traverses this table to retrieve proven
    resolutions from HistoricalCase.resolution, then generates
    an AiInsight and ultimately a Recommendation.

    Recommendation engine chain:
        Prediction → CaseMatch → HistoricalCase → AiInsight → Recommendation

    ``prediction_id`` : UUID of the source prediction (disease, PSI, mortality,
                        or harvest).  Stored as plain UUID (not typed FK)
                        because it can reference any prediction hypertable.
    ``prediction_type``: discriminates which prediction table to join
                         ('psi' | 'disease' | 'mortality' | 'harvest').
    ``similarity_score``: cosine / embedding similarity [0.0000 … 1.0000].
    ``matched_at``    : when the CBR engine produced this match.

    TimescaleDB hypertable — partition column: ``matched_at``.
    Composite PK: (id, matched_at).

    Alembic note:
        After table creation run:
            SELECT create_hypertable('case_matches', 'matched_at',
                chunk_time_interval => INTERVAL '30 days');
    """

    __tablename__ = "case_matches"
    __table_args__ = (
        # Fast lookup: all matches for a given prediction
        Index("ix_case_matches_prediction",      "prediction_id", "matched_at"),
        # Fast lookup: all predictions matched to a given case
        Index("ix_case_matches_case_id",         "case_id"),
        # Top-N matches by similarity for a prediction
        Index("ix_case_matches_similarity",      "prediction_id", "similarity_score"),
        CheckConstraint(
            "similarity_score BETWEEN 0 AND 1",
            name="ck_case_match_similarity_range",
        ),
        CheckConstraint(
            "prediction_type IN ('psi','disease','mortality','harvest')",
            name="ck_case_match_prediction_type_valid",
        ),
        {
            "comment": (
                "TimescaleDB hypertable — CBR engine: prediction-to-case similarity matches. "
                "Partition: matched_at / 30-day chunks."
            )
        },
    )

    # ── Composite PK (UUID + time for TimescaleDB) ────────────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID — stable row identifier.",
    )
    matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        server_default=func.now(),
        comment="Timestamp when the CBR engine produced this match (TimescaleDB partition key).",
    )

    # ── Source prediction (polymorphic reference) ─────────────────────────────
    prediction_id: Mapped[UUID] = mapped_column(
        nullable=False,
        comment=(
            "UUID of the source prediction. "
            "Use prediction_type to determine which hypertable to join. "
            "Stored without a DB-level FK to support cross-hypertable polymorphism."
        ),
    )
    prediction_type: Mapped[str] = mapped_column(
        nullable=False,
        comment="Discriminator: 'psi' | 'disease' | 'mortality' | 'harvest'.",
    )

    # ── Target historical case ────────────────────────────────────────────────
    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("historical_cases.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → historical_cases.id",
    )

    # ── CBR score ────────────────────────────────────────────────────────────
    similarity_score: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment="Cosine / embedding similarity between prediction features and case [0.0 … 1.0].",
    )

    # ── Relationship ──────────────────────────────────────────────────────────
    historical_case: Mapped["HistoricalCase"] = relationship(
        "HistoricalCase",
        back_populates="case_matches",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<CaseMatch id={self.id} "
            f"prediction_id={self.prediction_id} "
            f"prediction_type={self.prediction_type!r} "
            f"case_id={self.case_id} "
            f"similarity_score={self.similarity_score}>"
        )
