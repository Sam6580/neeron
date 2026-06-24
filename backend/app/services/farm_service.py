# app/services/farm_service.py

from typing import Any, Dict, List, Optional
from uuid import UUID

from app.models.zone import Zone
from app.repositories.farm_repository import FarmRepository
from app.repositories.zone_repository import ZoneRepository
from app.repositories.tank_repository import TankRepository
from app.repositories.alert_repository import AlertRepository
from app.repositories.dashboard_repository import DashboardRepository
from app.services.base import BaseService


class FarmService(BaseService):
    """
    Service managing farm-level business logic, KPI aggregation, and structural status.
    """

    def __init__(
        self,
        farm_repo: FarmRepository,
        zone_repo: ZoneRepository,
        tank_repo: TankRepository,
        alert_repo: AlertRepository,
        dashboard_repo: DashboardRepository,
    ):
        self.farm_repo = farm_repo
        self.zone_repo = zone_repo
        self.tank_repo = tank_repo
        self.alert_repo = alert_repo
        self.dashboard_repo = dashboard_repo

    async def get_farm_overview(self, farm_id: UUID) -> Dict[str, Any]:
        """
        Retrieves a comprehensive farm status overview, including structural metrics,
        health scores, active alert summary, and zone breakdown.
        """
        farm = await self.farm_repo.get(farm_id)
        if not farm:
            raise ValueError(f"Farm not found with ID {farm_id}")

        health_score = await self.get_farm_health(farm_id)
        active_alerts_count = await self.dashboard_repo.get_active_alert_count(farm_id)
        zones = await self.get_farm_zones(farm_id)
        biomass = await self.get_farm_biomass(farm_id)
        kpis = await self.get_farm_kpis(farm_id)
        alert_summary = await self.get_farm_alert_summary(farm_id)

        return {
            "farm_id": farm.id,
            "name": farm.name,
            "latitude": float(farm.latitude),
            "longitude": float(farm.longitude),
            "timezone": farm.timezone,
            "health_score": health_score,
            "active_alerts_count": active_alerts_count,
            "total_zones": len(zones),
            "total_biomass_kg": biomass,
            "kpis": kpis,
            "alert_summary": alert_summary,
        }

    async def get_farm_health(self, farm_id: UUID) -> float:
        """
        Retrieve the latest aggregate health score for the farm.
        """
        return await self.dashboard_repo.get_global_health_score(farm_id)

    async def get_farm_zones(self, farm_id: UUID) -> List[Zone]:
        """
        Retrieve all zones under this farm.
        """
        return await self.zone_repo.get_by_farm(farm_id)

    async def get_farm_kpis(self, farm_id: UUID) -> Dict[str, Any]:
        """
        Calculates key performance indicators for the farm.
        Includes carrying capacity, stocking density, totals.
        """
        farm = await self.farm_repo.get(farm_id)
        if not farm:
            return {}

        zones = await self.get_farm_zones(farm_id)
        tanks = await self.tank_repo.get_tank_dashboard(farm_id)

        total_volume = sum(tank["volume_m3"] for tank in tanks)
        total_max_biomass = sum(tank["max_biomass_kg"] for tank in tanks)
        
        # Calculate estimate of current biomass (75% of max safe biomass if not dynamically tracked)
        current_biomass = total_max_biomass * 0.75
        stocking_density = (current_biomass / total_volume) if total_volume > 0.0 else 0.0

        return {
            "carrying_capacity_kg": float(farm.carrying_capacity_kg),
            "total_max_biomass_kg": total_max_biomass,
            "estimated_biomass_kg": current_biomass,
            "total_volume_m3": total_volume,
            "stocking_density_kg_m3": round(stocking_density, 2),
            "total_zones": len(zones),
            "total_tanks": len(tanks),
        }

    async def get_farm_biomass(self, farm_id: UUID) -> float:
        """
        Retrieves the aggregate estimated biomass (kg) for the farm.
        """
        tanks = await self.tank_repo.get_tank_dashboard(farm_id)
        # Dynamic biomass estimate of 75% of max stocking biomass
        return sum(tank["max_biomass_kg"] for tank in tanks) * 0.75

    async def get_farm_alert_summary(self, farm_id: UUID) -> Dict[str, Any]:
        """
        Summarizes farm active alerts grouped by severity level.
        """
        active_alerts = await self.alert_repo.get_active_alerts(farm_id=farm_id)
        
        summary = {"Info": 0, "Warning": 0, "Critical": 0}
        for alert in active_alerts:
            if alert.severity in summary:
                summary[alert.severity] += 1

        return {
            "total_active": len(active_alerts),
            "by_severity": summary,
        }

    async def list_farms(self, skip: int = 0, limit: int = 100) -> List[Any]:
        """
        List all farms with pagination.
        """
        return await self.farm_repo.get_multi(skip=skip, limit=limit)

    async def get_farm(self, farm_id: UUID) -> Optional[Any]:
        """
        Get farm details by ID.
        """
        return await self.farm_repo.get(farm_id)
