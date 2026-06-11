"""Orchestrator: drives Conector → Localizador → Organizador → Conector.

Emits real-time events through the JobManager so the web UI can render
agent progress, the execution log and the final result.
"""

import asyncio
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from spec.core.config import get_settings
from spec.core.exceptions import GenieException
from spec.core.security import get_cipher, get_key_vault
from spec.extraction.agents.connector import ConnectorAgent
from spec.extraction.agents.locator import LocatorAgent
from spec.extraction.agents.organizer import OrganizerAgent
from spec.extraction.llm.factory import LLMProviderFactory
from spec.models.webapp import InputSpec, OutputSpec
from spec.webapp.catalog import find_model
from spec.webapp.jobs import Job, JobManager

logger = logging.getLogger(__name__)

_IN_LABELS = {
    "url": "URL",
    "path": "Pasta local",
    "db": "Banco de dados",
    "api": "API REST",
    "upload": "Upload",
}
_OUT_LABELS = {
    "url": "URL (webhook)",
    "path": "Pasta local",
    "db": "Banco de dados",
    "api": "API REST",
    "download": "Download",
}


def _display_target(spec: InputSpec | OutputSpec) -> str:
    """Build a credential-free display string for a source/destination."""

    target = re.sub(r"//[^/@]+@", "//••••@", spec.target or "")
    if isinstance(spec, InputSpec) and spec.type == "upload":
        return "arquivos enviados"
    if not target:
        return "saida.json" if getattr(spec, "type", "") == "download" else "—"
    return target


def build_download_links(job_id: str, artifacts: List[str]) -> Dict[str, str]:
    """Create short-lived signed download URLs for run artifacts.

    Args:
        job_id: Run identifier
        artifacts: Artifact filenames (e.g. ["output.csv", "output.json"])

    Returns:
        dict: Format → relative signed URL
    """

    settings = get_settings()
    cipher = get_cipher()
    expires = int(time.time()) + settings.download_link_ttl_seconds

    links: Dict[str, str] = {}
    for name in artifacts:
        fmt = name.rsplit(".", 1)[-1]
        signature = cipher.sign(f"{job_id}:{name}:{expires}")
        links[fmt] = f"/api/v1/downloads/{job_id}/{name}?exp={expires}&sig={signature}"
    return links


class Orchestrator:
    """Tech-lead of the three agents: coordinates, never extracts by itself."""

    def __init__(self, manager: JobManager) -> None:
        """Initialize the orchestrator.

        Args:
            manager: Job registry used for event emission
        """

        self.manager = manager

    def _resolve_provider(self, model_id: str):
        """Build the LLM provider for a catalog model using the encrypted vault.

        Args:
            model_id: Catalog model id

        Returns:
            BaseLLMProvider: Ready-to-use provider

        Raises:
            GenieException: If the model is unknown or has no key
        """

        model = find_model(model_id)
        if model is None:
            raise GenieException(f"Modelo desconhecido: {model_id}")

        api_key = get_key_vault().get_plaintext(model["provider"])
        factory = LLMProviderFactory()
        return factory.get_provider(
            provider_name=model["provider"],
            model=model["id"],
            api_key=api_key,
        )

    async def run_job(self, job: Job) -> None:
        """Execute the full pipeline for a job, emitting events throughout.

        Args:
            job: Job created by the JobManager (status "queued")
        """

        emit = self.manager.emit
        request = job.request
        model = find_model(request.model_id) or {"label": request.model_id}
        started = time.monotonic()

        def agent_emit(agent: str):
            def _fn(
                message: str = "", level: str = "", progress: Optional[int] = None
            ) -> None:
                emit(
                    job,
                    agent=agent,
                    type="progress" if progress is not None else "log",
                    message=message,
                    level=level,
                    progress=progress,
                )

            return _fn

        job.status = "running"
        connector = ConnectorAgent()

        try:
            emit(
                job,
                agent="sistema",
                type="log",
                message=f"Sessão iniciada · modelo={model['label']}",
            )

            # Resolve provider first: fail fast if the key is missing.
            provider = self._resolve_provider(request.model_id)

            # ── Conector: input ─────────────────────────────────────────
            in_label = _IN_LABELS.get(request.input.type, request.input.type)
            emit(
                job,
                agent="conector",
                type="progress",
                progress=10,
                message=f"Abrindo canal de entrada ({in_label})…",
            )
            items = await connector.open_input(request.input, agent_emit("conector"))
            emit(
                job,
                agent="conector",
                type="done",
                progress=100,
                level="ok",
                message=f"Conexão estabelecida · {len(items)} item(ns) enumerado(s)",
            )

            # ── Localizador ─────────────────────────────────────────────
            emit(
                job,
                agent="localizador",
                type="progress",
                progress=5,
                message="Carregando contexto da extração…",
            )
            preview = request.prompt[:96] + ("…" if len(request.prompt) > 96 else "")
            emit(job, agent="localizador", type="log", message=f'Prompt: "{preview}"')
            locator = LocatorAgent(provider)
            records, confidence, notes = await locator.run(
                items, request.prompt, agent_emit("localizador")
            )
            for note in notes[:5]:
                emit(job, agent="localizador", type="log", message=f"Nota: {note}")
            emit(
                job,
                agent="localizador",
                type="done",
                progress=100,
                level="ok",
                message=f"Extração concluída · {len(records)} registro(s) · confiança={confidence:.2f}",
            )

            # ── Organizador ─────────────────────────────────────────────
            emit(
                job,
                agent="organizador",
                type="progress",
                progress=10,
                message="Validando schema de saída…",
            )
            organizer = OrganizerAgent(provider)
            formatted, hints = await organizer.run(
                records, request.format, request.output.type, agent_emit("organizador")
            )
            emit(
                job,
                agent="organizador",
                type="done",
                progress=100,
                level="ok",
                message=f"{len(formatted)} registro(s) prontos para entrega",
            )

            # ── Conector: delivery ──────────────────────────────────────
            out_label = _OUT_LABELS.get(request.output.type, request.output.type)
            emit(
                job,
                agent="conector",
                type="log",
                message=f"Reabrindo canal de saída ({out_label})…",
            )
            receipt = await connector.deliver(
                request.output, formatted, hints, job.id, agent_emit("conector")
            )
            emit(
                job,
                agent="conector",
                type="log",
                level="ok",
                message="Entrega concluída",
            )

            download_links: Dict[str, str] = {}
            if request.output.type == "download":
                download_links = build_download_links(
                    job.id, receipt.get("artifacts", [])
                )

            elapsed = time.monotonic() - started
            result: Dict[str, Any] = {
                "job_id": job.id,
                "model": model["label"],
                "source": {
                    "type": request.input.type,
                    "target": _display_target(request.input),
                },
                "extraction": request.prompt,
                "delivered_to": {
                    "type": request.output.type,
                    "target": _display_target(request.output),
                    "format": request.format or "json",
                },
                "records": [r for r in formatted if isinstance(r, dict)] or records,
                "confidence": confidence,
                "receipt": receipt,
                "downloads": download_links,
                "delivered_at": datetime.now(timezone.utc).isoformat(),
            }

            job.result = result
            job.status = "done"
            emit(
                job,
                agent="sistema",
                type="finish",
                level="ok",
                status="done",
                message=f"Job {job.id} finalizado em {elapsed:.2f}s",
                result=result,
            )

        except asyncio.CancelledError:
            job.status = "cancelled"
            job.error = "Execução interrompida pelo usuário"
            emit(
                job,
                agent="sistema",
                type="error",
                level="error",
                status="cancelled",
                message="Execução interrompida pelo usuário",
            )
            raise
        except GenieException as e:
            job.status = "error"
            job.error = str(e)
            emit(
                job,
                agent="sistema",
                type="error",
                level="error",
                status="error",
                message=str(e),
            )
        except Exception as e:  # noqa: BLE001 - last-resort guard for the task
            logger.error("Job %s crashed: %s", job.id, e, exc_info=True)
            job.status = "error"
            job.error = f"Erro interno: {e}"
            emit(
                job,
                agent="sistema",
                type="error",
                level="error",
                status="error",
                message=f"Erro interno: {e}",
            )
