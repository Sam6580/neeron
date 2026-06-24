from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDMixin, TimestampMixin


# ─────────────────────────────────────────────────────────────────────────────
# Pathogen  (relational reference table)
# ─────────────────────────────────────────────────────────────────────────────
class Pathogen(Base, UUIDMixin, TimestampMixin):
    """
    Reference catalog of pathogens monitored across all farms.

    Maintained by aquaculture biosecurity experts.
    Referenced by BiosecurityRecord to tie detections to known threats.
    """

    __tablename__ = "pathogens"
    __table_args__ = (
        {"comment": "Reference catalog of monitored aquaculture pathogens."},
    )

    scientific_name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        comment="Full scientific / taxonomic name (e.g. 'Lepeophtheirus salmonis').",
    )
    common_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Common name used in the UI (e.g. 'Sea Lice').",
    )
    risk_threshold_count: Mapped[float] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        comment="Detection count above which a Warning alert is triggered.",
    )

    biosecurity_records: Mapped[list["BiosecurityRecord"]] = relationship(
        "BiosecurityRecord",
        back_populates="pathogen",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Pathogen id={self.id} common_name={self.common_name!r}>"


# ─────────────────────────────────────────────────────────────────────────────
# BiosecurityRecord  (TimescaleDB hypertable)
# ─────────────────────────────────────────────────────────────────────────────
class BiosecurityRecord(Base):
    """
    Pathogen detection and biosecurity event record for a tank.

    Captures individual detection events from qPCR tests, visual counts,
    or microscopy examinations.  Drives the Biosecurity & Health page
    risk matrix, quarantine workflows, and compliance audit trails.

    ``risk_level`` : assessed level at time of detection.
    ``status``     : current resolution state of this biosecurity event.
    ``treatment``  : prescribed or applied treatment protocol.

    TimescaleDB hypertable — partition column: ``time``.
    Composite PK: (id, time).

    Alembic note:
        After table creation run:
            SELECT create_hypertable('biosecurity_records', 'time',
                chunk_time_interval => INTERVAL '14 days');
    """

    __tablename__ = "biosecurity_records"
    __table_args__ = (
        Index("ix_biosecurity_records_tank_time",     "tank_id", "time"),
        Index("ix_biosecurity_records_pathogen",      "pathogen_id", "time"),
        Index("ix_biosecurity_records_risk_status",   "risk_level", "status"),
        CheckConstraint(
            "detection_method IN ('qPCR Test','Visual Count','Microscopy','eDNA Analysis')",
            name="ck_biosecurity_detection_method_valid",
        ),
        CheckConstraint(
            "risk_level IN ('Safe','Warning','Critical')",
            name="ck_biosecurity_risk_level_valid",
        ),
        CheckConstraint(
            "status IN ('Active','Under Treatment','Resolved','Monitoring')",
            name="ck_biosecurity_status_valid",
        ),
        CheckConstraint(
            "value >= 0",
            name="ck_biosecurity_value_non_negative",
        ),
        {
            "comment": (
                "TimescaleDB hypertable — pathogen detection and biosecurity events per tank. "
                "Partition: time / 14-day chunks."
            )
        },
    )

    # ── Composite PK (UUID + time for TimescaleDB) ────────────────────────────
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Surrogate UUID — stable reference for quarantine and compliance records.",
    )
    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="Detection timestamp (TimescaleDB partition key).",
    )

    # ── FKs ──────────────────────────────────────────────────────────────────
    tank_id: Mapped[UUID] = mapped_column(
        ForeignKey("tanks.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → tanks.id",
    )
    pathogen_id: Mapped[UUID] = mapped_column(
        ForeignKey("pathogens.id", ondelete="RESTRICT"),
        nullable=False,
        comment="FK → pathogens.id  (RESTRICT: retain detection records even if pathogen is updated).",
    )
    inspection_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("inspections.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK → inspections.id — the manual inspection that triggered this record (if any).",
    )

    # ── Detection details ─────────────────────────────────────────────────────
    detection_method: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="'qPCR Test' | 'Visual Count' | 'Microscopy' | 'eDNA Analysis'.",
    )
    value: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        comment="Quantified detection value (e.g. lice count per fish, Ct value, copies/µL).",
    )
    inspection_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Calendar date of the physical inspection or sample collection.",
    )

    # ── Risk classification ───────────────────────────────────────────────────
    risk_level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="'Safe' | 'Warning' | 'Critical'.",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Active",
        comment="'Active' | 'Under Treatment' | 'Resolved' | 'Monitoring'.",
    )

    # ── Treatment ─────────────────────────────────────────────────────────────
    treatment: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment=(
            "Prescribed or applied treatment protocol "
            "(e.g. 'Hydrogen Peroxide Bath', 'Emamectin Benzoate Feed Treatment')."
        ),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    pathogen: Mapped["Pathogen"] = relationship(
        "Pathogen",
        back_populates="biosecurity_records",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<BiosecurityRecord id={self.id} tank_id={self.tank_id} "
            f"pathogen_id={self.pathogen_id} risk_level={self.risk_level!r} "
            f"status={self.status!r}>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# VaccinationRecord  (relational — per tank / batch)
# ─────────────────────────────────────────────────────────────────────────────
class VaccinationRecord(Base, UUIDMixin):
    """
    Records vaccination events applied to a tank's fish population.

    Supports biosecurity compliance workflows and veterinary audit trails.
    """

    __tablename__ = "vaccination_records"
    __table_args__ = (
        Index("ix_vaccination_records_tank", "tank_id"),
        CheckConstraint(
            "route IN ('Intraperitoneal','Immersion','Oral')",
            name="ck_vaccination_route_valid",
        ),
        {"comment": "Vaccination events per tank — biosecurity compliance tracking."},
    )

    tank_id: Mapped[UUID] = mapped_column(
        ForeignKey("tanks.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → tanks.id",
    )
    vaccine_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Commercial or generic vaccine name.",
    )
    batch_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Manufacturer batch/lot number for traceability.",
    )
    administered_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="FK → users.id  (veterinarian or certified operator).",
    )
    administered_at: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date the vaccine was administered.",
    )
    route: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Administration route: 'Intraperitoneal' | 'Immersion' | 'Oral'.",
    )
    dose_per_fish_ml: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 4),
        nullable=True,
        comment="Dose per individual fish in millilitres (where applicable).",
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<VaccinationRecord id={self.id} tank_id={self.tank_id} "
            f"vaccine={self.vaccine_name!r}>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# ComplianceRecord  (relational — regulatory & audit)
# ─────────────────────────────────────────────────────────────────────────────
class ComplianceRecord(Base, UUIDMixin, TimestampMixin):
    """
    Regulatory compliance events for a farm or tank.

    Tracks regulatory inspections, certification renewals, chemical
    usage approvals, and licence submissions required by aquaculture
    regulatory bodies (e.g. Marine Scotland, Mattilsynet, SERNAPESCA).
    """

    __tablename__ = "compliance_records"
    __table_args__ = (
        Index("ix_compliance_records_farm",         "farm_id"),
        Index("ix_compliance_records_type_status",  "compliance_type", "status"),
        CheckConstraint(
            "status IN ('Compliant','Pending Review','Non-Compliant','Expired')",
            name="ck_compliance_status_valid",
        ),
        CheckConstraint(
            "compliance_type IN ("
            "'Regulatory Inspection','Chemical Usage Approval',"
            "'Licence Renewal','Treatment Notification',"
            "'Environmental Impact Report','Other')",
            name="ck_compliance_type_valid",
        ),
        {"comment": "Regulatory compliance records per farm — audit trail for inspections and certifications."},
    )

    farm_id: Mapped[UUID] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → farms.id  (compliance is typically at farm level).",
    )
    tank_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("tanks.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK → tanks.id  (optional: if compliance event is tank-specific).",
    )
    compliance_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Category of compliance event.",
    )
    authority: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Regulatory authority or body (e.g. 'Marine Scotland', 'Mattilsynet').",
    )
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Official reference or case number from the regulatory body.",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Pending Review",
        comment="'Compliant' | 'Pending Review' | 'Non-Compliant' | 'Expired'.",
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Deadline for submission or renewal.",
    )
    resolved_at: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date compliance was confirmed by the authority.",
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Soft-archive flag to hide historical records from active views.",
    )

    def __repr__(self) -> str:
        return (
            f"<ComplianceRecord id={self.id} farm_id={self.farm_id} "
            f"type={self.compliance_type!r} status={self.status!r}>"
        )
