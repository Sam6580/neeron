# app/api/v1/router.py

from fastapi import APIRouter, Depends

from app.api.v1 import (
    health,
    dashboard,
    farms,
    tanks,
    telemetry,
    predictions,
    recommendations,
    alerts,
    biosecurity,
    settings,
    users,
    insights,
    models,
    auth,
    ui,
)
from app.api.v1.dependencies.auth import get_current_active_user

api_router = APIRouter()

# Dependency applied to every authenticated data route.
_protected = [Depends(get_current_active_user)]

# Public routes (no authentication required)
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Authenticated routes (valid JWT access token required)
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"], dependencies=_protected)
api_router.include_router(farms.router, prefix="/farms", tags=["Farms"], dependencies=_protected)
api_router.include_router(tanks.router, prefix="/tanks", tags=["Tanks"], dependencies=_protected)
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["Telemetry"], dependencies=_protected)
api_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"], dependencies=_protected)
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"], dependencies=_protected)
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"], dependencies=_protected)
api_router.include_router(biosecurity.router, prefix="/biosecurity", tags=["Biosecurity"], dependencies=_protected)
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"], dependencies=_protected)
api_router.include_router(users.router, prefix="/users", tags=["Users"], dependencies=_protected)
api_router.include_router(insights.router, prefix="/insights", tags=["Insights"], dependencies=_protected)
api_router.include_router(models.router, prefix="/models", tags=["Models"], dependencies=_protected)
api_router.include_router(ui.router, prefix="/ui", tags=["UI"], dependencies=_protected)
