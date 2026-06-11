"""CRUD endpoints for extraction configurations (Phase 1, Stage 1.4.3)."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from spec.api.v1.dependencies import get_config_store
from spec.core.config_store import ConfigStore
from spec.core.exceptions import InvalidConfig
from spec.models.config import ExtractionConfig

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=ExtractionConfig, status_code=201)
async def create_config(
    config: ExtractionConfig,
    store: ConfigStore = Depends(get_config_store),
) -> ExtractionConfig:
    """Create an extraction configuration.

    Args:
        config: Configuration document
        store: Config store (injected)

    Returns:
        ExtractionConfig: Stored configuration

    Raises:
        HTTPException: 409 if the id already exists, 400 for invalid ids
    """

    try:
        if store.get(config.extraction_id) is not None:
            raise HTTPException(
                status_code=409,
                detail=f"Configuração '{config.extraction_id}' já existe (use PUT).",
            )
        return store.save(config)
    except InvalidConfig as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[ExtractionConfig])
async def list_configs(
    store: ConfigStore = Depends(get_config_store),
) -> list[ExtractionConfig]:
    """List all extraction configurations.

    Args:
        store: Config store (injected)

    Returns:
        list[ExtractionConfig]: Stored configurations
    """

    return store.list()


@router.get("/{config_id}", response_model=ExtractionConfig)
async def get_config(
    config_id: str,
    store: ConfigStore = Depends(get_config_store),
) -> ExtractionConfig:
    """Retrieve a configuration by id.

    Args:
        config_id: Configuration identifier
        store: Config store (injected)

    Returns:
        ExtractionConfig: Stored configuration

    Raises:
        HTTPException: 404 when absent, 400 for invalid ids
    """

    try:
        config = store.get(config_id)
    except InvalidConfig as e:
        raise HTTPException(status_code=400, detail=str(e))
    if config is None:
        raise HTTPException(
            status_code=404, detail=f"Configuração '{config_id}' não encontrada"
        )
    return config


@router.put("/{config_id}", response_model=ExtractionConfig)
async def update_config(
    config_id: str,
    config: ExtractionConfig,
    store: ConfigStore = Depends(get_config_store),
) -> ExtractionConfig:
    """Create or update a configuration.

    Args:
        config_id: Configuration identifier (must match the body)
        config: Configuration document
        store: Config store (injected)

    Returns:
        ExtractionConfig: Stored configuration

    Raises:
        HTTPException: 400 when ids mismatch or are invalid
    """

    if config.extraction_id != config_id:
        raise HTTPException(
            status_code=400,
            detail="extraction_id do corpo difere do id da URL",
        )
    try:
        return store.save(config)
    except InvalidConfig as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{config_id}")
async def delete_config(
    config_id: str,
    store: ConfigStore = Depends(get_config_store),
) -> dict[str, bool]:
    """Delete a configuration.

    Args:
        config_id: Configuration identifier
        store: Config store (injected)

    Returns:
        dict: {"deleted": true}

    Raises:
        HTTPException: 404 when absent
    """

    try:
        deleted = store.delete(config_id)
    except InvalidConfig as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not deleted:
        raise HTTPException(
            status_code=404, detail=f"Configuração '{config_id}' não encontrada"
        )
    return {"deleted": True}
