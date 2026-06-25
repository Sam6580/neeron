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
    AcousticActivityResponse,
    AcousticHistoryResponse,
    AcousticSeriesPoint,
    AcousticSummary,
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
    sensor_ids = [s.id for s in sensors]
    history_points = []
    
    if sensor_ids:
        readings = await service.get_time_series_multi(sensor_ids, start_time, end_time)
        for r in readings:
            history_points.append(
                TelemetryHistoryPoint(
                    timestamp=r.time,
                    value=float(r.value),
                    sensor_id=r.sensor_id,
                )
            )

    return BaseResponse(
        data=TelemetryHistoryResponse(
            tankId=tank_id,
            history=history_points,
        )
    )


@router.get("/acoustic", response_model=BaseResponse[AcousticActivityResponse])
async def get_acoustic_activity(
    tank_id: UUID,
    service: TelemetryService = Depends(get_telemetry_service),
):
    """
    Retrieves the current hydrophone acoustic activity metrics for a specific tank.

    Returns live acoustic decibel reading and Bio-Acoustic Sync confidence score.
    Anomaly detection is Not Yet Implemented (reserved for Acoustic Intelligence phase).
    """
    data = await service.get_acoustic_activity(tank_id)
    return BaseResponse(
        data=AcousticActivityResponse(
            tankId=tank_id,
            current_db=data["current_db"],
            bio_acoustic_sync=data["bio_acoustic_sync"],
            status=data["status"],
        )
    )


@router.get("/acoustic/history", response_model=BaseResponse[AcousticHistoryResponse])
async def get_acoustic_history(
    tank_id: UUID,
    start_time: datetime,
    end_time: datetime,
    service: TelemetryService = Depends(get_telemetry_service),
):
    """
    Returns time-series acoustic telemetry history for Analytics Dashboard chart rendering.

    Provides per-point acoustic_db and bio_acoustic_sync values along with
    aggregated summary statistics (average, min, max, stability score).
    No ML inference is performed — aggregation only.
    """
    data = await service.get_acoustic_analytics_data(tank_id, start_time, end_time)
    series = [
        AcousticSeriesPoint(
            time=pt["time"],
            acoustic_db=pt["acoustic_db"],
            bio_acoustic_sync=pt["bio_acoustic_sync"],
        )
        for pt in data["series"]
    ]
    summary_raw = data["summary"]
    return BaseResponse(
        data=AcousticHistoryResponse(
            tankId=tank_id,
            series=series,
            summary=AcousticSummary(
                average_db=summary_raw["average_db"],
                min_db=summary_raw["min_db"],
                max_db=summary_raw["max_db"],
                stability_score=summary_raw["stability_score"],
            ),
        )
    )
