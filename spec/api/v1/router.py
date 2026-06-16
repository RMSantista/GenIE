"""Router aggregator for API v1 endpoints.

This module combines all v1 endpoint routers into a single router
that can be included in the main FastAPI application.
"""

from fastapi import APIRouter

from spec.api.v1.endpoints.config import router as config_router
from spec.api.v1.endpoints.downloads import router as downloads_router
from spec.api.v1.endpoints.extract import router as extract_router
from spec.api.v1.endpoints.health import router as health_router
from spec.api.v1.endpoints.keys import router as keys_router
from spec.api.v1.endpoints.library import router as library_router
from spec.api.v1.endpoints.models import router as models_router
from spec.api.v1.endpoints.providers import router as providers_router
from spec.api.v1.endpoints.runs import router as runs_router
from spec.api.v1.endpoints.uploads import router as uploads_router

# Create main v1 router
router = APIRouter()

# Include all endpoint routers
router.include_router(health_router, tags=["health"])
router.include_router(extract_router, tags=["extraction"])
router.include_router(providers_router, prefix="/providers", tags=["providers"])
router.include_router(config_router, prefix="/configs", tags=["configs"])
router.include_router(library_router, prefix="/library", tags=["library"])
router.include_router(models_router, prefix="/models", tags=["models"])
router.include_router(keys_router, prefix="/keys", tags=["keys"])
router.include_router(uploads_router, prefix="/uploads", tags=["uploads"])
router.include_router(runs_router, prefix="/runs", tags=["runs"])
router.include_router(downloads_router, prefix="/downloads", tags=["downloads"])
