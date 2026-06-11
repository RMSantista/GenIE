"""Pydantic models for the GenIE web application (runs, keys, uploads)."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

InputType = Literal["url", "path", "db", "api", "upload"]
OutputType = Literal["url", "path", "db", "api", "download"]
AgentName = Literal["conector", "localizador", "organizador", "sistema"]
EventType = Literal["progress", "log", "done", "error", "finish"]
RunStatus = Literal["queued", "running", "done", "error", "cancelled"]


class InputSpec(BaseModel):
    """Source specification for the Connector agent.

    Attributes:
        type: Input kind (url, path, db, api, upload)
        target: Address (URL, filesystem path, DB URL, API endpoint)
        user: Username for db connections
        password: Password for db connections (transient, never persisted)
        token: Bearer token for api connections (transient, never persisted)
        query: Optional SQL query for db inputs
        upload_id: Upload batch id for upload inputs
    """

    type: InputType
    target: str = ""
    user: str = ""
    password: str = ""
    token: str = ""
    query: str = ""
    upload_id: Optional[str] = None


class OutputSpec(BaseModel):
    """Destination specification for the Connector agent.

    Attributes:
        type: Output kind (url, path, db, api, download)
        target: Address (webhook URL, path, DB URL, API endpoint)
        user: Username for db destinations
        password: Password for db destinations (transient)
        token: Bearer token for api destinations (transient)
        table: Destination table name for db outputs
    """

    type: OutputType
    target: str = ""
    user: str = ""
    password: str = ""
    token: str = ""
    table: str = ""


class RunRequest(BaseModel):
    """Request body for creating an extraction run.

    Attributes:
        model_id: Catalog model id (e.g. "gemini-2.5-flash")
        input: Input source spec
        prompt: What the Locator agent must extract
        output: Output destination spec
        format: Free-text instructions for the Organizer agent
    """

    model_id: str = Field(..., min_length=1)
    input: InputSpec
    prompt: str = Field(..., min_length=1)
    output: OutputSpec
    format: str = ""


class RunCreated(BaseModel):
    """Response for a created run."""

    job_id: str
    status: RunStatus


class RunInfo(BaseModel):
    """Current state of a run (no credentials are ever included).

    Attributes:
        job_id: Run identifier
        status: Current status
        model_id: Model used
        events: Number of emitted events
        result: Final result payload when done
        error: Error message when failed
    """

    job_id: str
    status: RunStatus
    model_id: str
    events: int
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AgentEvent(BaseModel):
    """Event streamed over SSE while a run executes.

    Attributes:
        seq: Monotonic sequence number within the run
        ts: Wall-clock time, HH:MM:SS
        agent: Emitting agent
        type: Event kind
        level: Log level hint for the UI ("", "ok", "error")
        message: Human-readable message
        progress: Agent progress 0-100 (when type == progress)
        status: Run status (when type == finish/error)
        result: Final result payload (when type == finish)
    """

    seq: int
    ts: str
    agent: AgentName
    type: EventType
    level: str = ""
    message: str = ""
    progress: Optional[int] = None
    status: Optional[RunStatus] = None
    result: Optional[Dict[str, Any]] = None


class ModelInfo(BaseModel):
    """Catalog entry for a selectable LLM model."""

    id: str
    provider: str
    provider_label: str
    label: str
    note: str
    has_key: bool
    masked_key: Optional[str] = None


class KeyRequest(BaseModel):
    """Request body for storing a provider API key."""

    provider: str = Field(..., min_length=1)
    key: str = Field(..., min_length=1)
    validate_key: bool = True


class KeyInfo(BaseModel):
    """Safe response after storing a key (never echoes the key)."""

    provider: str
    masked: str


class UploadedFile(BaseModel):
    """Metadata for one uploaded file."""

    name: str
    size: int


class UploadResponse(BaseModel):
    """Response for an upload batch."""

    upload_id: str
    files: List[UploadedFile]
