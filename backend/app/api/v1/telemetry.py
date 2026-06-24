# app/api/v1/telemetry.py

from datetime import datetime, timezone
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import get_telemetry_service, get_tank_service
from app.services.telemetry_service import TelemetryService
from app.services.tank_service import TankService
from app.schemas.base import BaseResponse
from app.schemas.telemetry import (
    TelemetryLatestResponse,
    TelemetryMetrics,
    TelemetryHistoryResponse,
    TelemetryHistoryPoint,
)

router = APIRouter()


@router.get("/latest", response_model=BaseResponse[TelemetryLatestResponse])
async def get_latest_telemetry(
    tank_id: UUID,
    telemetry_service: TelemetryService = Depends(get_telemetry_service),
    tank_service: TankService = Depends(get_tank_service),
):
    """
    Retrieves the latest pivoted environment metrics snapshot for a specific tank.
    """
    snap = await tank_service.get_tank_environment(tank_id)
    if not snap:
        # Return fallback metrics if no snapshots have been recorded yet
        return BaseResponse(
            data=TelemetryLatestResponse(
                tankId=tank_id,
                capturedAt=datetime.now(timezone.utc),
                metrics=TelemetryMetrics(
                    temperature=12.0,
                    ph=7.3,
                    dissolvedOxygen=8.0,
                    salinity=32.5,
                    ammonia=0.012,
                    turbidity=4.0,
                ),
            )
        )

    return BaseResponse(
        data=TelemetryLatestResponse(
            tankId=tank_id,
            capturedAt=snap.captured_at or datetime.now(timezone.utc),
            metrics=TelemetryMetrics(
                temperature=float(snap.temperature) if snap.temperature is not None else 12.0,
                ph=float(snap.ph) if snap.ph is not None else 7.3,
                dissolvedOxygen=float(snap.dissolved_oxygen) if snap.dissolved_oxygen is not None else 8.0,
                salinity=float(snap.salinity) if snap.salinity is not None else 32.5,
                ammonia=float(snap.ammonia) if snap.ammonia is not None else 0.012,
                turbidity=float(snap.turbidity) if snap.turbidity is not None else 4.0,
            ),
        )
    )


@router.get("/history", response_model=BaseResponse[TelemetryHistoryResponse])
async def get_telemetry_history(
    tank_id: UUID,
    start_time: datetime,
    end_time: datetime,
    service: TelemetryService = Depends(get_telemetry_service),
):
    """
    Retrieves historical ranges of raw telemetry readings for all active sensors on a tank.
    """
    sensors = await service.sensor_repo.get_active_sensors(tank_id)
    history_points = []
    
    for s in sensors:
        readings = await service.get_time_series(s.id, start_time, end_time)
        for r in readings:
            history_points.append(
                TelemetryHistoryPoint(
                    timestamp=r.time,
                    value=float(r.value),
                    sensor_id=s.id,
                )
            )

    return BaseResponse(
        data=TelemetryHistoryResponse(
            tankId=tank_id,
            history=history_points,
        )
    )
