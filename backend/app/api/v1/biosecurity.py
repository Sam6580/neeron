# app/api/v1/biosecurity.py

from typing import List, Any, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.deps import get_biosecurity_service, get_tank_service
from app.services.biosecurity_service import BiosecurityService
from app.services.tank_service import TankService
from app.repositories.base import BaseRepository
from app.models.biosecurity_record import Pathogen
from app.schemas.base import BaseResponse

router = APIRouter()


def _map_pathogen_name(p) -> str:
    if hasattr(p, "common_name") and p.common_name:
        return p.common_name
    return getattr(p, "name", "Unknown")


def _map_pathogen_scientific_name(p) -> str:
    if hasattr(p, "scientific_name") and p.scientific_name:
        return p.scientific_name
    return getattr(p, "name", "Unknown")


@router.get("", response_model=BaseResponse[Dict[str, Any]])
async def get_biosecurity_overview(
    farm_id: UUID,
    service: BiosecurityService = Depends(get_biosecurity_service),
):
    """
    Retrieves the biosecurity dashboard summary metrics for a farm.
    """
    res = await service.get_biosecurity_dashboard(farm_id)
    
    # Format response mapping
    return BaseResponse(
        data={
            "farmId": farm_id,
            "totalTanksCount": res["total_tanks"],
            "quarantinedTanksCount": res["quarantined_tanks_count"],
            "quarantinedTanks": [
                {
                    "tankId": q["tank_id"],
                    "name": q["name"],
                    "reason": q["quarantine_event"].reason,
                    "severity": q["quarantine_event"].severity,
                    "startedAt": q["quarantine_event"].started_at,
                }
                for q in res["quarantined_tanks"]
            ],
            "complianceReportsCount": len(res["compliance_reports"]),
        }
    )


@router.get("/pathogens", response_model=BaseResponse[List[Dict[str, Any]]])
async def list_pathogens(
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves the reference catalog of pathogens monitored in the system.
    """
    repo = BaseRepository(Pathogen, db)
    pathogens = await repo.get_multi(limit=100)
    return BaseResponse(
        data=[
            {
                "id": p.id,
                "name": _map_pathogen_name(p),
                "scientificName": _map_pathogen_scientific_name(p),  # scientific mapping
                "transmissionVector": getattr(p, "transmission_vector", "Waterborne"),
                "incubationPeriodDays": getattr(p, "incubation_days", 14),
            }
            for p in pathogens
        ]
    )


@router.get("/outbreaks", response_model=BaseResponse[List[Dict[str, Any]]])
async def list_outbreaks(
    farm_id: UUID,
    biosecurity_service: BiosecurityService = Depends(get_biosecurity_service),
):
    """
    Lists active pathogen outbreak incidents and quarantine statuses for all farm tanks.
    """
    outbreaks = await biosecurity_service.get_outbreaks_for_farm(farm_id)
    return BaseResponse(data=outbreaks)
