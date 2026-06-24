# app/services/alert_service.py

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.models.alert import Alert
from app.repositories.alert_repository import AlertRepository
from app.services.base import BaseService


class AlertService(BaseService):
    """
    Service managing alert lifecycle operations including active alerts and acknowledgments.
    """

    def __init__(self, alert_repo: AlertRepository):
        self.alert_repo = alert_repo

    async def get_active_alerts(
        self, farm_id: Optional[UUID] = None, tank_id: Optional[UUID] = None
    ) -> List[Alert]:
        """
        Retrieves active alerts, optionally filtered by farm or tank.
        """
        return await self.alert_repo.get_active_alerts(farm_id=farm_id, tank_id=tank_id)

    async def acknowledge_alert(
        self, alert_id: UUID, alert_time: datetime, user_id: UUID
    ) -> Optional[Alert]:
        """
        Acknowledges an active alert.
        """
        return await self.alert_repo.acknowledge_alert(
            alert_id=alert_id, alert_time=alert_time, user_id=user_id
        )

    async def get_alert_history(
        self, tank_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Alert]:
        """
        Retrieves historical logs of alerts for a specific tank with pagination.
        """
        return await self.alert_repo.get_alert_history(tank_id=tank_id, skip=skip, limit=limit)
