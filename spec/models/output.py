"""Models for output schema definition and field definitions."""

from typing import Dict, Optional

from pydantic import BaseModel, Field


class FieldDefinition(BaseModel):
    """Definition of a single output field.

    Attributes:
        name: Field name
        type: Field type (string, integer, date, etc.)
        required: Whether field is required
    """

    name: str = Field(..., description="Field name")
    type: str = Field(..., description="Field type")
    required: bool = Field(False, description="Is required")


class OutputSchema(BaseModel):
    """Output schema definition.

    Attributes:
        fields: Dictionary of field name to FieldDefinition
        primary_key: Optional primary key field
    """

    fields: Dict[str, FieldDefinition] = Field(..., description="Field definitions")
    primary_key: Optional[str] = Field(None, description="Primary key field")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "fields": {
                    "patient_id": {
                        "name": "patient_id",
                        "type": "string",
                        "required": True,
                    },
                    "patient_name": {
                        "name": "patient_name",
                        "type": "string",
                        "required": True,
                    },
                    "exam_date": {
                        "name": "exam_date",
                        "type": "date",
                        "required": True,
                    },
                    "result": {"name": "result", "type": "string", "required": False},
                },
                "primary_key": "patient_id",
            }
        }
