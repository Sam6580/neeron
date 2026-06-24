from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDMixin, TimestampMixin


# ─────────────────────────────────────────────────────────────────────────────
# Sensor
# ─────────────────────────────────────────────────────────────────────────────
class Sensor(Base, UUIDMixin, TimestampMixin):
    """
    Physical IoT sensor device attached to a Tank.

    Supported types: temperature | pH | dissolved_oxygen | ammonia |
                     salinity | feeder | aerator

    Status lifecycle: Active → Warning → Calibration Overdue → Offline
    """

    __tablename__ = "sensors"
    __table_args__ = (
        CheckConstraint(
            "type IN ('temperature','pH','dissolved_oxygen','ammonia',"
            "'salinity','feeder','aerator','hydrophone')",
            name="ck_sensor_type_valid",
        ),
        CheckConstraint(
            "status IN ('Active','Warning','Calibration Overdue','Offline')",
            name="ck_sensor_status_valid",
        ),
        {"comment": "IoT sensor registry — one row per physical device."},
    )

    # ── FK ──────────────────────────────────────────────────────────────────
    tank_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("tanks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="FK → tanks.id  (nullable: sensor may be unassigned / in storage).",
    )

    # ── Device identity ───────────────────────────────────────────────────────
    hardware_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Globally unique hardware/MAC identifier burned into firmware.",
    )
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Measurement type this sensor produces.",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Active",
        comment="Operational status of the device.",
    )
    calibration_due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Next mandatory calibration deadline (NULL = not yet scheduled).",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    tank: Mapped[Optional["Tank"]] = relationship(
        "Tank",
        back_populates="sensors",
    )
    sensor_health: Mapped[Optional["SensorHealth"]] = relationship(
        "SensorHealth",
        back_populates="sensor",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    calibrations: Mapped[list["Calibration"]] = relationship(
        "Calibration",
        back_populates="sensor",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Sensor id={self.id} hardware_id={self.hardware_id!r} type={self.type!r}>"


# ─────────────────────────────────────────────────────────────────────────────
# Calibration  (TimescaleDB hypertable — insert-heavy, time-partitioned)
# ─────────────────────────────────────────────────────────────────────────────
class Calibration(Base):
    """
    Records a calibration event for a sensor.

    TimescaleDB hypertable — partition column: ``time``.
    Composite PK: (id, time) satisfies TimescaleDB partition key requirement
    while providing a stable UUID reference for external systems.

    Alembic note:
        After table creation run:
            SELECT create_hypertable('calibrations', 'time',
                chunk_time_interval => INTERVAL '30 days');
    """

    __tablename__ = "calibrations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('success','failed')",
            name="ck_calibration_status_valid",
        ),
        Index("ix_calibrations_sensor_time", "sensor_id", "time"),
        {
            "comment": (
                "TimescaleDB hypertable — sensor calibration history. "
                "Partition: time / 30-day chunks."
            )
        },
    )

    # ── Composite PK (UUID + time for TimescaleDB) ────────────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID — stable reference for foreign keys.",
    )
    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="Calibration timestamp (TimescaleDB partition key).",
    )

    # ── FKs ──────────────────────────────────────────────────────────────────
    sensor_id: Mapped[UUID] = mapped_column(
        ForeignKey("sensors.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → sensors.id",
    )
    operator_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="FK → users.id  (RESTRICT preserves calibration audit trail).",
    )

    # ── Measurements ─────────────────────────────────────────────────────────
    offset_value: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        comment="Calibration offset applied to raw sensor readings.",
    )
    variance: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        comment="Measured variance from reference standard.",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="'success' or 'failed'.",
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    sensor: Mapped["Sensor"] = relationship("Sensor", back_populates="calibrations")
    operator: Mapped["User"] = relationship(
        "User", foreign_keys=[operator_id], lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Calibration id={self.id} sensor_id={self.sensor_id} status={self.status!r}>"
