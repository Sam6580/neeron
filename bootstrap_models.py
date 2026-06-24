import os

# Create base models directory
models_dir = "backend/app/models"
os.makedirs(models_dir, exist_ok=True)

models = {}

# 1. role.py
models["role.py"] = """from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.db.mixins import UUIDMixin

class Role(Base, UUIDMixin):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    permissions: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    users: Mapped[list["User"]] = relationship("User", back_populates="role")
"""

# 2. user.py
models["user.py"] = """from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID
from typing import Optional
from app.db.base import Base
from app.db.mixins import UUIDMixin, TimestampMixin

class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    two_factor_secret: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    role: Mapped["Role"] = relationship("Role", back_populates="users")
    farms: Mapped[list["Farm"]] = relationship("Farm", secondary="user_farm_mappings", back_populates="users")
"""

# 3. farm.py
models["farm.py"] = """from sqlalchemy import String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID
from app.db.base import Base
from app.db.mixins import UUIDMixin, TimestampMixin

class Farm(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "farms"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    carrying_capacity_kg: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    zones: Mapped[list["Zone"]] = relationship("Zone", back_populates="farm", cascade="all, delete-orphan")
    users: Mapped[list["User"]] = relationship("User", secondary="user_farm_mappings", back_populates="farms")

class UserFarmMapping(Base):
    __tablename__ = "user_farm_mappings"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    farm_id: Mapped[UUID] = mapped_column(ForeignKey("farms.id", ondelete="CASCADE"), primary_key=True)
"""

# 4. zone.py
models["zone.py"] = """from sqlalchemy import String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID
from typing import Optional
from app.db.base import Base
from app.db.mixins import UUIDMixin

class Zone(Base, UUIDMixin):
    __tablename__ = "zones"

    farm_id: Mapped[UUID] = mapped_column(ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    farm: Mapped["Farm"] = relationship("Farm", back_populates="zones")
    tanks: Mapped[list["Tank"]] = relationship("Tank", back_populates="zone", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("farm_id", "name", name="uq_zone_farm_name"),
    )
"""

# 5. tank.py
models["tank.py"] = """from sqlalchemy import String, Numeric, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID
from app.db.base import Base
from app.db.mixins import UUIDMixin, TimestampMixin

class Tank(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tanks"

    zone_id: Mapped[UUID] = mapped_column(ForeignKey("zones.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    volume_m3: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    max_biomass_kg: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    species: Mapped[str] = mapped_column(String(100), default="Atlantic Salmon", nullable=False)
    digital_twin_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    zone: Mapped["Zone"] = relationship("Zone", back_populates="tanks")
    sensors: Mapped[list["Sensor"]] = relationship("Sensor", back_populates="tank")

    __table_args__ = (
        UniqueConstraint("zone_id", "name", name="uq_tank_zone_name"),
    )
"""

# 6. sensor.py
models["sensor.py"] = """from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.db.base import Base
from app.db.mixins import UUIDMixin, TimestampMixin

class Sensor(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sensors"

    tank_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("tanks.id", ondelete="SET NULL"), nullable=True)
    hardware_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Active", nullable=False)
    calibration_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    tank: Mapped[Optional["Tank"]] = relationship("Tank", back_populates="sensors")
    sensor_health: Mapped[Optional["SensorHealth"]] = relationship("SensorHealth", back_populates="sensor", uselist=False, cascade="all, delete-orphan")
"""

# 7. sensor_health.py
models["sensor_health.py"] = """from sqlalchemy import String, Numeric, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.db.base import Base

class SensorHealth(Base):
    __tablename__ = "sensor_health"

    sensor_id: Mapped[UUID] = mapped_column(ForeignKey("sensors.id", ondelete="CASCADE"), primary_key=True)
    signal_strength: Mapped[str] = mapped_column(String(50), nullable=False)
    battery_level: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    drift_score: Mapped[float] = mapped_column(Numeric(5, 4), default=0.0000, nullable=False)
    health_status: Mapped[str] = mapped_column(String(50), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    sensor: Mapped["Sensor"] = relationship("Sensor", back_populates="sensor_health")
"""

# 8. telemetry.py
models["telemetry.py"] = """from sqlalchemy import Numeric, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.db.base import Base

class Telemetry(Base):
    __tablename__ = "telemetry"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    sensor_id: Mapped[UUID] = mapped_column(ForeignKey("sensors.id", ondelete="RESTRICT"), primary_key=True)
    value: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
"""

# 9. tank_environment_snapshot.py
models["tank_environment_snapshot.py"] = """from sqlalchemy import Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from app.db.base import Base

class TankEnvironmentSnapshot(Base):
    __tablename__ = "tank_environment_snapshots"

    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    tank_id: Mapped[UUID] = mapped_column(ForeignKey("tanks.id", ondelete="CASCADE"), primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    temperature: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    ph: Mapped[Optional[float]] = mapped_column(Numeric(4, 2), nullable=True)
    dissolved_oxygen: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    salinity: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    ammonia: Mapped[Optional[float]] = mapped_column(Numeric(6, 4), nullable=True)
    turbidity: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
"""

# 10. tank_production_metric.py
models["tank_production_metric.py"] = """from sqlalchemy import Numeric, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from datetime import datetime
from app.db.base import Base

class TankProductionMetric(Base):
    __tablename__ = "tank_production_metrics"

    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    tank_id: Mapped[UUID] = mapped_column(ForeignKey("tanks.id", ondelete="CASCADE"), primary_key=True)
    population: Mapped[int] = mapped_column(Integer, nullable=False)
    biomass_kg: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    average_weight_g: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    fcr: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    mortality_rate: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    feed_consumption_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
"""

# 11. alert.py
models["alert.py"] = """from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.db.base import Base

class Alert(Base):
    __tablename__ = "alerts"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    tank_id: Mapped[UUID] = mapped_column(ForeignKey("tanks.id", ondelete="CASCADE"), primary_key=True)
    sensor_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("sensors.id", ondelete="SET NULL"), nullable=True)
    type: Mapped[str] = mapped_column(String(100), primary_key=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
"""

# 12. recommendation.py
models["recommendation.py"] = """from sqlalchemy import String, Text, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from app.db.base import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tank_id: Mapped[UUID] = mapped_column(ForeignKey("tanks.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(150), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False)
    expected_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    resolved_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
"""

# 13. recommendation_feedback.py
models["recommendation_feedback.py"] = """from sqlalchemy import String, Text, ForeignKeyConstraint, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.db.base import Base

class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"

    recommendation_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    recommendation_id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    action_taken: Mapped[str] = mapped_column(String(100), nullable=False)
    effectiveness_score: Mapped[int] = mapped_column(nullable=False)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["recommendation_time", "recommendation_id"],
            ["recommendations.time", "recommendations.id"],
            ondelete="CASCADE"
        ),
    )
"""

# 14. psi_prediction.py
models["psi_prediction.py"] = """from sqlalchemy import String, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
from datetime import datetime
from app.db.base import Base

class PsiPrediction(Base):
    __tablename__ = "psi_predictions"

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tank_id: Mapped[UUID] = mapped_column(ForeignKey("tanks.id", ondelete="CASCADE"), nullable=False)
    psi_score: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    stress_level: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
"""

# 15. psi_factor.py
models["psi_factor.py"] = """from sqlalchemy import String, Numeric, ForeignKeyConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from datetime import datetime
from app.db.base import Base

class PsiFactor(Base):
    __tablename__ = "psi_factors"

    prediction_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    prediction_id: Mapped[UUID] = mapped_column(primary_key=True)
    factor_name: Mapped[str] = mapped_column(String(100), primary_key=True)
    contribution: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    importance_score: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["prediction_time", "prediction_id"],
            ["psi_predictions.generated_at", "psi_predictions.id"],
            ondelete="CASCADE"
        ),
    )
"""

# 16. disease_prediction.py
models["disease_prediction.py"] = """from sqlalchemy import Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
from datetime import datetime
from app.db.base import Base

class DiseasePrediction(Base):
    __tablename__ = "disease_predictions"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tank_id: Mapped[UUID] = mapped_column(ForeignKey("tanks.id", ondelete="CASCADE"), nullable=False)
    model_version_id: Mapped[UUID] = mapped_column(ForeignKey("model_versions.id", ondelete="RESTRICT"), nullable=False)
    pathogen_id: Mapped[UUID] = mapped_column(ForeignKey("pathogens.id", ondelete="RESTRICT"), nullable=False)
    probability: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    confidence_low: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    confidence_high: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
"""

# 17. mortality_prediction.py
models["mortality_prediction.py"] = """from sqlalchemy import Numeric, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
from datetime import datetime
from app.db.base import Base

class MortalityPrediction(Base):
    __tablename__ = "mortality_predictions"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tank_id: Mapped[UUID] = mapped_column(ForeignKey("tanks.id", ondelete="CASCADE"), nullable=False)
    model_version_id: Mapped[UUID] = mapped_column(ForeignKey("model_versions.id", ondelete="RESTRICT"), nullable=False)
    forecast_horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    mortality_rate_projected: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    confidence_low: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    confidence_high: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
"""

# 18. harvest_prediction.py
models["harvest_prediction.py"] = """from sqlalchemy import Numeric, ForeignKey, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
from datetime import datetime, date
from typing import Optional
from app.db.base import Base

class HarvestPrediction(Base):
    __tablename__ = "harvest_predictions"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tank_id: Mapped[UUID] = mapped_column(ForeignKey("tanks.id", ondelete="CASCADE"), nullable=False)
    model_version_id: Mapped[UUID] = mapped_column(ForeignKey("model_versions.id", ondelete="RESTRICT"), nullable=False)
    estimated_harvest_date: Mapped[date] = mapped_column(Date, nullable=False)
    projected_mean_weight_g: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    projected_biomass_kg: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    growth_rate_fcr: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    revenue_projection_usd: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
"""

# 19. historical_case.py
models["historical_case.py"] = """from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.db.base import Base
from app.db.mixins import UUIDMixin

class HistoricalCase(Base, UUIDMixin):
    __tablename__ = "historical_cases"

    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(100), nullable=False)
    outcome: Mapped[str] = mapped_column(Text, nullable=False)
    resolution: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
"""

# 20. case_match.py
models["case_match.py"] = """from sqlalchemy import Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from datetime import datetime
from app.db.base import Base

class CaseMatch(Base):
    __tablename__ = "case_matches"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    prediction_id: Mapped[UUID] = mapped_column(primary_key=True)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("historical_cases.id", ondelete="CASCADE"), primary_key=True)
    similarity_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
"""

# 21. ai_insight.py
models["ai_insight.py"] = """from sqlalchemy import String, Text, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from app.db.base import Base

class AiInsight(Base):
    __tablename__ = "ai_insights"

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tank_id: Mapped[UUID] = mapped_column(ForeignKey("tanks.id", ondelete="CASCADE"), nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
"""

# 22. threshold_config.py
models["threshold_config.py"] = """from sqlalchemy import String, Numeric, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.db.base import Base
from app.db.mixins import UUIDMixin

class ThresholdConfig(Base, UUIDMixin):
    __tablename__ = "threshold_configs"

    farm_id: Mapped[UUID] = mapped_column(ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    minimum_value: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    maximum_value: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    warning_min: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    warning_max: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    critical_min: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    critical_max: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    updated_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("farm_id", "metric_name", name="uq_threshold_farm_metric"),
    )
"""

# 23. biosecurity_record.py
models["biosecurity_record.py"] = """from sqlalchemy import String, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from datetime import datetime
from app.db.base import Base

class BiosecurityRecord(Base):
    __tablename__ = "biosecurity_records"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    tank_id: Mapped[UUID] = mapped_column(ForeignKey("tanks.id", ondelete="CASCADE"), primary_key=True)
    pathogen_id: Mapped[UUID] = mapped_column(ForeignKey("pathogens.id", ondelete="RESTRICT"), primary_key=True)
    detection_method: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False)
"""

# 24. digital_twin_snapshot.py
models["digital_twin_snapshot.py"] = """from sqlalchemy import String, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from datetime import datetime
from app.db.base import Base

class DigitalTwinSnapshot(Base):
    __tablename__ = "digital_twin_snapshots"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    tank_id: Mapped[UUID] = mapped_column(ForeignKey("tanks.id", ondelete="CASCADE"), primary_key=True)
    simulated_biomass: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    simulated_oxygen: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    simulated_growth: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    scenario_name: Mapped[str] = mapped_column(String(100), primary_key=True)
"""

# 25. ml_feature_store.py
models["ml_feature_store.py"] = """from sqlalchemy import ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from datetime import datetime
from app.db.base import Base

class MlFeatureStore(Base):
    __tablename__ = "ml_feature_store"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    tank_id: Mapped[UUID] = mapped_column(ForeignKey("tanks.id", ondelete="CASCADE"), primary_key=True)
    telemetry_features: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    biological_features: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    environmental_features: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    engineered_features: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
"""

# 26. data_quality_check.py
models["data_quality_check.py"] = """from sqlalchemy import String, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from datetime import datetime
from app.db.base import Base

class DataQualityCheck(Base):
    __tablename__ = "data_quality_checks"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    sensor_id: Mapped[UUID] = mapped_column(ForeignKey("sensors.id", ondelete="CASCADE"), primary_key=True)
    validation_type: Mapped[str] = mapped_column(String(100), primary_key=True)
    result: Mapped[str] = mapped_column(String(50), nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
"""

# 27. model_health_metric.py
models["model_health_metric.py"] = """from sqlalchemy import Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.db.base import Base

class ModelHealthMetric(Base):
    __tablename__ = "model_health_metrics"

    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    model_version_id: Mapped[UUID] = mapped_column(ForeignKey("model_versions.id", ondelete="CASCADE"), primary_key=True)
    accuracy: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    precision: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    recall: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    f1_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    data_quality_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    agreement_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
"""

# 28. notification.py
models["notification.py"] = """from sqlalchemy import ForeignKey, DateTime, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from datetime import datetime
from app.db.base import Base

class Notification(Base):
    __tablename__ = "notifications"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    alert_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    alert_tank_id: Mapped[UUID] = mapped_column(ForeignKey("tanks.id", ondelete="CASCADE"), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(100), primary_key=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
"""

# 29. ai_model.py
models["ai_model.py"] = """from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base import Base
from app.db.mixins import UUIDMixin

class AiModel(Base, UUIDMixin):
    __tablename__ = "ai_models"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    versions: Mapped[list["ModelVersion"]] = relationship("ModelVersion", back_populates="model", cascade="all, delete-orphan")
"""

# 30. model_version.py
models["model_version.py"] = """from sqlalchemy import String, ForeignKey, JSON, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.db.base import Base
from app.db.mixins import UUIDMixin

class ModelVersion(Base, UUIDMixin):
    __tablename__ = "model_versions"

    model_id: Mapped[UUID] = mapped_column(ForeignKey("ai_models.id", ondelete="CASCADE"), nullable=False)
    version_tag: Mapped[str] = mapped_column(String(50), nullable=False)
    hyperparameters: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Archived", nullable=False)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deployed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    model: Mapped["AiModel"] = relationship("AiModel", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("model_id", "version_tag", name="uq_model_version_tag"),
    )
"""

# __init__.py exports
exports_list = []
for filename in sorted(models.keys()):
    model_name = filename[:-3].replace('_', ' ').title().replace(' ', '')
    # Adjust edge cases for casing
    if model_name == "AiInsight":
        model_name = "AiInsight"
    elif model_name == "AiModel":
        model_name = "AiModel"
    elif model_name == "PsiFactor":
        model_name = "PsiFactor"
    elif model_name == "PsiPrediction":
        model_name = "PsiPrediction"
    elif model_name == "MlFeatureStore":
        model_name = "MlFeatureStore"
    
    exports_list.append(f"from app.models.{filename[:-3]} import {model_name}")

models["__init__.py"] = "\n".join(exports_list) + "\n"

# Write all models to files
for filename, content in models.items():
    filepath = os.path.join(models_dir, filename)
    with open(filepath, "w") as f:
        f.write(content)

print(f"Successfully bootstrapped {len(models)} model files in {models_dir}")
