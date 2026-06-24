# app/services/telemetry_service.py

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from uuid import UUID

from app.models.telemetry import Telemetry
from app.repositories.sensor_repository import SensorRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.services.base import BaseService


class TelemetryService(BaseService):
    """
    Service managing raw sensor readings, time-series metrics, and water quality analysis.
    """

    def __init__(
        self,
        telemetry_repo: TelemetryRepository,
        sensor_repo: SensorRepository,
    ):
        self.telemetry_repo = telemetry_repo
        self.sensor_repo = sensor_repo

    async def get_latest_metrics(self, tank_id: UUID) -> List[Telemetry]:
        """
        Fetches the latest reading for each active sensor attached to the tank.
        """
        sensors = await self.sensor_repo.get_active_sensors(tank_id)
        latest_readings = []
        for sensor in sensors:
            reading = await self.telemetry_repo.get_latest_reading(sensor.id)
            if reading:
                latest_readings.append(reading)
        return latest_readings

    async def get_time_series(
        self, sensor_id: UUID, start_time: datetime, end_time: datetime
    ) -> List[Telemetry]:
        """
        Retrieves historical telemetry readings for a specific sensor in a given timeframe.
        """
        return await self.telemetry_repo.get_time_range(sensor_id, start_time, end_time)

    async def get_environment_summary(
        self, tank_id: UUID, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """
        Returns average, min, and max parameters for water metrics in a tank over a given range.
        """
        return await self.telemetry_repo.get_water_quality_metrics(tank_id, start_time, end_time)

    async def calculate_water_quality_index(self, tank_id: UUID) -> float:
        """
        Calculates a composite water quality index score (0.0 to 100.0)
        based on DO, pH, ammonia, temperature, and salinity variances over the last 7 days.
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=7)

        sensors = await self.sensor_repo.get_active_sensors(tank_id)
        if not sensors:
            return 100.0

        score = 100.0
        for sensor in sensors:
            stats = await self.telemetry_repo.get_sensor_statistics(sensor.id, start_time, end_time)
            if "std_dev" in stats and stats["std_dev"] is not None:
                std_dev = stats["std_dev"]
                stype = sensor.type.lower() if sensor.type else ""
                
                # Apply penalty factors based on variance from typical standard deviation thresholds
                if "oxygen" in stype or "do" in stype:
                    penalty = std_dev * 10.0
                elif "ph" in stype:
                    penalty = std_dev * 30.0
                elif "temp" in stype or "temperature" in stype:
                    penalty = std_dev * 8.0
                elif "salinity" in stype:
                    penalty = std_dev * 5.0
                elif "ammonia" in stype:
                    penalty = std_dev * 500.0
                else:
                    penalty = std_dev * 2.0
                
                score -= penalty

        return float(max(0.0, min(100.0, score)))
