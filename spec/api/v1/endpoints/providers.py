"""LLM provider management endpoints."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from spec.api.v1.dependencies import get_llm_factory
from spec.core.exceptions import InvalidConfig, LLMProviderError
from spec.extraction.llm.factory import LLMProviderFactory
from spec.models.provider import ProviderConfigRequest, ProviderConfigResponse, ProviderInfo

logger = logging.getLogger(__name__)

router = APIRouter()

_VALIDATION_PROMPT = "Say OK"
_VALIDATION_SCHEMA: dict[str, Any] = {}
_VALIDATION_INSTRUCTIONS = "Reply with the word OK."


@router.get("", response_model=list[ProviderInfo])
async def list_providers(
    factory: LLMProviderFactory = Depends(get_llm_factory),
) -> list[ProviderInfo]:
    """List all available LLM providers with their current status.

    Returns:
        list[ProviderInfo]: All providers with configuration and active status
    """

    active_provider = factory.settings.llm_provider
    provider_metadata = factory.list_providers()

    result: list[ProviderInfo] = []

    for meta in provider_metadata:
        name = meta["name"]
        api_key = factory._get_api_key_for_provider(name)

        result.append(
            ProviderInfo(
                name=name,
                display_name=meta["display_name"],
                default_model=meta["default_model"],
                available_models=meta["available_models"],
                is_configured=bool(api_key),
                is_active=(name == active_provider),
            )
        )

    return result


@router.get("/active", response_model=ProviderInfo)
async def get_active_provider(
    factory: LLMProviderFactory = Depends(get_llm_factory),
) -> ProviderInfo:
    """Return the currently active LLM provider.

    Returns:
        ProviderInfo: Active provider details

    Raises:
        HTTPException: 404 if no active provider is configured
    """

    active_name = factory.settings.llm_provider
    provider_metadata = factory.list_providers()

    meta = next((m for m in provider_metadata if m["name"] == active_name), None)

    if meta is None:
        raise HTTPException(
            status_code=404,
            detail=f"Active provider '{active_name}' is not a recognized provider",
        )

    api_key = factory._get_api_key_for_provider(active_name)

    return ProviderInfo(
        name=active_name,
        display_name=meta["display_name"],
        default_model=meta["default_model"],
        available_models=meta["available_models"],
        is_configured=bool(api_key),
        is_active=True,
    )


@router.post("/configure", response_model=ProviderConfigResponse)
async def configure_provider(
    request: ProviderConfigRequest,
    factory: LLMProviderFactory = Depends(get_llm_factory),
) -> ProviderConfigResponse:
    """Configure the active LLM provider and validate the API key.

    Tests the API key by making a minimal LLM call before saving it.
    On success the provider becomes the new default for all extractions.

    Args:
        request: Provider name, API key, and optional model override

    Returns:
        ProviderConfigResponse: Configuration result

    Raises:
        HTTPException: 400 if provider is unknown or API key validation fails
    """

    supported = {m["name"] for m in factory.list_providers()}

    if request.provider not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider '{request.provider}'. Supported: {sorted(supported)}",
        )

    try:
        provider = factory.get_provider(
            provider_name=request.provider,
            model=request.model,
            api_key=request.api_key,
        )
    except InvalidConfig as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        logger.debug(f"Validating API key for provider: {request.provider}")
        await provider.extract(
            content=_VALIDATION_PROMPT,
            schema=_VALIDATION_SCHEMA,
            instructions=_VALIDATION_INSTRUCTIONS,
        )
    except LLMProviderError as e:
        logger.warning(f"API key validation failed for {request.provider}: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"API key validation failed for '{request.provider}': {e}",
        )
    except Exception as e:
        logger.error(f"Unexpected error validating {request.provider}: {e}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Could not validate API key for '{request.provider}': {e}",
        )

    factory.set_provider_config(
        provider=request.provider,
        api_key=request.api_key,
        model=request.model,
    )

    provider_metadata = factory.list_providers()
    meta = next(m for m in provider_metadata if m["name"] == request.provider)
    active_model = request.model or meta["default_model"]

    logger.info(f"Provider configured successfully: {request.provider} / {active_model}")

    return ProviderConfigResponse(
        success=True,
        provider=request.provider,
        model=active_model,
        message=f"Provider '{request.provider}' configured successfully with model '{active_model}'",
    )
