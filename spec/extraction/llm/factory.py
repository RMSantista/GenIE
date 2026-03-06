"""Factory for creating LLM provider instances."""

import logging
from typing import Optional

from spec.core.config import Settings, get_settings
from spec.core.exceptions import InvalidConfig
from spec.extraction.llm.base import BaseLLMProvider
from spec.extraction.llm.anthropic import AnthropicProvider

logger = logging.getLogger(__name__)


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
        provider_name: str = "anthropic",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> BaseLLMProvider:
        """Get or create an LLM provider instance.

        Args:
            provider_name: Provider name ("anthropic", "openai", etc.)
            model: Model identifier (uses default if not provided)
            api_key: API key (uses config if not provided)

        Returns:
            BaseLLMProvider: Provider instance

        Raises:
            InvalidConfig: If provider not supported or API key missing
        """

        # Use defaults from settings if not provided
        if model is None:
            model = "claude-sonnet-4-20250514"
        if api_key is None:
            api_key = self.settings.anthropic_api_key

        # Create cache key
        cache_key = f"{provider_name}:{model}:{api_key[:10] if api_key else 'none'}"

        # Return cached provider if available
        if cache_key in self._providers:
            return self._providers[cache_key]

        # Create new provider based on name
        if provider_name.lower() == "anthropic":
            if not api_key:
                raise InvalidConfig("Anthropic API key is required")
            provider = AnthropicProvider(api_key=api_key, model=model)
            logger.debug(f"Created AnthropicProvider with model: {model}")

        elif provider_name.lower() == "openai":
            raise InvalidConfig("OpenAI provider not yet implemented (Phase 2)")

        elif provider_name.lower() == "google":
            raise InvalidConfig("Google provider not yet implemented (Phase 3)")

        else:
            raise InvalidConfig(f"Unknown LLM provider: {provider_name}")

        # Cache the provider
        self._providers[cache_key] = provider

        return provider
