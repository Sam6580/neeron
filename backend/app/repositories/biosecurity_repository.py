from typing import List
from uuid import UUID
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.biosecurity_record import BiosecurityRecord, VaccinationRecord, ComplianceRecord
from app.repositories.base import BaseRepository


class BiosecurityRepository(BaseRepository[BiosecurityRecord]):
    """Repository class for Biosecurity and regulatory compliance operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(BiosecurityRecord, session)

    async def get_latest_pathogen_counts(self, tank_id: UUID) -> List[BiosecurityRecord]:
        """Retrieves the latest biosecurity/pathogen inspection records for a tank."""
        # Find all biosecurity records for the tank, ordered by time descending
        query = (
            select(self.model)
            .where(self.model.tank_id == tank_id)
            .order_by(desc(self.model.time))
        )
        result = await self.session.execute(query)
        records = result.scalars().all()
        
        # Filter for unique pathogens (keep only the latest)
        latest_pathogens = {}
        for rec in records:
            if rec.pathogen_id not in latest_pathogens:
                latest_pathogens[rec.pathogen_id] = rec
                
        return list(latest_pathogens.values())

    async def get_vaccination_history(self, tank_id: UUID) -> List[VaccinationRecord]:
        """Retrieves vaccination schedules and historical logs for a tank."""
        query = (
            select(VaccinationRecord)
            .where(VaccinationRecord.tank_id == tank_id)
            .order_by(desc(VaccinationRecord.administered_at))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_compliance_status(self, farm_id: UUID) -> List[ComplianceRecord]:
        """Retrieves all regulatory compliance certifications and reports for a farm."""
        query = (
            select(ComplianceRecord)
            .where(and_(
                ComplianceRecord.farm_id == farm_id,
                ComplianceRecord.is_archived == False
            ))
            .order_by(desc(ComplianceRecord.due_date))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
