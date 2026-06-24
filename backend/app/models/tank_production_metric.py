from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TankProductionMetric(Base):
    """
    Periodic biological production snapshot for a tank.

    Records biomass growth, feed conversion efficiency, population, and
    mortality at each operator data-entry or automated polling interval
    (typically daily or per-shift).

    Used by:
      - Analytics page (growth trend charts, FCR tracking).
      - Harvest prediction model (biomass trajectory input feature).
      - Dashboard summary (current_biomass, current_fcr KPIs).

    TimescaleDB hypertable — partition column: ``recorded_at``.
    Composite PK: (id, recorded_at) satisfies TimescaleDB constraint.

    Alembic note:
        After table creation run:
            SELECT create_hypertable('tank_production_metrics', 'recorded_at',
                chunk_time_interval => INTERVAL '30 days');
    """

    __tablename__ = "tank_production_metrics"
    __table_args__ = (
        Index(
            "ix_production_metrics_tank_recorded",
            "tank_id",
            "recorded_at",
        ),
        CheckConstraint("population >= 0",          name="ck_prod_metric_population_non_negative"),
        CheckConstraint("biomass_kg >= 0",           name="ck_prod_metric_biomass_non_negative"),
        CheckConstraint("average_weight_g >= 0",     name="ck_prod_metric_avg_weight_non_negative"),
        CheckConstraint("fcr >= 0",                  name="ck_prod_metric_fcr_non_negative"),
        CheckConstraint(
            "mortality_rate BETWEEN 0 AND 1",
            name="ck_prod_metric_mortality_range",
        ),
        CheckConstraint(
            "feed_consumption_kg >= 0",
            name="ck_prod_metric_feed_non_negative",
        ),
        {
            "comment": (
                "TimescaleDB hypertable — biological production snapshots per tank. "
                "Partition: recorded_at / 30-day chunks."
            )
        },
    )

    # ── Composite PK (UUID + time for TimescaleDB) ────────────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID — stable identifier for harvest prediction linkage.",
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="Observation timestamp (TimescaleDB partition key).",
    )

    # ── FK ──────────────────────────────────────────────────────────────────
    tank_id: Mapped[UUID] = mapped_column(
        ForeignKey("tanks.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → tanks.id",
    )

    # ── Biological metrics ────────────────────────────────────────────────────
    population: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Live fish count in the tank at time of recording (≥ 0).",
    )
    biomass_kg: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Total live weight (kg) — population × average_weight_g / 1000.",
    )
    average_weight_g: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Mean individual fish weight in grams (≥ 0).",
    )

    # ── Feed conversion ───────────────────────────────────────────────────────
    fcr: Mapped[float] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        comment=(
            "Feed Conversion Ratio — kg feed consumed / kg biomass gained. "
            "Industry target: < 1.20 for Atlantic Salmon."
        ),
    )
    feed_consumption_kg: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Total feed delivered to tank during this period (kg).",
    )

    # ── Mortality ─────────────────────────────────────────────────────────────
    mortality_rate: Mapped[float] = mapped_column(
        Numeric(6, 4),
        nullable=False,
        comment="Fractional mortality rate for this period (0.0 … 1.0).",
    )

    def __repr__(self) -> str:
        return (
            f"<TankProductionMetric id={self.id} "
            f"tank_id={self.tank_id} recorded_at={self.recorded_at} "
            f"biomass_kg={self.biomass_kg} fcr={self.fcr}>"
        )
