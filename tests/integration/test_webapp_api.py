"""End-to-end tests for the web app API: models, keys, uploads, runs, downloads."""

import asyncio
import json
from typing import Any, Dict

import httpx
import pytest

from spec.core.config import get_settings
from spec.core.security import get_key_vault, reset_security_singletons
from spec.extraction.agents import orchestrator as orchestrator_module
from spec.main import app


@pytest.fixture
def isolated_storage(tmp_path, monkeypatch):
    """Point data dirs at a temp folder and reset security singletons."""

    settings = get_settings()
    monkeypatch.setattr(settings, "data_dir", str(tmp_path))
    monkeypatch.setattr(settings, "db_path", str(tmp_path / "genie.db"))
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "outputs_dir", str(tmp_path / "outputs"))
    monkeypatch.setattr(settings, "allowed_fs_roots", str(tmp_path))
    monkeypatch.setattr(settings, "master_key", None)
    reset_security_singletons()
    yield settings
    reset_security_singletons()


@pytest.fixture
async def client(isolated_storage):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


class FakeProvider:
    """Deterministic stand-in for an LLM provider."""

    def __init__(self, records=None) -> None:
        self.records = records or [
            {"Data": "2026-03-14", "Exame": "Glicose", "Resultado": "118 mg/dL"}
        ]

    async def extract(self, content: str, schema: Dict[str, Any], instructions: str = ""):
        return {"records": self.records, "confidence": 0.94, "notes": ""}


class TestModels:
    async def test_catalog_without_keys(self, client):
        response = await client.get("/api/v1/models")

        assert response.status_code == 200
        models = response.json()
        assert len(models) >= 4
        assert all(m["has_key"] is False for m in models)
        assert all("key" not in (m.get("masked_key") or "") for m in models)


class TestKeys:
    async def test_store_list_delete(self, client):
        stored = await client.post(
            "/api/v1/keys",
            json={"provider": "google", "key": "AIzaSyFakeKey1234", "validate_key": False},
        )
        assert stored.status_code == 200
        body = stored.json()
        assert body["masked"].startswith("AIza")
        assert "AIzaSyFakeKey1234" not in json.dumps(body)

        listed = await client.get("/api/v1/keys")
        assert listed.status_code == 200
        assert listed.json() == [{"provider": "google", "masked": body["masked"]}]

        models = (await client.get("/api/v1/models")).json()
        google = [m for m in models if m["provider"] == "google"]
        assert all(m["has_key"] for m in google)

        deleted = await client.delete("/api/v1/keys/google")
        assert deleted.status_code == 200
        assert (await client.delete("/api/v1/keys/google")).status_code == 404

    async def test_unknown_provider_rejected(self, client):
        response = await client.post(
            "/api/v1/keys",
            json={"provider": "skynet", "key": "x", "validate_key": False},
        )

        assert response.status_code == 400


class TestUploads:
    async def test_accepts_supported_files(self, client):
        response = await client.post(
            "/api/v1/uploads",
            files=[
                ("files", ("exame.txt", b"Glicose: 118 mg/dL", "text/plain")),
                ("files", ("dados.csv", b"a,b\n1,2", "text/csv")),
            ],
        )

        assert response.status_code == 200
        body = response.json()
        assert len(body["upload_id"]) == 32
        assert {f["name"] for f in body["files"]} == {"exame.txt", "dados.csv"}

    async def test_rejects_unsupported_extension(self, client):
        response = await client.post(
            "/api/v1/uploads",
            files=[("files", ("virus.exe", b"MZ", "application/octet-stream"))],
        )

        assert response.status_code == 400

    async def test_sanitizes_traversal_names(self, client, isolated_storage):
        response = await client.post(
            "/api/v1/uploads",
            files=[("files", ("../../evil.txt", b"data", "text/plain"))],
        )

        assert response.status_code == 200
        name = response.json()["files"][0]["name"]
        assert "/" not in name and ".." not in name


class TestRuns:
    async def test_unknown_model_rejected(self, client):
        response = await client.post(
            "/api/v1/runs",
            json={
                "model_id": "modelo-x",
                "input": {"type": "url", "target": "https://x"},
                "prompt": "extraia",
                "output": {"type": "download"},
            },
        )

        assert response.status_code == 400

    async def test_missing_key_rejected(self, client):
        response = await client.post(
            "/api/v1/runs",
            json={
                "model_id": "gemini-2.5-flash",
                "input": {"type": "url", "target": "https://x"},
                "prompt": "extraia",
                "output": {"type": "download"},
            },
        )

        assert response.status_code == 400
        assert "API Key" in response.json()["detail"]

    async def test_full_pipeline_upload_to_download(self, client, monkeypatch):
        get_key_vault().store("google", "AIzaSyFakeKey1234")
        monkeypatch.setattr(
            orchestrator_module.Orchestrator,
            "_resolve_provider",
            lambda self, model_id: FakeProvider(),
        )

        upload = await client.post(
            "/api/v1/uploads",
            files=[("files", ("exames.txt", b"Glicose: 118 mg/dL (ref 70-99)", "text/plain"))],
        )
        upload_id = upload.json()["upload_id"]

        created = await client.post(
            "/api/v1/runs",
            json={
                "model_id": "gemini-2.5-flash",
                "input": {"type": "upload", "upload_id": upload_id},
                "prompt": "Extraia exame, resultado e referência",
                "output": {"type": "download"},
                "format": "",
            },
        )
        assert created.status_code == 201
        job_id = created.json()["job_id"]

        for _ in range(50):
            info = (await client.get(f"/api/v1/runs/{job_id}")).json()
            if info["status"] in ("done", "error", "cancelled"):
                break
            await asyncio.sleep(0.1)

        assert info["status"] == "done", info.get("error")
        result = info["result"]
        assert result["records"] == FakeProvider().records
        assert set(result["downloads"]) == {"json", "csv"}

        # SSE replay terminates for finished jobs and carries the finish event.
        events = await client.get(f"/api/v1/runs/{job_id}/events")
        assert events.status_code == 200
        assert '"type": "finish"' in events.text or '"type":"finish"' in events.text

        # Signed download link works...
        download = await client.get(result["downloads"]["json"])
        assert download.status_code == 200
        assert download.json() == FakeProvider().records

        # ...and a tampered signature is refused.
        tampered = result["downloads"]["json"].replace("sig=", "sig=ff")
        assert (await client.get(tampered)).status_code == 403

    async def test_credentials_never_leak_into_events(self, client, monkeypatch):
        get_key_vault().store("google", "AIzaSyFakeKey1234")
        monkeypatch.setattr(
            orchestrator_module.Orchestrator,
            "_resolve_provider",
            lambda self, model_id: FakeProvider(),
        )

        created = await client.post(
            "/api/v1/runs",
            json={
                "model_id": "gemini-2.5-flash",
                "input": {
                    "type": "db",
                    "target": "postgres://user:SENHA_SECRETA@host:5432/db",
                    "password": "SENHA_SECRETA",
                },
                "prompt": "extraia tudo",
                "output": {"type": "download"},
            },
        )
        job_id = created.json()["job_id"]

        for _ in range(50):
            info = (await client.get(f"/api/v1/runs/{job_id}")).json()
            if info["status"] in ("done", "error", "cancelled"):
                break
            await asyncio.sleep(0.1)

        events = await client.get(f"/api/v1/runs/{job_id}/events")
        assert "SENHA_SECRETA" not in events.text
        assert "SENHA_SECRETA" not in json.dumps(info)
