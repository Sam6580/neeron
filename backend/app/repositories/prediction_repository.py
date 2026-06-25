from typing import List, Optional
from uuid import UUID
from sqlalchemy import desc, select, func
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

    async def get_latest_psi_for_tanks(self, tank_ids: List[UUID]) -> List[PsiPrediction]:
        """Batch retrieve the latest PSI prediction for a list of tanks."""
        if not tank_ids:
            return []
        subq = (
            select(
                PsiPrediction,
                func.row_number().over(
                    partition_by=PsiPrediction.tank_id,
                    order_by=desc(PsiPrediction.generated_at)
                ).label("rn")
            )
            .where(PsiPrediction.tank_id.in_(tank_ids))
            .subquery()
        )
        from sqlalchemy.orm import aliased
        psi_alias = aliased(PsiPrediction, subq)
        query = select(psi_alias).where(subq.c.rn == 1)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_disease_predictions_for_tanks(
        self, tank_ids: List[UUID]
    ) -> List[DiseasePrediction]:
        """Batch retrieve the latest disease predictions for a list of tanks."""
        if not tank_ids:
            return []
        subq = (
            select(
                DiseasePrediction,
                func.row_number().over(
                    partition_by=DiseasePrediction.tank_id,
                    order_by=desc(DiseasePrediction.time)
                ).label("rn")
            )
            .where(DiseasePrediction.tank_id.in_(tank_ids))
            .subquery()
        )
        from sqlalchemy.orm import aliased
        disease_alias = aliased(DiseasePrediction, subq)
        query = select(disease_alias).where(subq.c.rn == 1)
        result = await self.session.execute(query)
        return list(result.scalars().all())
