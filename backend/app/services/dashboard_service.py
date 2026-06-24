# app/services/dashboard_service.py

from typing import Any, Dict, List
from uuid import UUID

from app.models.recommendation import Recommendation
from app.repositories.dashboard_repository import DashboardRepository
from app.services.base import BaseService


class DashboardService(BaseService):
    """
    Service class specialized in orchestrating farm and infrastructure level statistics for dashboard views.
    """

    def __init__(self, dashboard_repo: DashboardRepository):
        self.dashboard_repo = dashboard_repo

    async def get_dashboard_overview(self, farm_id: UUID) -> Dict[str, Any]:
        """
        Aggregates global health score, active alert count, and recent recommendations.
        """
        health_score = await self.get_global_health_score(farm_id)
        active_alerts_count = await self.dashboard_repo.get_active_alert_count(farm_id)
        recent_recs = await self.get_recent_recommendations(farm_id, limit=5)
        alert_summary = await self.get_active_alert_summary(farm_id)
        zone_summary = await self.get_zone_overview(farm_id)

        return {
            "farm_id": farm_id,
            "health_score": health_score,
            "active_alerts_count": active_alerts_count,
            "alert_summary": alert_summary,
            "zone_overview": zone_summary,
            "recent_recommendations": recent_recs,
        }

    async def get_global_health_score(self, farm_id: UUID) -> float:
        """
        Retrieve the latest aggregate health score for the farm.
        """
        return await self.dashboard_repo.get_global_health_score(farm_id)

    async def get_active_alert_summary(self, farm_id: UUID) -> Dict[str, Any]:
        """
        Breaks down alert severity counts (Info, Warning, Critical) for the farm.
        """
        counts = await self.dashboard_repo.get_active_alert_severity_summary(farm_id)
        return {
            "total": sum(counts.values()),
            "severities": counts,
        }

    async def get_risk_trends(self, farm_id: UUID, days: int = 7) -> List[Dict[str, Any]]:
        """
        Retrieve the risk score trend over a given timeframe.
        """
        return await self.dashboard_repo.get_risk_trend(farm_id, days=days)

    async def get_zone_overview(self, farm_id: UUID) -> List[Dict[str, Any]]:
        """
        Get the summary metrics per zone on this farm.
        """
        return await self.dashboard_repo.get_zone_summary(farm_id)

    async def get_recent_recommendations(self, farm_id: UUID, limit: int = 5) -> List[Recommendation]:
        """
        Fetch the most recent pending recommendations for a farm.
        """
        return await self.dashboard_repo.get_recent_recommendations(farm_id, limit=limit)
