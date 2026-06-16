"""Multipart upload endpoint with sanitization and limits."""

import logging
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from spec.core.config import get_settings
from spec.extraction.agents.connector import new_upload_id
from spec.extraction.parsers.content import SUPPORTED_EXTENSIONS
from spec.models.webapp import UploadedFile, UploadResponse

logger = logging.getLogger(__name__)

router = APIRouter()

_SAFE_NAME_RE = re.compile(r"[^\w.\- ]", re.UNICODE)
_CHUNK = 1024 * 1024


def _sanitize_filename(raw: str, index: int) -> str:
    """Build a safe filename from a client-provided name.

    Args:
        raw: Original filename from the multipart part
        index: Position in the batch (fallback naming)

    Returns:
        str: Safe basename without path separators
    """

    name = Path(raw or f"arquivo-{index}").name
    name = _SAFE_NAME_RE.sub("_", name).strip(". ")
    return name or f"arquivo-{index}"


@router.post("", response_model=UploadResponse)
async def upload_files(files: list[UploadFile]) -> UploadResponse:
    """Receive files for a future run and store them under a batch id.

    Enforces per-file size limits, a batch count limit and an extension
    allowlist; filenames are sanitized against path traversal.

    Args:
        files: Multipart files

    Returns:
        UploadResponse: Batch id and accepted file metadata

    Raises:
        HTTPException: 400/413 for invalid or oversized uploads
    """

    settings = get_settings()

    if not files:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")
    if len(files) > settings.max_files_per_upload:
        raise HTTPException(
            status_code=400,
            detail=f"Máximo de {settings.max_files_per_upload} arquivos por envio",
        )

    upload_id = new_upload_id()
    upload_dir = Path(settings.uploads_dir) / upload_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    max_bytes = settings.max_upload_mb * 1024 * 1024
    accepted: list[UploadedFile] = []

    for index, upload in enumerate(files, 1):
        name = _sanitize_filename(upload.filename or "", index)
        suffix = Path(name).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Extensão não suportada: '{name}'. "
                f"Aceitas: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            )

        destination = upload_dir / name
        if destination.exists():
            destination = upload_dir / f"{Path(name).stem}-{index}{suffix}"

        size = 0
        with open(destination, "wb") as out:
            while chunk := await upload.read(_CHUNK):
                size += len(chunk)
                if size > max_bytes:
                    out.close()
                    destination.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"'{name}' excede o limite de {settings.max_upload_mb} MB",
                    )
                out.write(chunk)

        accepted.append(UploadedFile(name=destination.name, size=size))

    logger.info("Upload %s: %d file(s) accepted", upload_id, len(accepted))
    return UploadResponse(upload_id=upload_id, files=accepted)
