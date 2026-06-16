"""Run lifecycle endpoints: create, inspect, cancel and stream via SSE."""

import asyncio
import json
import logging
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from spec.core.config import get_settings
from spec.core.security import get_key_vault
from spec.extraction.agents.orchestrator import Orchestrator
from spec.models.webapp import RunCreated, RunInfo, RunRequest
from spec.webapp.catalog import find_model
from spec.webapp.jobs import get_job_manager

logger = logging.getLogger(__name__)

router = APIRouter()

_HEARTBEAT_SECONDS = 15.0


def _has_provider_key(provider: str) -> bool:
    """Check key availability: encrypted vault first, env fallback.

    Args:
        provider: Provider name

    Returns:
        bool: True if a key is available
    """

    if get_key_vault().has(provider):
        return True
    settings = get_settings()
    env_keys = {
        "google": settings.google_api_key,
        "openai": settings.openai_api_key,
        "anthropic": settings.anthropic_api_key,
    }
    return bool(env_keys.get(provider))


@router.post("", response_model=RunCreated, status_code=201)
async def create_run(request: RunRequest) -> RunCreated:
    """Create and start an extraction run.

    Args:
        request: Model, input, prompt, output and format

    Returns:
        RunCreated: Job id with initial status

    Raises:
        HTTPException: 400 for unknown model or missing key/input
    """

    model = find_model(request.model_id)
    if model is None:
        raise HTTPException(
            status_code=400, detail=f"Modelo desconhecido: {request.model_id}"
        )

    if not _has_provider_key(model["provider"]):
        raise HTTPException(
            status_code=400,
            detail=f"Configure uma API Key para {model['provider_label']} antes de executar.",
        )

    if request.input.type == "upload" and not request.input.upload_id:
        raise HTTPException(
            status_code=400, detail="Envie os arquivos antes de executar (upload)."
        )
    if request.input.type == "text" and not request.input.content.strip():
        raise HTTPException(
            status_code=400, detail="Entrada 'text' requer o campo 'content'."
        )
    if (
        request.input.type not in ("upload", "text")
        and not request.input.target.strip()
    ):
        raise HTTPException(
            status_code=400, detail="Informe o endereço da origem dos dados."
        )
    if request.output.type not in ("download",) and not request.output.target.strip():
        raise HTTPException(
            status_code=400, detail="Informe o endereço do destino dos dados."
        )

    manager = get_job_manager()
    job = manager.create(request)
    orchestrator = Orchestrator(manager)
    job.task = asyncio.create_task(orchestrator.run_job(job))

    logger.info(
        "Run %s created (model=%s, in=%s, out=%s)",
        job.id,
        request.model_id,
        request.input.type,
        request.output.type,
    )
    return RunCreated(job_id=job.id, status=job.status)


@router.get("/{job_id}", response_model=RunInfo)
async def get_run(job_id: str) -> RunInfo:
    """Return the current state of a run.

    Args:
        job_id: Run identifier

    Returns:
        RunInfo: Status, event count, result/error
    """

    job = get_job_manager().get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' não encontrado")
    return RunInfo(
        job_id=job.id,
        status=job.status,
        model_id=job.request.model_id,
        events=len(job.events),
        result=job.result,
        error=job.error,
    )


@router.post("/{job_id}/cancel", response_model=RunInfo)
async def cancel_run(job_id: str) -> RunInfo:
    """Cancel a running job (also aborts in-flight LLM calls).

    Args:
        job_id: Run identifier

    Returns:
        RunInfo: Updated state
    """

    manager = get_job_manager()
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' não encontrado")

    if job.task and not job.task.done():
        job.task.cancel()
        try:
            await job.task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass

    return RunInfo(
        job_id=job.id,
        status=job.status,
        model_id=job.request.model_id,
        events=len(job.events),
        result=job.result,
        error=job.error,
    )


@router.get("/{job_id}/events")
async def stream_events(job_id: str, request: Request) -> StreamingResponse:
    """Stream run events as Server-Sent Events.

    Replays history when ``Last-Event-ID`` is provided, then follows live
    events until the run finishes. Sends heartbeat comments to keep proxies
    from closing the connection.

    Args:
        job_id: Run identifier
        request: Incoming request (for Last-Event-ID and disconnects)

    Returns:
        StreamingResponse: text/event-stream
    """

    manager = get_job_manager()
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' não encontrado")

    last_id: Optional[int] = None
    header = request.headers.get("last-event-id")
    if header and header.isdigit():
        last_id = int(header)

    async def event_source() -> AsyncGenerator[str, None]:
        stream = manager.stream(job, last_event_id=last_id)
        iterator = stream.__aiter__()
        try:
            while True:
                if await request.is_disconnected():
                    return
                try:
                    event = await asyncio.wait_for(
                        iterator.__anext__(), timeout=_HEARTBEAT_SECONDS
                    )
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                    continue
                except StopAsyncIteration:
                    return
                payload = json.dumps(
                    event.model_dump(exclude_none=True), ensure_ascii=False
                )
                yield f"id: {event.seq}\ndata: {payload}\n\n"
        finally:
            await stream.aclose()

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
