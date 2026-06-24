# app/api/v1/farms.py

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import get_farm_service
from app.services.farm_service import FarmService
from app.schemas.base import BaseResponse
from app.schemas.farm import FarmResponse
from app.schemas.dashboard import DashboardHealthResponse

router = APIRouter()


@router.get("", response_model=BaseResponse[List[FarmResponse]])
async def list_farms(
    skip: int = 0,
    limit: int = 100,
    service: FarmService = Depends(get_farm_service),
):
    """
    Returns a list of all geographical farms registered in the platform.
    """
    farms = await service.list_farms(skip=skip, limit=limit)
    return BaseResponse(
        data=[
            FarmResponse(
                id=f.id,
                name=f.name,
                latitude=float(f.latitude),
                longitude=float(f.longitude),
                timezone=f.timezone,
                carryingCapacityKg=float(f.carrying_capacity_kg),
            )
            for f in farms
        ]
    )


@router.get("/{farm_id}", response_model=BaseResponse[FarmResponse])
async def get_farm_detail(
    farm_id: UUID,
    service: FarmService = Depends(get_farm_service),
):
    """
    Retrieves detailed properties for a single farm.
    """
    farm = await service.get_farm(farm_id)
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm not found with ID {farm_id}",
        )

    return BaseResponse(
        data=FarmResponse(
            id=farm.id,
            name=farm.name,
            latitude=float(farm.latitude),
            longitude=float(farm.longitude),
            timezone=farm.timezone,
            carryingCapacityKg=float(farm.carrying_capacity_kg),
        )
    )


@router.get("/{farm_id}/health", response_model=BaseResponse[DashboardHealthResponse])
async def get_farm_health(
    farm_id: UUID,
    service: FarmService = Depends(get_farm_service),
):
    """
    Retrieves the aggregate health parameters and score for a specific farm.
    """
    farm = await service.get_farm(farm_id)
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm not found with ID {farm_id}",
        )

    health_score = await service.get_farm_health(farm_id)
    snapshot = await service.dashboard_repo.get_farm_health_snapshot(farm_id)
    risk_score = float(snapshot.risk_score) if snapshot else 0.0
    psi_average = float(snapshot.psi_average) if snapshot else 0.0

    return BaseResponse(
        data=DashboardHealthResponse(
            farm_id=farm_id,
            health_score=health_score,
            risk_score=risk_score,
            psi_average=psi_average,
        )
    )
