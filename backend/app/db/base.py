from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy database models."""
    pass


# ── Model imports (Alembic autogenerate discovery) ────────────────────────────
# Batch 1 — Core Business
from app.models.role import Role                        # noqa: F401, E402
from app.models.user import User, NotificationPreference, AuditLog  # noqa: F401, E402
from app.models.farm import Farm, UserFarmMapping       # noqa: F401, E402
from app.models.zone import Zone                        # noqa: F401, E402
from app.models.tank import Tank, QuarantineEvent, Inspection  # noqa: F401, E402

# Batch 2 — Sensor & Telemetry
from app.models.sensor import Sensor, Calibration                                       # noqa: F401, E402
from app.models.sensor_health import SensorHealth                                       # noqa: F401, E402
from app.models.telemetry import Telemetry                                              # noqa: F401, E402
from app.models.tank_environment_snapshot import TankEnvironmentSnapshot                # noqa: F401, E402
from app.models.tank_production_metric import TankProductionMetric                      # noqa: F401, E402

# Batch 3 — Alerts, Recommendations & Notifications
from app.models.alert import Alert                                                      # noqa: F401, E402
from app.models.recommendation import Recommendation                                    # noqa: F401, E402
from app.models.recommendation_feedback import RecommendationFeedback                   # noqa: F401, E402
from app.models.notification import Notification                                        # noqa: F401, E402

# Batch 4 — Predictions
from app.models.psi_prediction import PsiPrediction                                     # noqa: F401, E402
from app.models.psi_factor import PsiFactor                                             # noqa: F401, E402
from app.models.disease_prediction import DiseasePrediction                             # noqa: F401, E402
from app.models.mortality_prediction import MortalityPrediction                         # noqa: F401, E402
from app.models.harvest_prediction import HarvestPrediction                             # noqa: F401, E402

# Batch 5 — Case Reasoning & Biosecurity
from app.models.historical_case import HistoricalCase                                   # noqa: F401, E402
from app.models.case_match import CaseMatch                                             # noqa: F401, E402
from app.models.ai_insight import AiInsight                                             # noqa: F401, E402
from app.models.biosecurity_record import (                                             # noqa: F401, E402
    Pathogen, BiosecurityRecord, VaccinationRecord, ComplianceRecord
)

# Batch 6 — AI / ML Governance & Operations
from app.models.ai_model import AiModel                                                 # noqa: F401, E402
from app.models.model_version import ModelVersion                                       # noqa: F401, E402
from app.models.model_health_metric import ModelHealthMetric                            # noqa: F401, E402
from app.models.ml_feature_store import MlFeatureStore                                  # noqa: F401, E402
from app.models.data_quality_check import DataQualityCheck                              # noqa: F401, E402
from app.models.digital_twin_snapshot import DigitalTwinSnapshot                        # noqa: F401, E402
from app.models.threshold_config import ThresholdConfig                                 # noqa: F401, E402
