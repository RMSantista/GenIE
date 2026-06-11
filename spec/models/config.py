"""Configuration models for extraction, input, output, and LLM settings."""

from typing import Dict, Optional

from pydantic import BaseModel, Field


class InputConfig(BaseModel):
    """Input configuration for source documents.

    Attributes:
        type: Source type ("text", "file", "pdf", etc.)
        source: Optional source path or identifier
        access_mode: Access mode for secure reading
    """

    type: str = Field(..., description="Source type")
    source: Optional[str] = Field(None, description="Source path/identifier")
    access_mode: str = Field("local_secure", description="Access mode")


class OutputConfig(BaseModel):
    """Output configuration for extraction results.

    Attributes:
        type: Output format ("json", "csv", "xlsx", etc.)
        destination: Optional output path
        schema: Optional output schema definition
        auto_adapt: Auto-adapt schema to new fields
    """

    type: str = Field("json", description="Output format")
    destination: Optional[str] = Field(None, description="Output path")
    schema: Optional[Dict[str, str]] = Field(None, description="Schema definition")
    auto_adapt: bool = Field(True, description="Auto-adapt schema")


class LLMConfig(BaseModel):
    """LLM provider configuration.

    Attributes:
        provider: LLM provider name ("anthropic", "openai")
        model: Model identifier
        api_key_ref: Reference to API key (env var or stored)
        fallback_to_ocr: Fallback to OCR if LLM fails
        temperature: Generation temperature (0.0-1.0)
        max_tokens: Maximum tokens in response
    """

    provider: str = Field("anthropic", description="LLM provider")
    model: str = Field("claude-sonnet-4-20250514", description="Model ID")
    api_key_ref: Optional[str] = Field(None, description="API key reference")
    fallback_to_ocr: bool = Field(False, description="Fallback to OCR")
    temperature: float = Field(0.0, ge=0.0, le=1.0, description="Temperature")
    max_tokens: int = Field(4096, ge=1, description="Max tokens")


class BehaviorConfig(BaseModel):
    """Extraction behavior configuration.

    Attributes:
        use_search_library: Use search library for pattern matching
        auto_create_patterns: Auto-create patterns after successful extraction
        layout_independent: Extract regardless of document layout
        update_on_change: Update patterns when data changes
    """

    use_search_library: bool = Field(True, description="Use search library")
    auto_create_patterns: bool = Field(True, description="Auto-create patterns")
    layout_independent: bool = Field(True, description="Layout-independent")
    update_on_change: bool = Field(True, description="Update on change")


class ExtractionConfig(BaseModel):
    """Complete extraction configuration.

    Attributes:
        extraction_id: Unique configuration identifier
        name: Human-readable name
        input: Input configuration
        output: Output configuration
        llm: LLM configuration
        behavior: Behavior configuration
        extraction_instructions: Instructions for data extraction
    """

    extraction_id: str = Field(..., description="Config ID")
    name: Optional[str] = Field(None, description="Config name")
    input: InputConfig = Field(..., description="Input config")
    output: OutputConfig = Field(..., description="Output config")
    llm: LLMConfig = Field(..., description="LLM config")
    behavior: BehaviorConfig = Field(..., description="Behavior config")
    extraction_instructions: str = Field(..., description="Extraction instructions")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "extraction_id": "config_001",
                "name": "Medical Report Extraction",
                "input": {
                    "type": "pdf",
                    "source": "/uploads/reports",
                    "access_mode": "local_secure",
                },
                "output": {
                    "type": "json",
                    "destination": "/outputs",
                    "auto_adapt": True,
                },
                "llm": {
                    "provider": "anthropic",
                    "model": "claude-sonnet-4-20250514",
                    "temperature": 0.0,
                    "max_tokens": 4096,
                },
                "behavior": {
                    "use_search_library": True,
                    "auto_create_patterns": True,
                    "layout_independent": True,
                    "update_on_change": True,
                },
                "extraction_instructions": "Extract patient name, age, and test results.",
            }
        }
