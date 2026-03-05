# CLAUDE.md — GENIE Project

## Project Identity

**GENIE** = **GEN**eric **I**nformation **E**xtractor

A Python framework for intelligent data extraction using LLMs. GENIE is a **generic** (not general) extractor — it's a parametrizable system that requires configuration for each use case, not an automatic "extract everything" tool.

**Analogy:** A universal mold — it can make anything, but you need to tell it the recipe.

---

## Architecture Overview

```
Client Apps (TabEx JS, other apps)
        │
   REST API (FastAPI)
        │
┌───────▼────────────────────────────────┐
│           GENIE CORE (Python)          │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │     Configuration Manager        │  │
│  │  • I/O format selection          │  │
│  │  • LLM conversational config     │  │
│  │  • API key management            │  │
│  └──────────────────────────────────┘  │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │     ExtractionEngine             │  │
│  │  (Orchestrator)                  │  │
│  │  1. Read content (MCP/parser)    │  │
│  │  2. Generate layout fingerprint  │  │
│  │  3. Search Library lookup        │  │
│  │  4. LLM extraction (fallback)    │  │
│  │  5. Save pattern to library      │  │
│  │  6. Adapt & format output        │  │
│  └──────────────────────────────────┘  │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │     Search Library               │  │
│  │  • REGEX patterns                │  │
│  │  • SQL queries                   │  │
│  │  • Extraction instructions       │  │
│  │  • Layout fingerprints           │  │
│  │  Storage: JSON + SQLite          │  │
│  └──────────────────────────────────┘  │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │     Output Manager               │  │
│  │  • Format conversion             │  │
│  │  • Schema adaptation             │  │
│  │  • Auto-column generation        │  │
│  └──────────────────────────────────┘  │
│                                        │
│  LLM Providers ── OCR Fallback         │
│  (Anthropic, OpenAI, Google)           │
└────────────────────────────────────────┘
```

---

## Core Components

### ExtractionEngine (Orchestrator)
- Main entry point for all extraction operations
- Coordinates the flow: content reading → fingerprint → library lookup → LLM fallback → output
- Uses dependency injection for all sub-components
- File: `genie/extraction/engine.py`

### Search Library
- Stores successful extraction patterns (REGEX/Query/Instructions) to avoid repeated LLM tokenization
- Dual storage: JSON for portability, SQLite for performance
- Patterns are indexed by layout fingerprint
- Dramatically reduces LLM costs after initial extraction
- File: `genie/search_library/`

### Schema Manager Agent
- Handles automatic schema adaptation
- When new data fields are detected (e.g., new exam types), creates new output columns automatically
- Manages field normalization via synonym dictionaries
- File: `genie/extraction/agents/schema_manager.py`

### Extractor Agent
- Performs the actual data extraction via LLM
- Receives OCR text + extraction instructions
- Returns structured JSON
- Supports multi-provider: Anthropic (primary), OpenAI, Google
- File: `genie/extraction/agents/extractor.py`

### Output Manager
- Converts extracted data to configured output format
- Handles schema changes (new columns, modified fields)
- Supports: JSON, CSV, XLSX, DB insert, XML, YAML
- File: `genie/output/manager.py`

### Layout Fingerprint
- Generates a hash-based fingerprint from document structure
- Used to match documents against stored patterns in Search Library
- Layout-independent extraction — same data from different document layouts
- File: `genie/extraction/layout/fingerprint.py`

---

## Project Structure

```
genie/
├── genie/                          # Core package
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry
│   │
│   ├── api/                        # API layer
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py
│   │       ├── endpoints/
│   │       │   ├── extract.py       # POST /api/v1/extract
│   │       │   ├── config.py        # CRUD configurations
│   │       │   └── library.py       # Search Library management
│   │       └── dependencies.py      # Dependency injection
│   │
│   ├── core/                       # Core infrastructure
│   │   ├── __init__.py
│   │   ├── config.py               # App settings (pydantic)
│   │   ├── exceptions.py           # Custom exceptions hierarchy
│   │   ├── security.py             # API key encryption
│   │   └── logging_config.py
│   │
│   ├── models/                     # Pydantic models
│   │   ├── __init__.py
│   │   ├── extraction.py           # ExtractionRequest/Response
│   │   ├── config.py               # ExtractionConfig
│   │   ├── library.py              # SearchPattern
│   │   └── output.py               # OutputSchema
│   │
│   ├── extraction/                 # Extraction engine
│   │   ├── __init__.py
│   │   ├── engine.py               # ExtractionEngine (orchestrator)
│   │   ├── agents/
│   │   │   ├── extractor.py        # Extractor Agent
│   │   │   └── schema_manager.py   # Schema Manager Agent
│   │   ├── layout/
│   │   │   └── fingerprint.py      # Layout fingerprinting
│   │   ├── llm/
│   │   │   ├── factory.py          # LLM provider factory
│   │   │   ├── base.py             # Base provider interface
│   │   │   ├── anthropic.py
│   │   │   ├── openai.py
│   │   │   └── google.py
│   │   └── parsers/
│   │       ├── pdf.py
│   │       ├── image.py
│   │       ├── spreadsheet.py
│   │       └── text.py
│   │
│   ├── search_library/             # Pattern storage
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseStorage ABC
│   │   ├── json_storage.py
│   │   └── sqlite_storage.py
│   │
│   ├── output/                     # Output management
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   ├── adapters/
│   │   │   ├── json_adapter.py
│   │   │   ├── csv_adapter.py
│   │   │   ├── xlsx_adapter.py
│   │   │   └── db_adapter.py
│   │   └── schema_adapter.py       # Auto-adapt schema
│   │
│   ├── mcp/                        # MCP integrations
│   │   ├── __init__.py
│   │   ├── file_reader.py
│   │   └── db_connector.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── validators.py
│       ├── converters.py
│       └── helpers.py
│
├── sdks/                           # Client SDKs
│   ├── javascript/                 # For TabEx integration
│   │   ├── package.json
│   │   └── src/genie-client.js
│   └── python/
│       ├── pyproject.toml
│       └── genie_sdk/client.py
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_extraction_engine.py
│   │   ├── test_llm_providers.py
│   │   ├── test_search_library.py
│   │   └── test_parsers.py
│   ├── integration/
│   │   ├── test_api.py
│   │   ├── test_end_to_end.py
│   │   └── test_mcp.py
│   └── fixtures/
│       ├── sample_pdfs/
│       ├── sample_images/
│       └── sample_configs.json
│
├── config/
│   ├── development.yaml
│   ├── production.yaml
│   └── docker.yaml
│
├── data/
│   ├── search_library/
│   │   ├── patterns.json
│   │   └── patterns.db
│   └── uploads/
│
├── docs/
│   ├── api/openapi.yaml
│   ├── guides/
│   └── examples/
│
├── scripts/
│   ├── setup.sh
│   ├── migrate_library.py
│   └── test_llm_connection.py
│
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── CLAUDE.md                       # ← This file
└── README.md
```

---

## Key Design Decisions

### 1. Generic, not General
GENIE requires configuration to know **WHAT** to extract. It does not auto-extract everything from a document. The user defines fields, instructions, and output format. The framework adapts to any document layout within that configuration.

### 2. Search Library First, LLM Second
Cost efficiency is a core principle. The extraction flow always tries the Search Library before falling back to LLM:
1. Generate layout fingerprint
2. Look up matching patterns in Search Library
3. If found → apply REGEX/query (zero LLM cost)
4. If not found → use LLM → save pattern to library for future use

### 3. Auto Schema Adaptation
When the Extractor Agent finds new data fields not in the current schema (e.g., a new exam type), the Schema Manager Agent automatically adds new columns/fields to the output. No manual intervention required.

### 4. Layout-Independent Extraction
Extraction must work regardless of document layout. The same data should be extracted whether the source is Lab A's PDF format or Lab B's format. Layout fingerprinting identifies the source format; extraction patterns handle the differences.

### 5. Independent Library, TabEx as First Consumer
GENIE is a standalone framework. TabEx (JavaScript) is the first integration test case, consuming GENIE via REST API and/or JavaScript SDK.

---

## Code Standards

### Python
- **Version:** 3.11+
- **Type hints:** Required on ALL functions and methods — no exceptions
- **Models:** Pydantic v2 for all data models
- **Async:** Use `async/await` for all I/O operations
- **Framework:** FastAPI for API layer
- **Package manager:** Poetry
- **Docstrings:** Required on all public classes and methods (Google style)

### Patterns
- Dependency Injection via FastAPI `Depends()`
- Factory Pattern for LLM providers (`LLMProviderFactory`)
- Strategy Pattern for output adapters
- Abstract Base Classes for extensible components (`BaseStorage`, `BaseLLMProvider`)
- Custom exception hierarchy rooted in `GenieException`

### Error Handling

```python
# Exception hierarchy
GenieException (base)
├── LayoutNotRecognized    # Layout not in library
├── ExtractionFailed       # Extraction process failed
├── LLMProviderError       # LLM API error
├── InvalidConfig          # Bad configuration
└── StorageError           # Search Library error
```

### Logging
- Structured logging with `logging` module
- Log levels: DEBUG for development, INFO for production
- Include context: `extraction_id`, `config_id`, `layout_fingerprint`

### Testing
- `pytest` as test runner
- Unit tests for each component
- Integration tests for API endpoints and end-to-end flows
- Fixtures in `tests/fixtures/` (sample PDFs, images, configs)
- Minimum test coverage target: **80%**

---

## Key Integration Patterns

### TabEx (JavaScript) → GENIE

```javascript
// JavaScript SDK usage
const genie = new GenieClient({
  apiUrl: 'http://localhost:8000',
  apiKey: process.env.GENIE_API_KEY
});

const result = await genie.extract('medical_reports_v1', {
  type: 'file',
  path: '/uploads/report.pdf'
});
```

### Python Direct Usage

```python
from genie.extraction.engine import ExtractionEngine
from genie.models.extraction import ExtractionRequest

engine = get_extraction_engine()  # via DI
result = await engine.extract(ExtractionRequest(
    config_id="medical_reports_v1",
    source={"type": "file", "path": "/uploads/report.pdf"}
))
```

### API Endpoint

```http
POST /api/v1/extract
{
  "config_id": "medical_reports_v1",
  "source": {
    "type": "file",
    "path": "/uploads/report.pdf"
  }
}
```

---

## Technology Stack

### Backend
- Python 3.11+, FastAPI, Uvicorn
- Pydantic v2 (models & settings)
- Anthropic / OpenAI / Google AI SDKs
- `pytesseract` (OCR), `PyPDF2`, `openpyxl`
- SQLAlchemy 2.0 (DB connectivity)
- `cryptography` (API key encryption)

### Infrastructure
- Docker + Docker Compose
- PostgreSQL (configuration storage)
- SQLite (Search Library)
- Redis (cache, optional)
- Nginx (reverse proxy)

---

## Performance Targets

| Metric | Target |
|---|---|
| Simple document extraction | < 2s |
| Complex document extraction | < 10s |
| Search Library hit rate | > 95% |
| LLM accuracy (new layouts) | > 90% |
| LLM token reduction after library built | > 80% |

---

## Development Methodology

> **RESERVED SECTION**
>
> This section will be defined with the Agent Orchestrator methodology. Details to be added include:
> - Agent orchestration patterns
> - Task decomposition strategy
> - Agent communication protocols
> - Development workflow and iteration cycles
> - CI/CD pipeline integration
>
> To be completed in a future session.

---

## Project Phases

| Phase | Deliverable | License |
|---|---|---|
| 1 | GENIE Core (Extractor) | Open Source |
| 2 | GENIE Templates | Open Source |
| 3 | GENIE Schema Manager | Commercial |
| 4 | Integrations (TabEx Pro) | Product |

---

## Quick Reference — Common Commands

```bash
# Setup
poetry install
poetry shell

# Run development server
uvicorn genie.main:app --reload --port 8000

# Run tests
pytest
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest --cov=genie --cov-report=html

# Docker
docker-compose up -d
docker-compose logs -f genie

# Linting / Formatting
ruff check .
ruff format .
mypy genie/
```

---

## Important Context

- GENIE is written in Python but must be consumable by JavaScript apps (TabEx) via API + SDK
- The Search Library is the key to cost efficiency — always prioritize pattern reuse over LLM calls
- MCP (Model Context Protocol) is used for file reading and database connections
- OCR text is the primary input for document extraction (LLM reads OCR output, not raw images)
- Configuration is done via conversational LLM interface + structured config files
- All LLM provider integrations must have fallback to REGEX when AI is unavailable
