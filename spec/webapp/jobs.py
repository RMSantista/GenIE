"""In-memory job registry with SSE event fan-out.

Runs live in process memory: events are kept for replay (reconnects with
Last-Event-ID) and fanned out to any number of SSE subscribers. Credentials
inside the original request are never serialized into events or results.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional

from spec.models.webapp import AgentEvent, RunRequest, RunStatus

logger = logging.getLogger(__name__)

_TERMINAL: frozenset = frozenset({"done", "error", "cancelled"})


class Job:
    """A single extraction run and its event history.

    Attributes:
        id: Job identifier
        request: Original run request (kept in memory only)
        status: Current run status
        events: Emitted events, in order
        result: Final result payload when finished
        error: Error message when failed
        task: Asyncio task executing the orchestration
    """

    def __init__(self, request: RunRequest) -> None:
        """Initialize a queued job for the given request."""

        self.id: str = f"genie-{uuid.uuid4().hex[:10]}"
        self.request = request
        self.status: RunStatus = "queued"
        self.events: List[AgentEvent] = []
        self.result: Optional[dict] = None
        self.error: Optional[str] = None
        self.task: Optional[asyncio.Task] = None
        self._subscribers: List[asyncio.Queue] = []
        self._seq = 0

    @property
    def is_finished(self) -> bool:
        """Whether the job reached a terminal status."""

        return self.status in _TERMINAL


class JobManager:
    """Registry and event bus for extraction runs."""

    def __init__(self, max_jobs: int = 200) -> None:
        """Initialize the manager.

        Args:
            max_jobs: Maximum retained jobs before oldest are evicted
        """

        self._jobs: Dict[str, Job] = {}
        self._max_jobs = max_jobs

    def create(self, request: RunRequest) -> Job:
        """Register a new job.

        Args:
            request: Validated run request

        Returns:
            Job: Newly created job (status "queued")
        """

        job = Job(request)
        self._jobs[job.id] = job

        while len(self._jobs) > self._max_jobs:
            oldest_id = next(iter(self._jobs))
            evicted = self._jobs.pop(oldest_id)
            if evicted.task and not evicted.task.done():
                evicted.task.cancel()

        return job

    def get(self, job_id: str) -> Optional[Job]:
        """Fetch a job by id.

        Args:
            job_id: Job identifier

        Returns:
            Optional[Job]: Job or None
        """

        return self._jobs.get(job_id)

    def emit(
        self,
        job: Job,
        agent: str,
        type: str,
        message: str = "",
        level: str = "",
        progress: Optional[int] = None,
        status: Optional[RunStatus] = None,
        result: Optional[dict] = None,
    ) -> AgentEvent:
        """Append an event to a job and fan it out to subscribers.

        Args:
            job: Target job
            agent: Emitting agent name
            type: Event type
            message: Human-readable message
            level: UI log level hint
            progress: Agent progress 0-100
            status: Run status for finish/error events
            result: Final result payload for finish events

        Returns:
            AgentEvent: The emitted event
        """

        job._seq += 1
        event = AgentEvent(
            seq=job._seq,
            ts=datetime.now().strftime("%H:%M:%S"),
            agent=agent,  # type: ignore[arg-type]
            type=type,  # type: ignore[arg-type]
            level=level,
            message=message,
            progress=progress,
            status=status,
            result=result,
        )
        job.events.append(event)

        for queue in list(job._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:  # pragma: no cover - unbounded queues
                logger.warning("Dropping event for slow subscriber on job %s", job.id)

        return event

    async def stream(
        self,
        job: Job,
        last_event_id: Optional[int] = None,
    ) -> AsyncGenerator[AgentEvent, None]:
        """Yield job events, replaying history then following live updates.

        Args:
            job: Job to follow
            last_event_id: Replay only events with seq greater than this

        Yields:
            AgentEvent: Each event in order
        """

        queue: asyncio.Queue = asyncio.Queue()
        job._subscribers.append(queue)

        try:
            replay_from = last_event_id or 0
            for event in list(job.events):
                if event.seq > replay_from:
                    yield event

            if job.is_finished:
                return

            while True:
                event = await queue.get()
                yield event
                if event.type in ("finish", "error") and event.status in _TERMINAL:
                    return
        finally:
            if queue in job._subscribers:
                job._subscribers.remove(queue)


_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """Get the global JobManager singleton.

    Returns:
        JobManager: Process-wide job registry
    """

    global _manager
    if _manager is None:
        _manager = JobManager()
    return _manager
