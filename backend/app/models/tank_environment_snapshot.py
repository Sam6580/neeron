from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TankEnvironmentSnapshot(Base):
    """
    Pre-pivoted, per-tank environmental snapshot.

    Each row consolidates all active sensor streams for a single tank
    into a single, analytics-ready row.  This avoids expensive pivot
    joins every time the dashboard, ML pipeline, or PSI predictor
    needs current water-quality parameters.

    Populated by one of:
      - Application-layer MQTT ingestion worker (5-second sliding window).
      - PostgreSQL trigger on the raw ``telemetry`` table.

    TimescaleDB hypertable — partition column: ``captured_at``.
    Composite PK: (id, captured_at) satisfies TimescaleDB constraint.

    Alembic note:
        After table creation run:
            SELECT create_hypertable('tank_environment_snapshots', 'captured_at',
                chunk_time_interval => INTERVAL '7 days');
    """

    __tablename__ = "tank_environment_snapshots"
    __table_args__ = (
        # Primary analytical access pattern: latest snapshot per tank
        Index(
            "ix_env_snapshot_tank_captured",
            "tank_id",
            "captured_at",
        ),
        CheckConstraint(
            "temperature BETWEEN -5.00 AND 40.00",
            name="ck_env_snapshot_temp_range",
        ),
        CheckConstraint(
            "ph BETWEEN 0.00 AND 14.00",
            name="ck_env_snapshot_ph_range",
        ),
        CheckConstraint(
            "dissolved_oxygen >= 0",
            name="ck_env_snapshot_do_non_negative",
        ),
        CheckConstraint(
            "salinity >= 0",
            name="ck_env_snapshot_salinity_non_negative",
        ),
        CheckConstraint(
            "ammonia >= 0",
            name="ck_env_snapshot_ammonia_non_negative",
        ),
        CheckConstraint(
            "turbidity >= 0",
            name="ck_env_snapshot_turbidity_non_negative",
        ),
        {
            "comment": (
                "TimescaleDB hypertable — pivoted per-tank environmental snapshots. "
                "Partition: captured_at / 7-day chunks."
            )
        },
    )

    # ── Composite PK (UUID + time for TimescaleDB) ────────────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID — stable identifier for ML feature linkage.",
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="Snapshot bucket timestamp (TimescaleDB partition key).",
    )

    # ── FK ──────────────────────────────────────────────────────────────────
    tank_id: Mapped[UUID] = mapped_column(
        ForeignKey("tanks.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → tanks.id",
    )

    # ── Water-quality parameters ──────────────────────────────────────────────
    temperature: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2),
        nullable=True,
        comment="Water temperature in °C (−5.00 … 40.00).",
    )
    ph: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 2),
        nullable=True,
        comment="pH value (0.00 … 14.00).",
    )
    dissolved_oxygen: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2),
        nullable=True,
        comment="Dissolved oxygen concentration in mg/L (≥ 0).",
    )
    salinity: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2),
        nullable=True,
        comment="Salinity in PSU / g/kg (≥ 0).",
    )
    ammonia: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 4),
        nullable=True,
        comment="Total ammonia nitrogen (TAN) in mg/L (≥ 0).",
    )
    turbidity: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2),
        nullable=True,
        comment="Water turbidity in NTU (≥ 0).",
    )

    def __repr__(self) -> str:
        return (
            f"<TankEnvironmentSnapshot id={self.id} "
            f"tank_id={self.tank_id} captured_at={self.captured_at}>"
        )
