from __future__ import annotations

from datetime import datetime
from uuid import UUID
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    """
    Platform user.  All access is gated by the associated Role.
    Two-factor authentication is supported via a TOTP secret.
    """

    __tablename__ = "users"

    # ── FK ──────────────────────────────────────────────────────────────────
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="FK → roles.id  (CASCADE restriction keeps orphan‑safety).",
    )

    # ── Identity ─────────────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique login email address.",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Bcrypt / Argon2 hashed password.",
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # ── Status ───────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="Soft-disable without deleting the record.",
    )

    # ── 2FA ──────────────────────────────────────────────────────────────────
    two_factor_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
    )
    two_factor_secret: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True,
        comment="Base-32 TOTP secret (stored encrypted at rest).",
    )

    # ── Refresh Token ────────────────────────────────────────────────────────
    refresh_token: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="Persisted refresh token for authentication hardening.",
    )
    refresh_token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Expiration timestamp of the stored refresh token.",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="selectin")

    farms: Mapped[list["Farm"]] = relationship(
        "Farm",
        secondary="user_farm_mappings",
        back_populates="users",
        lazy="selectin",
    )

    notification_preference: Mapped[Optional["NotificationPreference"]] = relationship(
        "NotificationPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        lazy="dynamic",
    )

    # ── Computed helpers ─────────────────────────────────────────────────────
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


# ─────────────────────────────────────────────────────────────────────────────
# Notification preferences  (1-to-1 owned by User)
# ─────────────────────────────────────────────────────────────────────────────
class NotificationPreference(Base):
    """Per-user notification channel & filter preferences."""

    __tablename__ = "notification_preferences"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        comment="FK → users.id  (1-to-1).",
    )
    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    critical_alerts_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="notification_preference")

    def __repr__(self) -> str:
        return f"<NotificationPreference user_id={self.user_id}>"


# ─────────────────────────────────────────────────────────────────────────────
# Audit log  (TimescaleDB hypertable; insert-only)
# ─────────────────────────────────────────────────────────────────────────────
class AuditLog(Base):
    """
    Immutable audit trail for all platform mutation events.
    TimescaleDB hypertable partitioned on `time`.
    Composite PK: (time, event_type) as required by TimescaleDB.
    """

    __tablename__ = "audit_logs"

    from datetime import datetime
    from sqlalchemy import DateTime, JSON

    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="Event timestamp (TimescaleDB partition key).",
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        comment="Categorised event (e.g. 'THRESHOLD_UPDATED').",
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="FK → users.id  (nullable for system events).",
    )
    action: Mapped[str] = mapped_column(Text, nullable=False)
    target_entity: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    target_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    old_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog time={self.time} event_type={self.event_type!r}>"
