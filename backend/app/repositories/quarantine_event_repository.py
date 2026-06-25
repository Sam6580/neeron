from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tank import QuarantineEvent
from app.repositories.base import BaseRepository


class QuarantineEventRepository(BaseRepository[QuarantineEvent]):
    """Repository class for QuarantineEvent operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(QuarantineEvent, session)

    async def get_active_quarantine_events_for_tanks(
        self, tank_ids: List[UUID]
    ) -> List[QuarantineEvent]:
        """Batch retrieve active (uncleared) quarantine events for a list of tank IDs."""
        if not tank_ids:
            return []
        query = select(QuarantineEvent).where(
            QuarantineEvent.tank_id.in_(tank_ids),
            QuarantineEvent.cleared_at.is_(None)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_quarantine_event(
        self, tank_id: UUID
    ) -> Optional[QuarantineEvent]:
        """Retrieve the active (uncleared) quarantine event for a specific tank."""
        query = select(QuarantineEvent).where(
            QuarantineEvent.tank_id == tank_id,
            QuarantineEvent.cleared_at.is_(None)
        ).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_quarantine_events(
        self, tank_id: UUID
    ) -> List[QuarantineEvent]:
        """Retrieve all quarantine events for a specific tank (both active and historical)."""
        query = select(QuarantineEvent).where(QuarantineEvent.tank_id == tank_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
