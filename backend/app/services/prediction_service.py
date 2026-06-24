# app/services/prediction_service.py

from typing import Any, Dict
from uuid import UUID

from app.repositories.prediction_repository import PredictionRepository
from app.repositories.tank_repository import TankRepository
from app.services.base import BaseService


class PredictionService(BaseService):
    """
    Service managing AI forecasts, aggregating predictions, and determining risk profiles.
    """

    def __init__(
        self,
        prediction_repo: PredictionRepository,
        tank_repo: TankRepository,
    ):
        self.prediction_repo = prediction_repo
        self.tank_repo = tank_repo

    async def get_latest_predictions(self, tank_id: UUID) -> Dict[str, Any]:
        """
        Combines the latest forecasted indicators (PSI, disease, mortality, harvest) for a tank.
        """
        psi = await self.prediction_repo.get_latest_psi(tank_id)
        disease = await self.prediction_repo.get_latest_disease_prediction(tank_id)
        mortality = await self.prediction_repo.get_latest_mortality_prediction(tank_id)
        harvest = await self.prediction_repo.get_latest_harvest_prediction(tank_id)

        return {
            "psi": psi,
            "disease": disease,
            "mortality": mortality,
            "harvest": harvest,
        }

    async def aggregate_prediction_scores(self, farm_id: UUID) -> Dict[str, Any]:
        """
        Averages Physiological Stress Index (PSI) and pathogen risk probability across all farm tanks.
        """
        tanks = await self.tank_repo.get_tank_dashboard(farm_id)
        if not tanks:
            return {
                "average_psi": 0.0,
                "average_disease_probability": 0.0,
                "tank_count": 0,
            }

        psi_total = 0.0
        psi_count = 0
        disease_total = 0.0
        disease_count = 0

        for tank_data in tanks:
            tank_id = tank_data["tank_id"]
            psi = await self.prediction_repo.get_latest_psi(tank_id)
            if psi and psi.psi_score is not None:
                psi_total += float(psi.psi_score)
                psi_count += 1

            disease = await self.prediction_repo.get_latest_disease_prediction(tank_id)
            if disease and disease.probability is not None:
                disease_total += float(disease.probability)
                disease_count += 1

        avg_psi = (psi_total / psi_count) if psi_count > 0 else 0.0
        avg_disease = (disease_total / disease_count) if disease_count > 0 else 0.0

        return {
            "average_psi": round(avg_psi, 4),
            "average_disease_probability": round(avg_disease, 4),
            "tank_count": len(tanks),
        }

    async def calculate_overall_risk_level(self, tank_id: UUID) -> str:
        """
        Evaluates predictions to determine a single safety risk level:
        'Low' | 'Medium' | 'High' | 'Critical'.
        """
        psi = await self.prediction_repo.get_latest_psi(tank_id)
        disease = await self.prediction_repo.get_latest_disease_prediction(tank_id)

        levels = []
        if psi and psi.stress_level:
            levels.append(psi.stress_level)
        if disease and disease.risk_level:
            levels.append(disease.risk_level)

        if not levels:
            return "Low"

        # Map string levels to priority order
        severity_map = {
            "Critical": 4,
            "High": 3,
            "Medium": 2,
            "Moderate": 2,
            "Low": 1,
            "Unknown": 1,
        }

        max_val = 1
        for lvl in levels:
            max_val = max(max_val, severity_map.get(lvl, 1))

        reverse_map = {4: "Critical", 3: "High", 2: "Medium", 1: "Low"}
        return reverse_map[max_val]
