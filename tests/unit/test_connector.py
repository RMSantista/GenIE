"""Tests for the Connector agent (filesystem safety, content parsing, DB output)."""

import json
import sqlite3
from pathlib import Path

import pytest

from spec.core.exceptions import ExtractionFailed, InvalidConfig
from spec.extraction.agents.connector import (
    ConnectorAgent,
    ensure_path_allowed,
    new_upload_id,
)
from spec.extraction.parsers.content import bytes_to_text, html_to_text
from spec.models.webapp import InputSpec, OutputSpec


def noop_emit(message: str = "", level: str = "", progress=None) -> None:
    """No-op event sink for tests."""


class TestPathSafety:
    def test_blocks_system_paths(self) -> None:
        with pytest.raises(InvalidConfig):
            ensure_path_allowed(Path("/etc/shadow"))

    def test_blocks_traversal(self, tmp_path) -> None:
        with pytest.raises(InvalidConfig):
            ensure_path_allowed(Path("/usr/../etc/passwd"))

    def test_allows_home(self) -> None:
        resolved = ensure_path_allowed(Path.home() / "docs")

        assert resolved == (Path.home() / "docs").resolve()


class TestContentParsing:
    def test_csv(self) -> None:
        text = bytes_to_text(b"a,b\n1,2\n", "data.csv")

        assert "a\tb" in text
        assert "1\t2" in text

    def test_json_pretty(self) -> None:
        text = bytes_to_text(b'{"x":1}', "data.json")

        assert '"x": 1' in text

    def test_html_strips_tags_and_scripts(self) -> None:
        html = "<html><script>evil()</script><body><h1>Título</h1><p>texto</p></body></html>"
        text = html_to_text(html)

        assert "Título" in text
        assert "texto" in text
        assert "evil" not in text

    def test_docx_rejected_with_guidance(self) -> None:
        with pytest.raises(ExtractionFailed, match="docx"):
            bytes_to_text(b"PK...", "doc.docx")


class TestUploadInput:
    @pytest.mark.asyncio
    async def test_missing_upload_id_rejected(self) -> None:
        connector = ConnectorAgent()
        spec = InputSpec(type="upload", upload_id=None)

        with pytest.raises(InvalidConfig):
            await connector.open_input(spec, noop_emit)

    @pytest.mark.asyncio
    async def test_traversal_upload_id_rejected(self) -> None:
        connector = ConnectorAgent()
        spec = InputSpec(type="upload", upload_id="../../etc")

        with pytest.raises(InvalidConfig):
            await connector.open_input(spec, noop_emit)

    def test_new_upload_id_format(self) -> None:
        upload_id = new_upload_id()

        assert len(upload_id) == 32
        assert all(c in "0123456789abcdef" for c in upload_id)


class TestPathInput:
    @pytest.mark.asyncio
    async def test_reads_folder(self, tmp_path, monkeypatch) -> None:
        from spec.core.config import get_settings

        monkeypatch.setattr(get_settings(), "allowed_fs_roots", str(tmp_path))
        (tmp_path / "um.txt").write_text("conteúdo um", encoding="utf-8")
        (tmp_path / "dois.csv").write_text("a,b\n1,2", encoding="utf-8")
        (tmp_path / "ignorado.bin").write_bytes(b"\x00\x01")

        connector = ConnectorAgent()
        items = await connector.open_input(
            InputSpec(type="path", target=str(tmp_path)), noop_emit
        )

        names = {item["name"] for item in items}
        assert names == {"um.txt", "dois.csv"}


class TestDbDelivery:
    @pytest.mark.asyncio
    async def test_writes_sqlite(self, tmp_path, monkeypatch) -> None:
        from spec.core.config import get_settings

        monkeypatch.setattr(get_settings(), "allowed_fs_roots", str(tmp_path))
        db_file = tmp_path / "saida.db"
        records = [
            {"exame": "Glicose", "resultado": "118 mg/dL"},
            {"exame": "TSH", "resultado": "2.1 µUI/mL", "extra": {"obs": "ok"}},
        ]

        connector = ConnectorAgent()
        receipt = await connector.deliver(
            OutputSpec(type="db", target=f"sqlite:///{db_file}", table="exames"),
            records,
            {},
            "genie-test",
            noop_emit,
        )

        assert receipt["rows"] == 2
        conn = sqlite3.connect(db_file)
        rows = conn.execute("SELECT exame, resultado, extra FROM exames ORDER BY exame").fetchall()
        conn.close()
        assert rows[0][0] == "Glicose"
        assert json.loads(rows[1][2]) == {"obs": "ok"}


class TestDownloadDelivery:
    @pytest.mark.asyncio
    async def test_writes_json_and_csv(self, tmp_path, monkeypatch) -> None:
        from spec.core.config import get_settings

        monkeypatch.setattr(get_settings(), "outputs_dir", str(tmp_path))
        records = [{"campo": "valor", "n": 1}]

        connector = ConnectorAgent()
        receipt = await connector.deliver(
            OutputSpec(type="download"), records, {}, "genie-abc", noop_emit
        )

        assert sorted(receipt["artifacts"]) == ["output.csv", "output.json"]
        saved = json.loads((tmp_path / "genie-abc" / "output.json").read_text())
        assert saved == records
