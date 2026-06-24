from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, JSON, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Telemetry(Base):
    """
    Raw IoT telemetry stream — one row per sensor reading.

    TimescaleDB hypertable — partition column: ``time``.
    Composite PK: (id, time) satisfies the TimescaleDB requirement that
    the partition key be part of any primary / unique constraint,
    while ``id`` provides a stable UUID reference.

    This table feeds the MQTT ingest pipeline.
    Downstream ``tank_environment_snapshots`` pivots these values
    per-tank for ML/dashboard consumption.

    Alembic note:
        After table creation run:
            SELECT create_hypertable('telemetry', 'time',
                chunk_time_interval => INTERVAL '1 day');
    """

    __tablename__ = "telemetry"
    __table_args__ = (
        # Composite index: most queries filter by sensor then slice by time
        Index("ix_telemetry_sensor_time", "sensor_id", "time"),
        {
            "comment": (
                "TimescaleDB hypertable — raw IoT sensor readings. "
                "Partition: time / 1-day chunks."
            )
        },
    )

    # ── Composite PK (UUID + time for TimescaleDB) ────────────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID — stable FK target for downstream references.",
    )
    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="Reading timestamp (TimescaleDB partition key).",
    )

    # ── FK ──────────────────────────────────────────────────────────────────
    sensor_id: Mapped[UUID] = mapped_column(
        ForeignKey("sensors.id", ondelete="RESTRICT"),
        nullable=False,
        comment="FK → sensors.id  (RESTRICT: retain readings even if sensor is decommissioned).",
    )

    # ── Payload ───────────────────────────────────────────────────────────────
    value: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        comment="Numeric sensor reading in the sensor's native unit.",
    )
    raw_payload: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Full MQTT JSON payload for audit / re-processing.",
    )

    def __repr__(self) -> str:
        return (
            f"<Telemetry id={self.id} sensor_id={self.sensor_id} "
            f"time={self.time} value={self.value}>"
        )
