from __future__ import annotations

from uuid import UUID
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SensorHealth(Base):
    """
    Real-time health snapshot for a sensor device.

    One-to-one with Sensor — primary key is the sensor_id FK itself,
    guaranteeing a single health record per device.

    Updated in-place on every heartbeat; no time-series history here
    (see ``data_quality_checks`` for historical drift tracking).
    """

    __tablename__ = "sensor_health"
    __table_args__ = (
        CheckConstraint(
            "signal_strength IN ('Strong','Medium','Weak','Offline')",
            name="ck_sensor_health_signal_valid",
        ),
        CheckConstraint(
            "health_status IN ('Optimal','Warning','Maintenance Required','Fault')",
            name="ck_sensor_health_status_valid",
        ),
        CheckConstraint(
            "battery_level BETWEEN 0 AND 100",
            name="ck_sensor_health_battery_range",
        ),
        CheckConstraint(
            "drift_score >= 0",
            name="ck_sensor_health_drift_non_negative",
        ),
        {"comment": "Live sensor health snapshot — 1-to-1 with sensors table."},
    )

    # ── PK / FK (same column — 1-to-1 pattern) ───────────────────────────────
    sensor_id: Mapped[UUID] = mapped_column(
        ForeignKey("sensors.id", ondelete="CASCADE"),
        primary_key=True,
        comment="FK → sensors.id  (also the sole PK — 1-to-1 relationship).",
    )

    # ── Connectivity ──────────────────────────────────────────────────────────
    signal_strength: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="RF/LoRa/Ethernet signal quality: 'Strong' | 'Medium' | 'Weak' | 'Offline'.",
    )
    battery_level: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Battery percentage (0–100). NULL for wired/PoE sensors.",
    )

    # ── Diagnostics ───────────────────────────────────────────────────────────
    drift_score: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=0.0,
        comment=(
            "Sensor drift index [0.0 = no drift). "
            "Triggers maintenance alert when > 0.05."
        ),
    )
    health_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Overall diagnosis: 'Optimal' | 'Warning' | 'Maintenance Required' | 'Fault'.",
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="UTC timestamp of the most recent heartbeat / telemetry packet.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Row-level update timestamp (auto-maintained).",
    )

    # ── Relationship ──────────────────────────────────────────────────────────
    sensor: Mapped["Sensor"] = relationship(
        "Sensor",
        back_populates="sensor_health",
    )

    def __repr__(self) -> str:
        return (
            f"<SensorHealth sensor_id={self.sensor_id} "
            f"status={self.health_status!r} drift={self.drift_score}>"
        )
