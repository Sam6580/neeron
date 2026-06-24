# app/services/ai_insight_service.py

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.models.ai_insight import AiInsight
from app.repositories.base import BaseRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.tank_repository import TankRepository
from app.services.base import BaseService


class AiInsightService(BaseService):
    """
    Service formulating AI analytics narratives, explaining predictions, and mapping CBR linkages.
    """

    def __init__(
        self,
        insight_repo: BaseRepository[AiInsight],
        prediction_repo: PredictionRepository,
        tank_repo: TankRepository,
        recommendation_repo: RecommendationRepository,
    ):
        self.insight_repo = insight_repo
        self.prediction_repo = prediction_repo
        self.tank_repo = tank_repo
        self.recommendation_repo = recommendation_repo

    async def generate_dashboard_insights(self, farm_id: UUID) -> List[AiInsight]:
        """
        Computes/generates transient (non-persisted) dashboard insights based on farm tanks stress indexes.
        """
        tanks = await self.tank_repo.get_tank_dashboard(farm_id)
        insights = []
        now = datetime.now(timezone.utc)

        for tank_data in tanks:
            tank_id = tank_data["tank_id"]
            psi = await self.prediction_repo.get_latest_psi(tank_id)
            if psi and psi.psi_score is not None and float(psi.psi_score) > 2.2:
                # Heuristic mapping for transient insights
                level = psi.stress_level or "Elevated"
                insight = AiInsight(
                    id=uuid4(),
                    generated_at=now,
                    tank_id=tank_id,
                    source_model_id=psi.source_model_id if hasattr(psi, "source_model_id") else None,
                    title=f"Elevated stress in {tank_data['name']}",
                    description=(
                        f"Physiological Stress Index (PSI) is currently {float(psi.psi_score):.2f} "
                        f"({level}). This is driven by recent water quality fluctuations."
                    ),
                    priority="High" if float(psi.psi_score) > 3.0 else "Medium",
                    confidence=0.86,
                    expires_at=now + timedelta(days=1),
                )
                insights.append(insight)

        return insights

    async def create_dashboard_insights(self, insights_data: List[Dict[str, Any]]) -> List[AiInsight]:
        """
        Persists generated dashboard insights into the database.
        """
        created = []
        for data in insights_data:
            if isinstance(data, dict):
                obj = AiInsight(**data)
            else:
                obj = data
            res = await self.insight_repo.create(obj)
            created.append(res)
        return created

    async def generate_tank_insights(self, tank_id: UUID) -> List[AiInsight]:
        """
        Generates transient (non-persisted) insights for a single tank.
        """
        tank = await self.tank_repo.get(tank_id)
        if not tank:
            return []

        insights = []
        now = datetime.now(timezone.utc)

        psi = await self.prediction_repo.get_latest_psi(tank_id)
        if psi and psi.psi_score is not None:
            insight = AiInsight(
                id=uuid4(),
                generated_at=now,
                tank_id=tank_id,
                source_model_id=psi.source_model_id if hasattr(psi, "source_model_id") else None,
                title=f"Stress Analysis for {tank.name}",
                description=f"Model PSI is {float(psi.psi_score):.2f}. Stress classification is {psi.stress_level}.",
                priority="Critical" if psi.stress_level == "Critical" else ("High" if psi.stress_level == "High" else "Medium"),
                confidence=0.89,
                expires_at=now + timedelta(days=1),
            )
            insights.append(insight)

        disease = await self.prediction_repo.get_latest_disease_prediction(tank_id)
        if disease and disease.probability is not None and float(disease.probability) > 0.20:
            prob_pct = float(disease.probability) * 100.0
            insight = AiInsight(
                id=uuid4(),
                generated_at=now,
                tank_id=tank_id,
                source_model_id=disease.source_model_id if hasattr(disease, "source_model_id") else None,
                title=f"Pathogen Outbreak Risk: {disease.pathogen}",
                description=f"Early indicator flags a {prob_pct:.1f}% outbreak probability for {disease.pathogen}.",
                priority="High" if float(disease.probability) > 0.50 else "Medium",
                confidence=0.91,
                expires_at=now + timedelta(days=2),
            )
            insights.append(insight)

        return insights

    async def create_tank_insights(self, insights_data: List[Dict[str, Any]]) -> List[AiInsight]:
        """
        Persists generated tank insights into the database.
        """
        created = []
        for data in insights_data:
            if isinstance(data, dict):
                obj = AiInsight(**data)
            else:
                obj = data
            res = await self.insight_repo.create(obj)
            created.append(res)
        return created

    async def build_risk_explanation(self, tank_id: UUID) -> str:
        """
        Provides a detailed narrative explaining current disease and pathogen risks for a tank.
        """
        disease = await self.prediction_repo.get_latest_disease_prediction(tank_id)
        if not disease or disease.probability is None:
            return "No recent disease prediction model outputs are available for this tank."

        prob_pct = float(disease.probability) * 100.0
        return (
            f"The pathogen risk model has flagged a {prob_pct:.1f}% probability of a {disease.pathogen} "
            f"outbreak in this tank. This risk is categorized as {disease.risk_level} based on recent "
            f"turbidity variances and feed intake deviations, suggesting immediate inspection is warranted."
        )

    async def build_recommendation_explanation(self, recommendation_id: UUID, recommendation_time: datetime) -> str:
        """
        Explains the rationale and model outputs behind a generated recommendation.
        """
        rec = await self.recommendation_repo.get((recommendation_id, recommendation_time))
        if not rec:
            return "Recommendation details not found."

        conf_pct = float(rec.confidence) * 100.0
        return (
            f"The recommendation to '{rec.action}' was triggered by the NEERON recommendation engine "
            f"with a confidence score of {conf_pct:.1f}%. The model projects the expected outcome as: "
            f"'{rec.expected_outcome}'."
        )

    async def build_acoustic_insight(
        self,
        tank_id: UUID,
        current_db: float,
        bio_acoustic_sync: float,
    ) -> str:
        """
        Generates a plain-language narrative for the hydrophone acoustic activity card.

        Current implementation:
        Returns a static descriptive narrative using provided metric values.

        Reason:
        Acoustic ML classification (anomaly detection, behavioral embeddings, FFT)
        is reserved for a dedicated Acoustic Intelligence phase.
        This method is a Phase 10.1 infrastructure placeholder.

        Not Yet Implemented:
        - Anomaly scoring
        - Behavior classification
        - Historical trend comparison
        """
        sync_label = "Optimal"
        if bio_acoustic_sync < 70.0:
            sync_label = "Critical"
        elif bio_acoustic_sync < 85.0:
            sync_label = "Warning"

        return (
            f"Hydrophone acoustic telemetry reads {current_db:.1f} dB with a Bio-Acoustic Sync "
            f"confidence of {bio_acoustic_sync:.1f}% (status: {sync_label}). "
            f"Acoustic anomaly detection and behavioral classification are Not Yet Implemented "
            f"and are reserved for the Acoustic Intelligence phase."
        )
