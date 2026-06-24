# app/schemas/settings.py

from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SensorStatusResponse(BaseModel):
    sensor_id: UUID
    hardware_id: str
    type: str
    status: str
    calibration_due_at: Optional[datetime] = None
    tank_id: Optional[UUID] = None


class ThresholdConfigResponse(BaseModel):
    id: UUID
    farm_id: UUID
    metric_name: str
    warning_min: float
    warning_max: float
    critical_min: float
    critical_max: float
    updated_by: Optional[UUID] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class ThresholdUpdatePayload(BaseModel):
    farmId: UUID
    metricName: str
    warningMin: float
    warningMax: float
    criticalMin: float
    criticalMax: float
