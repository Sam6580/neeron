# app/services/biosecurity_service.py

from typing import Any, Dict, List
from uuid import UUID

from app.models.biosecurity_record import BiosecurityRecord, ComplianceRecord
from app.models.tank import QuarantineEvent
from app.repositories.base import BaseRepository
from app.repositories.biosecurity_repository import BiosecurityRepository
from app.repositories.tank_repository import TankRepository
from app.services.base import BaseService


class BiosecurityService(BaseService):
    """
    Service managing biosecurity tracking, quarantine states, and regulatory compliance logs.
    """

    def __init__(
        self,
        biosecurity_repo: BiosecurityRepository,
        tank_repo: TankRepository,
        quarantine_repo: BaseRepository[QuarantineEvent],
    ):
        self.biosecurity_repo = biosecurity_repo
        self.tank_repo = tank_repo
        self.quarantine_repo = quarantine_repo

    async def get_biosecurity_dashboard(self, farm_id: UUID) -> Dict[str, Any]:
        """
        Summarizes pathogen presence, active quarantined tanks, and upcoming compliance deadlines.
        """
        tanks = await self.tank_repo.get_tank_dashboard(farm_id)
        quarantined_tanks = []
        pathogen_summary = {}

        for tank_data in tanks:
            tank_id = tank_data["tank_id"]
            
            # Check for active quarantines
            active_events = await self.quarantine_repo.get_multi(
                filters={"tank_id": tank_id, "cleared_at": None}
            )
            if active_events:
                quarantined_tanks.append({
                    "tank_id": tank_id,
                    "name": tank_data["name"],
                    "quarantine_event": active_events[0],
                })

            # Summarize latest pathogen inspection records
            records = await self.biosecurity_repo.get_latest_pathogen_counts(tank_id)
            for rec in records:
                # Pathogen name relationship fallback
                pathogen_name = rec.pathogen.name if getattr(rec, "pathogen", None) else "Unknown Pathogen"
                if pathogen_name not in pathogen_summary:
                    pathogen_summary[pathogen_name] = []
                pathogen_summary[pathogen_name].append({
                    "tank_id": tank_id,
                    "tank_name": tank_data["name"],
                    "risk_level": rec.risk_level,
                    "status": rec.status,
                    "time": rec.time,
                })

        compliance = await self.biosecurity_repo.get_compliance_status(farm_id)

        return {
            "farm_id": farm_id,
            "total_tanks": len(tanks),
            "quarantined_tanks_count": len(quarantined_tanks),
            "quarantined_tanks": quarantined_tanks,
            "active_pathogens": pathogen_summary,
            "compliance_reports": compliance,
        }

    async def get_pathogen_summary(self, tank_id: UUID) -> List[BiosecurityRecord]:
        """
        Retrieves the latest pathogen count records for a specific tank.
        """
        return await self.biosecurity_repo.get_latest_pathogen_counts(tank_id)

    async def get_quarantine_status(self, tank_id: UUID) -> Dict[str, Any]:
        """
        Retrieves active quarantine info and historical events for a specific tank.
        """
        all_events = await self.quarantine_repo.get_multi(filters={"tank_id": tank_id})
        active = [e for e in all_events if e.cleared_at is None]
        history = [e for e in all_events if e.cleared_at is not None]

        return {
            "tank_id": tank_id,
            "is_quarantined": len(active) > 0,
            "active_quarantines": active,
            "quarantine_history": history,
        }

    async def get_compliance_overview(self, farm_id: UUID) -> List[ComplianceRecord]:
        """
        Retrieves active/upcoming regulatory compliance records for the farm.
        """
        return await self.biosecurity_repo.get_compliance_status(farm_id)
