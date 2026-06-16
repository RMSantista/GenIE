"""Models for search library patterns and pattern fields."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PatternField(BaseModel):
    """Definition of a single field in an extraction pattern.

    Attributes:
        field_name: Name of the field to extract
        extraction_method: Method to use ("regex", "instruction", "query")
        pattern: REGEX pattern (for extraction_method="regex")
        instruction: Extraction instruction (for extraction_method="instruction")
        validation: Validation pattern (optional)
        post_process: Post-processing function (optional)
    """

    field_name: str = Field(..., description="Field name")
    extraction_method: str = Field(..., description="regex, instruction, or query")
    pattern: Optional[str] = Field(None, description="REGEX pattern")
    instruction: Optional[str] = Field(None, description="Extraction instruction")
    validation: Optional[str] = Field(None, description="Validation pattern")
    post_process: Optional[str] = Field(None, description="Post-processing")


class SearchPattern(BaseModel):
    """A stored pattern in the search library.

    Attributes:
        layout_id: Unique ID for this layout pattern
        config_id: Configuration ID this pattern belongs to
        fingerprint: Layout fingerprint (structure hash)
        created_at: Pattern creation timestamp
        last_used: Last use timestamp
        success_rate: Success rate (0.0-1.0), moving average
        use_count: Number of times pattern was used
        fields: List of pattern fields
    """

    layout_id: str = Field(..., description="Layout ID")
    config_id: str = Field(..., description="Configuration ID")
    fingerprint: str = Field(..., description="Layout fingerprint")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_used: datetime = Field(..., description="Last use timestamp")
    success_rate: float = Field(1.0, ge=0.0, le=1.0, description="Success rate")
    use_count: int = Field(0, ge=0, description="Use count")
    fields: List[PatternField] = Field(..., description="Pattern fields")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "layout_id": "layout_abc123",
                "config_id": "config_001",
                "fingerprint": "a1b2c3d4e5f6g7h8",
                "created_at": "2026-03-05T10:00:00",
                "last_used": "2026-03-05T15:30:00",
                "success_rate": 0.95,
                "use_count": 42,
                "fields": [
                    {
                        "field_name": "patient_name",
                        "extraction_method": "regex",
                        "pattern": r"Patient:\s*([^\n]+)",
                        "validation": r".{2,}",
                        "post_process": None,
                    }
                ],
            }
        }


class LibraryMetadata(BaseModel):
    """Metadata about the search library.

    Attributes:
        version: Library version
        total_patterns: Total number of patterns
        last_updated: Last update timestamp
    """

    version: str = Field(..., description="Library version")
    total_patterns: int = Field(..., description="Total patterns")
    last_updated: datetime = Field(..., description="Last update")
