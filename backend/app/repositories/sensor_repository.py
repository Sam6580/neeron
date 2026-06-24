from typing import List, Optional
from uuid import UUID
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.sensor import Sensor
from app.repositories.base import BaseRepository


class SensorRepository(BaseRepository[Sensor]):
    """Repository class for Sensor operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Sensor, session)

    async def get_by_hardware_id(self, hardware_id: str) -> Optional[Sensor]:
        """Retrieve a sensor by its unique hardware ID (MAC address)."""
        query = select(self.model).where(self.model.hardware_id == hardware_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_sensors(self, tank_id: UUID) -> List[Sensor]:
        """Retrieve all active sensors currently assigned to a tank."""
        query = select(self.model).where(
            and_(
                self.model.tank_id == tank_id,
                self.model.status == "Active"
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_sensors_by_farm(self, farm_id: UUID) -> List[Sensor]:
        """Retrieve all sensors associated with any tank in a farm."""
        from app.models.tank import Tank
        from app.models.zone import Zone
        query = (
            select(self.model)
            .join(Tank, self.model.tank_id == Tank.id)
            .join(Zone, Tank.zone_id == Zone.id)
            .where(Zone.farm_id == farm_id)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
