# app/schemas/recommendation.py

from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RecommendationResponse(BaseModel):
    id: UUID
    tankId: UUID
    action: str = Field(..., max_length=200)
    confidence: float
    priority: str = Field(..., max_length=50)
    expectedOutcome: str
    status: str = Field(..., max_length=50)
    generatedAt: datetime


class RecommendationActionResponse(BaseModel):
    id: UUID
    executed_at: datetime
    recommendation_id: UUID
    user_id: UUID
    action: str
