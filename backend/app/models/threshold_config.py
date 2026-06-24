from __future__ import annotations

from uuid import UUID
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDMixin


class ThresholdConfig(Base, UUIDMixin):
    """
    Per-farm water quality threshold configuration.

    Directly powers the Settings & Operations Control page
    "Global Threshold Configuration" section.

    Each row defines the full warning/critical band for one water quality
    metric on one farm.  When a ``tank_environment_snapshot`` value falls
    outside these bands, the alert engine generates an Alert with the
    corresponding severity.

    Logical ordering invariant (enforced by CHECK constraint):
        critical_min ≤ warning_min ≤ warning_max ≤ critical_max

    Supported metrics:
        'temperature' | 'pH' | 'dissolved_oxygen' | 'ammonia' | 'salinity'

    ``updated_by`` : FK → users.id — tracks who last modified this config
                     for the Settings page audit trail.
    """

    __tablename__ = "threshold_configs"
    __table_args__ = (
        UniqueConstraint("farm_id", "metric_name", name="uq_threshold_farm_metric"),
        Index("ix_threshold_configs_farm",   "farm_id"),
        Index("ix_threshold_configs_metric", "metric_name"),
        CheckConstraint(
            "metric_name IN ("
            "'temperature','pH','dissolved_oxygen','ammonia','salinity')",
            name="ck_threshold_metric_name_valid",
        ),
        # Logical ordering: critical_min ≤ warning_min ≤ warning_max ≤ critical_max
        CheckConstraint(
            "critical_min <= warning_min",
            name="ck_threshold_critical_min_lte_warning_min",
        ),
        CheckConstraint(
            "warning_min <= warning_max",
            name="ck_threshold_warning_min_lte_warning_max",
        ),
        CheckConstraint(
            "warning_max <= critical_max",
            name="ck_threshold_warning_max_lte_critical_max",
        ),
        {
            "comment": (
                "Per-farm water quality threshold bands. "
                "Powers the Settings & Operations Control page. "
                "Alert engine reads these to classify sensor readings."
            )
        },
    )

    # ── FK ──────────────────────────────────────────────────────────────────
    farm_id: Mapped[UUID] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → farms.id — threshold applies to all tanks within this farm.",
    )

    # ── Metric ────────────────────────────────────────────────────────────────
    metric_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment=(
            "Water quality parameter: "
            "'temperature' | 'pH' | 'dissolved_oxygen' | 'ammonia' | 'salinity'."
        ),
    )

    # ── Warning band (operator caution zone) ─────────────────────────────────
    warning_min: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        comment=(
            "Lower warning threshold. "
            "Values below this trigger a 'Warning' severity alert."
        ),
    )
    warning_max: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        comment=(
            "Upper warning threshold. "
            "Values above this trigger a 'Warning' severity alert."
        ),
    )

    # ── Critical band (immediate action required) ─────────────────────────────
    critical_min: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        comment=(
            "Lower critical threshold. "
            "Values below this trigger a 'Critical' severity alert."
        ),
    )
    critical_max: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        comment=(
            "Upper critical threshold. "
            "Values above this trigger a 'Critical' severity alert."
        ),
    )

    # ── Audit trail ───────────────────────────────────────────────────────────
    updated_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="FK → users.id — last operator who modified this threshold config.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Auto-updated timestamp — shown in Settings page audit column.",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    farm: Mapped["Farm"] = relationship("Farm", lazy="selectin")
    updated_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[updated_by],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<ThresholdConfig id={self.id} farm_id={self.farm_id} "
            f"metric={self.metric_name!r} "
            f"warning=[{self.warning_min},{self.warning_max}] "
            f"critical=[{self.critical_min},{self.critical_max}]>"
        )
