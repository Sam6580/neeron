# app/api/v1/settings.py

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import get_settings_service
from app.services.settings_service import SettingsService
from app.schemas.base import BaseResponse
from app.schemas.settings import (
    SensorStatusResponse,
    ThresholdConfigResponse,
    ThresholdUpdatePayload,
)
from app.api.v1.dependencies.auth import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.get("/sensors", response_model=BaseResponse[List[SensorStatusResponse]])
async def get_sensor_status(
    farm_id: UUID,
    service: SettingsService = Depends(get_settings_service),
):
    """
    Retrieves status indicators, operational state, and calibration due dates for all farm sensors.
    """
    sensors = await service.get_sensor_status(farm_id)
    return BaseResponse(
        data=[
            SensorStatusResponse(
                sensor_id=s["sensor_id"],
                hardware_id=s["hardware_id"],
                type=s["type"],
                status=s["status"],
                calibration_due_at=s["calibration_due_at"],
                tank_id=s["tank_id"],
            )
            for s in sensors
        ]
    )


@router.get("/thresholds", response_model=BaseResponse[List[ThresholdConfigResponse]])
async def get_threshold_configs(
    farm_id: UUID,
    service: SettingsService = Depends(get_settings_service),
):
    """
    Retrieves the standard warning/critical metric thresholds configured for the farm.
    """
    thresholds = await service.get_thresholds(farm_id)
    return BaseResponse(data=thresholds)


@router.put("/thresholds", response_model=BaseResponse[ThresholdConfigResponse])
async def update_threshold_configs(
    payload: ThresholdUpdatePayload,
    current_user: User = Depends(get_current_active_user),
    service: SettingsService = Depends(get_settings_service),
):
    """
    Updates warning/critical threshold parameters for a specific metric.
    """
    # Use authenticated user ID for audit trailing
    user_id = current_user.id
    try:
        config = await service.update_thresholds(
            farm_id=payload.farmId,
            metric_name=payload.metricName,
            warning_min=payload.warningMin,
            warning_max=payload.warningMax,
            critical_min=payload.criticalMin,
            critical_max=payload.criticalMax,
            user_id=user_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    return BaseResponse(data=config)
