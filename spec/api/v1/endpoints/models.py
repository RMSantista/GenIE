"""Model catalog endpoint: lists selectable models with key status."""

import logging

from fastapi import APIRouter

from spec.core.security import get_key_vault
from spec.models.webapp import ModelInfo
from spec.webapp.catalog import MODELS

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[ModelInfo])
async def list_models() -> list[ModelInfo]:
    """List the model catalog with per-provider key status.

    The API key itself is never returned — only a boolean and a masked
    preview (first 4 characters).

    Returns:
        list[ModelInfo]: Catalog entries with has_key/masked_key
    """

    vault = get_key_vault()
    result = []
    for model in MODELS:
        masked = vault.masked(model["provider"])
        result.append(
            ModelInfo(
                id=model["id"],
                provider=model["provider"],
                provider_label=model["provider_label"],
                label=model["label"],
                note=model["note"],
                has_key=masked is not None,
                masked_key=masked,
            )
        )
    return result
