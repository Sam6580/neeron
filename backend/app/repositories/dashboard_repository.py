from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farm_health_snapshot import FarmHealthSnapshot
from app.models.system_health_snapshot import SystemHealthSnapshot
from app.models.alert import Alert
from app.models.tank import Tank
from app.models.zone import Zone
from app.models.recommendation import Recommendation
from app.models.psi_prediction import PsiPrediction
from app.repositories.base import BaseRepository


class DashboardRepository(BaseRepository[FarmHealthSnapshot]):
    """
    Repository class specialized in gathering aggregate metrics,
    snapshots, and summaries to feed the NEERON executive dashboard.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(FarmHealthSnapshot, session)

    async def get_global_health_score(self, farm_id: UUID) -> float:
        """Retrieve the latest aggregate health score for a farm."""
        query = (
            select(self.model.health_score)
            .where(self.model.farm_id == farm_id)
            .order_by(desc(self.model.recorded_at))
            .limit(1)
        )
        result = await self.session.execute(query)
        val = result.scalar_one_or_none()
        return float(val) if val is not None else 100.0

    async def get_active_alert_count(self, farm_id: UUID) -> int:
        """Count all unresolved Active alerts across all tanks in a farm."""
        query = (
            select(func.count(Alert.id))
            .join(Tank, Alert.tank_id == Tank.id)
            .join(Zone, Tank.zone_id == Zone.id)
            .where(
                and_(
                    Zone.farm_id == farm_id,
                    Alert.status == "Active"
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_risk_trend(self, farm_id: UUID, days: int = 7) -> List[Dict[str, Any]]:
        """Retrieve the historical timeline of farm risk scores."""
        start_time = datetime.now(timezone.utc) - timedelta(days=days)
        query = (
            select(self.model.recorded_at, self.model.risk_score)
            .where(
                and_(
                    self.model.farm_id == farm_id,
                    self.model.recorded_at >= start_time
                )
            )
            .order_by(self.model.recorded_at)
        )
        result = await self.session.execute(query)
        rows = result.all()
        return [{"recorded_at": row[0], "risk_score": float(row[1])} for row in rows]

    async def get_zone_summary(self, farm_id: UUID) -> List[Dict[str, Any]]:
        """
        Summarize active zones in the farm.
        Includes zone name, tank count, and average predicted stress index (PSI) for its tanks.
        """
        # Fetch zones
        zones_query = select(Zone).where(Zone.farm_id == farm_id)
        zones_result = await self.session.execute(zones_query)
        zones = zones_result.scalars().all()

        summary = []
        for zone in zones:
            # Count tanks
            tanks_query = select(Tank).where(Tank.zone_id == zone.id)
            tanks_result = await self.session.execute(tanks_query)
            tanks = tanks_result.scalars().all()
            tank_count = len(tanks)

            # Average PSI of those tanks
            avg_psi = 0.0
            if tank_count > 0:
                psi_sum = 0.0
                valid_count = 0
                for tank in tanks:
                    # Get latest PSI prediction for tank
                    psi_query = (
                        select(PsiPrediction.psi_score)
                        .where(PsiPrediction.tank_id == tank.id)
                        .order_by(desc(PsiPrediction.generated_at))
                        .limit(1)
                    )
                    psi_result = await self.session.execute(psi_query)
                    psi_val = psi_result.scalar_one_or_none()
                    if psi_val is not None:
                        psi_sum += float(psi_val)
                        valid_count += 1
                if valid_count > 0:
                    avg_psi = psi_sum / valid_count

            summary.append({
                "zone_id": zone.id,
                "name": zone.name,
                "tank_count": tank_count,
                "average_psi": round(avg_psi, 2),
            })

        return summary

    async def get_recent_recommendations(self, farm_id: UUID, limit: int = 5) -> List[Recommendation]:
        """Fetch latest active recommendations generated for any tank on a farm."""
        query = (
            select(Recommendation)
            .join(Tank, Recommendation.tank_id == Tank.id)
            .join(Zone, Tank.zone_id == Zone.id)
            .where(
                and_(
                    Zone.farm_id == farm_id,
                    Recommendation.status == "Pending"
                )
            )
            .order_by(desc(Recommendation.time))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_system_health_snapshot(self) -> Optional[SystemHealthSnapshot]:
        """Retrieve the latest global system infrastructure snapshot."""
        query = (
            select(SystemHealthSnapshot)
            .order_by(desc(SystemHealthSnapshot.recorded_at))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_farm_health_snapshot(self, farm_id: UUID) -> Optional[FarmHealthSnapshot]:
        """Retrieve the latest farm health snapshot."""
        query = (
            select(self.model)
            .where(self.model.farm_id == farm_id)
            .order_by(desc(self.model.recorded_at))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
