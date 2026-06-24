# app/schemas/telemetry.py

from uuid import UUID
from datetime import datetime
from typing import Any, Dict, List, Optional
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


# ── Hydrophone / Bio-Acoustic schemas ────────────────────────────────────────

class AcousticActivityResponse(BaseModel):
    """Real-time acoustic status for a single tank."""
    tankId: UUID
    current_db: float
    bio_acoustic_sync: float
    status: str


class AcousticSeriesPoint(BaseModel):
    """A single point in the acoustic time-series chart."""
    time: datetime
    acoustic_db: float
    bio_acoustic_sync: float


class AcousticSummary(BaseModel):
    """Aggregated acoustic statistics over a time range."""
    average_db: float
    min_db: float
    max_db: float
    stability_score: float


class AcousticHistoryResponse(BaseModel):
    """Analytics-ready acoustic history payload."""
    tankId: UUID
    series: List[AcousticSeriesPoint]
    summary: AcousticSummary
