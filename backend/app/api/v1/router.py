# app/api/v1/router.py

from fastapi import APIRouter

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
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(farms.router, prefix="/farms", tags=["Farms"])
api_router.include_router(tanks.router, prefix="/tanks", tags=["Tanks"])
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["Telemetry"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(biosecurity.router, prefix="/biosecurity", tags=["Biosecurity"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(insights.router, prefix="/insights", tags=["Insights"])
api_router.include_router(models.router, prefix="/models", tags=["Models"])
