"""Tests for health check endpoint."""

import pytest
import httpx

from spec.main import app


@pytest.fixture
async def client():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


async def test_root_endpoint(client: httpx.AsyncClient):
    """Test root endpoint."""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "0.1.0"


async def test_health_endpoint(client: httpx.AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data
    assert "environment" in data


async def test_health_endpoint_response_structure(client: httpx.AsyncClient):
    """Test health endpoint response has correct structure."""
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    required_fields = ["status", "version", "timestamp", "environment"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"

    assert isinstance(data["status"], str)
    assert isinstance(data["version"], str)
    assert isinstance(data["timestamp"], str)
    assert isinstance(data["environment"], str)
