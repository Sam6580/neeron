# app/models/ui.py
"""
Read-model storage for the web UI.

The frontend consumes rich, view-shaped DTOs (tanks with production + water
metrics, dashboard aggregates, analytics cards, etc.). Rather than computing
these from the normalized domain tables on every request, we persist each
view payload as JSON in a single generic table and serve it directly. This
keeps the UI endpoints simple, fast, and database-portable.
"""

from sqlalchemy import Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UiResource(Base):
    __tablename__ = "ui_resources"

    # e.g. "zones", "tanks", "alerts", "dashboard"
    collection: Mapped[str] = mapped_column(String(64), primary_key=True)
    # the item's stable id (or "main" for singletons like the dashboard)
    item_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    # ordering hint for list collections
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # the full view DTO, exactly as the frontend expects it
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UiResource {self.collection}/{self.item_id}>"
