from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ai_insight import AiInsight
from app.repositories.base import BaseRepository


class AiInsightRepository(BaseRepository[AiInsight]):
    """Repository class for AiInsight operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(AiInsight, session)
