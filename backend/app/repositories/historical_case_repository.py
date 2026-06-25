from sqlalchemy.ext.asyncio import AsyncSession
from app.models.historical_case import HistoricalCase
from app.repositories.base import BaseRepository


class HistoricalCaseRepository(BaseRepository[HistoricalCase]):
    """Repository class for HistoricalCase operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(HistoricalCase, session)
