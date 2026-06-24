from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MlFeatureStore(Base):
    """
    ML feature store — pre-computed features ready for model inference
    and retraining pipelines.

    Each row stores ONE feature value for a specific tank at a specific
    observation time (``feature_timestamp``).  Grouping is handled by
    ``feature_group`` and ``source_table`` for pipeline routing.

    Feature groups:
        'telemetry'     — raw sensor-derived features (temp, DO, pH…)
        'biological'    — production metrics (biomass, FCR, mortality rate…)
        'environmental' — aggregated environmental snapshots
        'engineered'    — computed features (rolling means, lag features,
                          interaction terms, embedding vectors…)

    ``feature_timestamp`` records when the underlying observation was
    made (not when the feature was computed), enabling point-in-time
    correct retraining without data leakage.

    TimescaleDB hypertable — partition column: ``feature_timestamp``.
    Composite PK: (id, feature_timestamp).

    Alembic note:
        After table creation run:
            SELECT create_hypertable('ml_feature_store', 'feature_timestamp',
                chunk_time_interval => INTERVAL '7 days');
    """

    __tablename__ = "ml_feature_store"
    __table_args__ = (
        # Primary retraining query: all features for a tank in a time window
        Index("ix_ml_feature_store_tank_ts",    "tank_id", "feature_timestamp"),
        # Training pipeline query: all features of a group in a time window
        Index("ix_ml_feature_store_group_ts",   "feature_group", "feature_timestamp"),
        # Lineage query: all features derived from a specific source table
        Index("ix_ml_feature_store_source",     "source_table", "feature_timestamp"),
        CheckConstraint(
            "feature_group IN ('telemetry','biological','environmental','engineered')",
            name="ck_ml_feature_group_valid",
        ),
        {
            "comment": (
                "TimescaleDB hypertable — pre-computed ML features for inference and retraining. "
                "Partition: feature_timestamp / 7-day chunks."
            )
        },
    )

    # ── Composite PK (UUID + time for TimescaleDB) ────────────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID — stable row identifier.",
    )
    feature_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment=(
            "Observation timestamp of the underlying data — NOT the compute time. "
            "Ensures point-in-time correct retraining (TimescaleDB partition key)."
        ),
    )

    # ── Scope ─────────────────────────────────────────────────────────────────
    tank_id: Mapped[UUID] = mapped_column(
        ForeignKey("tanks.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → tanks.id — the tank this feature was computed for.",
    )

    # ── Feature identity ──────────────────────────────────────────────────────
    feature_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment=(
            "Machine-readable feature name "
            "(e.g. 'temp_rolling_mean_1h', 'do_lag_15m', 'psi_ma_7d')."
        ),
    )
    feature_group: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="'telemetry' | 'biological' | 'environmental' | 'engineered'.",
    )
    source_table: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment=(
            "Source table name from which this feature was derived. "
            "e.g. 'tank_environment_snapshots' | 'tank_production_metrics' | 'telemetry'."
        ),
    )

    # ── Feature value (dual representation) ───────────────────────────────────
    feature_value: Mapped[Optional[float]] = mapped_column(
        Numeric(18, 6),
        nullable=True,
        comment="Scalar feature value. NULL for vector/embedding features (use feature_vector).",
    )
    feature_vector: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment=(
            "JSON array or object for multi-dimensional features "
            "(e.g. embedding vectors, frequency-domain features)."
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<MlFeatureStore id={self.id} tank_id={self.tank_id} "
            f"feature_name={self.feature_name!r} "
            f"feature_group={self.feature_group!r} "
            f"feature_timestamp={self.feature_timestamp}>"
        )
