# app/schemas/__init__.py
# Public re-exports for Pydantic validation schemas

from app.schemas.base import BaseResponse, PaginatedResponse, PaginationMeta
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    DashboardHealthResponse,
    DashboardTrendsResponse,
)
from app.schemas.farm import FarmResponse
from app.schemas.tank import (
    TankResponse,
    TankDetailResponse,
    TankHealthResponse,
    TankEnvironmentSnapshotResponse,
    TankPredictionsResponse,
)
from app.schemas.telemetry import (
    TelemetryLatestResponse,
    TelemetryHistoryResponse,
    TelemetryHistoryPoint,
    TelemetryMetrics,
)
from app.schemas.recommendation import (
    RecommendationResponse,
    RecommendationActionResponse,
)
from app.schemas.alert import AlertResponse
from app.schemas.settings import (
    SensorStatusResponse,
    ThresholdConfigResponse,
    ThresholdUpdatePayload,
)
from app.schemas.user import UserResponse, AuditLogResponse
from app.schemas.insight import AiInsightResponse
from app.schemas.model import (
    AiModelResponse,
    ModelVersionResponse,
    ModelHealthMetricResponse,
)
from app.schemas.health import HealthResponse

__all__ = [
    "BaseResponse",
    "PaginatedResponse",
    "PaginationMeta",
    "DashboardOverviewResponse",
    "DashboardHealthResponse",
    "DashboardTrendsResponse",
    "FarmResponse",
    "TankResponse",
    "TankDetailResponse",
    "TankHealthResponse",
    "TankEnvironmentSnapshotResponse",
    "TankPredictionsResponse",
    "TelemetryLatestResponse",
    "TelemetryHistoryResponse",
    "TelemetryHistoryPoint",
    "TelemetryMetrics",
    "RecommendationResponse",
    "RecommendationActionResponse",
    "AlertResponse",
    "SensorStatusResponse",
    "ThresholdConfigResponse",
    "ThresholdUpdatePayload",
    "UserResponse",
    "AuditLogResponse",
    "AiInsightResponse",
    "AiModelResponse",
    "ModelVersionResponse",
    "ModelHealthMetricResponse",
    "HealthResponse",
]
