"""Pytest configuration and fixtures for GENIE tests."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from spec.core.config import Settings
from spec.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Provide test settings."""
    settings = Settings(
        environment="test",
        log_level="DEBUG",
        api_host="localhost",
        api_port=8000,
        data_dir="./data_test",
        search_library_path="./data_test/patterns.json",
        config_dir="./data_test/configs",
        uploads_dir="./data_test/uploads",
    )
    return settings


@pytest.fixture
def client():
    """Provide FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_text_content() -> str:
    """Sample text content for testing."""
    return """
    Patient Name: John Doe
    Age: 35
    Date: 2026-03-05
    Test Results: Normal
    Notes: No issues found
    """


@pytest.fixture
def sample_extraction_request() -> dict:
    """Sample extraction request."""
    return {
        "config_id": "test_config",
        "source": {
            "type": "text",
            "content": """
                Patient Name: John Doe
                Age: 35
                Date: 2026-03-05
            """
        },
        "force_llm": False,
        "options": {
            "auto_create_patterns": True
        }
    }
