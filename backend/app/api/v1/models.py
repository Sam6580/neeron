# app/api/v1/models.py

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.deps import get_settings_service
from app.services.settings_service import SettingsService
from app.repositories.base import BaseRepository
from app.models.ai_model import AiModel
from app.schemas.base import BaseResponse
from app.schemas.model import AiModelResponse, ModelHealthMetricResponse

router = APIRouter()


@router.get("", response_model=BaseResponse[List[AiModelResponse]])
async def list_models(
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves the catalog of deployed AI models.
    """
    repo = BaseRepository(AiModel, db)
    models = await repo.get_multi(limit=100)
    return BaseResponse(data=models)


@router.get("/health", response_model=BaseResponse[List[ModelHealthMetricResponse]])
async def get_models_health(
    service: SettingsService = Depends(get_settings_service),
):
    """
    Retrieves performance metrics diagnostics (accuracy, F1, quality scores) for all models.
    """
    health_metrics = await service.get_model_health()
    return BaseResponse(
        data=[
            ModelHealthMetricResponse(
                id=m["id"],
                recorded_at=m["recorded_at"],
                model_version_id=m["model_version_id"],
                accuracy=m["accuracy"],
                precision=m["precision"],
                recall=m["recall"],
                f1_score=m["f1_score"],
                data_quality_score=m["data_quality_score"],
                agreement_score=m["agreement_score"],
            )
            for m in health_metrics
        ]
    )


@router.get("/{model_id}", response_model=BaseResponse[AiModelResponse])
async def get_model_detail(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves details for a single AI model by ID.
    """
    repo = BaseRepository(AiModel, db)
    model = await repo.get(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI Model not found with ID {model_id}",
        )
    return BaseResponse(data=model)
