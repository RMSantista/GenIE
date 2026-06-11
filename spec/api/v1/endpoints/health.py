"""Health check endpoint for API status verification."""

from datetime import datetime

from fastapi import APIRouter, Depends

from spec.api.v1.dependencies import get_app_settings
from spec.core.config import Settings

router = APIRouter()


class HealthResponse(dict):
    """Health check response model.

    Attributes:
        status: Health status ("healthy" or "unhealthy")
        timestamp: Check timestamp
        version: API version
        environment: Current environment
    """

    pass


@router.get("/health", response_model=dict[str, str | datetime])
async def health_check(settings: Settings = Depends(get_app_settings)) -> dict:
    """Health check endpoint.

    Returns the current health status of the API and its configuration.

    Args:
        settings: Application settings (injected via Depends)

    Returns:
        dict: Health status information including timestamp, version, and environment

    Example:
        GET /api/v1/health
        Response: {
            "status": "healthy",
            "version": "0.1.0",
            "timestamp": "2026-03-05T10:30:45.123456",
            "environment": "development"
        }
    """

    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
    }
