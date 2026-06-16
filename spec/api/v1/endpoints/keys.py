"""Encrypted API key management endpoints.

Security contract:
- Keys are encrypted (AES-256-GCM) before touching disk.
- No endpoint ever returns a key in plaintext — only masked previews.
- Optional live validation performs one minimal LLM call before saving.
"""

import logging

from fastapi import APIRouter, HTTPException

from spec.core.exceptions import InvalidConfig, LLMProviderError
from spec.core.security import get_key_vault
from spec.extraction.llm.factory import LLMProviderFactory
from spec.models.webapp import KeyInfo, KeyRequest
from spec.webapp.catalog import MODELS

logger = logging.getLogger(__name__)

router = APIRouter()

_KNOWN_PROVIDERS = {m["provider"] for m in MODELS}


@router.get("", response_model=list[KeyInfo])
async def list_keys() -> list[KeyInfo]:
    """List providers that have a stored key (masked previews only).

    Returns:
        list[KeyInfo]: Provider + masked preview pairs
    """

    vault = get_key_vault()
    return [
        KeyInfo(provider=provider, masked=vault.masked(provider) or "")
        for provider in sorted(_KNOWN_PROVIDERS)
        if vault.has(provider)
    ]


@router.post("", response_model=KeyInfo)
async def store_key(request: KeyRequest) -> KeyInfo:
    """Validate (optionally) and store a provider API key, encrypted.

    Args:
        request: Provider, plaintext key and validation flag

    Returns:
        KeyInfo: Masked confirmation (the key is never echoed back)

    Raises:
        HTTPException: 400 for unknown provider or failed validation
    """

    provider_name = request.provider.lower().strip()
    if provider_name not in _KNOWN_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Provedor desconhecido '{request.provider}'. "
            f"Suportados: {sorted(_KNOWN_PROVIDERS)}",
        )

    if request.validate_key:
        try:
            provider = LLMProviderFactory().get_provider(
                provider_name=provider_name,
                api_key=request.key,
            )
            await provider.extract(
                content="ping",
                schema={"ok": True},
                instructions='Responda apenas com o JSON {"ok": true}.',
            )
        except (LLMProviderError, InvalidConfig) as e:
            logger.warning("Key validation failed for %s: %s", provider_name, e)
            raise HTTPException(
                status_code=400,
                detail=f"A chave informada foi recusada pelo provedor '{provider_name}'. "
                "Verifique a chave e tente novamente.",
            )
        except Exception as e:  # noqa: BLE001 - network/SDK failures
            logger.error("Unexpected validation error for %s: %s", provider_name, e)
            raise HTTPException(
                status_code=400,
                detail=f"Não foi possível validar a chave do provedor '{provider_name}': {e}",
            )

    masked = get_key_vault().store(provider_name, request.key)
    return KeyInfo(provider=provider_name, masked=masked)


@router.delete("/{provider}")
async def delete_key(provider: str) -> dict[str, bool]:
    """Remove a stored provider key.

    Args:
        provider: Provider name

    Returns:
        dict: {"deleted": bool}
    """

    deleted = get_key_vault().delete(provider.lower().strip())
    if not deleted:
        raise HTTPException(
            status_code=404, detail=f"Sem chave armazenada para '{provider}'"
        )
    return {"deleted": True}
