"""Tests for the legacy provider management endpoints."""

from unittest.mock import AsyncMock

import httpx
import pytest

from spec.extraction.llm.factory import LLMProviderFactory
from spec.main import app


@pytest.fixture
async def client():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


class TestProvidersEndpoints:
    async def test_list_providers(self, client):
        response = await client.get("/api/v1/providers")

        assert response.status_code == 200
        providers = response.json()
        assert {p["name"] for p in providers} == {"google", "openai", "anthropic"}
        assert sum(1 for p in providers if p["is_active"]) == 1

    async def test_active_provider(self, client):
        response = await client.get("/api/v1/providers/active")

        assert response.status_code == 200
        assert response.json()["is_active"] is True

    async def test_configure_unknown_provider(self, client):
        response = await client.post(
            "/api/v1/providers/configure",
            json={"provider": "skynet", "api_key": "x"},
        )

        assert response.status_code == 400

    async def test_configure_validates_and_persists(self, client, tmp_path, monkeypatch):
        from spec.core.config import get_settings
        from spec.core.security import reset_security_singletons

        settings = get_settings()
        monkeypatch.setattr(settings, "data_dir", str(tmp_path))
        monkeypatch.setattr(settings, "db_path", str(tmp_path / "genie.db"))
        monkeypatch.setattr(settings, "master_key", None)
        reset_security_singletons()

        fake_provider = AsyncMock()
        fake_provider.extract = AsyncMock(return_value={"ok": True})
        monkeypatch.setattr(
            LLMProviderFactory,
            "get_provider",
            lambda self, **kwargs: fake_provider,
        )

        app.dependency_overrides.clear()
        try:
            response = await client.post(
                "/api/v1/providers/configure",
                json={"provider": "google", "api_key": "AIzaSyTest123", "model": None},
            )
        finally:
            reset_security_singletons()

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "AIzaSyTest123" not in str(body)

    async def test_configure_rejected_when_validation_fails(self, client, monkeypatch):
        from spec.core.exceptions import LLMProviderError

        fake_provider = AsyncMock()
        fake_provider.extract = AsyncMock(side_effect=LLMProviderError("chave inválida"))
        monkeypatch.setattr(
            LLMProviderFactory,
            "get_provider",
            lambda self, **kwargs: fake_provider,
        )

        response = await client.post(
            "/api/v1/providers/configure",
            json={"provider": "openai", "api_key": "sk-bad"},
        )

        assert response.status_code == 400
