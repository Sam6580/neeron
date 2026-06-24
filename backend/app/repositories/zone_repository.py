from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.zone import Zone
from app.repositories.base import BaseRepository


class ZoneRepository(BaseRepository[Zone]):
    """Repository class for Zone operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Zone, session)

    async def get_by_farm(self, farm_id: UUID) -> List[Zone]:
        """Retrieve all zones associated with a farm."""
        query = select(self.model).where(self.model.farm_id == farm_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
