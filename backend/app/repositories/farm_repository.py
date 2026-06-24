from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.farm import Farm
from app.repositories.base import BaseRepository


class FarmRepository(BaseRepository[Farm]):
    """Repository class for Farm operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Farm, session)

    async def get_by_name(self, name: str) -> Optional[Farm]:
        """Retrieve a farm by its unique name."""
        query = select(self.model).where(self.model.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
