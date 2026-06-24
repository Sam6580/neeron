# app/services/recommendation_service.py

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.models.recommendation import Recommendation
from app.models.recommendation_action import RecommendationAction
from app.repositories.recommendation_repository import RecommendationRepository
from app.services.base import BaseService


class RecommendationService(BaseService):
    """
    Service managing recommendation actions, operator feedback, and effectiveness metrics.
    """

    def __init__(self, rec_repo: RecommendationRepository):
        self.rec_repo = rec_repo

    async def get_active_recommendations(
        self, farm_id: Optional[UUID] = None, tank_id: Optional[UUID] = None
    ) -> List[Recommendation]:
        """
        Retrieves all pending recommendations, optionally filtered by farm or tank.
        """
        return await self.rec_repo.get_pending_recommendations(farm_id=farm_id, tank_id=tank_id)

    async def execute_recommendation(
        self,
        recommendation_id: UUID,
        recommendation_time: datetime,
        user_id: UUID,
        notes: Optional[str] = None,
    ) -> RecommendationAction:
        """
        Marks a recommendation as Accepted and records the action execution log.
        """
        return await self.rec_repo.record_user_action(
            recommendation_id=recommendation_id,
            recommendation_time=recommendation_time,
            user_id=user_id,
            action="Accepted",
            feedback_notes=notes,
        )

    async def dismiss_recommendation(
        self,
        recommendation_id: UUID,
        recommendation_time: datetime,
        user_id: UUID,
        notes: Optional[str] = None,
    ) -> RecommendationAction:
        """
        Marks a recommendation as Dismissed (Rejected) and records the action execution log.
        """
        return await self.rec_repo.record_user_action(
            recommendation_id=recommendation_id,
            recommendation_time=recommendation_time,
            user_id=user_id,
            action="Rejected",
            feedback_notes=notes,
        )

    async def recommendation_effectiveness(
        self, model_version_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Retrieves statistics on recommendation acceptance rates and average operator feedback score.
        """
        return await self.rec_repo.get_recommendation_performance(model_version_id=model_version_id)
