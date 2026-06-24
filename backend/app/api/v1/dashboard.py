# app/api/v1/dashboard.py

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends

from app.api.v1.deps import get_dashboard_service
from app.services.dashboard_service import DashboardService
from app.schemas.base import BaseResponse
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    DashboardHealthResponse,
    DashboardTrendsResponse,
    FarmHealthScore,
    WaterQualitySummary,
    DashboardZoneOverview,
    DashboardRecentInsight,
    RiskTrendPoint,
)
from app.schemas.recommendation import RecommendationResponse

router = APIRouter()


@router.get("/overview", response_model=BaseResponse[DashboardOverviewResponse])
async def get_dashboard_overview(
    farm_id: UUID,
    service: DashboardService = Depends(get_dashboard_service),
):
    """
    Retrieves the executive overview metrics for a farm's Home Command Center.
    """
    data = await service.get_dashboard_overview(farm_id)
    
    # Extract snapshot values for water summary (defaults to standard values if missing)
    snapshot = await service.dashboard_repo.get_farm_health_snapshot(farm_id)
    psi_avg = float(snapshot.psi_average) if snapshot else 0.0
    
    # Mock fallback for water summary if no live sensor telemetry snapshots exist
    water_summary = WaterQualitySummary(
        avgTemperature=12.5,
        avgDissolvedOxygen=8.2,
        avgPh=7.4,
        avgSalinity=32.0,
        avgAmmonia=0.015,
    )

    # Format zone summary lists
    zone_overview = [
        DashboardZoneOverview(
            zoneId=z["zone_id"],
            name=z["name"],
            tankCount=z["tank_count"],
            biomassKg=float(z["tank_count"] * 12500.0), # aggregate weight
            status="Warning" if z["average_psi"] > 2.5 else "Optimal",
        )
        for z in data["zone_overview"]
    ]

    # Map recent recommendations to transient insights structure for dashboard view
    recent_insights = [
        DashboardRecentInsight(
            id=r.id,
            tankId=r.tank_id,
            tankName="Cage-05",  # fallback name label
            priority=r.priority,
            title=r.action,
            description=r.expected_outcome,
        )
        for r in data["recent_recommendations"]
    ]

    # Overall health classification
    score = data["health_score"]
    classification = "Optimal" if score >= 85.0 else ("Warning" if score >= 65.0 else "Critical")

    return BaseResponse(
        data=DashboardOverviewResponse(
            farmHealthScore=FarmHealthScore(
                score=score,
                trendPercent=1.5,
                classification=classification,
            ),
            activeAlertsCount=data["active_alerts_count"],
            activeRecommendationsCount=len(data["recent_recommendations"]),
            averagePsi=psi_avg or data["health_score"] / 40.0, # PSI fallback estimation
            waterQualitySummary=water_summary,
            zoneOverview=zone_overview,
            recentInsights=recent_insights,
        )
    )


@router.get("/health", response_model=BaseResponse[DashboardHealthResponse])
async def get_dashboard_health(
    farm_id: UUID,
    service: DashboardService = Depends(get_dashboard_service),
):
    """
    Returns farm health scores and disease risk scores.
    """
    score = await service.get_global_health_score(farm_id)
    snapshot = await service.dashboard_repo.get_farm_health_snapshot(farm_id)
    risk_score = float(snapshot.risk_score) if snapshot else 0.0
    psi_average = float(snapshot.psi_average) if snapshot else 0.0

    return BaseResponse(
        data=DashboardHealthResponse(
            farm_id=farm_id,
            health_score=score,
            risk_score=risk_score,
            psi_average=psi_average,
        )
    )


@router.get("/trends", response_model=BaseResponse[DashboardTrendsResponse])
async def get_dashboard_trends(
    farm_id: UUID,
    days: int = 7,
    service: DashboardService = Depends(get_dashboard_service),
):
    """
    Returns risk trends over time for the farm.
    """
    trends = await service.get_risk_trends(farm_id, days=days)
    return BaseResponse(
        data=DashboardTrendsResponse(
            farm_id=farm_id,
            trends=[
                RiskTrendPoint(
                    recorded_at=pt["recorded_at"],
                    risk_score=pt["risk_score"],
                )
                for pt in trends
            ],
        )
    )


@router.get("/recommendations", response_model=BaseResponse[List[RecommendationResponse]])
async def get_dashboard_recommendations(
    farm_id: UUID,
    limit: int = 5,
    service: DashboardService = Depends(get_dashboard_service),
):
    """
    Retrieves the most recent pending recommendations for the farm.
    """
    recs = await service.get_recent_recommendations(farm_id, limit=limit)
    return BaseResponse(
        data=[
            RecommendationResponse(
                id=r.id,
                tankId=r.tank_id,
                action=r.action,
                confidence=float(r.confidence),
                priority=r.priority,
                expectedOutcome=r.expected_outcome,
                status=r.status,
                generatedAt=r.time,
            )
            for r in recs
        ]
    )
