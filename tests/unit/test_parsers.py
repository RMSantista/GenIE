"""Tests for content parsers."""

from pathlib import Path

import pytest

from spec.core.exceptions import InvalidConfig
from spec.extraction.parsers.text import TextParser


class TestTextParser:
    """Tests for TextParser."""

    @pytest.mark.asyncio
    async def test_extract_text_from_content(self):
        """Test extracting text from direct content."""
        source = {
            "type": "text",
            "content": "Hello, this is test content",
        }

        result = await TextParser.extract_text(source)
        assert result == "Hello, this is test content"

    @pytest.mark.asyncio
    async def test_extract_text_missing_content(self):
        """Test error when content is missing."""
        source = {
            "type": "text",
        }

        with pytest.raises(InvalidConfig):
            await TextParser.extract_text(source)

    @pytest.mark.asyncio
    async def test_extract_text_from_file(self):
        """Test extracting text from file."""
        # Create temporary test file
        test_file = Path("/tmp/test_content.txt")
        test_file.write_text("File content here", encoding="utf-8")

        try:
            source = {
                "type": "file",
                "path": str(test_file),
            }

            result = await TextParser.extract_text(source)
            assert result == "File content here"
        finally:
            test_file.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_extract_text_file_not_found(self):
        """Test error when file not found."""
        source = {
            "type": "file",
            "path": "/nonexistent/file.txt",
        }

        with pytest.raises(InvalidConfig):
            await TextParser.extract_text(source)

    @pytest.mark.asyncio
    async def test_extract_text_invalid_source_type(self):
        """Test error for invalid source type."""
        source = {
            "type": "invalid_type",
            "content": "test",
        }

        with pytest.raises(InvalidConfig):
            await TextParser.extract_text(source)

    @pytest.mark.asyncio
    async def test_extract_text_non_txt_file(self):
        """Test error when file is not .txt."""
        source = {
            "type": "file",
            "path": "/path/to/document.pdf",
        }

        with pytest.raises(InvalidConfig):
            await TextParser.extract_text(source)
