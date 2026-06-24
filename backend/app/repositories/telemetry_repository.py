from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telemetry import Telemetry
from app.models.tank_environment_snapshot import TankEnvironmentSnapshot
from app.repositories.base import BaseRepository


class TelemetryRepository(BaseRepository[Telemetry]):
    """Repository class for Telemetry and sensor reading operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Telemetry, session)

    async def get_latest_reading(self, sensor_id: UUID) -> Optional[Telemetry]:
        """Fetch the single latest reading for a specific sensor."""
        query = (
            select(self.model)
            .where(self.model.sensor_id == sensor_id)
            .order_by(desc(self.model.time))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_time_range(
        self, sensor_id: UUID, start_time: datetime, end_time: datetime
    ) -> List[Telemetry]:
        """Retrieve all telemetry readings for a sensor within a time range."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.sensor_id == sensor_id,
                    self.model.time >= start_time,
                    self.model.time <= end_time,
                )
            )
            .order_by(desc(self.model.time))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_water_quality_metrics(
        self, tank_id: UUID, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """
        Retrieves min, max, and average metrics for all water quality parameters
        of a tank from environmental snapshots within a time range.
        """
        query = (
            select(
                func.avg(TankEnvironmentSnapshot.temperature).label("avg_temp"),
                func.min(TankEnvironmentSnapshot.temperature).label("min_temp"),
                func.max(TankEnvironmentSnapshot.temperature).label("max_temp"),
                
                func.avg(TankEnvironmentSnapshot.ph).label("avg_ph"),
                func.min(TankEnvironmentSnapshot.ph).label("min_ph"),
                func.max(TankEnvironmentSnapshot.ph).label("max_ph"),

                func.avg(TankEnvironmentSnapshot.dissolved_oxygen).label("avg_do"),
                func.min(TankEnvironmentSnapshot.dissolved_oxygen).label("min_do"),
                func.max(TankEnvironmentSnapshot.dissolved_oxygen).label("max_do"),

                func.avg(TankEnvironmentSnapshot.salinity).label("avg_sal"),
                func.min(TankEnvironmentSnapshot.salinity).label("min_sal"),
                func.max(TankEnvironmentSnapshot.salinity).label("max_sal"),

                func.avg(TankEnvironmentSnapshot.ammonia).label("avg_nh3"),
                func.min(TankEnvironmentSnapshot.ammonia).label("min_nh3"),
                func.max(TankEnvironmentSnapshot.ammonia).label("max_nh3"),

                func.avg(TankEnvironmentSnapshot.turbidity).label("avg_turb"),
                func.min(TankEnvironmentSnapshot.turbidity).label("min_turb"),
                func.max(TankEnvironmentSnapshot.turbidity).label("max_turb"),
            )
            .where(
                and_(
                    TankEnvironmentSnapshot.tank_id == tank_id,
                    TankEnvironmentSnapshot.captured_at >= start_time,
                    TankEnvironmentSnapshot.captured_at <= end_time,
                )
            )
        )
        result = await self.session.execute(query)
        r = result.one_or_none()

        if not r or r.avg_temp is None:
            return {"message": "No data found for this period"}

        return {
            "temperature": {"avg": float(r.avg_temp), "min": float(r.min_temp), "max": float(r.max_temp)},
            "ph": {"avg": float(r.avg_ph), "min": float(r.min_ph), "max": float(r.max_ph)},
            "dissolved_oxygen": {"avg": float(r.avg_do), "min": float(r.min_do), "max": float(r.max_do)},
            "salinity": {"avg": float(r.avg_sal), "min": float(r.min_sal), "max": float(r.max_sal)},
            "ammonia": {"avg": float(r.avg_nh3), "min": float(r.min_nh3), "max": float(r.max_nh3)},
            "turbidity": {"avg": float(r.avg_turb), "min": float(r.min_turb), "max": float(r.max_turb)},
        }

    async def get_sensor_statistics(
        self, sensor_id: UUID, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """Calculates min, max, average, and standard deviation from raw telemetry readings."""
        query = (
            select(
                func.avg(self.model.value).label("avg_val"),
                func.min(self.model.value).label("min_val"),
                func.max(self.model.value).label("max_val"),
                func.stddev(self.model.value).label("std_val"),
                func.count(self.model.id).label("count_val")
            )
            .where(
                and_(
                    self.model.sensor_id == sensor_id,
                    self.model.time >= start_time,
                    self.model.time <= end_time,
                )
            )
        )
        result = await self.session.execute(query)
        r = result.one_or_none()

        if not r or r.count_val == 0:
            return {"message": "No telemetry found for this sensor in the specified period"}

        return {
            "sensor_id": sensor_id,
            "count": int(r.count_val),
            "average": float(r.avg_val),
            "min": float(r.min_val),
            "max": float(r.max_val),
            "std_dev": float(r.std_val) if r.std_val is not None else 0.0,
        }
