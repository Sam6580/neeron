from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Notification(Base):
    """
    Per-user notification derived from an alert event.

    Each Alert fan-outs into one Notification per subscribed user,
    respecting their NotificationPreference delivery channel settings.

    ``read_status``      : whether the user has seen this notification.
    ``delivery_channel`` : how the notification was delivered.
    ``priority``         : mirrors the source alert severity for quick filtering.

    TimescaleDB hypertable — partition column: ``time``.
    Composite PK: (id, time) provides a stable UUID reference while
    satisfying the TimescaleDB partition-key-in-PK requirement.

    Alembic note:
        After table creation run:
            SELECT create_hypertable('notifications', 'time',
                chunk_time_interval => INTERVAL '30 days');
    """

    __tablename__ = "notifications"
    __table_args__ = (
        # Primary access pattern: unread notifications for a user, newest first
        Index("ix_notifications_user_time",    "user_id", "time"),
        Index("ix_notifications_read_status",  "user_id", "is_read"),
        CheckConstraint(
            "delivery_channel IN ('in_app','email','sms','push')",
            name="ck_notification_channel_valid",
        ),
        CheckConstraint(
            "priority IN ('Info','Warning','Critical')",
            name="ck_notification_priority_valid",
        ),
        {
            "comment": (
                "TimescaleDB hypertable — per-user notification inbox. "
                "Partition: time / 30-day chunks."
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
        server_default=func.now(),
        comment="Notification delivery timestamp (TimescaleDB partition key).",
    )

    # ── FKs ──────────────────────────────────────────────────────────────────
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → users.id  (notification recipient).",
    )
    alert_id: Mapped[UUID] = mapped_column(
        nullable=False,
        comment=(
            "UUID of the source alert (alerts.id). "
            "Stored as plain UUID (not FK) because hypertable composite FKs "
            "require both partition columns — use app-layer join when needed."
        ),
    )
    alert_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="alerts.time of the source alert — retained for join queries.",
    )

    # ── Delivery metadata ─────────────────────────────────────────────────────
    delivery_channel: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="in_app",
        comment="Channel used: 'in_app' | 'email' | 'sms' | 'push'.",
    )
    priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Mirrors source alert severity: 'Info' | 'Warning' | 'Critical'.",
    )

    # ── Read state ────────────────────────────────────────────────────────────
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="True once the user has viewed this notification in the UI.",
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the notification was marked as read.",
    )

    def __repr__(self) -> str:
        return (
            f"<Notification id={self.id} user_id={self.user_id} "
            f"channel={self.delivery_channel!r} is_read={self.is_read}>"
        )
