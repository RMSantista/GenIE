"""Router aggregator for API v1 endpoints.

This module combines all v1 endpoint routers into a single router
that can be included in the main FastAPI application.
"""

from fastapi import APIRouter

from spec.api.v1.endpoints.health import router as health_router
from spec.api.v1.endpoints.extract import router as extract_router
from spec.api.v1.endpoints.providers import router as providers_router

# Create main v1 router
router = APIRouter()

# Include all endpoint routers
router.include_router(health_router, tags=["health"])
router.include_router(extract_router, tags=["extraction"])
router.include_router(providers_router, prefix="/providers", tags=["providers"])
