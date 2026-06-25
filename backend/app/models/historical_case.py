from __future__ import annotations

from uuid import UUID
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.base import Base
from app.db.mixins import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.case_match import CaseMatch
    from app.models.ai_insight import AiInsight


class HistoricalCase(Base, UUIDMixin, TimestampMixin):
    """
    Catalog of past aquaculture operational incidents and their resolutions.

    Used by the Case-Based Reasoning (CBR) engine to match active
    predictions against historical precedents and surface proven
    remediation strategies.

    Recommendation engine chain:
        Prediction → CaseMatch → HistoricalCase → AiInsight → Recommendation

    ``scenario_type`` : categorises the case for similarity matching
                        (e.g. 'Dissolved Oxygen Depletion', 'Sea Lice Influx').
    ``severity``      : operational impact classification.
    ``outcome``       : what happened (e.g. 'FCR restored, zero mortalities').
    ``resolution``    : the corrective actions taken.

    This is a relational (non-hypertable) reference table.
    Rows are curated by aquaculture experts and updated infrequently.
    """

    __tablename__ = "historical_cases"
    __table_args__ = (
        Index("ix_historical_cases_scenario_type", "scenario_type"),
        Index("ix_historical_cases_severity",      "severity"),
        CheckConstraint(
            "severity IN ('Low','Medium','High','Critical')",
            name="ck_historical_case_severity_valid",
        ),
        {
            "comment": (
                "CBR case catalog — curated historical incidents and resolutions. "
                "Feeds the recommendation engine via case_matches."
            )
        },
    )

    # ── Descriptors ──────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Short, human-readable case title shown in the UI.",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Detailed narrative describing the incident conditions.",
    )
    scenario_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment=(
            "Machine-readable category used by the similarity engine. "
            "e.g. 'Dissolved Oxygen Depletion' | 'Sea Lice Influx' | "
            "'High Ammonia Event' | 'Thermal Stress' | 'Gill Disease'."
        ),
    )
    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Impact severity: 'Low' | 'Medium' | 'High' | 'Critical'.",
    )

    # ── Resolution record ─────────────────────────────────────────────────────
    outcome: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Factual description of what occurred (observable result).",
    )
    resolution: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment=(
            "Step-by-step corrective actions taken. "
            "Surfaced by the recommendation engine as proven remediation."
        ),
    )

    # ── Recommendation-engine readiness ───────────────────────────────────────
    # tags / embeddings can be added here in a future migration as a
    # JSON column (e.g. `scenario_vector JSONB`) for vector similarity search.

    # ── Relationships ─────────────────────────────────────────────────────────
    case_matches: Mapped[list["CaseMatch"]] = relationship(
        "CaseMatch",
        back_populates="historical_case",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    ai_insights: Mapped[list["AiInsight"]] = relationship(
        "AiInsight",
        back_populates="historical_case",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return (
            f"<HistoricalCase id={self.id} "
            f"scenario_type={self.scenario_type!r} severity={self.severity!r}>"
        )
