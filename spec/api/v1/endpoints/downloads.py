"""Signed, short-lived download endpoint for run artifacts."""

import logging
import re
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from spec.core.config import get_settings
from spec.core.security import get_cipher

logger = logging.getLogger(__name__)

router = APIRouter()

_JOB_ID_RE = re.compile(r"^genie-[a-f0-9]{10}$")
_ARTIFACT_RE = re.compile(r"^output\.(json|csv)$")

_MEDIA_TYPES = {".json": "application/json", ".csv": "text/csv"}


@router.get("/{job_id}/{artifact}")
async def download_artifact(
    job_id: str, artifact: str, exp: int, sig: str
) -> FileResponse:
    """Serve a run artifact when the signed link is valid and unexpired.

    Args:
        job_id: Run identifier
        artifact: Artifact filename (output.json / output.csv)
        exp: Expiration timestamp (unix seconds)
        sig: HMAC-SHA256 signature of "job_id:artifact:exp"

    Returns:
        FileResponse: The artifact

    Raises:
        HTTPException: 403 for invalid/expired links, 404 when missing
    """

    if not _JOB_ID_RE.match(job_id) or not _ARTIFACT_RE.match(artifact):
        raise HTTPException(status_code=403, detail="Link de download inválido")

    if exp < int(time.time()):
        raise HTTPException(status_code=403, detail="Link de download expirado")

    if not get_cipher().verify(f"{job_id}:{artifact}:{exp}", sig):
        raise HTTPException(status_code=403, detail="Assinatura de download inválida")

    settings = get_settings()
    path = (Path(settings.outputs_dir) / job_id / artifact).resolve()
    outputs_root = Path(settings.outputs_dir).resolve()
    if not path.is_relative_to(outputs_root) or not path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    return FileResponse(
        path,
        media_type=_MEDIA_TYPES.get(path.suffix, "application/octet-stream"),
        filename=f"genie-{job_id}{path.suffix}",
    )
