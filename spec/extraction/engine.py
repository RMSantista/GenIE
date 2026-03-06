"""Main extraction engine orchestrator."""

import logging
import uuid
from typing import Any, Dict, Optional
from time import time

from spec.core.exceptions import ExtractionFailed, InvalidConfig
from spec.extraction.layout.fingerprint import LayoutFingerprint
from spec.extraction.llm.factory import LLMProviderFactory
from spec.extraction.parsers.pdf import PDFParser
from spec.extraction.parsers.text import TextParser
from spec.models.extraction import ExtractionRequest, ExtractionResponse
from spec.output.manager import OutputManager
from spec.search_library.base import BaseStorage
from spec.search_library.matcher import PatternMatcher

logger = logging.getLogger(__name__)


class ExtractionEngine:
    """Main orchestrator for document extraction.

    Coordinates the full extraction pipeline:
    1. Read content from source
    2. Generate layout fingerprint
    3. Search library lookup
    4. LLM extraction (fallback)
    5. Save pattern (auto)
    6. Adapt and format output

    Attributes:
        search_library: Storage for patterns
        llm_factory: Factory for LLM providers
        output_manager: Output formatting manager
        fingerprint_generator: Layout fingerprinting
    """

    def __init__(
        self,
        search_library: BaseStorage,
        llm_factory: LLMProviderFactory,
        output_manager: OutputManager,
    ) -> None:
        """Initialize extraction engine.

        Args:
            search_library: Search library storage instance
            llm_factory: LLM provider factory
            output_manager: Output manager instance
        """

        self.search_library = search_library
        self.llm_factory = llm_factory
        self.output_manager = output_manager
        self.fingerprint_generator = LayoutFingerprint()

        logger.debug("Initialized ExtractionEngine")

    async def extract(self, request: ExtractionRequest) -> ExtractionResponse:
        """Execute document extraction.

        Args:
            request: Extraction request with config and source

        Returns:
            ExtractionResponse: Extraction results

        Raises:
            ExtractionFailed: If extraction cannot be completed
        """

        start_time = time()
        extraction_id = self._generate_extraction_id()

        try:
            logger.info(f"Starting extraction {extraction_id} with config {request.config_id}")

            # 1. Read content
            logger.debug("Step 1: Reading content from source")
            content = await self._read_content(request.source)
            logger.debug(f"Read {len(content)} chars from source")

            # 2. Generate fingerprint
            logger.debug("Step 2: Generating layout fingerprint")
            layout_fingerprint = self.fingerprint_generator.generate(content)
            logger.debug(f"Generated fingerprint: {layout_fingerprint}")

            # 3. Search library lookup
            logger.debug("Step 3: Searching library for matching pattern")
            pattern = await self.search_library.find_pattern(
                layout_fingerprint,
                request.config_id,
            )

            method_used = "unknown"
            extracted_data = {}
            confidence = 0.0

            # 4. Extract data
            if pattern and not request.force_llm:
                logger.debug("Step 4a: Using pattern from library")
                extracted_data = await PatternMatcher.extract_with_pattern(
                    content, pattern
                )
                method_used = "search_library"
                confidence = 0.95

                # Validate
                is_valid = await PatternMatcher.validate_extraction(
                    extracted_data, pattern
                )
                if is_valid:
                    logger.info(f"Extraction successful via library")
                else:
                    logger.warning("Pattern validation failed, falling back to LLM")
                    method_used = "unknown"  # Reset for LLM
                    extracted_data = {}

            if not extracted_data or method_used == "unknown":
                logger.debug("Step 4b: Using LLM for extraction")
                extracted_data, confidence = await self._extract_with_llm(
                    content,
                    request.config_id,
                    request.source,
                )
                method_used = "llm"

                # 5. Auto-save pattern if configured
                if request.options and request.options.get("auto_create_patterns", True):
                    logger.debug("Step 5: Auto-saving pattern")
                    try:
                        new_pattern = self._generate_pattern_from_extraction(
                            content,
                            extracted_data,
                            layout_fingerprint,
                        )
                        await self.search_library.save_pattern(
                            layout_fingerprint,
                            request.config_id,
                            new_pattern,
                        )
                        logger.info("Pattern saved to library")
                    except Exception as e:
                        logger.warning(f"Failed to save pattern: {e}")

            # 6. Adapt output
            logger.debug("Step 6: Adapting output")
            output = await self.output_manager.adapt_and_format(
                extracted_data,
                request.source,
            )

            # Calculate processing time
            processing_time_ms = int((time() - start_time) * 1000)

            response = ExtractionResponse(
                extraction_id=extraction_id,
                status="success",
                method_used=method_used,
                data=output,
                confidence=confidence,
                processing_time_ms=processing_time_ms,
                layout_fingerprint=layout_fingerprint,
                error=None,
            )

            logger.info(
                f"Extraction {extraction_id} completed in {processing_time_ms}ms "
                f"using {method_used}"
            )

            return response

        except Exception as e:
            logger.error(f"Extraction {extraction_id} failed: {e}", exc_info=True)

            processing_time_ms = int((time() - start_time) * 1000)

            return ExtractionResponse(
                extraction_id=extraction_id,
                status="error",
                method_used="unknown",
                data={},
                confidence=0.0,
                processing_time_ms=processing_time_ms,
                layout_fingerprint=None,
                error=str(e),
            )

    async def _read_content(self, source: Dict[str, Any]) -> str:
        """Read content from source.

        Args:
            source: Source specification (type, path/content)

        Returns:
            str: Content text

        Raises:
            InvalidConfig: If source type is not supported
        """

        source_type = source.get("type", "").lower()

        if source_type == "text":
            return await TextParser.extract_text(source)

        elif source_type in ("pdf", "file"):
            if str(source.get("path", "")).endswith(".pdf"):
                return await PDFParser.extract_text(source)
            else:
                return await TextParser.extract_text(source)

        else:
            raise InvalidConfig(f"Unsupported source type: {source_type}")

    async def _extract_with_llm(
        self,
        content: str,
        config_id: str,
        source: Dict[str, Any],
    ) -> tuple[Dict[str, Any], float]:
        """Extract data using LLM.

        Args:
            content: Document content
            config_id: Configuration ID
            source: Source specification

        Returns:
            tuple: (extracted_data dict, confidence score)

        Raises:
            ExtractionFailed: If LLM extraction fails
        """

        try:
            # Get LLM provider (use default for now)
            llm_provider = self.llm_factory.get_provider()

            # Basic schema for Phase 1
            schema = {"fields": {}}

            # Call LLM
            extracted_data = await llm_provider.extract(
                content=content,
                schema=schema,
                instructions=f"Extract structured data from this document for config {config_id}",
            )

            confidence = 0.90

            return extracted_data, confidence

        except Exception as e:
            raise ExtractionFailed(f"LLM extraction failed: {e}")

    def _generate_pattern_from_extraction(
        self,
        content: str,
        extracted_data: Dict[str, Any],
        layout_fingerprint: str,
    ) -> Dict[str, Any]:
        """Generate extraction pattern from successful LLM extraction.

        Note: Phase 1 uses placeholder patterns. Phase 2 will auto-generate REGEX.

        Args:
            content: Original content
            extracted_data: Extracted data
            layout_fingerprint: Layout fingerprint

        Returns:
            dict: Pattern definition
        """

        fields = []

        for field_name, value in extracted_data.items():
            if value is None:
                continue

            # Phase 1: Placeholder
            # Phase 2: Auto-generate REGEX from content and value
            field_def = {
                "field_name": field_name,
                "extraction_method": "regex",
                "pattern": "",  # To be generated in Phase 2
                "instruction": None,
                "validation": None,
                "post_process": None,
            }
            fields.append(field_def)

        return {
            "layout_fingerprint": layout_fingerprint,
            "fields": fields,
        }

    @staticmethod
    def _generate_extraction_id() -> str:
        """Generate unique extraction ID.

        Returns:
            str: Extraction ID
        """

        return f"ext_{uuid.uuid4().hex[:12]}"
