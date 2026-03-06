"""Pattern matching engine for search library patterns."""

import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PatternMatcher:
    """Match and extract data using stored patterns.

    Supports multiple extraction methods:
    - REGEX: Regular expression patterns
    - Instruction: LLM-based extraction (Phase 2)
    - Query: SQL-like queries (Phase 2)
    """

    @staticmethod
    async def extract_with_pattern(
        content: str,
        pattern: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract data using a stored pattern.

        Args:
            content: Document content
            pattern: Pattern definition with fields

        Returns:
            dict: Extracted data

        Raises:
            ValueError: If pattern is invalid
        """

        extracted = {}

        for field in pattern.get("fields", []):
            field_name = field.get("field_name")
            extraction_method = field.get("extraction_method", "regex")

            if extraction_method == "regex":
                pattern_str = field.get("pattern")
                if not pattern_str:
                    logger.warning(f"Field {field_name} has no pattern")
                    extracted[field_name] = None
                    continue

                try:
                    match = re.search(pattern_str, content, re.MULTILINE | re.DOTALL)
                    value = match.group(1) if match else None
                    extracted[field_name] = value

                    if value:
                        logger.debug(f"Matched field {field_name}: {value[:50]}...")
                    else:
                        logger.debug(f"Field {field_name} not matched")

                except re.error as e:
                    logger.error(f"Invalid regex pattern for {field_name}: {e}")
                    extracted[field_name] = None

            elif extraction_method in ("instruction", "query"):
                # Phase 2+ features
                logger.warning(f"Extraction method '{extraction_method}' not yet supported")
                extracted[field_name] = None

            else:
                logger.warning(f"Unknown extraction method: {extraction_method}")
                extracted[field_name] = None

        return extracted

    @staticmethod
    async def validate_extraction(
        data: Dict[str, Any],
        pattern: Dict[str, Any],
    ) -> bool:
        """Validate extracted data against pattern requirements.

        Args:
            data: Extracted data
            pattern: Pattern definition with validation rules

        Returns:
            bool: True if all validations pass

        Raises:
            ValueError: If validation patterns are invalid
        """

        for field in pattern.get("fields", []):
            field_name = field.get("field_name")
            validation_pattern = field.get("validation")

            if not validation_pattern:
                continue

            value = data.get(field_name)

            if value is None:
                logger.debug(f"Field {field_name} is None, skipping validation")
                continue

            try:
                if not re.match(validation_pattern, str(value)):
                    logger.warning(
                        f"Validation failed for {field_name}: '{value}' "
                        f"does not match pattern '{validation_pattern}'"
                    )
                    return False

            except re.error as e:
                logger.error(f"Invalid validation pattern for {field_name}: {e}")
                return False

        logger.debug("All validations passed")
        return True

    @staticmethod
    def apply_post_processing(
        data: Dict[str, Any],
        pattern: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply post-processing rules to extracted data.

        Note: This is a placeholder for Phase 2 advanced processing.

        Args:
            data: Extracted data
            pattern: Pattern with post-processing rules

        Returns:
            dict: Post-processed data
        """

        result = dict(data)

        for field in pattern.get("fields", []):
            field_name = field.get("field_name")
            post_process = field.get("post_process")

            if not post_process:
                continue

            value = result.get(field_name)
            if value is None:
                continue

            # Phase 2: Implement actual post-processing (trim, uppercase, etc.)
            logger.debug(f"Post-processing rule for {field_name}: {post_process}")

        return result
