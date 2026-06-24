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


class DataQualityCheck(Base):
    """
    Automated data quality validation result for a sensor reading.

    Runs on each ingested telemetry batch to detect anomalies, stuck
    sensors, range violations, and drift.  Results power:

      - Data Quality Dashboard (anomaly scores, pass/fail rates).
      - Sensor health degradation alerts.
      - ML feature store gating (only 'Pass' data enters training pipelines).

    Validation types:
        'Range Check'       — value within configured min/max bounds.
        'Stuck Sensor Check'— variance over a rolling window is near zero.
        'Drift Scan'        — running drift index compared to baseline.
        'Spike Filter'      — z-score outlier detection on recent window.

    Results:
        'Pass'    — data accepted into the feature store.
        'Fail'    — data rejected; alert may be triggered.
        'Suspect' — data accepted with a quality warning flag.

    TimescaleDB hypertable — partition column: ``time``.
    Composite PK: (id, time).

    Alembic note:
        After table creation run:
            SELECT create_hypertable('data_quality_checks', 'time',
                chunk_time_interval => INTERVAL '7 days');
    """

    __tablename__ = "data_quality_checks"
    __table_args__ = (
        Index("ix_data_quality_checks_sensor_time", "sensor_id", "time"),
        Index("ix_data_quality_checks_result",      "result",    "time"),
        CheckConstraint(
            "validation_type IN ("
            "'Range Check','Stuck Sensor Check','Drift Scan','Spike Filter')",
            name="ck_dqc_validation_type_valid",
        ),
        CheckConstraint(
            "result IN ('Pass','Fail','Suspect')",
            name="ck_dqc_result_valid",
        ),
        CheckConstraint(
            "anomaly_score BETWEEN 0 AND 1",
            name="ck_dqc_anomaly_score_range",
        ),
        {
            "comment": (
                "TimescaleDB hypertable — automated sensor data quality checks. "
                "Partition: time / 7-day chunks. "
                "Powers the Data Quality Dashboard and ML feature store gating."
            )
        },
    )

    # ── Composite PK (UUID + time for TimescaleDB) ────────────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID — stable row identifier.",
    )
    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="Validation execution timestamp (TimescaleDB partition key).",
    )

    # ── FK ──────────────────────────────────────────────────────────────────
    sensor_id: Mapped[UUID] = mapped_column(
        ForeignKey("sensors.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → sensors.id — which sensor's data was validated.",
    )

    # ── Validation payload ────────────────────────────────────────────────────
    validation_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="'Range Check' | 'Stuck Sensor Check' | 'Drift Scan' | 'Spike Filter'.",
    )
    result: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="'Pass' | 'Fail' | 'Suspect'.",
    )
    anomaly_score: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        comment=(
            "Anomaly severity score [0.0 = normal … 1.0 = extreme anomaly]. "
            "Computed by the validation algorithm (e.g. z-score normalised to 0-1)."
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DataQualityCheck id={self.id} sensor_id={self.sensor_id} "
            f"validation_type={self.validation_type!r} result={self.result!r} "
            f"anomaly_score={self.anomaly_score}>"
        )
