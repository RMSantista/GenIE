"""Application configuration using Pydantic Settings."""

from typing import Optional
from pathlib import Path
from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file.

    Attributes:
        environment: Environment name (development, production, test)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        api_host: API server host
        api_port: API server port
        data_dir: Data directory path
        search_library_path: Search library JSON file path
        config_dir: Configuration directory path
        uploads_dir: Uploads directory path
        anthropic_api_key: Anthropic API key
        openai_api_key: OpenAI API key
    """

    environment: str = "development"
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    data_dir: str = "./data"
    search_library_path: str = "./data/search_library/patterns.json"
    config_dir: str = "./data/configs"
    uploads_dir: str = "./data/uploads"

    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}

    @model_validator(mode="after")
    def create_directories(self) -> "Settings":
        """Ensure required directories exist after initialization."""
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)
        Path(self.uploads_dir).mkdir(parents=True, exist_ok=True)
        Path(self.search_library_path).parent.mkdir(parents=True, exist_ok=True)
        return self


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global settings instance.

    Returns:
        Settings: Global settings object (singleton)
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
