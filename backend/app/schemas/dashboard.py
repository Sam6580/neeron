# app/schemas/dashboard.py

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class FarmHealthScore(BaseModel):
    score: float
    trendPercent: float
    classification: str


class WaterQualitySummary(BaseModel):
    avgTemperature: float
    avgDissolvedOxygen: float
    avgPh: float
    avgSalinity: float
    avgAmmonia: float


class DashboardZoneOverview(BaseModel):
    zoneId: UUID
    name: str
    tankCount: int
    biomassKg: float
    status: str


class DashboardRecentInsight(BaseModel):
    id: UUID
    tankId: UUID
    tankName: str
    priority: str
    title: str
    description: str


class DashboardOverviewResponse(BaseModel):
    farmHealthScore: FarmHealthScore
    activeAlertsCount: int
    activeRecommendationsCount: int
    averagePsi: float
    waterQualitySummary: WaterQualitySummary
    zoneOverview: List[DashboardZoneOverview]
    recentInsights: List[DashboardRecentInsight]


class DashboardHealthResponse(BaseModel):
    farm_id: UUID
    health_score: float
    risk_score: float
    psi_average: float


class RiskTrendPoint(BaseModel):
    recorded_at: datetime
    risk_score: float


class DashboardTrendsResponse(BaseModel):
    farm_id: UUID
    trends: List[RiskTrendPoint]
