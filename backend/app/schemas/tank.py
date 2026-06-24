# app/schemas/tank.py

from uuid import UUID
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class TankResponse(BaseModel):
    id: UUID
    name: str = Field(..., max_length=100)
    type: str = Field(..., max_length=50)
    volumeM3: float
    maxBiomassKg: float
    species: str = Field(..., max_length=100)
    currentBiomassKg: float
    healthStatus: str


class TankDetailResponse(BaseModel):
    id: UUID
    name: str
    type: str
    volumeM3: float
    maxBiomassKg: float
    species: str
    digitalTwinConfig: Dict[str, Any]
    created_at: datetime


class TankStability(BaseModel):
    temperature: str
    dissolved_oxygen: str
    ph: str


class TankAverages7d(BaseModel):
    temperature: Optional[float] = None
    dissolved_oxygen: Optional[float] = None
    ph: Optional[float] = None


class TankHealthResponse(BaseModel):
    tank_id: UUID
    psi_score: Optional[float] = None
    stress_level: str
    psi_generated_at: Optional[datetime] = None
    stability: TankStability
    averages_7d: Optional[TankAverages7d] = None


class TankEnvironmentSnapshotResponse(BaseModel):
    temperature: Optional[float] = None
    ph: Optional[float] = None
    dissolved_oxygen: Optional[float] = None
    salinity: Optional[float] = None
    ammonia: Optional[float] = None
    turbidity: Optional[float] = None
    captured_at: Optional[datetime] = None


class PredictionDetail(BaseModel):
    id: Optional[UUID] = None
    score: Optional[float] = None
    level: Optional[str] = None
    generated_at: Optional[datetime] = None
    pathogen: Optional[str] = None
    probability: Optional[float] = None
    risk_level: Optional[str] = None
    mortality_rate: Optional[float] = None
    predicted_loss_kg: Optional[float] = None
    confidence: Optional[float] = None
    projected_harvest_date: Optional[datetime] = None
    projected_biomass: Optional[float] = None
    avg_weight_g: Optional[float] = None
    fcr: Optional[float] = None
    revenue_projection_usd: Optional[float] = None
    time: Optional[datetime] = None


class TankPredictionsResponse(BaseModel):
    psi: Optional[Dict[str, Any]] = None
    disease: Optional[Dict[str, Any]] = None
    mortality: Optional[Dict[str, Any]] = None
    harvest: Optional[Dict[str, Any]] = None
