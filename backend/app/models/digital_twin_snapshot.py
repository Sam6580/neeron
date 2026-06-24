from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DigitalTwinSnapshot(Base):
    """
    Simulated tank state snapshot from the Digital Twin engine.

    The Digital Twin runs forward simulations of tank conditions under
    configurable scenarios (e.g. 'Baseline', 'Increased Feed', 'Reduced
    Stocking', 'Aeration Boost') to support what-if analysis and
    proactive planning.

    ``scenario_name``    : identifies the simulation run; multiple scenarios
                           can exist per tank per simulation_time.
    ``simulation_time``  : the simulated point in time being modelled —
                           distinct from the wall-clock timestamp of the row.
    ``simulated_biomass``: projected total live weight (kg) in scenario.
    ``simulated_growth`` : projected daily growth rate (g/fish/day).
    ``simulated_oxygen`` : projected dissolved oxygen level (mg/L).

    TimescaleDB hypertable — partition column: ``simulation_time``.
    Composite PK: (id, simulation_time).

    Alembic note:
        After table creation run:
            SELECT create_hypertable('digital_twin_snapshots', 'simulation_time',
                chunk_time_interval => INTERVAL '30 days');
    """

    __tablename__ = "digital_twin_snapshots"
    __table_args__ = (
        Index("ix_digital_twin_tank_sim_time",     "tank_id", "simulation_time"),
        Index("ix_digital_twin_scenario",          "scenario_name", "simulation_time"),
        CheckConstraint("simulated_biomass >= 0",  name="ck_dt_biomass_non_negative"),
        CheckConstraint("simulated_growth >= 0",   name="ck_dt_growth_non_negative"),
        CheckConstraint("simulated_oxygen >= 0",   name="ck_dt_oxygen_non_negative"),
        {
            "comment": (
                "TimescaleDB hypertable — Digital Twin scenario simulation snapshots. "
                "Partition: simulation_time / 30-day chunks."
            )
        },
    )

    # ── Composite PK (UUID + time for TimescaleDB) ────────────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID — stable row identifier.",
    )
    simulation_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment=(
            "The simulated point in time (NOT wall-clock). "
            "TimescaleDB partition key."
        ),
    )

    # ── FK ──────────────────────────────────────────────────────────────────
    tank_id: Mapped[UUID] = mapped_column(
        ForeignKey("tanks.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → tanks.id — the tank being simulated.",
    )

    # ── Scenario ──────────────────────────────────────────────────────────────
    scenario_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment=(
            "Simulation scenario label. "
            "e.g. 'Baseline' | 'Increased Feed +10%' | "
            "'Reduced Stocking' | 'Aeration Boost'."
        ),
    )

    # ── Simulated state variables ─────────────────────────────────────────────
    simulated_biomass: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Projected total live weight (kg) of the fish population at simulation_time.",
    )
    simulated_growth: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        comment="Projected daily growth rate in grams per fish per day (g/fish/day).",
    )
    simulated_oxygen: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        comment="Projected dissolved oxygen concentration (mg/L) at simulation_time.",
    )

    def __repr__(self) -> str:
        return (
            f"<DigitalTwinSnapshot id={self.id} tank_id={self.tank_id} "
            f"scenario={self.scenario_name!r} "
            f"simulation_time={self.simulation_time} "
            f"simulated_biomass={self.simulated_biomass}>"
        )
