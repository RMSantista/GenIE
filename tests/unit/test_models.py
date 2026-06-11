"""Tests for Pydantic models."""

from datetime import datetime

import pytest

from spec.models.config import (
    InputConfig,
    LLMConfig,
)
from spec.models.extraction import ExtractionRequest, ExtractionResponse
from spec.models.library import PatternField, SearchPattern
from spec.models.output import FieldDefinition, OutputSchema


class TestExtractionRequest:
    """Tests for ExtractionRequest model."""

    def test_extraction_request_valid(self):
        """Test creating valid extraction request."""
        request = ExtractionRequest(
            config_id="config_001",
            source={"type": "text", "content": "test content"},
        )

        assert request.config_id == "config_001"
        assert request.source["type"] == "text"
        assert request.force_llm is False

    def test_extraction_request_required_fields(self):
        """Test extraction request with missing required fields."""
        with pytest.raises(ValueError):
            ExtractionRequest(config_id="config_001")


class TestExtractionResponse:
    """Tests for ExtractionResponse model."""

    def test_extraction_response_valid(self):
        """Test creating valid extraction response."""
        response = ExtractionResponse(
            extraction_id="ext_123",
            status="success",
            method_used="llm",
            data={"field1": "value1"},
            confidence=0.95,
            processing_time_ms=1000,
        )

        assert response.extraction_id == "ext_123"
        assert response.status == "success"
        assert response.confidence == 0.95

    def test_extraction_response_confidence_bounds(self):
        """Test confidence score validation."""
        with pytest.raises(ValueError):
            ExtractionResponse(
                extraction_id="ext_123",
                status="success",
                method_used="llm",
                data={},
                confidence=1.5,  # Invalid: > 1.0
                processing_time_ms=1000,
            )


class TestInputConfig:
    """Tests for InputConfig model."""

    def test_input_config_text_type(self):
        """Test text input config."""
        config = InputConfig(type="text")
        assert config.type == "text"
        assert config.access_mode == "local_secure"

    def test_input_config_pdf_type(self):
        """Test PDF input config."""
        config = InputConfig(type="pdf", source="/path/to/file.pdf")
        assert config.type == "pdf"
        assert config.source == "/path/to/file.pdf"


class TestLLMConfig:
    """Tests for LLMConfig model."""

    def test_llm_config_defaults(self):
        """Test LLM config with defaults."""
        config = LLMConfig()
        assert config.provider == "anthropic"
        assert config.temperature == 0.0
        assert config.max_tokens == 4096

    def test_llm_config_temperature_bounds(self):
        """Test temperature validation."""
        with pytest.raises(ValueError):
            LLMConfig(temperature=1.5)  # Invalid: > 1.0


class TestPatternField:
    """Tests for PatternField model."""

    def test_pattern_field_regex(self):
        """Test regex pattern field."""
        field = PatternField(
            field_name="name",
            extraction_method="regex",
            pattern=r"Name:\s*([^\n]+)",
        )

        assert field.field_name == "name"
        assert field.extraction_method == "regex"


class TestSearchPattern:
    """Tests for SearchPattern model."""

    def test_search_pattern_valid(self):
        """Test creating valid search pattern."""
        now = datetime.utcnow()
        pattern = SearchPattern(
            layout_id="layout_123",
            config_id="config_001",
            fingerprint="abc123def456",
            created_at=now,
            last_used=now,
            success_rate=0.95,
            use_count=10,
            fields=[
                PatternField(
                    field_name="name",
                    extraction_method="regex",
                    pattern=r"Name:\s*([^\n]+)",
                )
            ],
        )

        assert pattern.layout_id == "layout_123"
        assert pattern.success_rate == 0.95
        assert len(pattern.fields) == 1


class TestFieldDefinition:
    """Tests for FieldDefinition model."""

    def test_field_definition_string(self):
        """Test string field definition."""
        field = FieldDefinition(name="patient_name", type="string", required=True)
        assert field.name == "patient_name"
        assert field.type == "string"
        assert field.required is True

    def test_field_definition_date(self):
        """Test date field definition."""
        field = FieldDefinition(name="exam_date", type="date")
        assert field.type == "date"


class TestOutputSchema:
    """Tests for OutputSchema model."""

    def test_output_schema_valid(self):
        """Test creating valid output schema."""
        schema = OutputSchema(
            fields={
                "name": FieldDefinition(name="name", type="string"),
                "age": FieldDefinition(name="age", type="integer"),
            },
            primary_key="name",
        )

        assert len(schema.fields) == 2
        assert schema.primary_key == "name"
