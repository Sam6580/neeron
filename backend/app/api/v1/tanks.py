# app/api/v1/tanks.py

import math
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import get_tank_service
from app.services.tank_service import TankService
from app.schemas.base import PaginatedResponse, PaginationMeta, BaseResponse
from app.schemas.tank import (
    TankResponse,
    TankDetailResponse,
    TankHealthResponse,
    TankEnvironmentSnapshotResponse,
    TankPredictionsResponse,
    TankStability,
    TankAverages7d,
)

router = APIRouter()


@router.get("", response_model=PaginatedResponse[TankResponse])
async def list_tanks(
    zone_id: Optional[UUID] = None,
    type: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    service: TankService = Depends(get_tank_service),
):
    """
    Retrieves a list of fish tanks with pagination, optionally filtered by zone or structural type.
    """
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 20

    skip = (page - 1) * limit
    tanks = await service.list_tanks(zone_id=zone_id, type=type, skip=skip, limit=limit)
    
    # Build filter criteria
    filters = {}
    if zone_id:
        filters["zone_id"] = zone_id
    if type:
        filters["type"] = type
        
    total_count = await service.tank_repo.count(filters=filters)
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 0

    data = []
    for t in tanks:
        health = await service.get_tank_health(t.id)
        status_lbl = health.get("stress_level", "Optimal")
        if status_lbl in ["Unknown", "low"]:
            status_lbl = "Optimal"
        elif status_lbl == "Medium":
            status_lbl = "Warning"

        data.append(
            TankResponse(
                id=t.id,
                name=t.name,
                type=t.type,
                volumeM3=float(t.volume_m3),
                maxBiomassKg=float(t.max_biomass_kg),
                species=t.species,
                currentBiomassKg=float(t.max_biomass_kg) * 0.75,
                healthStatus=status_lbl,
            )
        )

    return PaginatedResponse(
        data=data,
        pagination=PaginationMeta(
            currentPage=page,
            totalPages=max(1, total_pages),
            limit=limit,
            totalCount=total_count,
        ),
    )


@router.get("/{tank_id}", response_model=BaseResponse[TankDetailResponse])
async def get_tank_detail(
    tank_id: UUID,
    service: TankService = Depends(get_tank_service),
):
    """
    Retrieves static details and parameters for a specific tank.
    """
    tank = await service.tank_repo.get(tank_id)
    if not tank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tank not found with ID {tank_id}",
        )

    return BaseResponse(
        data=TankDetailResponse(
            id=tank.id,
            name=tank.name,
            type=tank.type,
            volumeM3=float(tank.volume_m3),
            maxBiomassKg=float(tank.max_biomass_kg),
            species=tank.species,
            digitalTwinConfig=tank.digital_twin_config or {},
            created_at=tank.created_at,
        )
    )


@router.get("/{tank_id}/health", response_model=BaseResponse[TankHealthResponse])
async def get_tank_health(
    tank_id: UUID,
    service: TankService = Depends(get_tank_service),
):
    """
    Calculates parameter stability and stress levels for a tank.
    """
    tank = await service.tank_repo.get(tank_id)
    if not tank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tank not found with ID {tank_id}",
        )

    health = await service.get_tank_health(tank_id)
    stability = health.get("stability", {})
    averages = health.get("averages_7d", {})

    return BaseResponse(
        data=TankHealthResponse(
            tank_id=tank_id,
            psi_score=health.get("psi_score"),
            stress_level=health.get("stress_level", "Unknown"),
            psi_generated_at=health.get("psi_generated_at"),
            stability=TankStability(
                temperature=stability.get("temperature", "Unknown"),
                dissolved_oxygen=stability.get("dissolved_oxygen", "Unknown"),
                ph=stability.get("ph", "Unknown"),
            ),
            averages_7d=TankAverages7d(
                temperature=averages.get("temperature") if averages else None,
                dissolved_oxygen=averages.get("dissolved_oxygen") if averages else None,
                ph=averages.get("ph") if averages else None,
            ) if averages else None,
        )
    )


@router.get("/{tank_id}/environment", response_model=BaseResponse[Optional[TankEnvironmentSnapshotResponse]])
async def get_tank_environment(
    tank_id: UUID,
    service: TankService = Depends(get_tank_service),
):
    """
    Retrieves the latest environmental metrics snapshot for the tank.
    """
    tank = await service.tank_repo.get(tank_id)
    if not tank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tank not found with ID {tank_id}",
        )

    snap = await service.get_tank_environment(tank_id)
    if not snap:
        return BaseResponse(data=None)

    return BaseResponse(
        data=TankEnvironmentSnapshotResponse(
            temperature=float(snap.temperature) if snap.temperature is not None else None,
            ph=float(snap.ph) if snap.ph is not None else None,
            dissolved_oxygen=float(snap.dissolved_oxygen) if snap.dissolved_oxygen is not None else None,
            salinity=float(snap.salinity) if snap.salinity is not None else None,
            ammonia=float(snap.ammonia) if snap.ammonia is not None else None,
            turbidity=float(snap.turbidity) if snap.turbidity is not None else None,
            captured_at=snap.captured_at,
        )
    )


@router.get("/{tank_id}/predictions", response_model=BaseResponse[TankPredictionsResponse])
async def get_tank_predictions(
    tank_id: UUID,
    service: TankService = Depends(get_tank_service),
):
    """
    Retrieves the complete set of AI forecasts (PSI, disease, mortality, harvest) for the tank.
    """
    tank = await service.tank_repo.get(tank_id)
    if not tank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tank not found with ID {tank_id}",
        )

    preds = await service.get_tank_predictions(tank_id)
    return BaseResponse(
        data=TankPredictionsResponse(
            psi=preds.get("psi"),
            disease=preds.get("disease"),
            mortality=preds.get("mortality"),
            harvest=preds.get("harvest"),
        )
    )
