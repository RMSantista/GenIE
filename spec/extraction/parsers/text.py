"""Text content parser."""

import logging
from pathlib import Path
from typing import Any, Dict

from spec.core.exceptions import InvalidConfig

logger = logging.getLogger(__name__)


class TextParser:
    """Parser for text content sources."""

    @staticmethod
    async def extract_text(source: Dict[str, Any]) -> str:
        """Extract text from source.

        Supports:
        - "text" source type with "content" field
        - "file" source type with "path" field to .txt file

        Args:
            source: Source specification with type and content/path

        Returns:
            str: Extracted text

        Raises:
            InvalidConfig: If source format is invalid
        """

        source_type = source.get("type", "").lower()

        if source_type == "text":
            content = source.get("content")
            if not content:
                raise InvalidConfig("Text source must have 'content' field")
            logger.debug(f"Extracted {len(content)} chars from text source")
            return str(content)

        elif source_type == "file":
            path = source.get("path")
            if not path:
                raise InvalidConfig("File source must have 'path' field")

            if not path.endswith(".txt"):
                raise InvalidConfig("File must be .txt for TextParser")

            file_path = Path(path)
            if not file_path.exists():
                raise InvalidConfig(f"File not found: {path}")

            try:
                text = file_path.read_text(encoding="utf-8")
                logger.debug(f"Extracted {len(text)} chars from file: {path}")
                return text
            except Exception as e:
                raise InvalidConfig(f"Failed to read file {path}: {e}")

        else:
            raise InvalidConfig(
                f"TextParser does not support source type: {source_type}"
            )
