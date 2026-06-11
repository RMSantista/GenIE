"""Application configuration using Pydantic Settings."""

from pathlib import Path
from typing import Optional

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
        google_api_key: Google AI API key
        llm_provider: Active LLM provider name (default: "google")
        llm_model: Active LLM model override (None = use provider default)
    """

    environment: str = "development"
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    data_dir: str = "./data"
    search_library_path: str = "./data/search_library/patterns.json"
    config_dir: str = "./data/configs"
    uploads_dir: str = "./data/uploads"
    outputs_dir: str = "./data/outputs"
    db_path: str = "./data/genie.db"

    master_key: Optional[str] = None  # env: GENIE_MASTER_KEY (base64, 32 bytes)
    genie_master_key: Optional[str] = None  # alias accepted for convenience

    cors_origins: str = (
        "http://localhost:8000,http://127.0.0.1:8000,http://localhost:5173"
    )
    allowed_fs_roots: Optional[str] = None  # extra roots, separated by os.pathsep
    max_upload_mb: int = 50
    max_files_per_upload: int = 20
    download_link_ttl_seconds: int = 900

    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    llm_provider: str = "google"
    llm_model: Optional[str] = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @model_validator(mode="after")
    def create_directories(self) -> "Settings":
        """Ensure required directories exist and normalize aliases."""
        if self.genie_master_key and not self.master_key:
            self.master_key = self.genie_master_key
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)
        Path(self.uploads_dir).mkdir(parents=True, exist_ok=True)
        Path(self.outputs_dir).mkdir(parents=True, exist_ok=True)
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
