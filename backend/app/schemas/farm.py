# app/schemas/farm.py

from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class FarmResponse(BaseModel):
    id: UUID
    name: str = Field(..., max_length=100)
    latitude: float
    longitude: float
    timezone: str = Field(..., max_length=50)
    carryingCapacityKg: float

    model_config = ConfigDict(from_attributes=True)
