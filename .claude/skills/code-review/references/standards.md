# GenIE Code Standards

10 mandatory standards for all GenIE code. Each has explicit pass/fail criteria.

---

## 1. Type Hints on ALL Functions/Methods

**Pass:** Every function and method has complete type hints for parameters and return value.

**Fail:**
- Any function missing parameter or return type hints
- Use of `Any` without a justification comment
- Missing generic types (e.g., `list` instead of `list[str]`)

```python
# Pass
async def extract(self, request: ExtractionRequest) -> ExtractionResponse: ...

# Fail
async def extract(self, request): ...
def process(data) -> Any: ...
```

---

## 2. Async/Await for ALL I/O

**Pass:** All I/O operations (file, network, database) use `async/await`. No blocking calls in async context.

**Fail:**
- `open()` instead of `aiofiles.open()` in async functions
- `requests.get()` instead of `httpx.AsyncClient` in async context
- Synchronous database calls in async functions
- `time.sleep()` instead of `asyncio.sleep()` in async context

```python
# Pass
async def read_file(path: str) -> str:
    async with aiofiles.open(path) as f:
        return await f.read()

# Fail
async def read_file(path: str) -> str:
    with open(path) as f:  # BLOCKING in async context
        return f.read()
```

---

## 3. Pydantic v2 for ALL Data Models

**Pass:** All data structures use Pydantic v2 `BaseModel`. Configuration uses `BaseSettings`.

**Fail:**
- Plain dataclasses for API models
- Raw dicts passed between components
- Pydantic v1 syntax (`class Config:` instead of `model_config`)
- Missing field validators where data integrity matters

```python
# Pass
class ExtractionRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    config_id: str
    source: Source

# Fail
@dataclass
class ExtractionRequest:
    config_id: str
    source: dict
```

---

## 4. Dependency Injection via FastAPI Depends()

**Pass:** All service dependencies injected through `Depends()`. No direct instantiation in endpoints.

**Fail:**
- `engine = ExtractionEngine()` inside an endpoint
- Global mutable singletons
- Import-time side effects

```python
# Pass
@router.post("/extract")
async def extract(
    request: ExtractionRequest,
    engine: ExtractionEngine = Depends(get_extraction_engine),
) -> ExtractionResponse: ...

# Fail
@router.post("/extract")
async def extract(request: ExtractionRequest) -> ExtractionResponse:
    engine = ExtractionEngine()  # Direct instantiation
```

---

## 5. Custom Exceptions (GenieException Hierarchy)

**Pass:** All raised exceptions are from the `GenieException` hierarchy. Specific exception types used for specific errors.

**Fail:**
- Raising bare `Exception` or `ValueError`
- `except Exception: pass` (swallowed exceptions)
- Missing exception context (no `from` clause on re-raises)
- Catching `Exception` without re-raising as `GenieException`

```python
# Pass
raise ExtractionFailed(
    f"Failed to extract from {source.path}",
    extraction_id=extraction_id,
) from original_error

# Fail
raise Exception("extraction failed")
except Exception:
    pass
```

**Hierarchy:**
- `GenieException` (base)
  - `InvalidConfig`
  - `ExtractionFailed`
  - `LLMProviderError`
  - `LayoutNotRecognized`
  - `StorageError`

---

## 6. Search Library First

**Pass:** Extraction flow always checks Search Library before calling LLM. Successful LLM extractions save pattern to library.

**Fail:**
- Direct LLM call without library lookup
- Missing pattern save after successful LLM extraction
- Fingerprint not generated before lookup

```python
# Pass
fingerprint = generate_fingerprint(content)
pattern = await library.lookup(fingerprint)
if pattern:
    return apply_pattern(pattern, content)
result = await llm.extract(content, instructions)
await library.save(fingerprint, result.pattern)

# Fail
result = await llm.extract(content, instructions)  # No library check
```

---

## 7. Auto Schema Adapt

**Pass:** New fields detected during extraction are handled by Schema Manager. No manual schema updates required.

**Fail:**
- Hardcoded field lists that break on new data
- Ignoring unknown fields from LLM response
- Requiring code changes to support new output columns

---

## 8. Google-Style Docstrings on Public APIs

**Pass:** All public classes, methods, and functions have Google-style docstrings with Args, Returns, and Raises sections.

**Fail:**
- Missing docstring on public API
- Docstring without Args/Returns/Raises sections
- Outdated docstring (parameters changed but docstring not updated)

```python
# Pass
async def extract(self, request: ExtractionRequest) -> ExtractionResponse:
    """Extract data from a document source.

    Args:
        request: Extraction request with config_id and source.

    Returns:
        Extraction response with structured data.

    Raises:
        ExtractionFailed: If extraction process fails.
        InvalidConfig: If config_id is not found.
    """
```

---

## 9. Tests for New Functionality

**Pass:** New code has corresponding tests. Coverage target: 80%+. Tests cover happy path, error cases, and edge cases.

**Fail:**
- New function/class with zero tests
- Tests only cover happy path
- No integration test for new API endpoint
- Coverage below 80% for new code

---

## 10. Structured Logging with Context

**Pass:** Log statements include structured context: `extraction_id`, `config_id`, `layout_fingerprint` where applicable.

**Fail:**
- `print()` statements instead of `logger`
- Log messages without context identifiers
- Missing error logging in exception handlers
- Sensitive data in logs (API keys, PII)

```python
# Pass
logger.info(
    "Extraction completed",
    extra={"extraction_id": extraction_id, "config_id": config_id},
)

# Fail
print(f"Done extracting {file}")
logger.info("Extraction completed")  # No context
```
