# app/api/v1/deps.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories import (
    BaseRepository,
    FarmRepository,
    ZoneRepository,
    TankRepository,
    SensorRepository,
    TelemetryRepository,
    AlertRepository,
    RecommendationRepository,
    BiosecurityRepository,
    PredictionRepository,
    UserRepository,
    DashboardRepository,
    AuditLogRepository,
)
from app.models import (
    HistoricalCase,
    CaseMatch,
    QuarantineEvent,
    ThresholdConfig,
    ModelHealthMetric,
    SystemHealthSnapshot,
    AiInsight,
    AiModel,
    ModelVersion,
)
from app.services import (
    DashboardService,
    FarmService,
    TankService,
    TelemetryService,
    PredictionService,
    RecommendationService,
    RecommendationEngineService,
    BiosecurityService,
    SettingsService,
    AiInsightService,
    UserService,
    AlertService,
    AuthService,
)


async def get_dashboard_service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    return DashboardService(dashboard_repo=DashboardRepository(db))


async def get_farm_service(db: AsyncSession = Depends(get_db)) -> FarmService:
    return FarmService(
        farm_repo=FarmRepository(db),
        zone_repo=ZoneRepository(db),
        tank_repo=TankRepository(db),
        alert_repo=AlertRepository(db),
        dashboard_repo=DashboardRepository(db),
    )


async def get_tank_service(db: AsyncSession = Depends(get_db)) -> TankService:
    return TankService(
        tank_repo=TankRepository(db),
        telemetry_repo=TelemetryRepository(db),
        prediction_repo=PredictionRepository(db),
        alert_repo=AlertRepository(db),
    )


async def get_telemetry_service(db: AsyncSession = Depends(get_db)) -> TelemetryService:
    return TelemetryService(
        telemetry_repo=TelemetryRepository(db),
        sensor_repo=SensorRepository(db),
    )


async def get_prediction_service(db: AsyncSession = Depends(get_db)) -> PredictionService:
    return PredictionService(
        prediction_repo=PredictionRepository(db),
        tank_repo=TankRepository(db),
    )


async def get_recommendation_service(db: AsyncSession = Depends(get_db)) -> RecommendationService:
    return RecommendationService(rec_repo=RecommendationRepository(db))


async def get_recommendation_engine_service(
    db: AsyncSession = Depends(get_db),
) -> RecommendationEngineService:
    return RecommendationEngineService(
        rec_repo=RecommendationRepository(db),
        prediction_repo=PredictionRepository(db),
        case_repo=BaseRepository(HistoricalCase, db),
        case_match_repo=BaseRepository(CaseMatch, db),
        tank_repo=TankRepository(db),
    )


async def get_biosecurity_service(db: AsyncSession = Depends(get_db)) -> BiosecurityService:
    return BiosecurityService(
        biosecurity_repo=BiosecurityRepository(db),
        tank_repo=TankRepository(db),
        quarantine_repo=BaseRepository(QuarantineEvent, db),
    )


async def get_settings_service(db: AsyncSession = Depends(get_db)) -> SettingsService:
    return SettingsService(
        sensor_repo=SensorRepository(db),
        threshold_repo=BaseRepository(ThresholdConfig, db),
        model_health_repo=BaseRepository(ModelHealthMetric, db),
        system_health_repo=BaseRepository(SystemHealthSnapshot, db),
    )


async def get_ai_insight_service(db: AsyncSession = Depends(get_db)) -> AiInsightService:
    return AiInsightService(
        insight_repo=BaseRepository(AiInsight, db),
        prediction_repo=PredictionRepository(db),
        tank_repo=TankRepository(db),
        recommendation_repo=RecommendationRepository(db),
    )


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(
        user_repo=UserRepository(db),
        audit_log_repo=AuditLogRepository(db),
    )


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(
        user_repo=UserRepository(db),
        audit_log_repo=AuditLogRepository(db),
    )


async def get_alert_service(db: AsyncSession = Depends(get_db)) -> AlertService:
    return AlertService(alert_repo=AlertRepository(db))
