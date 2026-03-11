# GenIE Code Standards

The 10 mandatory standards. Apply during analysis to identify which standards are relevant to each change.

## 1. Type Hints on ALL Functions/Methods

Every function and method must have complete type annotations — parameters and return types. No exceptions.

```python
async def extract(self, request: ExtractionRequest) -> ExtractionResponse:
```

## 2. Async/Await for ALL I/O

All I/O operations (file reads, API calls, database queries, network requests) must use `async/await`. Blocking I/O is not acceptable.

## 3. Pydantic v2 for ALL Data Models

Every data structure used for input, output, configuration, or inter-component communication must be a Pydantic v2 model. No plain dicts for structured data.

## 4. Dependency Injection via Depends()

Use FastAPI's `Depends()` for all component wiring. No direct instantiation of services in endpoint handlers.

## 5. Custom Exceptions (GenieException Hierarchy)

Raise exceptions from the GenieException tree. Never raise bare `Exception` or `ValueError` for domain errors.

```
GenieException (base)
├── LayoutNotRecognized
├── ExtractionFailed
├── LLMProviderError
├── InvalidConfig
└── StorageError
```

## 6. Search Library First

Always check the Search Library before invoking an LLM. This is both a design decision and a code standard — enforce it in every extraction path.

## 7. Auto Schema Adapt

When new fields are detected, adapt the schema automatically. Do not reject unknown fields or require manual schema updates.

## 8. Google-Style Docstrings

All public classes and methods require Google-style docstrings with Args, Returns, and Raises sections.

```python
def generate_fingerprint(self, content: str) -> str:
    """Generate a layout fingerprint from document content.

    Args:
        content: Raw text content from OCR or parser.

    Returns:
        A 16-character hex string (SHA256-based).

    Raises:
        LayoutNotRecognized: If content is empty or unparseable.
    """
```

## 9. Tests (80%+ Coverage)

- Write unit tests for every new component.
- Write integration tests for API endpoints and end-to-end flows.
- Minimum coverage target: 80%.
- Use pytest. Fixtures go in `tests/fixtures/`.

## 10. Structured Logging with Context

Use the `logging` module with structured output. Always include contextual identifiers.

Required context fields:
- `extraction_id` — unique ID per extraction request
- `config_id` — configuration being used
- `layout_fingerprint` — fingerprint of the document being processed

```python
logger.info(
    "Extraction complete",
    extra={
        "extraction_id": extraction_id,
        "config_id": config_id,
        "layout_fingerprint": fingerprint,
    },
)
```
