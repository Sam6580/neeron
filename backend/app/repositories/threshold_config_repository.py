from sqlalchemy.ext.asyncio import AsyncSession
from app.models.threshold_config import ThresholdConfig
from app.repositories.base import BaseRepository


class ThresholdConfigRepository(BaseRepository[ThresholdConfig]):
    """Repository class for ThresholdConfig operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(ThresholdConfig, session)
