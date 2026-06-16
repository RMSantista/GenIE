"""Dependency injection for FastAPI endpoints.

This module provides factory functions for creating and injecting dependencies
into endpoint handlers using FastAPI's Depends() mechanism.
"""

import logging

from fastapi import Depends

from spec.core.config import Settings, get_settings
from spec.core.config_store import ConfigStore
from spec.extraction.engine import ExtractionEngine
from spec.extraction.llm.factory import LLMProviderFactory
from spec.output.manager import OutputManager
from spec.search_library.json_storage import JSONStorage


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


def get_search_library(settings: Settings = Depends(get_app_settings)) -> JSONStorage:
    """Get search library instance.

    Args:
        settings: Application settings (injected)

    Returns:
        JSONStorage: Search library instance
    """
    return JSONStorage(storage_path=settings.search_library_path)


def get_llm_factory(
    settings: Settings = Depends(get_app_settings),
) -> LLMProviderFactory:
    """Get LLM provider factory.

    Args:
        settings: Application settings (injected)

    Returns:
        LLMProviderFactory: Factory for creating LLM providers
    """
    return LLMProviderFactory(settings=settings)


def get_output_manager() -> OutputManager:
    """Get output manager instance.

    Returns:
        OutputManager: Output manager for formatting results
    """
    return OutputManager()


def get_config_store(settings: Settings = Depends(get_app_settings)) -> ConfigStore:
    """Get extraction configuration store.

    Args:
        settings: Application settings (injected)

    Returns:
        ConfigStore: File-backed configuration store
    """
    return ConfigStore(config_dir=settings.config_dir)


def get_extraction_engine(
    search_library: JSONStorage = Depends(get_search_library),
    llm_factory: LLMProviderFactory = Depends(get_llm_factory),
    output_manager: OutputManager = Depends(get_output_manager),
    config_store: ConfigStore = Depends(get_config_store),
) -> ExtractionEngine:
    """Get extraction engine instance.

    This is the main orchestrator for extraction operations.

    Args:
        search_library: Search library instance (injected)
        llm_factory: LLM provider factory (injected)
        output_manager: Output manager (injected)

    Returns:
        ExtractionEngine: Configured extraction engine
    """
    return ExtractionEngine(
        search_library=search_library,
        llm_factory=llm_factory,
        output_manager=output_manager,
        config_store=config_store,
    )
