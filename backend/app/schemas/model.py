# app/schemas/model.py

from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AiModelResponse(BaseModel):
    id: UUID
    name: str = Field(..., max_length=100)
    algorithm: str = Field(..., max_length=100)
    status: str = Field(..., max_length=50)
    owner: str = Field(..., max_length=100)
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModelVersionResponse(BaseModel):
    id: UUID
    model_id: UUID
    version: str = Field(..., max_length=50)
    artifact_uri: str = Field(..., max_length=255)
    deployed_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class ModelHealthMetricResponse(BaseModel):
    id: UUID
    recorded_at: datetime
    model_version_id: UUID
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    data_quality_score: Optional[float] = None
    agreement_score: Optional[float] = None

    class Config:
        from_attributes = True
