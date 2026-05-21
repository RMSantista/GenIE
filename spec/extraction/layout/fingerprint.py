"""Layout fingerprinting for document structure identification."""

import hashlib
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class LayoutFingerprint:
    """Generate deterministic fingerprints of document layout structure.

    A fingerprint is a hash of the document's structural elements,
    independent of actual data values. This allows matching documents
    with similar layouts but different data.

    Strategy:
    1. Remove numeric data (replace with "N")
    2. Remove date patterns (replace with "D")
    3. Remove proper nouns/capitalized words (replace with "X")
    4. Normalize whitespace
    5. Hash the resulting structure
    """

    def __init__(self, sensitivity: str = "medium") -> None:
        """Initialize fingerprint generator.

        Args:
            sensitivity: Sensitivity level ("low", "medium", "high")
        """

        self.sensitivity = sensitivity
        logger.debug(f"Initialized LayoutFingerprint with sensitivity: {sensitivity}")

    def generate(self, content: str) -> str:
        """Generate fingerprint for document content.

        Args:
            content: Document text

        Returns:
            str: 16-character hex fingerprint

        Returns a deterministic hash that is the same for documents
        with the same layout but different data values.
        """

        structure = self._extract_structure(content)
        fingerprint = hashlib.sha256(structure.encode()).hexdigest()[:16]

        logger.debug(f"Generated fingerprint: {fingerprint}")

        return fingerprint

    def _extract_structure(self, content: str) -> str:
        """Extract structural elements from content.

        Removes data, normalizes formatting, keeps layout.

        Args:
            content: Document text

        Returns:
            str: Normalized structural representation
        """

        text = content

        # Normalize all whitespace: collapse tabs/spaces and newlines
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n+", "\n", text)

        # Process per line to preserve line structure
        lines = text.split("\n")
        processed_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if ":" in line:
                # Label line: keep the label part, normalize the value
                label, _, _ = line.partition(":")
                label = label.strip()
                processed_lines.append(f"{label}:V")
            else:
                # Free text: remove numbers, dates, proper nouns
                line = re.sub(r"\d{4}-\d{1,2}-\d{1,2}", "D", line)
                line = re.sub(r"\d{1,2}/\d{1,2}/\d{2,4}", "D", line)
                line = re.sub(r"\d+", "N", line)
                line = re.sub(r"\b[A-Z][a-z]+\b", "X", line)
                if line.strip():
                    processed_lines.append(line.strip()[:80])

        result = "\n".join(processed_lines)
        return result

    def similarity(self, fp1: str, fp2: str) -> float:
        """Calculate similarity between two fingerprints.

        Uses Hamming distance (character-by-character comparison).

        Args:
            fp1: First fingerprint
            fp2: Second fingerprint

        Returns:
            float: Similarity score 0.0-1.0 (1.0 = identical)
        """

        if fp1 == fp2:
            return 1.0

        if not fp1 or not fp2:
            return 0.0

        # Hamming distance between fingerprints
        matches = sum(c1 == c2 for c1, c2 in zip(fp1, fp2))
        similarity = matches / max(len(fp1), len(fp2))

        logger.debug(f"Fingerprint similarity: {similarity:.2%}")

        return similarity
