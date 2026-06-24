# app/schemas/telemetry.py

from uuid import UUID
from datetime import datetime
from typing import Dict, Any, List
from pydantic import BaseModel


class TelemetryMetrics(BaseModel):
    temperature: float
    ph: float
    dissolvedOxygen: float
    salinity: float
    ammonia: float
    turbidity: float


class TelemetryLatestResponse(BaseModel):
    tankId: UUID
    capturedAt: datetime
    metrics: TelemetryMetrics


class TelemetryHistoryPoint(BaseModel):
    timestamp: datetime
    value: float
    sensor_id: UUID


class TelemetryHistoryResponse(BaseModel):
    tankId: UUID
    history: List[TelemetryHistoryPoint]
