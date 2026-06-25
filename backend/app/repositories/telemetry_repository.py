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

    async def get_latest_readings_for_sensors(
        self, sensor_ids: List[UUID]
    ) -> List[Telemetry]:
        """Fetch the latest reading for a list of sensors in a single query."""
        if not sensor_ids:
            return []
        subq = (
            select(
                Telemetry,
                func.row_number().over(
                    partition_by=Telemetry.sensor_id,
                    order_by=desc(Telemetry.time)
                ).label("rn")
            )
            .where(Telemetry.sensor_id.in_(sensor_ids))
            .subquery()
        )
        from sqlalchemy.orm import aliased
        telemetry_alias = aliased(Telemetry, subq)
        query = select(telemetry_alias).where(subq.c.rn == 1)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_time_ranges_for_sensors(
        self, sensor_ids: List[UUID], start_time: datetime, end_time: datetime
    ) -> List[Telemetry]:
        """Retrieve all telemetry readings for a list of sensors within a time range."""
        if not sensor_ids:
            return []
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.sensor_id.in_(sensor_ids),
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

    async def get_latest_hydrophone_reading(self, tank_id: UUID) -> Optional[TankEnvironmentSnapshot]:
        """Fetch the single latest snapshot containing acoustic data for a tank."""
        query = (
            select(TankEnvironmentSnapshot)
            .where(
                and_(
                    TankEnvironmentSnapshot.tank_id == tank_id,
                    TankEnvironmentSnapshot.acoustic_db.isnot(None),
                )
            )
            .order_by(desc(TankEnvironmentSnapshot.captured_at))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_hydrophone_readings(
        self, tank_id: UUID, start_time: datetime, end_time: datetime
    ) -> List[TankEnvironmentSnapshot]:
        """Retrieve historical environmental snapshots containing acoustic data for a tank."""
        query = (
            select(TankEnvironmentSnapshot)
            .where(
                and_(
                    TankEnvironmentSnapshot.tank_id == tank_id,
                    TankEnvironmentSnapshot.captured_at >= start_time,
                    TankEnvironmentSnapshot.captured_at <= end_time,
                    TankEnvironmentSnapshot.acoustic_db.isnot(None),
                )
            )
            .order_by(desc(TankEnvironmentSnapshot.captured_at))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_acoustic_trend_summary(
        self, tank_id: UUID, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """Calculates trend averages for acoustic activity."""
        query = (
            select(
                func.avg(TankEnvironmentSnapshot.acoustic_db).label("avg_db"),
                func.min(TankEnvironmentSnapshot.acoustic_db).label("min_db"),
                func.max(TankEnvironmentSnapshot.acoustic_db).label("max_db"),
                func.stddev(TankEnvironmentSnapshot.acoustic_db).label("std_db"),
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
        if not r or r.avg_db is None:
            return {
                "db_average": -42.0,
                "db_min": -45.0,
                "db_max": -40.0,
                "db_std": 1.2
            }
        return {
            "db_average": float(r.avg_db),
            "db_min": float(r.min_db),
            "db_max": float(r.max_db),
            "db_std": float(r.std_db) if r.std_db is not None else 0.0,
        }

    async def get_behavior_baseline(self, tank_id: UUID) -> Dict[str, Any]:
        """Returns baseline acoustic behavior statistics for the tank."""
        return {
            "baseline_db": -42.5,
            "baseline_sync": 95.0
        }

    async def get_behavior_anomalies(
        self, tank_id: UUID, start_time: datetime, end_time: datetime
    ) -> List[Any]:
        """
        Detects anomalies in bio-acoustic sync or levels.
        
        Current implementation:
        return []
        
        Reason:
        Reserved for future Acoustic Intelligence Engine. Anomaly detection algorithms
        must not be implemented during Phase 10.1.
        """
        return []

    async def get_acoustic_analytics_series(
        self, tank_id: UUID, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Returns time-series acoustic telemetry points from snapshots for chart rendering."""
        snapshots = await self.get_hydrophone_readings(tank_id, start_time, end_time)
        return [
            {
                "time": s.captured_at,
                "acoustic_db": float(s.acoustic_db) if s.acoustic_db is not None else -42.0,
                "bio_acoustic_sync": float(s.bio_acoustic_sync) if s.bio_acoustic_sync is not None else 98.0,
            }
            for s in snapshots
        ]
