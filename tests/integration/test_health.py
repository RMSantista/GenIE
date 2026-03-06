"""Tests for health check endpoint."""

import pytest
from fastapi.testclient import TestClient

from spec.main import app


def test_root_endpoint():
    """Test root endpoint."""
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "0.1.0"


def test_health_endpoint():
    """Test health check endpoint."""
    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data
    assert "environment" in data


def test_health_endpoint_response_structure():
    """Test health endpoint response has correct structure."""
    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    # Check all required fields
    required_fields = ["status", "version", "timestamp", "environment"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"

    # Check field types
    assert isinstance(data["status"], str)
    assert isinstance(data["version"], str)
    assert isinstance(data["timestamp"], str)
    assert isinstance(data["environment"], str)
