# GenIE Coding Conventions

## The 10 Code Standards

1. **Type hints on ALL functions and methods** — no exceptions
2. **Pydantic v2 for all data models** — never use plain dicts for structured data
3. **async/await for all I/O operations** — database, file, network, LLM calls
4. **Google-style docstrings on all public classes and methods**
5. **Custom exceptions only** — never raise bare `Exception` or `ValueError`
6. **Dependency injection via FastAPI `Depends()`** — no global state
7. **Config-driven behavior** — never hardcode values; use `core/config.py` settings
8. **Structured logging with context** — include extraction_id, config_id, layout_fingerprint
9. **Happy path first** — handle the expected case before edge cases
10. **Tests for every public function** — minimum 80% coverage target

## Exception Hierarchy

All custom exceptions inherit from `GenieException`. Raise the most specific exception available.

```python
class GenieException(Exception):
    """Base exception for all GenIE errors."""
    def __init__(self, message: str, details: dict | None = None) -> None:
        self.details = details or {}
        super().__init__(message)

class InvalidConfig(GenieException):
    """Bad or missing configuration. Raise when config_id not found or config validation fails."""

class ExtractionFailed(GenieException):
    """Extraction process failed. Raise when the engine cannot produce a result."""

class LLMProviderError(GenieException):
    """LLM API error. Raise on timeout, rate limit, auth failure, or malformed response."""

class LayoutNotRecognized(GenieException):
    """Layout not in library. Raise when fingerprint has no matching pattern."""

class StorageError(GenieException):
    """Search Library error. Raise on read/write failures in JSON or SQLite storage."""
```

### Usage Examples

```python
# Validating configuration
async def get_config(config_id: str) -> ExtractionConfig:
    config = await storage.load(config_id)
    if config is None:
        raise InvalidConfig(f"Configuration not found: {config_id}")
    return config

# LLM provider call with proper error handling
async def call_llm(prompt: str) -> str:
    try:
        response = await self.client.messages.create(...)
        return response.content[0].text
    except anthropic.APIError as e:
        raise LLMProviderError(
            f"Anthropic API failed: {e}",
            details={"provider": "anthropic", "status": e.status_code},
        ) from e

# Search Library lookup
async def find_pattern(fingerprint: str) -> SearchPattern | None:
    try:
        return await self.storage.get_by_fingerprint(fingerprint)
    except Exception as e:
        raise StorageError(
            f"Failed to query Search Library: {e}",
            details={"fingerprint": fingerprint},
        ) from e
```

## Naming Conventions

Name things by **WHAT** they represent, not **HOW** they work:

| Good                    | Bad                       | Why                              |
|-------------------------|---------------------------|----------------------------------|
| `extraction_result`     | `llm_output_dict`         | Describes purpose, not mechanism |
| `find_matching_pattern` | `query_sqlite_patterns`   | Storage backend may change       |
| `OutputAdapter`         | `JsonWriter`              | Strategy may vary                |
| `layout_fingerprint`    | `hash_string`             | Domain meaning over implementation |

## No Hardcoding

Every configurable value must come from `core/config.py` (Pydantic Settings):

```python
# WRONG — hardcoded
TIMEOUT = 30
MAX_RETRIES = 3

# RIGHT — config-driven
from genie.core.config import get_settings

settings = get_settings()
timeout = settings.llm_timeout
max_retries = settings.llm_max_retries
```

## Happy Path First

Structure functions with the expected flow at the top level. Handle edge cases with early returns or assertions:

```python
async def extract(self, request: ExtractionRequest) -> ExtractionResponse:
    """Extract data from source document."""
    config = await self._load_config(request.config_id)
    content = await self._read_content(request.source)
    fingerprint = self._generate_fingerprint(content)

    # Happy path: pattern exists in library
    pattern = await self._find_pattern(fingerprint)
    if pattern:
        return await self._apply_pattern(pattern, content)

    # Fallback: LLM extraction
    result = await self._extract_with_llm(config, content)
    await self._save_pattern(fingerprint, result.pattern)
    return result
```

## Design Patterns

### Factory — LLM Providers

```python
class LLMProviderFactory:
    _providers: dict[str, type[BaseLLMProvider]] = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "google": GoogleProvider,
    }

    @classmethod
    def create(cls, provider_name: str, **kwargs) -> BaseLLMProvider:
        provider_class = cls._providers.get(provider_name)
        if not provider_class:
            raise InvalidConfig(f"Unknown LLM provider: {provider_name}")
        return provider_class(**kwargs)
```

### Strategy — Output Adapters

```python
class OutputManager:
    def __init__(self, adapters: dict[str, OutputAdapter]) -> None:
        self._adapters = adapters

    async def format(self, data: list[dict], format_type: str) -> bytes:
        adapter = self._adapters.get(format_type)
        if not adapter:
            raise InvalidConfig(f"Unsupported output format: {format_type}")
        return await adapter.convert(data)
```

### ABC — Extensible Components

```python
from abc import ABC, abstractmethod

class BaseStorage(ABC):
    @abstractmethod
    async def get_by_fingerprint(self, fingerprint: str) -> SearchPattern | None: ...

    @abstractmethod
    async def save_pattern(self, pattern: SearchPattern) -> None: ...

class BaseLLMProvider(ABC):
    @abstractmethod
    async def extract(self, prompt: str, content: str) -> ExtractionResult: ...

    @abstractmethod
    async def health_check(self) -> bool: ...
```

## Async Patterns

Always use async I/O. Never block the event loop:

```python
# File I/O
import aiofiles
async with aiofiles.open(path, mode="r") as f:
    content = await f.read()

# SQLite
import aiosqlite
async with aiosqlite.connect(db_path) as db:
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()

# HTTP calls
import httpx
async with httpx.AsyncClient() as client:
    response = await client.post(url, json=payload, timeout=settings.http_timeout)
```

## Pydantic v2 Model Conventions

```python
from pydantic import BaseModel, Field, ConfigDict

class ExtractionRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    config_id: str = Field(..., description="Configuration identifier")
    source: SourceInput = Field(..., description="Input source specification")
    options: ExtractionOptions = Field(default_factory=ExtractionOptions)
```
