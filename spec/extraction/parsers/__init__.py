"""Content parsers for various document formats."""

from spec.extraction.parsers.pdf import PDFParser
from spec.extraction.parsers.text import TextParser

__all__ = [
    "TextParser",
    "PDFParser",
]
