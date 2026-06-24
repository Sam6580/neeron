from typing import Optional
from uuid import UUID
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.psi_prediction import PsiPrediction
from app.models.disease_prediction import DiseasePrediction
from app.models.mortality_prediction import MortalityPrediction
from app.models.harvest_prediction import HarvestPrediction
from app.repositories.base import BaseRepository


class PredictionRepository(BaseRepository[PsiPrediction]):
    """
    Repository class encapsulating getter operations for the different NEERON prediction models.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(PsiPrediction, session)

    async def get_latest_psi(self, tank_id: UUID) -> Optional[PsiPrediction]:
        """Fetch the latest Physiological Stress Index (PSI) prediction."""
        query = (
            select(PsiPrediction)
            .where(PsiPrediction.tank_id == tank_id)
            .order_by(desc(PsiPrediction.generated_at))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_latest_disease_prediction(self, tank_id: UUID) -> Optional[DiseasePrediction]:
        """Fetch the latest disease risk probability forecast."""
        query = (
            select(DiseasePrediction)
            .where(DiseasePrediction.tank_id == tank_id)
            .order_by(desc(DiseasePrediction.time))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_latest_mortality_prediction(self, tank_id: UUID) -> Optional[MortalityPrediction]:
        """Fetch the latest stocking mortality forecast."""
        query = (
            select(MortalityPrediction)
            .where(MortalityPrediction.tank_id == tank_id)
            .order_by(desc(MortalityPrediction.time))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_latest_harvest_prediction(self, tank_id: UUID) -> Optional[HarvestPrediction]:
        """Fetch the latest optimal harvest window projection."""
        query = (
            select(HarvestPrediction)
            .where(HarvestPrediction.tank_id == tank_id)
            .order_by(desc(HarvestPrediction.time))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
