"""Tests for configuration management."""

from pathlib import Path

from spec.core.config import Settings, get_settings


class TestSettings:
    """Tests for Settings configuration."""

    def test_settings_defaults(self):
        """Test settings with default values."""
        settings = Settings()

        assert settings.environment == "development"
        assert settings.log_level == "INFO"
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000

    def test_settings_custom_values(self):
        """Test settings with custom values."""
        settings = Settings(
            environment="production",
            log_level="WARNING",
            api_port=9000,
        )

        assert settings.environment == "production"
        assert settings.log_level == "WARNING"
        assert settings.api_port == 9000

    def test_get_settings_singleton(self):
        """Test get_settings returns singleton."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_settings_directories_created(self):
        """Test that settings creates required directories."""
        settings = Settings(
            data_dir="./test_data_temp",
            config_dir="./test_data_temp/configs",
            uploads_dir="./test_data_temp/uploads",
            search_library_path="./test_data_temp/patterns.json",
        )

        # Verify directories exist
        assert Path(settings.data_dir).exists()
        assert Path(settings.config_dir).exists()
        assert Path(settings.uploads_dir).exists()

        # Cleanup
        import shutil
        shutil.rmtree(settings.data_dir, ignore_errors=True)
