# app/api/v1/recommendations.py

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import get_recommendation_service
from app.services.recommendation_service import RecommendationService
from app.schemas.base import BaseResponse
from app.schemas.recommendation import RecommendationResponse, RecommendationActionResponse
from app.api.v1.dependencies.auth import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.get("", response_model=BaseResponse[List[RecommendationResponse]])
async def list_recommendations(
    tank_id: Optional[UUID] = None,
    farm_id: Optional[UUID] = None,
    status_filter: Optional[str] = "pending",
    service: RecommendationService = Depends(get_recommendation_service),
):
    """
    Retrieves all recommendations, optionally filtered by tank_id, farm_id, or status.
    """
    if status_filter == "pending":
        recs = await service.get_active_recommendations(farm_id=farm_id, tank_id=tank_id)
    else:
        filters = {}
        if tank_id:
            filters["tank_id"] = tank_id
        if status_filter:
            # Capitalize to match model constraint Pending/Accepted/Dismissed/Completed
            filters["status"] = status_filter.capitalize()
        recs = await service.rec_repo.get_multi(filters=filters)

    return BaseResponse(
        data=[
            RecommendationResponse(
                id=r.id,
                tankId=r.tank_id,
                action=r.action,
                confidence=float(r.confidence),
                priority=r.priority,
                expectedOutcome=r.expected_outcome,
                status=r.status.lower(),
                generatedAt=r.time,
            )
            for r in recs
        ]
    )


@router.post("/{id}/accept", response_model=BaseResponse[RecommendationActionResponse])
async def accept_recommendation(
    id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: RecommendationService = Depends(get_recommendation_service),
):
    """
    Registers operator acceptance of a specific AI recommendation.
    """
    recs = await service.rec_repo.get_multi(filters={"id": id}, limit=1)
    if not recs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation not found with ID {id}",
        )
    rec = recs[0]

    # Use authenticated user ID for audit trail logging
    user_id = current_user.id
    action_log = await service.execute_recommendation(
        recommendation_id=rec.id,
        recommendation_time=rec.time,
        user_id=user_id,
        notes="Accepted via API v1 endpoint",
    )

    return BaseResponse(
        data=RecommendationActionResponse(
            id=action_log.id,
            executed_at=action_log.executed_at,
            recommendation_id=action_log.recommendation_id,
            user_id=action_log.user_id,
            action=action_log.action,
        )
    )


@router.post("/{id}/dismiss", response_model=BaseResponse[RecommendationActionResponse])
async def dismiss_recommendation(
    id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: RecommendationService = Depends(get_recommendation_service),
):
    """
    Registers operator dismissal of a specific AI recommendation.
    """
    recs = await service.rec_repo.get_multi(filters={"id": id}, limit=1)
    if not recs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation not found with ID {id}",
        )
    rec = recs[0]

    # Use authenticated user ID for audit trail logging
    user_id = current_user.id
    action_log = await service.dismiss_recommendation(
        recommendation_id=rec.id,
        recommendation_time=rec.time,
        user_id=user_id,
        notes="Dismissed via API v1 endpoint",
    )

    return BaseResponse(
        data=RecommendationActionResponse(
            id=action_log.id,
            executed_at=action_log.executed_at,
            recommendation_id=action_log.recommendation_id,
            user_id=action_log.user_id,
            action=action_log.action,
        )
    )
