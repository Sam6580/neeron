# app/schemas/alert.py

from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class AlertResponse(BaseModel):
    id: UUID
    time: datetime
    tank_id: UUID
    sensor_id: Optional[UUID] = None
    type: str = Field(..., max_length=100)
    severity: str = Field(..., max_length=50)
    status: str = Field(..., max_length=50)
    message: str
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)
