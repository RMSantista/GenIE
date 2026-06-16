"""Health check endpoint for API status verification."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from spec.api.v1.dependencies import get_app_settings
from spec.core.config import Settings

router = APIRouter()


@router.get("/health")
async def health_check(settings: Settings = Depends(get_app_settings)) -> dict:
    """Health check endpoint.

    Returns the current health status of the API and its configuration.

    Args:
        settings: Application settings (injected via Depends)

    Returns:
        dict: Health status with timestamp, version and environment

    Example:
        GET /api/v1/health
        Response: {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": "2026-06-11T10:30:45.123456+00:00",
            "environment": "development"
        }
    """

    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.environment,
    }
