# app/api/v1/predictions.py

from typing import List, Any, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import get_prediction_service
from app.services.prediction_service import PredictionService
from app.schemas.base import BaseResponse

router = APIRouter()


@router.get("/disease", response_model=BaseResponse[List[Dict[str, Any]]])
async def get_disease_predictions(
    tank_id: UUID,
    service: PredictionService = Depends(get_prediction_service),
):
    """
    Retrieves the latest disease outbreak risk forecasts for a specific tank.
    """
    preds = await service.get_latest_predictions(tank_id)
    d = preds.get("disease")
    if not d:
        return BaseResponse(data=[])

    # Convert model attributes to match front-end expectation
    prob_val = getattr(d, "probability", None)
    if prob_val is None:
        prob_val = float(d.risk_score) / 10.0 if getattr(d, "risk_score", None) is not None else 0.0

    pathogen_id_val = getattr(d, "pathogen_id", None)
    
    scientific_name_val = getattr(d, "pathogen", None)
    if scientific_name_val is None:
        scientific_name_val = getattr(d, "disease_name", "Unknown")

    return BaseResponse(
        data=[
            {
                "tankId": d.tank_id,
                "pathogenId": pathogen_id_val,
                "scientificName": scientific_name_val,
                "probability": float(prob_val),
                "confidenceLow": float(prob_val) * 0.9,
                "confidenceHigh": float(prob_val) * 1.1,
                "time": d.time,
            }
        ]
    )


@router.get("/mortality", response_model=BaseResponse[Dict[str, Any]])
async def get_mortality_predictions(
    tank_id: UUID,
    service: PredictionService = Depends(get_prediction_service),
):
    """
    Retrieves the latest predicted loss ratios and confidence intervals.
    """
    preds = await service.get_latest_predictions(tank_id)
    m = preds.get("mortality")
    if not m:
        return BaseResponse(
            data={
                "tankId": tank_id,
                "mortality_rate": 0.0,
                "predicted_loss_kg": 0.0,
                "confidence": 1.0,
                "time": None,
            }
        )

    return BaseResponse(
        data={
            "tankId": m.tank_id,
            "mortality_rate": float(m.mortality_rate) if m.mortality_rate is not None else 0.0,
            "predicted_loss_kg": float(m.predicted_loss_kg) if m.predicted_loss_kg is not None else 0.0,
            "confidence": float(m.confidence) if m.confidence is not None else 0.0,
            "time": m.time,
        }
    )


@router.get("/harvest", response_model=BaseResponse[Dict[str, Any]])
async def get_harvest_predictions(
    tank_id: UUID,
    service: PredictionService = Depends(get_prediction_service),
):
    """
    Retrieves the optimal harvest date projections and gross revenue estimations.
    """
    preds = await service.get_latest_predictions(tank_id)
    h = preds.get("harvest")
    if not h:
        return BaseResponse(data={})

    return BaseResponse(
        data={
            "tankId": h.tank_id,
            "projectedHarvestDate": h.projected_harvest_date,
            "projectedBiomassKg": float(h.projected_biomass) if h.projected_biomass is not None else 0.0,
            "avgWeightG": float(h.avg_weight_g) if h.avg_weight_g is not None else 0.0,
            "fcr": float(h.fcr) if h.fcr is not None else 0.0,
            "revenueProjectionUsd": float(h.revenue_projection_usd) if h.revenue_projection_usd is not None else None,
            "confidence": float(h.confidence) if h.confidence is not None else 0.0,
            "time": h.time,
        }
    )
