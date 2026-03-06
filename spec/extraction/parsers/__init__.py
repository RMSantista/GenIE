"""Content parsers for various document formats."""

from spec.extraction.parsers.text import TextParser
from spec.extraction.parsers.pdf import PDFParser

__all__ = [
    "TextParser",
    "PDFParser",
]
