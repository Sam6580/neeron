# app/api/v1/insights.py

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends

from app.api.v1.deps import get_ai_insight_service
from app.services.ai_insight_service import AiInsightService
from app.schemas.base import BaseResponse
from app.schemas.insight import AiInsightResponse

router = APIRouter()


@router.get("/dashboard", response_model=BaseResponse[List[AiInsightResponse]])
async def get_dashboard_insights(
    farm_id: UUID,
    service: AiInsightService = Depends(get_ai_insight_service),
):
    """
    Computes and returns a list of transient AI insights tailored for the dashboard.
    """
    insights = await service.generate_dashboard_insights(farm_id)
    return BaseResponse(
        data=[
            AiInsightResponse(
                id=i.id,
                tankId=i.tank_id,
                priority=i.priority,
                confidence=float(i.confidence),
                title=i.title,
                description=i.description,
                generatedAt=i.generated_at,
                expiresAt=i.expires_at,
            )
            for i in insights
        ]
    )


@router.get("/tanks/{tank_id}", response_model=BaseResponse[List[AiInsightResponse]])
async def get_tank_insights(
    tank_id: UUID,
    service: AiInsightService = Depends(get_ai_insight_service),
):
    """
    Computes and returns a list of transient AI insights for a specific tank.
    """
    insights = await service.generate_tank_insights(tank_id)
    return BaseResponse(
        data=[
            AiInsightResponse(
                id=i.id,
                tankId=i.tank_id,
                priority=i.priority,
                confidence=float(i.confidence),
                title=i.title,
                description=i.description,
                generatedAt=i.generated_at,
                expiresAt=i.expires_at,
            )
            for i in insights
        ]
    )
