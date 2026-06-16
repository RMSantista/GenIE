"""JSON-based search library storage implementation."""

import asyncio
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from spec.core.exceptions import StorageError
from spec.search_library.base import BaseStorage

logger = logging.getLogger(__name__)


class JSONStorage(BaseStorage):
    """File-based search library using JSON storage.

    Features:
    - Simple JSON file storage for portability
    - In-memory cache for performance
    - Thread-safe operations with locks
    - Pattern success rate tracking
    """

    def __init__(
        self, storage_path: str = "./data/search_library/patterns.json"
    ) -> None:
        """Initialize JSON storage.

        Args:
            storage_path: Path to patterns.json file

        Raises:
            StorageError: If directory cannot be created
        """

        self.storage_path = Path(storage_path)
        self._lock = asyncio.Lock()
        self._cache: Optional[Dict[str, Any]] = None

        # Ensure directory exists
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise StorageError(f"Failed to create storage directory: {e}")

        # Initialize storage file if needed
        self._ensure_storage_exists()

        logger.debug(f"Initialized JSONStorage at: {self.storage_path}")

    def _ensure_storage_exists(self) -> None:
        """Create storage file if it doesn't exist."""

        if not self.storage_path.exists():
            try:
                initial_data = {
                    "patterns": [],
                    "metadata": {
                        "version": "1.0",
                        "created_at": datetime.utcnow().isoformat(),
                        "total_patterns": 0,
                        "last_updated": datetime.utcnow().isoformat(),
                    },
                }
                self._save_storage(initial_data)
                logger.info(f"Created new storage file: {self.storage_path}")
            except Exception as e:
                raise StorageError(f"Failed to create storage file: {e}")

    def _load_storage(self) -> Dict[str, Any]:
        """Load storage from disk.

        Returns:
            dict: Storage data

        Raises:
            StorageError: If file cannot be read
        """

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise StorageError(f"Corrupt storage file {self.storage_path}: {e}")
        except Exception as e:
            raise StorageError(f"Failed to read storage file: {e}")

    def _save_storage(self, data: Dict[str, Any]) -> None:
        """Save storage to disk.

        Args:
            data: Storage data to save

        Raises:
            StorageError: If file cannot be written
        """

        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise StorageError(f"Failed to write storage file: {e}")

    async def find_pattern(
        self,
        fingerprint: str,
        config_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Find pattern by fingerprint and config.

        Args:
            fingerprint: Layout fingerprint
            config_id: Configuration ID

        Returns:
            dict: Pattern if found, None otherwise
        """

        async with self._lock:
            if self._cache is None:
                self._cache = self._load_storage()

            for pattern in self._cache.get("patterns", []):
                if (
                    pattern.get("fingerprint") == fingerprint
                    and pattern.get("config_id") == config_id
                ):
                    # Update metadata
                    pattern["last_used"] = datetime.utcnow().isoformat()
                    pattern["use_count"] = pattern.get("use_count", 0) + 1

                    # Persist changes
                    self._save_storage(self._cache)

                    logger.debug(f"Found pattern for fingerprint: {fingerprint}")
                    return pattern

            logger.debug(f"No pattern found for fingerprint: {fingerprint}")
            return None

    async def save_pattern(
        self,
        fingerprint: str,
        config_id: str,
        pattern: Dict[str, Any],
    ) -> None:
        """Save new pattern to storage.

        Args:
            fingerprint: Layout fingerprint
            config_id: Configuration ID
            pattern: Pattern definition

        Raises:
            StorageError: If save fails
        """

        async with self._lock:
            try:
                if self._cache is None:
                    self._cache = self._load_storage()

                # Create pattern record
                now = datetime.utcnow().isoformat()
                layout_id = self._generate_layout_id()

                new_pattern = {
                    "layout_id": layout_id,
                    "config_id": config_id,
                    "fingerprint": fingerprint,
                    "created_at": now,
                    "last_used": now,
                    "use_count": 1,
                    "success_rate": 1.0,
                    "fields": pattern.get("fields", []),
                }

                # Add to storage
                self._cache["patterns"].append(new_pattern)
                self._cache["metadata"]["total_patterns"] = len(self._cache["patterns"])
                self._cache["metadata"]["last_updated"] = now

                # Persist
                self._save_storage(self._cache)

                logger.info(
                    f"Saved pattern: layout_id={layout_id}, fingerprint={fingerprint}"
                )

            except Exception as e:
                raise StorageError(f"Failed to save pattern: {e}")

    async def update_success_rate(
        self,
        fingerprint: str,
        success: bool,
    ) -> None:
        """Update pattern success rate.

        Uses moving average: new_rate = (old_rate * (uses - 1) + success_value) / uses

        Args:
            fingerprint: Layout fingerprint
            success: True if extraction was successful
        """

        async with self._lock:
            if self._cache is None:
                self._cache = self._load_storage()

            for pattern in self._cache.get("patterns", []):
                if pattern.get("fingerprint") == fingerprint:
                    use_count = pattern.get("use_count", 1)
                    old_rate = pattern.get("success_rate", 1.0)
                    success_value = 1.0 if success else 0.0

                    # Moving average
                    new_rate = (old_rate * (use_count - 1) + success_value) / use_count
                    pattern["success_rate"] = round(new_rate, 3)

                    self._cache["metadata"][
                        "last_updated"
                    ] = datetime.utcnow().isoformat()

                    self._save_storage(self._cache)

                    logger.debug(
                        f"Updated success rate for {fingerprint}: {new_rate:.2%}"
                    )
                    break

    async def list_patterns(
        self,
        config_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List patterns, optionally filtered by config.

        Args:
            config_id: Optional config ID for filtering

        Returns:
            list: List of pattern dictionaries
        """

        async with self._lock:
            if self._cache is None:
                self._cache = self._load_storage()

            patterns = self._cache.get("patterns", [])

            if config_id:
                patterns = [p for p in patterns if p.get("config_id") == config_id]

            logger.debug(f"Listed {len(patterns)} patterns")
            return patterns

    async def get_metadata(self) -> Dict[str, Any]:
        """Get library metadata.

        Returns:
            dict: Metadata
        """

        async with self._lock:
            if self._cache is None:
                self._cache = self._load_storage()

            return self._cache.get("metadata", {})

    @staticmethod
    def _generate_layout_id() -> str:
        """Generate unique layout ID.

        Returns:
            str: 12-character hex ID based on timestamp
        """

        timestamp = datetime.utcnow().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]
