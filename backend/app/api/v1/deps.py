# app/api/v1/deps.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.base import BaseRepository
from app.repositories.farm_repository import FarmRepository
from app.repositories.zone_repository import ZoneRepository
from app.repositories.tank_repository import TankRepository
from app.repositories.sensor_repository import SensorRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.repositories.alert_repository import AlertRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.biosecurity_repository import BiosecurityRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.user_repository import UserRepository
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.threshold_config_repository import ThresholdConfigRepository
from app.repositories.historical_case_repository import HistoricalCaseRepository
from app.repositories.ai_insight_repository import AiInsightRepository
from app.repositories.quarantine_event_repository import QuarantineEventRepository

from app.models.historical_case import HistoricalCase
from app.models.case_match import CaseMatch
from app.models.tank import QuarantineEvent
from app.models.threshold_config import ThresholdConfig
from app.models.model_health_metric import ModelHealthMetric
from app.models.system_health_snapshot import SystemHealthSnapshot
from app.models.ai_insight import AiInsight
from app.models.ai_model import AiModel
from app.models.model_version import ModelVersion

from app.services.dashboard_service import DashboardService
from app.services.farm_service import FarmService
from app.services.tank_service import TankService
from app.services.telemetry_service import TelemetryService
from app.services.prediction_service import PredictionService
from app.services.recommendation_service import RecommendationService
from app.services.recommendation_engine_service import RecommendationEngineService
from app.services.biosecurity_service import BiosecurityService
from app.services.settings_service import SettingsService
from app.services.ai_insight_service import AiInsightService
from app.services.user_service import UserService
from app.services.alert_service import AlertService
from app.services.auth_service import AuthService


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
        case_repo=HistoricalCaseRepository(db),
        case_match_repo=BaseRepository(CaseMatch, db),
        tank_repo=TankRepository(db),
    )


async def get_biosecurity_service(db: AsyncSession = Depends(get_db)) -> BiosecurityService:
    return BiosecurityService(
        biosecurity_repo=BiosecurityRepository(db),
        tank_repo=TankRepository(db),
        quarantine_repo=QuarantineEventRepository(db),
    )


async def get_settings_service(db: AsyncSession = Depends(get_db)) -> SettingsService:
    return SettingsService(
        sensor_repo=SensorRepository(db),
        threshold_repo=ThresholdConfigRepository(db),
        model_health_repo=BaseRepository(ModelHealthMetric, db),
        system_health_repo=BaseRepository(SystemHealthSnapshot, db),
    )


async def get_ai_insight_service(db: AsyncSession = Depends(get_db)) -> AiInsightService:
    return AiInsightService(
        insight_repo=AiInsightRepository(db),
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
