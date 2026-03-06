"""Base class for search library storage implementations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseStorage(ABC):
    """Abstract base class for search library storage.

    All storage implementations must inherit from this class and implement
    the abstract methods.
    """

    @abstractmethod
    async def find_pattern(
        self,
        fingerprint: str,
        config_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Find a pattern by fingerprint and config.

        Args:
            fingerprint: Layout fingerprint
            config_id: Configuration ID

        Returns:
            dict: Pattern if found, None otherwise
        """

        pass

    @abstractmethod
    async def save_pattern(
        self,
        fingerprint: str,
        config_id: str,
        pattern: Dict[str, Any],
    ) -> None:
        """Save a new pattern to storage.

        Args:
            fingerprint: Layout fingerprint
            config_id: Configuration ID
            pattern: Pattern definition
        """

        pass

    @abstractmethod
    async def update_success_rate(
        self,
        fingerprint: str,
        success: bool,
    ) -> None:
        """Update success rate for a pattern.

        Args:
            fingerprint: Layout fingerprint
            success: True if last use was successful
        """

        pass

    @abstractmethod
    async def list_patterns(
        self,
        config_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List all patterns, optionally filtered by config.

        Args:
            config_id: Optional config ID for filtering

        Returns:
            list: List of pattern dictionaries
        """

        pass

    @abstractmethod
    async def get_metadata(self) -> Dict[str, Any]:
        """Get library metadata.

        Returns:
            dict: Metadata including version, total_patterns, last_updated
        """

        pass
