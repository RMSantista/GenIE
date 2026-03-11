# GenIE Project Map

## Directory Structure

```
genie/
├── spec/                               # Core package
│   ├── main.py                         # FastAPI entry point, app creation, middleware
│   │
│   ├── api/v1/                         # REST API layer
│   │   ├── router.py                   # Aggregates all endpoint routers
│   │   ├── dependencies.py             # Dependency injection (get_engine, get_storage, etc.)
│   │   └── endpoints/
│   │       ├── health.py               # GET /health — liveness and readiness checks
│   │       ├── extract.py              # POST /api/v1/extract — main extraction endpoint
│   │       ├── config.py               # CRUD for ExtractionConfig resources
│   │       └── library.py             # Search Library management (list, delete patterns)
│   │
│   ├── core/                           # Cross-cutting infrastructure
│   │   ├── config.py                   # Pydantic Settings — all app configuration
│   │   ├── exceptions.py              # GenieException hierarchy
│   │   ├── security.py               # API key encryption/decryption (Fernet)
│   │   └── logging_config.py          # Structured logging setup
│   │
│   ├── models/                         # Pydantic v2 data models (no business logic)
│   │   ├── extraction.py              # ExtractionRequest, ExtractionResponse
│   │   ├── config.py                  # ExtractionConfig, FieldDefinition
│   │   ├── library.py                # SearchPattern, LayoutFingerprint
│   │   └── output.py                 # OutputSchema, OutputField
│   │
│   ├── extraction/                     # Extraction engine domain
│   │   ├── engine.py                  # ExtractionEngine — orchestrator (coordinates all steps)
│   │   ├── agents/
│   │   │   ├── extractor.py           # LLM-based data extraction agent
│   │   │   └── schema_manager.py     # Auto schema adaptation (new columns, synonyms)
│   │   ├── layout/
│   │   │   └── fingerprint.py        # Hash-based layout fingerprint generator
│   │   ├── llm/
│   │   │   ├── base.py               # BaseLLMProvider ABC
│   │   │   ├── factory.py            # LLMProviderFactory (creates provider by name)
│   │   │   ├── anthropic.py          # Anthropic Claude integration
│   │   │   ├── openai.py            # OpenAI GPT integration
│   │   │   └── google.py            # Google Gemini integration
│   │   └── parsers/                   # Document content parsers
│   │       ├── pdf.py                # PDF → text (PyPDF2 + OCR fallback)
│   │       ├── image.py              # Image → text (pytesseract OCR)
│   │       ├── spreadsheet.py       # XLSX/CSV → structured data (openpyxl)
│   │       └── text.py              # Plain text passthrough
│   │
│   ├── search_library/                # Pattern storage (cost optimization layer)
│   │   ├── base.py                   # BaseStorage ABC — interface for all backends
│   │   ├── json_storage.py           # JSON file backend (portable, human-readable)
│   │   └── sqlite_storage.py        # SQLite backend (fast queries, production use)
│   │
│   ├── output/                        # Output formatting and delivery
│   │   ├── manager.py               # OutputManager — selects and runs adapter
│   │   ├── adapters/                 # Format-specific converters
│   │   │   ├── json_adapter.py
│   │   │   ├── csv_adapter.py
│   │   │   ├── xlsx_adapter.py
│   │   │   └── db_adapter.py        # Direct database insert
│   │   └── schema_adapter.py        # Auto-adapt output schema to new fields
│   │
│   ├── mcp/                          # MCP (Model Context Protocol) integrations
│   │   ├── file_reader.py           # Read files via MCP
│   │   └── db_connector.py          # Database access via MCP
│   │
│   └── utils/                        # Shared utilities
│       ├── validators.py            # Input validation helpers
│       ├── converters.py            # Data format converters
│       └── helpers.py               # General-purpose helpers
│
├── tests/                             # Test suite
│   ├── conftest.py                   # Shared fixtures, test settings, mock factories
│   ├── unit/                         # Unit tests (isolated, fast)
│   │   ├── test_extraction_engine.py
│   │   ├── test_llm_providers.py
│   │   ├── test_search_library.py
│   │   └── test_parsers.py
│   ├── integration/                  # Integration tests (API, end-to-end)
│   │   ├── test_api.py
│   │   ├── test_end_to_end.py
│   │   └── test_mcp.py
│   └── fixtures/                     # Test data
│       ├── sample_pdfs/
│       ├── sample_images/
│       └── sample_configs.json
│
├── config/                           # Environment-specific configuration
│   ├── development.yaml
│   ├── production.yaml
│   └── docker.yaml
│
├── data/                             # Runtime data (gitignored)
│   ├── search_library/              # Pattern storage files
│   │   ├── patterns.json
│   │   └── patterns.db
│   └── uploads/                     # Uploaded documents
│
├── pyproject.toml                   # Poetry project definition, dependencies
├── Dockerfile
└── docker-compose.yml
```

## Component Responsibilities

### API Layer (`api/v1/`)
Accept HTTP requests, validate input via Pydantic models, delegate to domain services via dependency injection, return responses. No business logic here.

### Core (`core/`)
Application-wide concerns: settings management, exception definitions, security utilities, logging. Imported by all other packages.

### Models (`models/`)
Pure data definitions. No methods with side effects. Used for request/response validation, configuration schemas, and internal data transfer.

### Extraction Engine (`extraction/`)
The heart of GenIE. The `ExtractionEngine` orchestrates the full extraction pipeline:
1. Parse document content (parsers)
2. Generate layout fingerprint (layout)
3. Query Search Library for cached pattern
4. Fall back to LLM extraction if no pattern found (agents + llm)
5. Save new pattern to Search Library
6. Return structured extraction result

### Search Library (`search_library/`)
Stores and retrieves extraction patterns (REGEX, SQL queries, LLM instructions) indexed by layout fingerprint. The primary cost-optimization mechanism — avoids repeated LLM calls for known layouts.

### Output (`output/`)
Convert extraction results to the requested output format. The `OutputManager` selects the appropriate adapter (JSON, CSV, XLSX, DB) and handles schema adaptation when new fields appear.

### MCP (`mcp/`)
Integrations with external systems via Model Context Protocol. File reading and database connectivity for sources that require MCP access.

### Utils (`utils/`)
Stateless helper functions shared across packages. Validators, converters, and general utilities.

## Key Files to Know

| File | Purpose |
|------|---------|
| `spec/main.py` | App startup, CORS, middleware, lifespan events |
| `spec/core/config.py` | All settings via `pydantic-settings` — the single source of configuration |
| `spec/core/exceptions.py` | Exception hierarchy — import from here, never define exceptions elsewhere |
| `spec/extraction/engine.py` | The orchestrator — start here to understand the extraction flow |
| `spec/extraction/llm/factory.py` | Provider creation — add new LLM providers here |
| `spec/search_library/base.py` | Storage interface — implement this to add new backends |
| `tests/conftest.py` | Test fixtures and shared mocks — check here before creating new fixtures |
| `pyproject.toml` | Dependencies and project metadata |
