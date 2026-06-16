"""Connector agent: opens input sources and delivers formatted output.

The Connector never calls an LLM. It handles all I/O: URLs, local folders,
databases, REST APIs, uploaded files (input) and webhooks, folders,
databases, REST APIs and signed downloads (output).
"""

import csv
import json
import logging
import re
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List

import httpx

from spec.core.config import get_settings
from spec.core.exceptions import ExtractionFailed, InvalidConfig
from spec.extraction.parsers.content import (
    SUPPORTED_EXTENSIONS,
    bytes_to_text,
    file_to_text,
)
from spec.models.webapp import InputSpec, OutputSpec

logger = logging.getLogger(__name__)

EmitFn = Callable[..., None]

_MAX_DIR_FILES = 200
_MAX_API_ITEMS = 500
_API_BATCH_CHARS = 20_000
_HTTP_TIMEOUT = httpx.Timeout(60.0, connect=15.0)

_DRIVE_FILE_RE = re.compile(
    r"drive\.google\.com/(?:file/d/|open\?id=|uc\?.*id=)([\w-]+)"
)
_DRIVE_FOLDER_RE = re.compile(r"drive\.google\.com/drive/(?:u/\d+/)?folders/")
_SAFE_IDENT_RE = re.compile(r"[^A-Za-z0-9_]")
_UPLOAD_ID_RE = re.compile(r"^[a-f0-9]{32}$")


def _safe_identifier(name: str, fallback: str) -> str:
    """Sanitize a SQL identifier (table/column name).

    Args:
        name: Proposed identifier
        fallback: Used when nothing safe remains

    Returns:
        str: Identifier containing only [A-Za-z0-9_]
    """

    cleaned = _SAFE_IDENT_RE.sub("_", name.strip())[:64].strip("_")
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"{fallback}_{cleaned}" if cleaned else fallback
    return cleaned


def _redact_url(url: str) -> str:
    """Strip credentials from a URL for display/log purposes."""

    return re.sub(r"//[^/@]+@", "//••••@", url)


def allowed_fs_roots() -> List[Path]:
    """Resolve the filesystem roots GenIE may read from / write to.

    Returns:
        list[Path]: Allowed root directories
    """

    settings = get_settings()
    roots = [
        Path.home().resolve(),
        Path(settings.data_dir).resolve(),
        Path.cwd().resolve(),
    ]
    if settings.allowed_fs_roots:
        import os

        for raw in settings.allowed_fs_roots.split(os.pathsep):
            if raw.strip():
                roots.append(Path(raw.strip()).resolve())
    return roots


def ensure_path_allowed(path: Path) -> Path:
    """Resolve a path and verify it sits under an allowed root.

    Args:
        path: Path requested by the user

    Returns:
        Path: Resolved absolute path

    Raises:
        InvalidConfig: If the path escapes all allowed roots
    """

    resolved = path.expanduser().resolve()
    for root in allowed_fs_roots():
        if resolved == root or resolved.is_relative_to(root):
            return resolved
    raise InvalidConfig(
        f"Acesso negado ao caminho '{path}'. Caminhos permitidos: diretório do usuário, "
        "diretório do projeto e raízes definidas em ALLOWED_FS_ROOTS."
    )


class ConnectorAgent:
    """I/O layer of the GenIE pipeline (no LLM calls)."""

    async def open_input(self, spec: InputSpec, emit: EmitFn) -> List[Dict[str, Any]]:
        """Open the input source and return a list of content items.

        Args:
            spec: Input specification
            emit: Event emitter (agent fixed to "conector" by caller)

        Returns:
            list[dict]: Items with id, name and text content

        Raises:
            InvalidConfig: For unsupported/blocked sources
            ExtractionFailed: When the source cannot be read
        """

        if spec.type == "upload":
            return self._open_upload(spec, emit)
        if spec.type == "path":
            return self._open_path(spec, emit)
        if spec.type == "url":
            return await self._open_url(spec, emit)
        if spec.type == "api":
            return await self._open_api(spec, emit)
        if spec.type == "db":
            return self._open_db(spec, emit)
        if spec.type == "text":
            return self._open_text(spec, emit)
        raise InvalidConfig(f"Tipo de entrada não suportado: {spec.type}")

    # ── Inputs ────────────────────────────────────────────────────────────

    def _open_text(self, spec: InputSpec, emit: EmitFn) -> List[Dict[str, Any]]:
        """Wrap inline text content (sent by integrating apps) as a single item."""

        content = spec.content.strip()
        if not content:
            raise InvalidConfig(
                "Entrada 'text' requer o campo 'content' com o texto a analisar."
            )
        name = spec.name.strip() or "conteudo.txt"
        emit(message=f"Recebido conteúdo inline ({len(content)} caracteres)")
        return [{"id": "text-1", "name": name, "content": content[:400_000]}]

    def _open_upload(self, spec: InputSpec, emit: EmitFn) -> List[Dict[str, Any]]:
        """Read previously uploaded files for this run."""

        if not spec.upload_id or not _UPLOAD_ID_RE.match(spec.upload_id):
            raise InvalidConfig("Upload inválido: envie os arquivos antes de executar.")

        settings = get_settings()
        upload_dir = (Path(settings.uploads_dir) / spec.upload_id).resolve()
        if not upload_dir.is_dir():
            raise InvalidConfig(
                f"Upload '{spec.upload_id}' não encontrado ou expirado."
            )

        items = []
        for file_path in sorted(upload_dir.iterdir()):
            if not file_path.is_file():
                continue
            emit(message=f"Lendo arquivo enviado: {file_path.name}")
            items.append(
                {
                    "id": f"up-{len(items) + 1}",
                    "name": file_path.name,
                    "content": file_to_text(file_path),
                }
            )

        if not items:
            raise ExtractionFailed("Nenhum arquivo legível encontrado no upload.")
        return items

    def _open_path(self, spec: InputSpec, emit: EmitFn) -> List[Dict[str, Any]]:
        """Read a local file or recursively scan a folder."""

        if not spec.target.strip():
            raise InvalidConfig("Informe o caminho da pasta ou arquivo.")

        root = ensure_path_allowed(Path(spec.target))
        if not root.exists():
            raise InvalidConfig(f"Caminho não encontrado: {root}")

        files: List[Path]
        if root.is_file():
            files = [root]
        else:
            files = sorted(
                p
                for p in root.rglob("*")
                if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
            )[:_MAX_DIR_FILES]

        if not files:
            raise ExtractionFailed(
                f"Nenhum arquivo suportado em '{root}'. "
                f"Extensões: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        items = []
        for idx, file_path in enumerate(files, 1):
            emit(message=f"Lendo {file_path.name} ({idx}/{len(files)})")
            try:
                items.append(
                    {
                        "id": f"fs-{idx}",
                        "name": file_path.name,
                        "content": file_to_text(file_path),
                    }
                )
            except ExtractionFailed as e:
                emit(message=f"Ignorando {file_path.name}: {e}", level="error")

        if not items:
            raise ExtractionFailed("Nenhum arquivo pôde ser lido na pasta informada.")
        return items

    async def _open_url(self, spec: InputSpec, emit: EmitFn) -> List[Dict[str, Any]]:
        """Download a URL (HTML, PDF, JSON, text) and convert it to text."""

        url = spec.target.strip()
        if not url:
            raise InvalidConfig("Informe a URL de origem.")
        if not url.lower().startswith(("http://", "https://")):
            raise InvalidConfig("URL inválida: use http:// ou https://")

        if _DRIVE_FOLDER_RE.search(url):
            raise InvalidConfig(
                "Pastas do Google Drive exigem credenciais de service account "
                "(não configuradas). Use links diretos de arquivo, Upload ou Pasta local."
            )

        drive_match = _DRIVE_FILE_RE.search(url)
        if drive_match:
            url = (
                f"https://drive.google.com/uc?export=download&id={drive_match.group(1)}"
            )
            emit(message="Link do Google Drive convertido para download direto")

        emit(message=f"Baixando {_redact_url(url)}")
        async with httpx.AsyncClient(
            timeout=_HTTP_TIMEOUT, follow_redirects=True
        ) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise ExtractionFailed(f"Falha ao acessar a URL: {e}")

        name = Path(httpx.URL(url).path).name or "pagina.html"
        content = bytes_to_text(
            response.content, name, response.headers.get("content-type")
        )
        return [{"id": "url-1", "name": name, "content": content}]

    async def _open_api(self, spec: InputSpec, emit: EmitFn) -> List[Dict[str, Any]]:
        """Call a REST API (GET, optional Bearer token) and batch the JSON."""

        url = spec.target.strip()
        if not url.lower().startswith(("http://", "https://")):
            raise InvalidConfig("Endpoint de API inválido: use http:// ou https://")

        headers = {"Accept": "application/json"}
        if spec.token.strip():
            headers["Authorization"] = f"Bearer {spec.token.strip()}"

        emit(message=f"Consultando API {_redact_url(url)}")
        async with httpx.AsyncClient(
            timeout=_HTTP_TIMEOUT, follow_redirects=True
        ) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise ExtractionFailed(f"Falha na chamada à API de entrada: {e}")

        try:
            payload = response.json()
        except json.JSONDecodeError:
            return [
                {
                    "id": "api-1",
                    "name": "resposta.txt",
                    "content": bytes_to_text(
                        response.content,
                        "resposta.txt",
                        response.headers.get("content-type"),
                    ),
                }
            ]

        elements = payload if isinstance(payload, list) else [payload]
        elements = elements[:_MAX_API_ITEMS]

        items: List[Dict[str, Any]] = []
        batch: List[str] = []
        batch_chars = 0
        for element in elements:
            text = json.dumps(element, ensure_ascii=False, indent=2)
            if batch and batch_chars + len(text) > _API_BATCH_CHARS:
                items.append(
                    {
                        "id": f"api-{len(items) + 1}",
                        "name": f"lote-{len(items) + 1}.json",
                        "content": "\n".join(batch),
                    }
                )
                batch, batch_chars = [], 0
            batch.append(text)
            batch_chars += len(text)
        if batch:
            items.append(
                {
                    "id": f"api-{len(items) + 1}",
                    "name": f"lote-{len(items) + 1}.json",
                    "content": "\n".join(batch),
                }
            )
        return items

    def _open_db(self, spec: InputSpec, emit: EmitFn) -> List[Dict[str, Any]]:
        """Read rows from a database (SQLite natively, others via SQLAlchemy)."""

        target = spec.target.strip()
        if not target:
            raise InvalidConfig("Informe a URL do banco (ex.: sqlite:///dados.db)")

        if target.startswith("sqlite:///") or target.endswith(
            (".db", ".sqlite", ".sqlite3")
        ):
            return self._open_sqlite(target, spec.query, emit)
        return self._open_sqlalchemy(spec, emit)

    def _open_sqlite(
        self, target: str, query: str, emit: EmitFn
    ) -> List[Dict[str, Any]]:
        """Read a SQLite database in read-only mode."""

        raw_path = (
            target[len("sqlite:///") :] if target.startswith("sqlite:///") else target
        )
        db_path = ensure_path_allowed(Path(raw_path))
        if not db_path.is_file():
            raise InvalidConfig(f"Banco SQLite não encontrado: {db_path}")

        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            if query.strip():
                emit(message="Executando consulta personalizada")
                rows = conn.execute(query).fetchmany(2000)
                return [self._rows_item("consulta", rows)]

            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
            ]
            if not tables:
                raise ExtractionFailed("Banco SQLite sem tabelas de usuário.")

            items = []
            for table in tables[:20]:
                safe = _safe_identifier(table, "tabela")
                emit(message=f"Lendo tabela {safe}")
                rows = conn.execute(f'SELECT * FROM "{safe}" LIMIT 500').fetchall()
                items.append(self._rows_item(safe, rows))
            return items
        except sqlite3.Error as e:
            raise ExtractionFailed(f"Erro ao ler o banco SQLite: {e}")
        finally:
            conn.close()

    def _open_sqlalchemy(self, spec: InputSpec, emit: EmitFn) -> List[Dict[str, Any]]:
        """Read external databases (Postgres/MySQL/…) via SQLAlchemy if installed."""

        try:
            import sqlalchemy
        except ImportError:
            raise InvalidConfig(
                "Para conectar a este banco instale: pip install sqlalchemy "
                "e o driver adequado (psycopg2-binary, pymysql, …). "
                "Bancos SQLite funcionam sem dependências extras."
            )

        url = sqlalchemy.engine.make_url(spec.target)
        if spec.user:
            url = url.set(username=spec.user)
        if spec.password:
            url = url.set(password=spec.password)

        emit(message=f"Conectando a {url.render_as_string(hide_password=True)}")
        engine = sqlalchemy.create_engine(url)
        try:
            with engine.connect() as conn:
                if spec.query.strip():
                    result = conn.execute(sqlalchemy.text(spec.query))
                    rows = [dict(r._mapping) for r in result.fetchmany(2000)]
                    return [self._rows_item("consulta", rows)]

                inspector = sqlalchemy.inspect(engine)
                items = []
                for table in inspector.get_table_names()[:20]:
                    emit(message=f"Lendo tabela {table}")
                    result = conn.execute(
                        sqlalchemy.text(f'SELECT * FROM "{table}" LIMIT 500')
                    )
                    rows = [dict(r._mapping) for r in result.fetchall()]
                    items.append(self._rows_item(table, rows))
                return items
        except sqlalchemy.exc.SQLAlchemyError as e:
            raise ExtractionFailed(f"Erro ao ler o banco de dados: {e}")
        finally:
            engine.dispose()

    @staticmethod
    def _rows_item(name: str, rows: Any) -> Dict[str, Any]:
        """Serialize DB rows into a text item for the Locator."""

        dicts = [dict(r) for r in rows]
        return {
            "id": f"db-{name}",
            "name": f"{name} ({len(dicts)} linhas)",
            "content": json.dumps(dicts, ensure_ascii=False, indent=1, default=str),
        }

    # ── Outputs ───────────────────────────────────────────────────────────

    async def deliver(
        self,
        spec: OutputSpec,
        records: List[Any],
        hints: Dict[str, Any],
        job_id: str,
        emit: EmitFn,
    ) -> Dict[str, Any]:
        """Deliver formatted records to the configured destination.

        Args:
            spec: Output specification
            records: Formatted payloads from the Organizer
            hints: Delivery hints (method, headers, batch) from the Organizer
            job_id: Run identifier (used for download artifacts)
            emit: Event emitter

        Returns:
            dict: Delivery receipt (never includes credentials)
        """

        if spec.type == "download":
            return self._deliver_download(records, job_id, emit)
        if spec.type == "path":
            return self._deliver_path(spec, records, emit)
        if spec.type in ("url", "api"):
            return await self._deliver_http(spec, records, hints, emit)
        if spec.type == "db":
            return self._deliver_db(spec, records, emit)
        raise InvalidConfig(f"Tipo de saída não suportado: {spec.type}")

    def _write_artifacts(self, records: List[Any], directory: Path) -> Dict[str, str]:
        """Write output.json (+ output.csv when tabular) into a directory."""

        directory.mkdir(parents=True, exist_ok=True)
        json_path = directory / "output.json"
        json_path.write_text(
            json.dumps(records, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        artifacts = {"json": str(json_path)}

        flat = [r for r in records if isinstance(r, dict)]
        if flat:
            columns: List[str] = []
            for record in flat:
                for key in record:
                    if not str(key).startswith("_") and key not in columns:
                        columns.append(key)
            if columns:
                csv_path = directory / "output.csv"
                # utf-8-sig (BOM) so Excel pt-BR opens accents correctly.
                with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(
                        f, fieldnames=columns, extrasaction="ignore"
                    )
                    writer.writeheader()
                    for record in flat:
                        writer.writerow({k: record.get(k, "") for k in columns})
                artifacts["csv"] = str(csv_path)
        return artifacts

    def _deliver_download(
        self, records: List[Any], job_id: str, emit: EmitFn
    ) -> Dict[str, Any]:
        """Persist artifacts for signed in-browser download."""

        settings = get_settings()
        directory = Path(settings.outputs_dir) / job_id
        artifacts = self._write_artifacts(records, directory)
        emit(
            message=f"Arquivo(s) de saída gerado(s): {', '.join(Path(p).name for p in artifacts.values())}"
        )
        return {
            "mode": "download",
            "artifacts": sorted(Path(p).name for p in artifacts.values()),
        }

    def _deliver_path(
        self, spec: OutputSpec, records: List[Any], emit: EmitFn
    ) -> Dict[str, Any]:
        """Write artifacts into a user-specified local folder."""

        if not spec.target.strip():
            raise InvalidConfig("Informe a pasta de destino.")
        directory = ensure_path_allowed(Path(spec.target))
        if directory.suffix:
            directory = directory.parent / directory.stem
        artifacts = self._write_artifacts(records, directory)
        emit(message=f"Gravado em {directory}")
        return {
            "mode": "path",
            "directory": str(directory),
            "files": sorted(Path(p).name for p in artifacts.values()),
        }

    async def _deliver_http(
        self,
        spec: OutputSpec,
        records: List[Any],
        hints: Dict[str, Any],
        emit: EmitFn,
    ) -> Dict[str, Any]:
        """POST records to a webhook (url) or REST API (api, Bearer auth)."""

        url = spec.target.strip()
        if not url.lower().startswith(("http://", "https://")):
            raise InvalidConfig("Destino HTTP inválido: use http:// ou https://")

        headers = {"Content-Type": "application/json"}
        for key, value in (hints.get("headers") or {}).items():
            if str(key).lower() != "authorization":
                headers[str(key)] = str(value)
        if spec.type == "api" and spec.token.strip():
            headers["Authorization"] = f"Bearer {spec.token.strip()}"

        method = str(hints.get("method") or "POST").upper()
        batch = bool(hints.get("batch", True))

        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            if batch:
                emit(
                    message=f"Enviando {len(records)} registro(s) em lote para {_redact_url(url)}"
                )
                response = await client.request(
                    method, url, json=records, headers=headers
                )
                statuses = [response.status_code]
            else:
                statuses = []
                for idx, record in enumerate(records[:100], 1):
                    emit(
                        message=f"POST {idx}/{min(len(records), 100)} → {_redact_url(url)}"
                    )
                    response = await client.request(
                        method, url, json=record, headers=headers
                    )
                    statuses.append(response.status_code)

        failed = [s for s in statuses if s >= 400]
        if failed:
            raise ExtractionFailed(
                f"Destino HTTP retornou erro(s): {sorted(set(failed))} "
                f"em {len(failed)}/{len(statuses)} chamada(s)."
            )
        return {
            "mode": spec.type,
            "calls": len(statuses),
            "status": sorted(set(statuses)),
        }

    def _deliver_db(
        self, spec: OutputSpec, records: List[Any], emit: EmitFn
    ) -> Dict[str, Any]:
        """Insert records into a SQLite table (created/extended automatically)."""

        target = spec.target.strip()
        if not (
            target.startswith("sqlite:///")
            or target.endswith((".db", ".sqlite", ".sqlite3"))
        ):
            raise InvalidConfig(
                "Saída para banco suporta SQLite nativamente (sqlite:///caminho.db). "
                "Para outros bancos use a saída 'API REST' de um serviço intermediário "
                "ou instale sqlalchemy + driver."
            )

        raw_path = (
            target[len("sqlite:///") :] if target.startswith("sqlite:///") else target
        )
        db_path = ensure_path_allowed(Path(raw_path))
        db_path.parent.mkdir(parents=True, exist_ok=True)

        flat = [r for r in records if isinstance(r, dict)]
        if not flat:
            raise ExtractionFailed("Nenhum registro tabular para inserir no banco.")

        table = _safe_identifier(spec.table or "genie_output", "genie_output")
        columns: List[str] = []
        for record in flat:
            for key in record:
                safe = _safe_identifier(str(key), "campo")
                if not safe.startswith("_") and safe not in columns:
                    columns.append(safe)

        conn = sqlite3.connect(db_path)
        try:
            cols_sql = ", ".join(f'"{c}" TEXT' for c in columns)
            conn.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({cols_sql})')
            existing = {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')}
            for column in columns:
                if column not in existing:
                    conn.execute(f'ALTER TABLE "{table}" ADD COLUMN "{column}" TEXT')

            placeholders = ", ".join("?" for _ in columns)
            quoted = ", ".join(f'"{c}"' for c in columns)
            for record in flat:
                by_safe_key = {
                    _safe_identifier(str(k), "campo"): v for k, v in record.items()
                }
                values = []
                for column in columns:
                    value = by_safe_key.get(column)
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value, ensure_ascii=False, default=str)
                    elif value is not None:
                        value = str(value)
                    values.append(value)
                conn.execute(
                    f'INSERT INTO "{table}" ({quoted}) VALUES ({placeholders})', values
                )
            conn.commit()
        except sqlite3.Error as e:
            raise ExtractionFailed(f"Erro ao gravar no banco: {e}")
        finally:
            conn.close()

        emit(message=f"{len(flat)} registro(s) inseridos em {db_path.name}:{table}")
        return {
            "mode": "db",
            "database": str(db_path),
            "table": table,
            "rows": len(flat),
        }


def new_upload_id() -> str:
    """Generate a new upload batch identifier.

    Returns:
        str: 32-char hex id
    """

    return uuid.uuid4().hex
