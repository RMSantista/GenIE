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


class TestSqliteInput:
    @pytest.mark.asyncio
    async def test_reads_tables_as_items(self, tmp_path, monkeypatch) -> None:
        from spec.core.config import get_settings

        monkeypatch.setattr(get_settings(), "allowed_fs_roots", str(tmp_path))
        db_file = tmp_path / "origem.db"
        conn = sqlite3.connect(db_file)
        conn.execute("CREATE TABLE exames (nome TEXT, valor TEXT)")
        conn.execute("INSERT INTO exames VALUES ('Glicose', '118')")
        conn.commit()
        conn.close()

        connector = ConnectorAgent()
        items = await connector.open_input(
            InputSpec(type="db", target=f"sqlite:///{db_file}"), noop_emit
        )

        assert len(items) == 1
        assert "Glicose" in items[0]["content"]

    @pytest.mark.asyncio
    async def test_custom_query(self, tmp_path, monkeypatch) -> None:
        from spec.core.config import get_settings

        monkeypatch.setattr(get_settings(), "allowed_fs_roots", str(tmp_path))
        db_file = tmp_path / "origem.db"
        conn = sqlite3.connect(db_file)
        conn.execute("CREATE TABLE t (a INT)")
        conn.executemany("INSERT INTO t VALUES (?)", [(1,), (2,)])
        conn.commit()
        conn.close()

        connector = ConnectorAgent()
        items = await connector.open_input(
            InputSpec(type="db", target=str(db_file), query="SELECT a FROM t WHERE a > 1"),
            noop_emit,
        )

        assert len(items) == 1
        assert '"a": 2' in items[0]["content"]

    @pytest.mark.asyncio
    async def test_missing_db_rejected(self, tmp_path, monkeypatch) -> None:
        from spec.core.config import get_settings

        monkeypatch.setattr(get_settings(), "allowed_fs_roots", str(tmp_path))
        connector = ConnectorAgent()

        with pytest.raises(InvalidConfig):
            await connector.open_input(
                InputSpec(type="db", target=str(tmp_path / "nao_existe.db")), noop_emit
            )


class TestTextInput:
    @pytest.mark.asyncio
    async def test_inline_text_item(self) -> None:
        connector = ConnectorAgent()
        items = await connector.open_input(
            InputSpec(type="text", content="Glicose: 118", name="ocr.txt"), noop_emit
        )

        assert items == [{"id": "text-1", "name": "ocr.txt", "content": "Glicose: 118"}]

    @pytest.mark.asyncio
    async def test_blank_content_rejected(self) -> None:
        connector = ConnectorAgent()

        with pytest.raises(InvalidConfig):
            await connector.open_input(InputSpec(type="text", content="  "), noop_emit)


class TestHttpDelivery:
    class _FakeResponse:
        def __init__(self, status_code: int = 200) -> None:
            self.status_code = status_code

    class _FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            self.calls = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def request(self, method, url, json=None, headers=None):
            TestHttpDelivery.last_call = {
                "method": method, "url": url, "json": json, "headers": headers,
            }
            return TestHttpDelivery._FakeResponse(TestHttpDelivery.status)

    status = 200
    last_call: dict = {}

    @pytest.mark.asyncio
    async def test_batch_post_with_bearer(self, monkeypatch) -> None:
        import spec.extraction.agents.connector as connector_module

        monkeypatch.setattr(connector_module.httpx, "AsyncClient", self._FakeClient)
        TestHttpDelivery.status = 200

        connector = ConnectorAgent()
        receipt = await connector.deliver(
            OutputSpec(type="api", target="https://tabex.test/v2/exames", token="TBX_1"),
            [{"exame": "Glicose"}],
            {},
            "genie-test",
            noop_emit,
        )

        assert receipt == {"mode": "api", "calls": 1, "status": [200]}
        assert TestHttpDelivery.last_call["headers"]["Authorization"] == "Bearer TBX_1"
        assert TestHttpDelivery.last_call["json"] == [{"exame": "Glicose"}]

    @pytest.mark.asyncio
    async def test_error_status_raises(self, monkeypatch) -> None:
        import spec.extraction.agents.connector as connector_module

        monkeypatch.setattr(connector_module.httpx, "AsyncClient", self._FakeClient)
        TestHttpDelivery.status = 500

        connector = ConnectorAgent()
        with pytest.raises(ExtractionFailed):
            await connector.deliver(
                OutputSpec(type="url", target="https://hooks.test/x"),
                [{"a": 1}],
                {},
                "genie-test",
                noop_emit,
            )

    @pytest.mark.asyncio
    async def test_invalid_scheme_rejected(self) -> None:
        connector = ConnectorAgent()
        with pytest.raises(InvalidConfig):
            await connector.deliver(
                OutputSpec(type="api", target="ftp://x"), [{}], {}, "j", noop_emit
            )


class TestXlsxParsing:
    def test_xlsx_roundtrip(self) -> None:
        import io

        from openpyxl import Workbook

        from spec.extraction.parsers.content import xlsx_bytes_to_text

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Exames"
        sheet.append(["exame", "resultado"])
        sheet.append(["Glicose", 118])
        buffer = io.BytesIO()
        workbook.save(buffer)

        text = xlsx_bytes_to_text(buffer.getvalue())

        assert "# Planilha: Exames" in text
        assert "Glicose\t118" in text
