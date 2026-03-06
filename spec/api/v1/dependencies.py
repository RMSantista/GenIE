"""Dependency injection for FastAPI endpoints.

This module provides factory functions for creating and injecting dependencies
into endpoint handlers using FastAPI's Depends() mechanism.
"""

from typing import Optional
import logging

from spec.core.config import Settings, get_settings
from spec.extraction.engine import ExtractionEngine
from spec.extraction.llm.factory import LLMProviderFactory
from spec.search_library.json_storage import JSONStorage
from spec.output.manager import OutputManager


def get_app_settings() -> Settings:
    """Get application settings.

    Returns:
        Settings: Global settings object
    """
    return get_settings()


def get_logger(name: str = __name__) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (defaults to module name)

    Returns:
        logging.Logger: Configured logger
    """
    return logging.getLogger(name)


def get_search_library(settings: Settings = None) -> JSONStorage:
    """Get search library instance.

    Args:
        settings: Application settings (optional)

    Returns:
        JSONStorage: Search library instance

    Note:
        In a production environment, this could implement caching
        or use a singleton pattern for better performance.
    """
    if settings is None:
        settings = get_settings()
    return JSONStorage(storage_path=settings.search_library_path)


def get_llm_factory(settings: Settings = None) -> LLMProviderFactory:
    """Get LLM provider factory.

    Args:
        settings: Application settings (optional)

    Returns:
        LLMProviderFactory: Factory for creating LLM providers
    """
    if settings is None:
        settings = get_settings()
    return LLMProviderFactory(settings=settings)


def get_output_manager() -> OutputManager:
    """Get output manager instance.

    Returns:
        OutputManager: Output manager for formatting results
    """
    return OutputManager()


def get_extraction_engine(
    search_library: Optional[JSONStorage] = None,
    llm_factory: Optional[LLMProviderFactory] = None,
    output_manager: Optional[OutputManager] = None,
) -> ExtractionEngine:
    """Get extraction engine instance.

    This is the main orchestrator for extraction operations.

    Args:
        search_library: Search library instance
        llm_factory: LLM provider factory
        output_manager: Output manager

    Returns:
        ExtractionEngine: Configured extraction engine

    If any dependency is None, it will be created using its respective
    factory function.
    """
    if search_library is None:
        search_library = get_search_library()
    if llm_factory is None:
        llm_factory = get_llm_factory()
    if output_manager is None:
        output_manager = get_output_manager()

    return ExtractionEngine(
        search_library=search_library,
        llm_factory=llm_factory,
        output_manager=output_manager,
    )
