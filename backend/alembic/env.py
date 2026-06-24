import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Ensure the backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import declarative Base to register all SQLAlchemy models
from app.db.base import Base  # noqa: E402

# Import all models for Alembic autogenerate discovery
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

# Batch 7 — Snapshot & Actions (Phase 7 addition)
from app.models.farm_health_snapshot import FarmHealthSnapshot                         # noqa: F401, E402
from app.models.system_health_snapshot import SystemHealthSnapshot                     # noqa: F401, E402
from app.models.recommendation_action import RecommendationAction                       # noqa: F401, E402


DATABASE_URL = "postgresql+asyncpg://neeron_user:pwd@localhost:5432/neeron"


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By configuring the context with an Engine
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = os.getenv("DATABASE_URL", DATABASE_URL)
    config.set_main_option("sqlalchemy.url", url)
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    db_url = os.getenv("DATABASE_URL", DATABASE_URL)
    config.set_main_option("sqlalchemy.url", db_url)

    if db_url.startswith("sqlite://"):
        # Run synchronous migrations for SQLite testing / autogeneration
        from sqlalchemy import create_engine
        connectable = create_engine(db_url, poolclass=pool.NullPool)
        with connectable.connect() as connection:
            do_run_migrations(connection)
        connectable.dispose()
        return

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()



if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
