"""FastAPI application entry point for GENIE framework."""

import shutil
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from spec.api.v1.router import router as v1_router
from spec.core.config import get_settings
from spec.core.logging_config import get_logger, setup_logging

# Setup logging before anything else
settings = get_settings()
logger_instance = setup_logging(settings.log_level)
logger = get_logger(__name__)


def _cleanup_stale_dirs(root: Path, max_age_hours: int) -> None:
    """Remove stale upload/output batch directories left by old runs.

    Args:
        root: Directory containing per-batch subdirectories
        max_age_hours: Age threshold for removal
    """

    if not root.is_dir():
        return
    cutoff = time.time() - max_age_hours * 3600
    for batch_dir in root.iterdir():
        try:
            if batch_dir.is_dir() and batch_dir.stat().st_mtime < cutoff:
                shutil.rmtree(batch_dir, ignore_errors=True)
                logger.debug(f"Removed stale directory: {batch_dir}")
        except OSError:  # pragma: no cover - best-effort housekeeping
            continue


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for app startup and shutdown.

    Args:
        app: FastAPI application instance

    Yields:
        None

    This handles initialization and cleanup during app startup and shutdown.
    """

    # Startup
    logger.info(f"Starting GENIE API in {settings.environment} mode")
    logger.debug(f"Log level: {settings.log_level}")
    logger.debug(f"API: {settings.api_host}:{settings.api_port}")
    _cleanup_stale_dirs(Path(settings.uploads_dir), max_age_hours=24)
    _cleanup_stale_dirs(Path(settings.outputs_dir), max_age_hours=24)

    yield

    # Shutdown
    logger.info("Shutting down GENIE API")


# Create FastAPI application
app = FastAPI(
    title="GENIE - Generic Extractor of Information Engine",
    description="LLM-powered data extraction framework",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS: explicit origin allowlist (the SPA is served same-origin,
# so this only matters for external consumers like TabEx during development).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "Last-Event-ID"],
)

# Include API routers
app.include_router(v1_router, prefix="/api/v1")

# Serve the SPA (spec/web) at the root path
_WEB_DIR = Path(__file__).parent / "web"
if _WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=_WEB_DIR, html=True), name="web")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "spec.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
    )
