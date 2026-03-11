# GenIE Architecture Reference

## Architecture Diagram

```
Client Apps (TabEx JS, other apps)
        │
   REST API (FastAPI)
        │
┌───────▼────────────────────────────┐
│         GENIE CORE (Python)        │
│                                    │
│  Configuration Manager             │
│  ExtractionEngine (Orchestrator)   │
│  Search Library (JSON + SQLite)    │
│  Output Manager                    │
│  LLM Providers + OCR Fallback      │
└────────────────────────────────────┘
```

## 6-Step Extraction Pipeline

1. **Read Content** — Parse source document (PDF, image, spreadsheet, text) via MCP/parser.
2. **Generate Fingerprint** — Produce SHA256-based layout fingerprint (16-char hex) from document structure.
3. **Search Library Lookup** — Check stored patterns for matching fingerprint.
4. **LLM Extraction** — Fallback when no pattern found. Send OCR text + instructions to LLM provider.
5. **Save Pattern** — Store successful extraction pattern (REGEX/query/instructions) indexed by fingerprint.
6. **Format Output** — Convert extracted data to requested format (JSON, CSV, XLSX, DB, XML, YAML).

## Core Components and File Locations

### ExtractionEngine (Orchestrator)
- **File:** `spec/extraction/engine.py`
- **Role:** Main entry point. Coordinates the 6-step pipeline.
- **Pattern:** Dependency injection for all sub-components.

### Search Library
- **Directory:** `spec/search_library/`
- **Files:**
  - `spec/search_library/base.py` — BaseStorage ABC
  - `spec/search_library/json_storage.py` — JSON backend
  - `spec/search_library/sqlite_storage.py` — SQLite backend
- **Role:** Store and retrieve extraction patterns. Dual storage for portability (JSON) and performance (SQLite).

### Schema Manager Agent
- **File:** `spec/extraction/agents/schema_manager.py`
- **Role:** Auto-adapt output schema when new fields detected. Manage synonym dictionaries.

### Extractor Agent
- **File:** `spec/extraction/agents/extractor.py`
- **Role:** Perform LLM-based extraction. Receive OCR text + instructions, return structured JSON.
- **Providers:** Anthropic (primary), OpenAI, Google.

### Output Manager
- **File:** `spec/output/manager.py`
- **Adapters:** `spec/output/adapters/` (json, csv, xlsx, db)
- **Role:** Convert extracted data to configured output format. Handle schema changes.

### Layout Fingerprint
- **File:** `spec/extraction/layout/fingerprint.py`
- **Role:** Generate hash-based fingerprint from document structure for pattern matching.

### Configuration
- **File:** `spec/core/config.py`
- **Role:** App settings via Pydantic v2. I/O format selection, LLM config, API key management.

### API Endpoints
- **Directory:** `spec/api/v1/endpoints/`
- **Files:**
  - `spec/api/v1/endpoints/extract.py` — POST /api/v1/extract
  - `spec/api/v1/endpoints/config.py` — CRUD configurations
  - `spec/api/v1/endpoints/library.py` — Search Library management
- **Dependencies:** `spec/api/v1/dependencies.py`

### LLM Providers
- **Directory:** `spec/extraction/llm/`
- **Files:**
  - `spec/extraction/llm/factory.py` — LLMProviderFactory
  - `spec/extraction/llm/base.py` — BaseLLMProvider ABC
  - `spec/extraction/llm/anthropic.py`
  - `spec/extraction/llm/openai.py`
  - `spec/extraction/llm/google.py`

### Parsers
- **Directory:** `spec/extraction/parsers/`
- **Files:** `pdf.py`, `image.py`, `spreadsheet.py`, `text.py`

### Exception Hierarchy
- **File:** `spec/core/exceptions.py`
- **Tree:**
  - GenieException (base)
    - LayoutNotRecognized
    - ExtractionFailed
    - LLMProviderError
    - InvalidConfig
    - StorageError

### Tests
- **Directory:** `tests/`
- **Structure:**
  - `tests/unit/` — Component-level tests
  - `tests/integration/` — API and end-to-end tests
  - `tests/fixtures/` — Sample PDFs, images, configs
