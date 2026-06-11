"""PDF document parser."""

import logging
from pathlib import Path
from typing import Any, Dict

from PyPDF2 import PdfReader

from spec.core.exceptions import ExtractionFailed, InvalidConfig

logger = logging.getLogger(__name__)


class PDFParser:
    """Parser for PDF documents.

    Supports native PDFs with text content. Detects scanned PDFs
    (image-only, no extractable text).
    """

    SCANNED_PDF_THRESHOLD = 10  # Chars minimum for a page to be considered native

    @staticmethod
    async def extract_text(
        source: Dict[str, Any],
        detect_scanned: bool = True,
    ) -> str:
        """Extract text from PDF.

        Args:
            source: Source specification with type and path
            detect_scanned: If True, raise error for scanned PDFs

        Returns:
            str: Extracted text from PDF

        Raises:
            InvalidConfig: If source format is invalid
            ExtractionFailed: If PDF is scanned or corrupted
        """

        source_type = source.get("type", "").lower()

        if source_type not in ("file", "pdf"):
            raise InvalidConfig(
                f"PDFParser does not support source type: {source_type}"
            )

        path = source.get("path")
        if not path:
            raise InvalidConfig("PDF source must have 'path' field")

        if not str(path).lower().endswith(".pdf"):
            raise InvalidConfig("File must be .pdf for PDFParser")

        file_path = Path(path)
        if not file_path.exists():
            raise InvalidConfig(f"PDF file not found: {path}")

        try:
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                text_parts = []

                for page_num, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                    except Exception as e:
                        logger.warning(
                            f"Failed to extract text from page {page_num}: {e}"
                        )
                        page_text = ""

                    # Check if page has enough text (not scanned)
                    if detect_scanned and (
                        not page_text
                        or len(page_text) < PDFParser.SCANNED_PDF_THRESHOLD
                    ):
                        raise ExtractionFailed(
                            f"PDF appears to be scanned (no text on page {page_num}). "
                            "OCR support coming in Phase 3."
                        )

                    if page_text:
                        text_parts.append(page_text)

                text = "\n".join(text_parts).strip()

                if not text:
                    raise ExtractionFailed("No text could be extracted from PDF")

                logger.debug(
                    f"Extracted {len(text)} chars from {len(reader.pages)} pages: {path}"
                )

                return text

        except ExtractionFailed:
            raise
        except Exception as e:
            logger.error(f"Failed to read PDF {path}: {e}", exc_info=True)
            raise ExtractionFailed(f"Failed to process PDF {path}: {e}")
