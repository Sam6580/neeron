# app/services/settings_service.py

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.models.model_health_metric import ModelHealthMetric
from app.models.sensor import Sensor
from app.models.system_health_snapshot import SystemHealthSnapshot
from app.models.threshold_config import ThresholdConfig
from app.repositories.base import BaseRepository
from app.repositories.sensor_repository import SensorRepository
from app.repositories.threshold_config_repository import ThresholdConfigRepository
from app.services.base import BaseService


class SettingsService(BaseService):
    """
    Service managing operations control configurations, alert threshold logic,
    and system calibration telemetry.
    """

    def __init__(
        self,
        sensor_repo: SensorRepository,
        threshold_repo: ThresholdConfigRepository,
        model_health_repo: BaseRepository[ModelHealthMetric],
        system_health_repo: BaseRepository[SystemHealthSnapshot],
    ):
        self.sensor_repo = sensor_repo
        self.threshold_repo = threshold_repo
        self.model_health_repo = model_health_repo
        self.system_health_repo = system_health_repo

    async def get_sensor_status(self, farm_id: UUID) -> List[Dict[str, Any]]:
        """
        Lists sensors with MAC addresses, measurement types, operational status, and calibration deadlines.
        """
        sensors = await self.sensor_repo.get_sensors_by_farm(farm_id)
        return [
            {
                "sensor_id": s.id,
                "hardware_id": s.hardware_id,
                "type": s.type,
                "status": s.status,
                "calibration_due_at": s.calibration_due_at,
                "tank_id": s.tank_id,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }
            for s in sensors
        ]

    async def get_thresholds(self, farm_id: UUID) -> List[ThresholdConfig]:
        """
        Retrieves all water quality threshold configurations defined for the farm.
        """
        return await self.threshold_repo.get_multi(filters={"farm_id": farm_id})

    async def update_thresholds(
        self,
        farm_id: UUID,
        metric_name: str,
        warning_min: float,
        warning_max: float,
        critical_min: float,
        critical_max: float,
        user_id: UUID,
    ) -> ThresholdConfig:
        """
        Updates warning/critical threshold parameters for a specific metric on a farm.
        Enforces structural bands validation.
        """
        # Validate ordering constraints critical_min <= warning_min <= warning_max <= critical_max
        if not (critical_min <= warning_min <= warning_max <= critical_max):
            raise ValueError(
                "Ordering constraint violated: critical_min <= warning_min <= warning_max <= critical_max"
            )

        existing = await self.threshold_repo.get_multi(
            filters={"farm_id": farm_id, "metric_name": metric_name}
        )
        
        now = datetime.now(timezone.utc)
        if existing:
            config = existing[0]
            config.warning_min = warning_min
            config.warning_max = warning_max
            config.critical_min = critical_min
            config.critical_max = critical_max
            config.updated_by = user_id
            config.updated_at = now
            return await self.threshold_repo.update(config, config)
        else:
            new_config = ThresholdConfig(
                id=uuid4(),
                farm_id=farm_id,
                metric_name=metric_name,
                warning_min=warning_min,
                warning_max=warning_max,
                critical_min=critical_min,
                critical_max=critical_max,
                updated_by=user_id,
                updated_at=now,
            )
            return await self.threshold_repo.create(new_config)

    async def get_model_health(self) -> List[Dict[str, Any]]:
        """
        Lists deployed AI model health metrics from performance evaluation snapshots.
        """
        metrics = await self.model_health_repo.get_multi(limit=100)
        return [
            {
                "id": m.id,
                "recorded_at": m.recorded_at,
                "model_version_id": m.model_version_id,
                "accuracy": float(m.accuracy) if m.accuracy is not None else None,
                "precision": float(m.precision) if m.precision is not None else None,
                "recall": float(m.recall) if m.recall is not None else None,
                "f1_score": float(m.f1_score) if m.f1_score is not None else None,
                "data_quality_score": float(m.data_quality_score) if m.data_quality_score is not None else None,
                "agreement_score": float(m.agreement_score) if m.agreement_score is not None else None,
            }
            for m in metrics
        ]

    async def get_system_health(self) -> Optional[SystemHealthSnapshot]:
        """
        Retrieves the latest global infrastructure status snapshot.
        """
        snapshots = await self.system_health_repo.get_multi(limit=50)
        if not snapshots:
            return None
        
        # Sort in memory by recorded_at descending to return the latest
        snapshots.sort(key=lambda s: s.recorded_at, reverse=True)
        return snapshots[0]
