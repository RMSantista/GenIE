"""Pydantic models for LLM provider management."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProviderInfo(BaseModel):
    """Metadata and status for an LLM provider.

    Attributes:
        name: Provider identifier ("google", "openai", "anthropic")
        display_name: Human-readable provider name
        default_model: Default model used when none is specified
        available_models: List of supported model identifiers
        is_configured: True if an API key is set for this provider
        is_active: True if this is the currently active provider
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., description="Provider identifier")
    display_name: str = Field(..., description="Human-readable provider name")
    default_model: str = Field(..., description="Default model identifier")
    available_models: list[str] = Field(..., description="Supported model identifiers")
    is_configured: bool = Field(..., description="True if API key is set")
    is_active: bool = Field(..., description="True if this is the active provider")


class ProviderConfigRequest(BaseModel):
    """Request body for configuring a provider at runtime.

    Attributes:
        provider: Provider to activate ("google", "openai", "anthropic")
        api_key: API key for authentication
        model: Optional model override; None uses the provider default
    """

    model_config = ConfigDict(frozen=True)

    provider: str = Field(..., description="Provider name to activate")
    api_key: str = Field(..., description="API key for the provider")
    model: Optional[str] = Field(None, description="Model override (None = default)")


class ProviderConfigResponse(BaseModel):
    """Response after configuring a provider.

    Attributes:
        success: True if configuration succeeded
        provider: Provider that was configured
        model: Active model after configuration
        message: Human-readable status message
    """

    model_config = ConfigDict(frozen=True)

    success: bool = Field(..., description="True if configuration succeeded")
    provider: str = Field(..., description="Configured provider name")
    model: str = Field(..., description="Active model after configuration")
    message: str = Field(..., description="Status message")
