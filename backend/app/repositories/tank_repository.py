from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tank import Tank
from app.models.zone import Zone
from app.models.alert import Alert
from app.models.sensor import Sensor
from app.models.telemetry import Telemetry
from app.models.psi_prediction import PsiPrediction
from app.models.tank_environment_snapshot import TankEnvironmentSnapshot
from app.repositories.base import BaseRepository


class TankRepository(BaseRepository[Tank]):
    """Repository class for Tank operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Tank, session)

    async def get_tank_dashboard(self, farm_id: UUID) -> List[Dict[str, Any]]:
        """
        Retrieves dashboard statistics for all tanks in a farm.
        Includes current tank details, latest environment snapshot, and active alerts count.
        """
        # Select tanks belonging to the farm
        query = (
            select(self.model)
            .join(Zone, self.model.zone_id == Zone.id)
            .where(Zone.farm_id == farm_id)
        )
        tanks_result = await self.session.execute(query)
        tanks = tanks_result.scalars().all()

        dashboard_data = []
        for tank in tanks:
            # Get active alerts count
            alerts_query = select(func.count(Alert.id)).where(
                and_(
                    Alert.tank_id == tank.id,
                    Alert.status == "Active"
                )
            )
            alerts_count_result = await self.session.execute(alerts_query)
            active_alerts = alerts_count_result.scalar() or 0

            # Get latest environment snapshot
            snapshot_query = (
                select(TankEnvironmentSnapshot)
                .where(TankEnvironmentSnapshot.tank_id == tank.id)
                .order_by(desc(TankEnvironmentSnapshot.captured_at))
                .limit(1)
            )
            snapshot_result = await self.session.execute(snapshot_query)
            latest_snapshot = snapshot_result.scalar_one_or_none()

            dashboard_data.append({
                "tank_id": tank.id,
                "name": tank.name,
                "type": tank.type,
                "species": tank.species,
                "volume_m3": float(tank.volume_m3),
                "max_biomass_kg": float(tank.max_biomass_kg),
                "active_alerts_count": active_alerts,
                "latest_environment": {
                    "temperature": float(latest_snapshot.temperature) if latest_snapshot and latest_snapshot.temperature is not None else None,
                    "ph": float(latest_snapshot.ph) if latest_snapshot and latest_snapshot.ph is not None else None,
                    "dissolved_oxygen": float(latest_snapshot.dissolved_oxygen) if latest_snapshot and latest_snapshot.dissolved_oxygen is not None else None,
                    "salinity": float(latest_snapshot.salinity) if latest_snapshot and latest_snapshot.salinity is not None else None,
                    "ammonia": float(latest_snapshot.ammonia) if latest_snapshot and latest_snapshot.ammonia is not None else None,
                    "turbidity": float(latest_snapshot.turbidity) if latest_snapshot and latest_snapshot.turbidity is not None else None,
                    "captured_at": latest_snapshot.captured_at if latest_snapshot else None,
                } if latest_snapshot else None
            })

        return dashboard_data

    async def get_latest_environment_snapshot(self, tank_id: UUID) -> Optional[TankEnvironmentSnapshot]:
        """Fetch the latest TankEnvironmentSnapshot for a single tank."""
        query = (
            select(TankEnvironmentSnapshot)
            .where(TankEnvironmentSnapshot.tank_id == tank_id)
            .order_by(desc(TankEnvironmentSnapshot.captured_at))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_tank_health(self, tank_id: UUID) -> Dict[str, Any]:
        """
        Calculates stability of environmental variables (temperature, dissolved oxygen, pH)
        over the last 7 days and integrates the latest predicted stress score.
        """
        # Fetch latest PSI prediction
        psi_query = (
            select(PsiPrediction)
            .where(PsiPrediction.tank_id == tank_id)
            .order_by(desc(PsiPrediction.generated_at))
            .limit(1)
        )
        psi_result = await self.session.execute(psi_query)
        latest_psi = psi_result.scalar_one_or_none()

        # Calculate stability over the last 7 days from snapshots
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        stats_query = (
            select(
                func.avg(TankEnvironmentSnapshot.temperature).label("avg_temp"),
                func.avg(TankEnvironmentSnapshot.dissolved_oxygen).label("avg_do"),
                func.avg(TankEnvironmentSnapshot.ph).label("avg_ph"),
                # We can calculate standard deviation for stability
                func.stddev(TankEnvironmentSnapshot.temperature).label("std_temp"),
                func.stddev(TankEnvironmentSnapshot.dissolved_oxygen).label("std_do"),
                func.stddev(TankEnvironmentSnapshot.ph).label("std_ph")
            )
            .where(
                and_(
                    TankEnvironmentSnapshot.tank_id == tank_id,
                    TankEnvironmentSnapshot.captured_at >= seven_days_ago
                )
            )
        )
        stats_result = await self.session.execute(stats_query)
        stats = stats_result.one_or_none()

        def interpret_stability(std_val: Optional[float], warning_threshold: float) -> str:
            if std_val is None:
                return "Unknown"
            if std_val < warning_threshold * 0.5:
                return "Stable"
            if std_val < warning_threshold:
                return "Moderate"
            return "Unstable"

        return {
            "tank_id": tank_id,
            "psi_score": float(latest_psi.psi_score) if latest_psi else None,
            "stress_level": latest_psi.stress_level if latest_psi else "Unknown",
            "psi_generated_at": latest_psi.generated_at if latest_psi else None,
            "stability": {
                "temperature": interpret_stability(stats.std_temp, warning_threshold=1.5) if stats else "Unknown",
                "dissolved_oxygen": interpret_stability(stats.std_do, warning_threshold=1.0) if stats else "Unknown",
                "ph": interpret_stability(stats.std_ph, warning_threshold=0.3) if stats else "Unknown",
            },
            "averages_7d": {
                "temperature": float(stats.avg_temp) if stats and stats.avg_temp is not None else None,
                "dissolved_oxygen": float(stats.avg_do) if stats and stats.avg_do is not None else None,
                "ph": float(stats.avg_ph) if stats and stats.avg_ph is not None else None,
            } if stats else None
        }

    async def get_latest_telemetry(self, tank_id: UUID) -> List[Telemetry]:
        """Fetches the latest reading for each sensor attached to this tank."""
        # Find all active sensors for this tank
        sensors_query = select(Sensor).where(
            and_(
                Sensor.tank_id == tank_id,
                Sensor.status == "Active"
            )
        )
        sensors_result = await self.session.execute(sensors_query)
        sensors = sensors_result.scalars().all()

        latest_readings = []
        for sensor in sensors:
            telemetry_query = (
                select(Telemetry)
                .where(Telemetry.sensor_id == sensor.id)
                .order_by(desc(Telemetry.time))
                .limit(1)
            )
            telemetry_result = await self.session.execute(telemetry_query)
            reading = telemetry_result.scalar_one_or_none()
            if reading:
                latest_readings.append(reading)

        return latest_readings

    async def get_active_alerts(self, tank_id: UUID) -> List[Alert]:
        """Retrieves all active/unresolved alerts for the tank."""
        query = (
            select(Alert)
            .where(
                and_(
                    Alert.tank_id == tank_id,
                    Alert.status == "Active"
                )
            )
            .order_by(desc(Alert.time))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
