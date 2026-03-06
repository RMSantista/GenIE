"""Document extraction endpoint."""

from fastapi import APIRouter, Depends
import logging

from spec.api.v1.dependencies import get_extraction_engine
from spec.extraction.engine import ExtractionEngine
from spec.models.extraction import ExtractionRequest, ExtractionResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/extract", response_model=ExtractionResponse)
async def extract_data(
    request: ExtractionRequest,
    engine: ExtractionEngine = Depends(get_extraction_engine),
) -> ExtractionResponse:
    """Extract structured data from a document.

    This endpoint processes a document source and extracts structured
    data according to the specified configuration.

    Args:
        request: Extraction request with config and source
        engine: Extraction engine (injected)

    Returns:
        ExtractionResponse: Extracted data and metadata

    Example:
        POST /api/v1/extract
        {
            "config_id": "medical_reports_v1",
            "source": {
                "type": "text",
                "content": "Patient: John Doe, Age: 35..."
            }
        }

        Response:
        {
            "extraction_id": "ext_abc123def456",
            "status": "success",
            "method_used": "llm",
            "data": {"patient": "John Doe", "age": 35},
            "confidence": 0.95,
            "processing_time_ms": 1250,
            "layout_fingerprint": "a1b2c3d4e5f6g7h8"
        }
    """

    logger.info(
        f"Processing extraction request for config: {request.config_id}"
    )

    # Call the extraction engine
    response = await engine.extract(request)

    logger.debug(f"Extraction completed: {response.extraction_id}")

    return response
