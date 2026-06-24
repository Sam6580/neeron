from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.tank import Tank
from app.models.zone import Zone
from app.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    """Repository class for Alert operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Alert, session)

    async def get_active_alerts(
        self, farm_id: Optional[UUID] = None, tank_id: Optional[UUID] = None
    ) -> List[Alert]:
        """
        Retrieves all unresolved (Active) alerts.
        Supports filtering by farm_id or tank_id.
        """
        query = select(self.model).where(self.model.status == "Active")
        
        if tank_id:
            query = query.where(self.model.tank_id == tank_id)
        elif farm_id:
            query = (
                query.join(Tank, self.model.tank_id == Tank.id)
                .join(Zone, Tank.zone_id == Zone.id)
                .where(Zone.farm_id == farm_id)
            )
            
        query = query.order_by(desc(self.model.time))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def acknowledge_alert(
        self, alert_id: UUID, alert_time: datetime, user_id: UUID
    ) -> Optional[Alert]:
        """
        Acknowledge an alert using its composite key (id, time).
        Updates status, sets acknowledged_at, and flushes the session.
        """
        alert = await self.get((alert_id, alert_time))
        if not alert:
            return None

        alert.status = "Acknowledged"
        alert.acknowledged_at = datetime.now(timezone.utc)
        self.session.add(alert)
        await self.session.flush()
        return alert

    async def get_alert_history(
        self, tank_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Alert]:
        """Retrieve historical alerts for a tank with pagination."""
        query = (
            select(self.model)
            .where(self.model.tank_id == tank_id)
            .order_by(desc(self.model.time))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
