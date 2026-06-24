from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDMixin, TimestampMixin


class Role(Base, UUIDMixin, TimestampMixin):
    """
    Defines a named access-control role.

    Predefined role names:
        Administrator | Operations Manager | Aquaculture Analyst |
        Biologist | Viewer
    """

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Human-readable role label (e.g. 'Administrator').",
    )
    permissions: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="JSON map of permission keys to boolean grants.",
    )

    # ── Relationships ────────────────────────────────────────────────────────
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="role",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Role id={self.id} name={self.name!r}>"
