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

    async def process_raw_telemetry(self, tank_id, data: Dict[str, Any]) -> List[Telemetry]:
        """
        Ingest a raw MQTT telemetry payload for a tank.

        Maps each numeric value in ``data`` to a matching active sensor on the
        tank (by sensor ``type``) and persists one :class:`Telemetry` row per match.
        Returns the list of created readings.
        """
        from uuid import UUID as _UUID
        from datetime import datetime as _dt, timezone as _tz

        if isinstance(tank_id, str):
            try:
                tank_id = _UUID(tank_id)
            except ValueError:
                return []

        sensors = await self.sensor_repo.get_active_sensors(tank_id)
        if not sensors:
            return []

        # Aliases mapping payload keys -> substrings expected in sensor.type
        key_aliases = {
            "temperature": ["temp"],
            "temp": ["temp"],
            "ph": ["ph"],
            "dissolved_oxygen": ["oxygen", "do"],
            "do": ["oxygen", "do"],
            "oxygen": ["oxygen"],
            "salinity": ["salinity"],
            "ammonia": ["ammonia"],
            "turbidity": ["turbidity"],
        }

        now = _dt.now(_tz.utc)
        created: List[Telemetry] = []
        for key, value in data.items():
            if not isinstance(value, (int, float)):
                continue
            wanted = key_aliases.get(str(key).lower(), [str(key).lower()])
            for sensor in sensors:
                stype = (sensor.type or "").lower()
                if any(w in stype for w in wanted):
                    reading = Telemetry(
                        sensor_id=sensor.id,
                        time=now,
                        value=float(value),
                        raw_payload=data,
                    )
                    created.append(await self.telemetry_repo.create(reading))
                    break
        return created

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

    async def get_acoustic_activity(self, tank_id: UUID) -> Dict[str, Any]:
        """Retrieves the current acoustic decibels, sync percent, and status classification."""
        reading = await self.telemetry_repo.get_latest_hydrophone_reading(tank_id)
        if not reading:
            return {
                "current_db": -42.0,
                "bio_acoustic_sync": 98.0,
                "status": "Normal"
            }
        
        # Determine status classification based on simple non-ML threshold rules
        sync = float(reading.bio_acoustic_sync) if reading.bio_acoustic_sync is not None else 98.0
        status_str = "Normal"
        if sync < 70.0:
            status_str = "Critical"
        elif sync < 85.0:
            status_str = "Warning"
            
        return {
            "current_db": float(reading.acoustic_db) if reading.acoustic_db is not None else -42.0,
            "bio_acoustic_sync": sync,
            "status": status_str
        }

    async def get_acoustic_trends(
        self, tank_id: UUID, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """Retrieves summary analytics for acoustic trends."""
        return await self.telemetry_repo.get_acoustic_trend_summary(tank_id, start_time, end_time)

    async def get_acoustic_trend_summary(
        self, tank_id: UUID, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """Alias method to retrieve trend summaries."""
        return await self.telemetry_repo.get_acoustic_trend_summary(tank_id, start_time, end_time)

    async def get_behavior_baseline(self, tank_id: UUID) -> Dict[str, Any]:
        """Retrieves the baseline acoustic benchmarks for a tank."""
        return await self.telemetry_repo.get_behavior_baseline(tank_id)

    async def get_behavior_anomalies(
        self, tank_id: UUID, start_time: datetime, end_time: datetime
    ) -> List[Any]:
        """
        Placeholder for behavioral anomalies.
        
        Current implementation:
        return []
        
        Reason:
        Reserved for future Acoustic Intelligence Engine. No anomaly detection ML
        is implemented in Phase 10.1.
        """
        return await self.telemetry_repo.get_behavior_anomalies(tank_id, start_time, end_time)

    async def get_acoustic_analytics_data(
        self, tank_id: UUID, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """Compiles time series telemetry lists and summary statistics for Analytics Dashboard charts."""
        series = await self.telemetry_repo.get_acoustic_analytics_series(tank_id, start_time, end_time)
        trends = await self.telemetry_repo.get_acoustic_trend_summary(tank_id, start_time, end_time)
        
        # Derive a simple non-ML stability index from standard deviation
        std_dev = trends.get("db_std", 0.0)
        stability_score = max(0.0, min(100.0, 100.0 - (std_dev * 5.0)))
        
        return {
            "series": series,
            "summary": {
                "average_db": trends.get("db_average", -42.0),
                "min_db": trends.get("db_min", -45.0),
                "max_db": trends.get("db_max", -40.0),
                "stability_score": round(stability_score, 2)
            }
        }
