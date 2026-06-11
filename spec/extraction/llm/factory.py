"""Factory for creating LLM provider instances."""

import hashlib
import logging
from typing import Optional

from spec.core.config import Settings, get_settings
from spec.core.exceptions import InvalidConfig
from spec.extraction.llm.anthropic import AnthropicProvider
from spec.extraction.llm.base import BaseLLMProvider
from spec.extraction.llm.google import GoogleProvider
from spec.extraction.llm.openai import OpenAIProvider

logger = logging.getLogger(__name__)

_DEFAULT_MODELS: dict[str, str] = {
    "google": "gemini-2.5-flash",
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-6",
}

_SUPPORTED_PROVIDERS = frozenset(_DEFAULT_MODELS.keys())


class LLMProviderFactory:
    """Factory for creating and managing LLM provider instances.

    Attributes:
        settings: Application settings
        _providers: Cache of created provider instances
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """Initialize the factory.

        Args:
            settings: Application settings (default: global settings)
        """

        self.settings = settings or get_settings()
        self._providers: dict[str, BaseLLMProvider] = {}

    def get_provider(
        self,
        provider_name: str = "google",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> BaseLLMProvider:
        """Get or create an LLM provider instance.

        Args:
            provider_name: Provider name ("google", "openai", "anthropic")
            model: Model identifier (uses provider default if not provided)
            api_key: API key (uses settings if not provided)

        Returns:
            BaseLLMProvider: Provider instance

        Raises:
            InvalidConfig: If provider not supported or API key missing
        """

        provider_name = provider_name.lower()

        if provider_name not in _SUPPORTED_PROVIDERS:
            raise InvalidConfig(f"Unknown LLM provider: {provider_name}")

        resolved_model = model or _DEFAULT_MODELS[provider_name]
        resolved_key = api_key or self._get_api_key_for_provider(provider_name)

        if not resolved_key:
            raise InvalidConfig(f"API key for provider '{provider_name}' is not configured")

        # Never put key material (even a prefix) in cache keys: hash it.
        key_digest = hashlib.sha256(resolved_key.encode("utf-8")).hexdigest()[:16]
        cache_key = f"{provider_name}:{resolved_model}:{key_digest}"

        if cache_key in self._providers:
            return self._providers[cache_key]

        provider = self._create_provider(provider_name, resolved_key, resolved_model)
        self._providers[cache_key] = provider

        logger.debug(f"Created {provider_name} provider with model: {resolved_model}")

        return provider

    def get_default_provider(self) -> BaseLLMProvider:
        """Get the currently configured default provider.

        Uses settings.llm_provider and settings.llm_model.

        Returns:
            BaseLLMProvider: Default provider instance

        Raises:
            InvalidConfig: If default provider is not configured
        """

        return self.get_provider(
            provider_name=self.settings.llm_provider,
            model=self.settings.llm_model,
        )

    def set_provider_config(
        self,
        provider: str,
        api_key: str,
        model: Optional[str] = None,
    ) -> None:
        """Update the active provider configuration and clear cached instances.

        Args:
            provider: Provider name ("google", "openai", "anthropic")
            api_key: API key for the provider
            model: Model override (None = use provider default)

        Raises:
            InvalidConfig: If provider is not supported
        """

        provider = provider.lower()

        if provider not in _SUPPORTED_PROVIDERS:
            raise InvalidConfig(f"Unknown LLM provider: {provider}")

        # Persist encrypted (AES-256-GCM) instead of keeping plaintext in settings.
        from spec.core.security import get_key_vault

        get_key_vault().store(provider, api_key)

        self.settings.llm_provider = provider
        self.settings.llm_model = model

        self._providers.clear()

        logger.info(f"Provider configured: {provider}, model: {model or _DEFAULT_MODELS[provider]}")

    @staticmethod
    def list_providers() -> list[dict]:
        """Return metadata about all available providers.

        Returns:
            list[dict]: Provider metadata including name, display name, and models
        """

        return [
            {
                "name": "google",
                "display_name": "Google Gemini",
                "default_model": "gemini-2.5-flash",
                "available_models": ["gemini-2.5-flash", "gemini-2.5-pro"],
            },
            {
                "name": "openai",
                "display_name": "OpenAI GPT",
                "default_model": "gpt-4o",
                "available_models": ["gpt-4o", "gpt-4o-mini"],
            },
            {
                "name": "anthropic",
                "display_name": "Anthropic Claude",
                "default_model": "claude-sonnet-4-6",
                "available_models": [
                    "claude-sonnet-4-6",
                    "claude-haiku-4-5-20251001",
                ],
            },
        ]

    def _get_api_key_for_provider(self, provider_name: str) -> Optional[str]:
        """Resolve API key: encrypted vault first, env settings as fallback.

        Args:
            provider_name: Provider name

        Returns:
            Optional[str]: API key or None if not configured
        """

        # Lazy import to avoid a circular dependency at module load time.
        from spec.core.security import get_key_vault

        vault_key = get_key_vault().get_plaintext(provider_name)
        if vault_key:
            return vault_key

        key_map: dict[str, Optional[str]] = {
            "google": self.settings.google_api_key,
            "openai": self.settings.openai_api_key,
            "anthropic": self.settings.anthropic_api_key,
        }
        return key_map.get(provider_name)

    def _create_provider(
        self,
        provider_name: str,
        api_key: str,
        model: str,
    ) -> BaseLLMProvider:
        """Instantiate a provider by name.

        Args:
            provider_name: Provider name
            api_key: API key
            model: Model identifier

        Returns:
            BaseLLMProvider: New provider instance
        """

        if provider_name == "google":
            return GoogleProvider(api_key=api_key, model=model)
        elif provider_name == "openai":
            return OpenAIProvider(api_key=api_key, model=model)
        elif provider_name == "anthropic":
            return AnthropicProvider(api_key=api_key, model=model)

        raise InvalidConfig(f"Unknown LLM provider: {provider_name}")
