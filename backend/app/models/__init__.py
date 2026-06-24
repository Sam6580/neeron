# app/models/__init__.py
# Public re-exports — importers can use `from app.models import Tank` etc.

# Batch 1
from app.models.role import Role
from app.models.user import User, NotificationPreference, AuditLog
from app.models.farm import Farm, UserFarmMapping
from app.models.zone import Zone
from app.models.tank import Tank, QuarantineEvent, Inspection

# Batch 2
from app.models.sensor import Sensor, Calibration
from app.models.sensor_health import SensorHealth
from app.models.telemetry import Telemetry
from app.models.tank_environment_snapshot import TankEnvironmentSnapshot
from app.models.tank_production_metric import TankProductionMetric

# Batch 3
from app.models.alert import Alert
from app.models.recommendation import Recommendation
from app.models.recommendation_feedback import RecommendationFeedback
from app.models.notification import Notification

# Batch 4
from app.models.psi_prediction import PsiPrediction
from app.models.psi_factor import PsiFactor
from app.models.disease_prediction import DiseasePrediction
from app.models.mortality_prediction import MortalityPrediction
from app.models.harvest_prediction import HarvestPrediction

# Batch 5
from app.models.historical_case import HistoricalCase
from app.models.case_match import CaseMatch
from app.models.ai_insight import AiInsight
from app.models.biosecurity_record import (
    Pathogen, BiosecurityRecord, VaccinationRecord, ComplianceRecord
)

# Batch 6
from app.models.ai_model import AiModel
from app.models.model_version import ModelVersion
from app.models.model_health_metric import ModelHealthMetric
from app.models.ml_feature_store import MlFeatureStore
from app.models.data_quality_check import DataQualityCheck
from app.models.digital_twin_snapshot import DigitalTwinSnapshot
from app.models.threshold_config import ThresholdConfig

# Batch 7
from app.models.farm_health_snapshot import FarmHealthSnapshot
from app.models.system_health_snapshot import SystemHealthSnapshot
from app.models.recommendation_action import RecommendationAction

__all__ = [
    # Batch 1
    "Role",
    "User",
    "NotificationPreference",
    "AuditLog",
    "Farm",
    "UserFarmMapping",
    "Zone",
    "Tank",
    "QuarantineEvent",
    "Inspection",
    # Batch 2
    "Sensor",
    "Calibration",
    "SensorHealth",
    "Telemetry",
    "TankEnvironmentSnapshot",
    "TankProductionMetric",
    # Batch 3
    "Alert",
    "Recommendation",
    "RecommendationFeedback",
    "Notification",
    # Batch 4
    "PsiPrediction",
    "PsiFactor",
    "DiseasePrediction",
    "MortalityPrediction",
    "HarvestPrediction",
    # Batch 5
    "HistoricalCase",
    "CaseMatch",
    "AiInsight",
    "Pathogen",
    "BiosecurityRecord",
    "VaccinationRecord",
    "ComplianceRecord",
    # Batch 6
    "AiModel",
    "ModelVersion",
    "ModelHealthMetric",
    "MlFeatureStore",
    "DataQualityCheck",
    "DigitalTwinSnapshot",
    "ThresholdConfig",
    # Batch 7
    "FarmHealthSnapshot",
    "SystemHealthSnapshot",
    "RecommendationAction",
]

