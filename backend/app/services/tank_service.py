# app/services/tank_service.py

from typing import Any, Dict, List, Optional
from uuid import UUID

from app.models.tank_environment_snapshot import TankEnvironmentSnapshot
from app.repositories.tank_repository import TankRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.alert_repository import AlertRepository
from app.services.base import BaseService


class TankService(BaseService):
    """
    Service managing business logic for tanks, including environment tracking, health, and forecasts.
    """

    def __init__(
        self,
        tank_repo: TankRepository,
        telemetry_repo: TelemetryRepository,
        prediction_repo: PredictionRepository,
        alert_repo: AlertRepository,
    ):
        self.tank_repo = tank_repo
        self.telemetry_repo = telemetry_repo
        self.prediction_repo = prediction_repo
        self.alert_repo = alert_repo

    async def get_tank_dashboard(self, farm_id: UUID) -> List[Dict[str, Any]]:
        """
        Retrieves dashboard summary statistics for all tanks in a farm.
        """
        return await self.tank_repo.get_tank_dashboard(farm_id)

    async def get_tank_detail(self, tank_id: UUID) -> Dict[str, Any]:
        """
        Combines tank properties, latest telemetry snapshots, active alert count, and predictions.
        """
        tank = await self.tank_repo.get(tank_id)
        if not tank:
            raise ValueError(f"Tank not found with ID {tank_id}")

        environment = await self.get_tank_environment(tank_id)
        active_alerts = await self.alert_repo.get_active_alerts(tank_id=tank_id)
        predictions = await self.get_tank_predictions(tank_id)
        latest_telemetry = await self.tank_repo.get_latest_telemetry(tank_id)

        return {
            "id": tank.id,
            "name": tank.name,
            "type": tank.type,
            "volume_m3": float(tank.volume_m3),
            "max_biomass_kg": float(tank.max_biomass_kg),
            "species": tank.species,
            "zone_id": tank.zone_id,
            "created_at": tank.created_at,
            "updated_at": tank.updated_at,
            "latest_environment": environment,
            "active_alerts_count": len(active_alerts),
            "active_alerts": active_alerts,
            "predictions": predictions,
            "latest_telemetry": latest_telemetry,
        }

    async def get_tank_health(self, tank_id: UUID) -> Dict[str, Any]:
        """
        Retrieves environmental stability indicators and the latest PSI stress level.
        """
        return await self.tank_repo.get_tank_health(tank_id)

    async def get_tank_environment(self, tank_id: UUID) -> Optional[TankEnvironmentSnapshot]:
        """
        Fetches the latest environmental reading snapshot captured for the tank.
        """
        return await self.tank_repo.get_latest_environment_snapshot(tank_id)

    async def get_tank_predictions(self, tank_id: UUID) -> Dict[str, Any]:
        """
        Fetches combined predictions (PSI, disease risk, mortality, harvest).
        """
        psi = await self.prediction_repo.get_latest_psi(tank_id)
        disease = await self.prediction_repo.get_latest_disease_prediction(tank_id)
        mortality = await self.prediction_repo.get_latest_mortality_prediction(tank_id)
        harvest = await self.prediction_repo.get_latest_harvest_prediction(tank_id)

        return {
            "psi": {
                "id": psi.id if psi else None,
                "score": float(psi.psi_score) if psi else None,
                "level": psi.stress_level if psi else None,
                "generated_at": psi.generated_at if psi else None,
            } if psi else None,
            "disease": {
                "id": disease.id if disease else None,
                "pathogen": disease.pathogen if disease else None,
                "probability": float(disease.probability) if disease else None,
                "risk_level": disease.risk_level if disease else None,
                "time": disease.time if disease else None,
            } if disease else None,
            "mortality": {
                "id": mortality.id if mortality else None,
                "mortality_rate": float(mortality.mortality_rate) if mortality else None,
                "predicted_loss_kg": float(mortality.predicted_loss_kg) if mortality else None,
                "confidence": float(mortality.confidence) if mortality else None,
                "time": mortality.time if mortality else None,
            } if mortality else None,
            "harvest": {
                "id": harvest.id if harvest else None,
                "projected_harvest_date": harvest.projected_harvest_date if harvest else None,
                "projected_biomass": float(harvest.projected_biomass) if harvest else None,
                "avg_weight_g": float(harvest.avg_weight_g) if harvest else None,
                "fcr": float(harvest.fcr) if harvest else None,
                "revenue_projection_usd": float(harvest.revenue_projection_usd) if harvest and harvest.revenue_projection_usd is not None else None,
                "confidence": float(harvest.confidence) if harvest else None,
                "time": harvest.time if harvest else None,
            } if harvest else None,
        }

    async def list_tanks(
        self,
        zone_id: Optional[UUID] = None,
        type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Any]:
        """
        List all tanks with filters.
        """
        filters = {}
        if zone_id:
            filters["zone_id"] = zone_id
        if type:
            filters["type"] = type
        return await self.tank_repo.get_multi(skip=skip, limit=limit, filters=filters)
