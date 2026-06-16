"""Pydantic models for extraction requests and responses."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ExtractionRequest(BaseModel):
    """Request model for data extraction operations.

    Attributes:
        config_id: Unique identifier for extraction configuration
        source: Source specification (type, content/path, etc.)
        force_llm: If True, bypass search library and use LLM directly
        options: Optional additional extraction options
    """

    config_id: str = Field(..., description="Configuration identifier")
    source: Dict[str, Any] = Field(..., description="Source specification")
    force_llm: bool = Field(False, description="Force LLM extraction")
    options: Optional[Dict[str, Any]] = Field(None, description="Optional parameters")


class ExtractionResponse(BaseModel):
    """Response model for extraction results.

    Attributes:
        extraction_id: Unique ID for this extraction operation
        status: "success" or "error"
        method_used: "llm" or "search_library"
        data: Extracted structured data
        confidence: Confidence score (0.0 to 1.0)
        processing_time_ms: Time spent on extraction in milliseconds
        layout_fingerprint: Hash of document layout structure
        error: Error message if status is "error"
    """

    extraction_id: str = Field(..., description="Unique extraction ID")
    status: str = Field(..., description="success or error")
    method_used: str = Field(..., description="llm or search_library")
    data: Dict[str, Any] = Field(..., description="Extracted data")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    processing_time_ms: int = Field(..., ge=0, description="Processing time")
    layout_fingerprint: Optional[str] = Field(None, description="Layout hash")
    error: Optional[str] = Field(None, description="Error message if any")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "extraction_id": "ext_123456",
                "status": "success",
                "method_used": "llm",
                "data": {"field1": "value1", "field2": "value2"},
                "confidence": 0.95,
                "processing_time_ms": 1250,
                "layout_fingerprint": "a1b2c3d4e5f6g7h8",
                "error": None,
            }
        }
