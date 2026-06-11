"""Tests for config CRUD and Search Library endpoints (Phase 1, Stage 1.4.3)."""

import httpx
import pytest

from spec.core.config import get_settings
from spec.main import app


@pytest.fixture
def isolated_dirs(tmp_path, monkeypatch):
    """Point config and library storage at a temp folder."""

    settings = get_settings()
    monkeypatch.setattr(settings, "config_dir", str(tmp_path / "configs"))
    monkeypatch.setattr(
        settings, "search_library_path", str(tmp_path / "patterns.json")
    )
    return settings


@pytest.fixture
async def client(isolated_dirs):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


def _sample_config(config_id: str = "medical_reports_v1") -> dict:
    return {
        "extraction_id": config_id,
        "name": "Exames médicos",
        "input": {"type": "pdf", "source": "/uploads", "access_mode": "local_secure"},
        "output": {"type": "json", "auto_adapt": True},
        "llm": {"provider": "google", "model": "gemini-2.5-flash"},
        "behavior": {
            "use_search_library": True,
            "auto_create_patterns": True,
            "layout_independent": True,
            "update_on_change": True,
        },
        "extraction_instructions": "Extraia data, exame, resultado e referência.",
    }


class TestConfigCrud:
    async def test_create_get_update_delete(self, client):
        created = await client.post("/api/v1/configs", json=_sample_config())
        assert created.status_code == 201

        fetched = await client.get("/api/v1/configs/medical_reports_v1")
        assert fetched.status_code == 200
        assert fetched.json()["name"] == "Exames médicos"

        listed = await client.get("/api/v1/configs")
        assert [c["extraction_id"] for c in listed.json()] == ["medical_reports_v1"]

        updated_body = _sample_config()
        updated_body["name"] = "Exames v2"
        updated = await client.put(
            "/api/v1/configs/medical_reports_v1", json=updated_body
        )
        assert updated.status_code == 200
        assert updated.json()["name"] == "Exames v2"

        deleted = await client.delete("/api/v1/configs/medical_reports_v1")
        assert deleted.status_code == 200
        assert (await client.get("/api/v1/configs/medical_reports_v1")).status_code == 404

    async def test_duplicate_create_conflicts(self, client):
        assert (
            await client.post("/api/v1/configs", json=_sample_config())
        ).status_code == 201
        assert (
            await client.post("/api/v1/configs", json=_sample_config())
        ).status_code == 409

    async def test_id_mismatch_rejected(self, client):
        response = await client.put(
            "/api/v1/configs/outro_id", json=_sample_config("medical_reports_v1")
        )
        assert response.status_code == 400

    async def test_unsafe_id_rejected(self, client):
        response = await client.get("/api/v1/configs/..%2F..%2Fetc")
        assert response.status_code in (400, 404)


class TestLibraryEndpoints:
    async def test_empty_library(self, client):
        patterns = await client.get("/api/v1/library/patterns")
        assert patterns.status_code == 200
        assert patterns.json() == []

        stats = await client.get("/api/v1/library/stats")
        assert stats.status_code == 200
        assert stats.json()["total_patterns"] == 0

    async def test_patterns_and_stats_after_save(self, client, isolated_dirs):
        from spec.search_library.json_storage import JSONStorage

        storage = JSONStorage(storage_path=isolated_dirs.search_library_path)
        await storage.save_pattern(
            "fp-123", "medical_reports_v1", {"fields": [{"field_name": "exame"}]}
        )

        patterns = (await client.get("/api/v1/library/patterns")).json()
        assert len(patterns) == 1
        layout_id = patterns[0]["layout_id"]

        single = await client.get(f"/api/v1/library/patterns/{layout_id}")
        assert single.status_code == 200
        assert single.json()["config_id"] == "medical_reports_v1"

        missing = await client.get("/api/v1/library/patterns/layout_nao_existe")
        assert missing.status_code == 404

        stats = (await client.get("/api/v1/library/stats")).json()
        assert stats["total_patterns"] == 1
        assert stats["patterns_by_config"] == {"medical_reports_v1": 1}

        filtered = await client.get(
            "/api/v1/library/patterns", params={"config_id": "outro"}
        )
        assert filtered.json() == []
