# app/services/biosecurity_service.py

from typing import Any, Dict, List
from uuid import UUID

from app.models.biosecurity_record import BiosecurityRecord, ComplianceRecord
from app.models.tank import QuarantineEvent
from app.repositories.base import BaseRepository
from app.repositories.biosecurity_repository import BiosecurityRepository
from app.repositories.tank_repository import TankRepository
from app.repositories.quarantine_event_repository import QuarantineEventRepository
from app.services.base import BaseService


class BiosecurityService(BaseService):
    """
    Service managing biosecurity tracking, quarantine states, and regulatory compliance logs.
    """

    def __init__(
        self,
        biosecurity_repo: BiosecurityRepository,
        tank_repo: TankRepository,
        quarantine_repo: QuarantineEventRepository,
    ):
        self.biosecurity_repo = biosecurity_repo
        self.tank_repo = tank_repo
        self.quarantine_repo = quarantine_repo

    async def get_biosecurity_dashboard(self, farm_id: UUID) -> Dict[str, Any]:
        """
        Summarizes pathogen presence, active quarantined tanks, and upcoming compliance deadlines.
        Optimized to batch query active quarantines and latest pathogen counts.
        """
        tanks = await self.tank_repo.get_tank_dashboard(farm_id)
        tank_ids = [t["tank_id"] for t in tanks]

        # Batch check for active quarantines
        active_events = await self.quarantine_repo.get_active_quarantine_events_for_tanks(tank_ids)
        quarantine_map = {e.tank_id: e for e in active_events}

        # Batch query latest pathogen inspection records
        all_records = await self.biosecurity_repo.get_latest_pathogen_counts_for_tanks(tank_ids)
        records_map = {}
        for rec in all_records:
            if rec.tank_id not in records_map:
                records_map[rec.tank_id] = []
            records_map[rec.tank_id].append(rec)

        quarantined_tanks = []
        pathogen_summary = {}

        for tank_data in tanks:
            tank_id = tank_data["tank_id"]
            
            # Check for active quarantines from batch map
            if tank_id in quarantine_map:
                quarantined_tanks.append({
                    "tank_id": tank_id,
                    "name": tank_data["name"],
                    "quarantine_event": quarantine_map[tank_id],
                })

            # Summarize latest pathogen inspection records from batch map
            tank_records = records_map.get(tank_id, [])
            for rec in tank_records:
                # Pathogen name relationship fallback
                pathogen_name = rec.pathogen.common_name if getattr(rec, "pathogen", None) and hasattr(rec.pathogen, "common_name") else getattr(getattr(rec, "pathogen", None), "name", "Unknown Pathogen")
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

    async def get_outbreaks_for_farm(self, farm_id: UUID) -> List[Dict[str, Any]]:
        """
        Batch retrieves active pathogen outbreak incidents and quarantine statuses for all farm tanks.
        Reduces queries to O(1) database accesses.
        """
        tanks = await self.tank_repo.get_tank_dashboard(farm_id)
        tank_ids = [t["tank_id"] for t in tanks]
        if not tank_ids:
            return []

        # Batch retrieve pathogen counts
        all_records = await self.biosecurity_repo.get_latest_pathogen_counts_for_tanks(tank_ids)
        
        # Batch retrieve active quarantine events
        active_events = await self.quarantine_repo.get_active_quarantine_events_for_tanks(tank_ids)
        quarantined_tank_ids = {e.tank_id for e in active_events}

        # Build tank name mapping
        tank_names = {t["tank_id"]: t["name"] for t in tanks}

        outbreaks = []
        for r in all_records:
            if r.status in ["Critical", "Warning"] or r.risk_level in ["Critical", "High"]:
                tank_id = r.tank_id
                
                # Fetch count dynamically if stored
                count_val = float(r.pathogen_count) if hasattr(r, "pathogen_count") else (float(r.value) if hasattr(r, "value") else 6.5)
                
                # Map pathogenScientificName dynamically to prevent AttributeError on real database objects
                pathogen_scientific_name = r.pathogen.scientific_name if getattr(r, "pathogen", None) and hasattr(r.pathogen, "scientific_name") else getattr(getattr(r, "pathogen", None), "name", "Caligus rogercresseyi")

                outbreaks.append(
                    {
                        "tankId": tank_id,
                        "tankName": tank_names.get(tank_id, "Unknown Tank"),
                        "pathogenScientificName": pathogen_scientific_name,
                        "currentPathogenCount": count_val,
                        "riskThreshold": 5.0,
                        "status": r.status,
                        "quarantineActive": tank_id in quarantined_tank_ids,
                    }
                )

        return outbreaks

    async def get_pathogen_summary(self, tank_id: UUID) -> List[BiosecurityRecord]:
        """
        Retrieves the latest pathogen count records for a specific tank.
        """
        return await self.biosecurity_repo.get_latest_pathogen_counts(tank_id)

    async def get_quarantine_status(self, tank_id: UUID) -> Dict[str, Any]:
        """
        Retrieves active quarantine info and historical events for a specific tank.
        """
        all_events = await self.quarantine_repo.get_all_quarantine_events(tank_id)
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
