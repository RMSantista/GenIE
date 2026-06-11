"""Persistent store for extraction configurations (one JSON file per config).

Implements the configuration layer of GenIE's design decision nº 1
("Generic, not General"): each use case is described by an
ExtractionConfig that tells the engine WHAT to extract.
"""

import logging
import re
from pathlib import Path
from typing import List, Optional

from spec.core.exceptions import InvalidConfig, StorageError
from spec.models.config import ExtractionConfig

logger = logging.getLogger(__name__)

_CONFIG_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")


class ConfigStore:
    """File-backed CRUD for ExtractionConfig documents."""

    def __init__(self, config_dir: str) -> None:
        """Initialize the store.

        Args:
            config_dir: Directory where config JSON files live
        """

        self._dir = Path(config_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, config_id: str) -> Path:
        """Resolve the safe file path for a config id.

        Args:
            config_id: Configuration identifier

        Returns:
            Path: JSON file path

        Raises:
            InvalidConfig: If the id contains unsafe characters
        """

        if not _CONFIG_ID_RE.match(config_id):
            raise InvalidConfig(
                f"config_id inválido: '{config_id}' (use letras, números, '-' e '_')"
            )
        return self._dir / f"{config_id}.json"

    def save(self, config: ExtractionConfig) -> ExtractionConfig:
        """Create or replace a configuration.

        Args:
            config: Validated configuration

        Returns:
            ExtractionConfig: The stored configuration

        Raises:
            StorageError: If the file cannot be written
        """

        path = self._path_for(config.extraction_id)
        try:
            path.write_text(
                config.model_dump_json(indent=2),
                encoding="utf-8",
            )
        except OSError as e:
            raise StorageError(f"Falha ao gravar configuração: {e}")
        logger.info("Saved extraction config: %s", config.extraction_id)
        return config

    def get(self, config_id: str) -> Optional[ExtractionConfig]:
        """Load a configuration by id.

        Args:
            config_id: Configuration identifier

        Returns:
            Optional[ExtractionConfig]: Config or None when absent
        """

        path = self._path_for(config_id)
        if not path.is_file():
            return None
        try:
            return ExtractionConfig.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise StorageError(f"Configuração corrompida '{config_id}': {e}")

    def list(self) -> List[ExtractionConfig]:
        """List all stored configurations.

        Returns:
            list[ExtractionConfig]: Configs ordered by id
        """

        configs: List[ExtractionConfig] = []
        for path in sorted(self._dir.glob("*.json")):
            try:
                configs.append(
                    ExtractionConfig.model_validate_json(path.read_text(encoding="utf-8"))
                )
            except ValueError:
                logger.warning("Skipping corrupt config file: %s", path)
        return configs

    def delete(self, config_id: str) -> bool:
        """Delete a configuration.

        Args:
            config_id: Configuration identifier

        Returns:
            bool: True if a config was removed
        """

        path = self._path_for(config_id)
        if not path.is_file():
            return False
        path.unlink()
        logger.info("Deleted extraction config: %s", config_id)
        return True
