"""FastAPI application entry point for GENIE framework."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from spec.core.config import get_settings
from spec.core.logging_config import setup_logging, get_logger
from spec.api.v1.router import router as v1_router

# Setup logging before anything else
settings = get_settings()
logger_instance = setup_logging(settings.log_level)
logger = get_logger(__name__)


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

    yield

    # Shutdown
    logger.info("Shutting down GENIE API")


# Create FastAPI application
app = FastAPI(
    title="GENIE - Generic Extractor of Information Engine",
    description="LLM-powered data extraction framework",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS middleware (allow all for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(v1_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint.

    Returns:
        dict: Welcome message and API version
    """
    return {
        "message": "GENIE - Generic Extractor of Information Engine",
        "version": "0.1.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "spec.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
    )
