from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation import Recommendation
from app.models.recommendation_action import RecommendationAction
from app.models.recommendation_feedback import RecommendationFeedback
from app.models.tank import Tank
from app.models.zone import Zone
from app.repositories.base import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    """Repository class for Recommendation and feedback loop operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Recommendation, session)

    async def get_pending_recommendations(
        self, farm_id: Optional[UUID] = None, tank_id: Optional[UUID] = None
    ) -> List[Recommendation]:
        """Retrieve all recommendations with a status of 'Pending'."""
        query = select(self.model).where(self.model.status == "Pending")
        
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

    async def record_user_action(
        self,
        recommendation_id: UUID,
        recommendation_time: datetime,
        user_id: UUID,
        action: str,
        feedback_notes: Optional[str] = None,
    ) -> RecommendationAction:
        """
        Record user UI actions (Accepted, Rejected, Ignored) on a recommendation.
        Updates parent recommendation resolution details and adds a recommendation_actions log.
        """
        # Fetch parent recommendation
        recommendation = await self.get((recommendation_id, recommendation_time))
        if not recommendation:
            raise ValueError("Recommendation not found")

        now = datetime.now(timezone.utc)
        
        # Update parent recommendation
        recommendation.status = "Accepted" if action == "Accepted" else "Dismissed"
        recommendation.resolved_by = user_id
        recommendation.resolved_at = now
        recommendation.resolution_notes = feedback_notes
        self.session.add(recommendation)

        # Create recommendation action event log
        rec_action = RecommendationAction(
            id=uuid4(),
            executed_at=now,
            recommendation_id=recommendation_id,
            recommendation_time=recommendation_time,
            user_id=user_id,
            action=action,
        )
        self.session.add(rec_action)
        await self.session.flush()
        return rec_action

    async def get_recommendation_performance(
        self, model_version_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Calculates recommendation success rates and average effectiveness scores.
        """
        # Total generated count
        total_query = select(func.count(self.model.id))
        if model_version_id:
            total_query = total_query.where(self.model.generated_by_model == model_version_id)
        total_result = await self.session.execute(total_query)
        total_count = total_result.scalar() or 0

        # Accepted count
        accepted_query = select(func.count(self.model.id)).where(self.model.status == "Accepted")
        if model_version_id:
            accepted_query = accepted_query.where(self.model.generated_by_model == model_version_id)
        accepted_result = await self.session.execute(accepted_query)
        accepted_count = accepted_result.scalar() or 0

        # Average feedback effectiveness score
        avg_score_query = select(func.avg(RecommendationFeedback.effectiveness_score)).join(
            self.model,
            and_(
                RecommendationFeedback.recommendation_id == self.model.id,
                RecommendationFeedback.recommendation_time == self.model.time,
            )
        )
        if model_version_id:
            avg_score_query = avg_score_query.where(self.model.generated_by_model == model_version_id)
        avg_score_result = await self.session.execute(avg_score_query)
        avg_score = avg_score_result.scalar()

        acceptance_rate = (accepted_count / total_count * 100.0) if total_count > 0 else 0.0

        return {
            "model_version_id": model_version_id,
            "total_recommendations": total_count,
            "accepted_recommendations": accepted_count,
            "acceptance_rate_pct": round(acceptance_rate, 2),
            "average_effectiveness_score": round(float(avg_score), 2) if avg_score is not None else None,
        }
