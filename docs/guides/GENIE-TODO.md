# GENIE - Master Development TODO List

## Living Document

> **Status:** Pre-development (no code written yet)
> **Created:** 2026-03-05
> **Last Updated:** 2026-03-05
>
> **How to maintain:** Update checkboxes as items are completed. Add dates in `(YYYY-MM-DD)` after completed items. Add new items as requirements emerge. Never delete completed items — they serve as project history.

**Effort Indicators:** `[S]` < 2h | `[M]` 2-8h | `[L]` 1-3 days

---

## Phase 1: MVP Core (4-6 weeks)

### 1.1 Project Setup

**Requires:** Nothing (starting point)

#### Stage 1.1.1 — Repository & Tooling

- [ ] `[S]` Initialize Git repository with `.gitignore` (Python, IDE, .env)
- [ ] `[S]` Create `pyproject.toml` with Poetry (Python ^3.11)
- [ ] `[S]` Add core dependencies: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `anthropic`
- [ ] `[S]` Add dev dependencies: `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff`, `mypy`, `black`
- [ ] `[S]` Create `.env.example` with all required environment variables
- [ ] `[S]` Create `config/development.yaml` with default settings
- [ ] `[S]` Setup `ruff` and `mypy` configuration in `pyproject.toml`

#### Stage 1.1.2 — Folder Structure

- [ ] `[M]` Create full package structure under `genie/`:
  - `api/v1/endpoints/`, `api/v1/dependencies.py`
  - `core/` (`config.py`, `exceptions.py`, `security.py`, `logging_config.py`)
  - `models/` (`extraction.py`, `config.py`, `library.py`, `output.py`)
  - `extraction/engine.py`, `extraction/llm/`, `extraction/layout/`, `extraction/parsers/`, `extraction/agents/`
  - `search_library/` (`base.py`, `json_storage.py`)
  - `output/` (`manager.py`, `adapters/`, `schema_adapter.py`)
  - `mcp/`, `utils/`
- [ ] `[S]` Create `__init__.py` files for all packages
- [ ] `[S]` Create `tests/` structure: `unit/`, `integration/`, `fixtures/`
- [ ] `[S]` Create `data/search_library/` and `data/uploads/` with `.gitkeep`
- [ ] `[S]` Create `scripts/` directory with `setup.sh` placeholder

#### Stage 1.1.3 — Core Infrastructure

- [ ] `[M]` Implement `genie/core/config.py` — Pydantic Settings model (env vars, paths, API config)
- [ ] `[M]` Implement `genie/core/exceptions.py` — `GenieException` hierarchy:
  - `LayoutNotRecognized`, `ExtractionFailed`, `LLMProviderError`, `InvalidConfig`, `StorageError`
- [ ] `[M]` Implement `genie/core/logging_config.py` — structured logging setup (console + file handlers)
- [ ] `[S]` Implement `genie/core/security.py` — `SecureKeyStore` with Fernet encryption (placeholder)
- [ ] `[M]` Implement `genie/main.py` — FastAPI app creation, CORS, lifespan events
- [ ] `[S]` Implement `genie/api/v1/endpoints/health.py` — `GET /health` endpoint
- [ ] `[S]` Write test: `tests/unit/test_config.py` — validate settings loading
- [ ] `[S]` Write test: `tests/integration/test_health.py` — health endpoint responds 200

> **Quality Gate 1.1:** Server starts with `uvicorn genie.main:app --reload`, health endpoint returns `{"status": "healthy"}`, all tests pass.

---

### 1.2 Base Models & LLM Extraction

**Requires:** 1.1 completed

#### Stage 1.2.1 — Pydantic Models

- [ ] `[M]` Implement `genie/models/extraction.py`:
  - `ExtractionRequest` (config_id, source, force_llm, options)
  - `ExtractionResponse` (extraction_id, status, method_used, data, confidence, processing_time_ms, layout_fingerprint)
- [ ] `[M]` Implement `genie/models/config.py`:
  - `ExtractionConfig` (extraction_id, input, output, llm, behavior)
  - `InputConfig`, `OutputConfig`, `LLMConfig`, `BehaviorConfig`
- [ ] `[S]` Implement `genie/models/library.py`:
  - `SearchPattern`, `PatternField`, `LibraryMetadata`
- [ ] `[S]` Implement `genie/models/output.py`:
  - `OutputSchema`, `FieldDefinition`
- [ ] `[S]` Write tests: `tests/unit/test_models.py` — validation for all models

#### Stage 1.2.2 — LLM Provider Interface & Anthropic

- [ ] `[M]` Implement `genie/extraction/llm/base.py`:
  - `BaseLLMProvider` ABC with `extract()`, `_build_prompt()`, `_parse_response()`
- [ ] `[L]` Implement `genie/extraction/llm/anthropic.py`:
  - `AnthropicProvider` with async Claude API calls
  - Prompt engineering for structured extraction
  - JSON response parsing with markdown cleanup
- [ ] `[M]` Implement `genie/extraction/llm/factory.py`:
  - `LLMProviderFactory` — creates provider instances by name
- [ ] `[M]` Write tests: `tests/unit/test_llm_providers.py` — mock API calls, validate prompt building and response parsing
- [ ] `[S]` Create `scripts/test_llm_connection.py` — manual LLM connectivity test

#### Stage 1.2.3 — Text Parser & Basic Extraction

- [ ] `[M]` Implement `genie/extraction/parsers/text.py`:
  - `TextParser` — plain text content reading
- [ ] `[S]` Implement `genie/extraction/engine.py` — initial `ExtractionEngine` skeleton:
  - `extract()` method with LLM-only flow (no Search Library yet)
  - `_read_content()` dispatching to parsers
- [ ] `[M]` Implement `genie/api/v1/endpoints/extract.py`:
  - `POST /api/v1/extract` — accepts text source, returns extracted data
- [ ] `[M]` Implement `genie/api/v1/dependencies.py`:
  - Dependency injection for `ExtractionEngine`, `LLMProviderFactory`
- [ ] `[M]` Write tests: `tests/integration/test_api.py` — extract endpoint with text input
- [ ] `[S]` Write tests: `tests/unit/test_parsers.py` — text parser

> **Quality Gate 1.2:** `POST /api/v1/extract` with text source returns structured JSON via LLM. All unit and integration tests pass.

---

### 1.3 PDF Support & Layout Fingerprinting

**Requires:** 1.2 completed

#### Stage 1.3.1 — PDF Parser

- [ ] `[S]` Add dependency: `PyPDF2`
- [ ] `[M]` Implement `genie/extraction/parsers/pdf.py`:
  - `PDFParser` — text extraction from native PDFs (page-by-page)
  - Scanned PDF detection (fallback flag for OCR)
- [ ] `[S]` Update `ExtractionEngine._read_content()` to dispatch PDF sources to `PDFParser`
- [ ] `[S]` Update `POST /api/v1/extract` to accept `"type": "file"` sources with path
- [ ] `[S]` Add sample PDFs to `tests/fixtures/sample_pdfs/`
- [ ] `[M]` Write tests: `tests/unit/test_parsers.py` — PDF text extraction

#### Stage 1.3.2 — Layout Fingerprint Algorithm

- [ ] `[L]` Implement `genie/extraction/layout/fingerprint.py`:
  - `LayoutFingerprint.generate()` — structure extraction (remove variable data, keep labels/formatting)
  - `LayoutFingerprint.similarity()` — fingerprint comparison (Hamming distance)
  - Configurable sensitivity levels (low/medium/high)
- [ ] `[M]` Integrate fingerprinting into `ExtractionEngine.extract()` — generate fingerprint on every extraction
- [ ] `[M]` Write tests: `tests/unit/test_fingerprint.py`:
  - Same layout with different data produces same fingerprint
  - Different layouts produce different fingerprints
  - Similarity scoring works correctly

> **Quality Gate 1.3:** PDF extraction works end-to-end via API. Fingerprints are deterministic for same-layout documents. All tests pass.

---

### 1.4 Search Library (JSON) & Basic API

**Requires:** 1.3 completed

#### Stage 1.4.1 — JSON Storage Implementation

- [ ] `[M]` Implement `genie/search_library/base.py`:
  - `BaseStorage` ABC with `find_pattern()`, `save_pattern()`, `update_success_rate()`, `list_patterns()`
- [ ] `[L]` Implement `genie/search_library/json_storage.py`:
  - `JSONStorage` implementing `BaseStorage`
  - File-based CRUD with in-memory cache
  - Thread-safe read/write operations
  - Pattern matching by fingerprint + config_id
  - Success rate tracking (moving average)
- [ ] `[M]` Implement `genie/search_library/matcher.py`:
  - `PatternMatcher` — execute REGEX patterns against content
  - Validation of extracted data against pattern rules
- [ ] `[M]` Write tests: `tests/unit/test_search_library.py` — CRUD, pattern lookup, success rate

#### Stage 1.4.2 — ExtractionEngine Full Flow

- [ ] `[L]` Complete `genie/extraction/engine.py`:
  - Full extraction flow: fingerprint → library lookup → LLM fallback → save pattern
  - Confidence calculation based on extraction method
  - `force_llm` option support
  - Pattern auto-save after successful LLM extraction
- [ ] `[M]` Update `genie/api/v1/dependencies.py` — inject `SearchLibrary` into engine
- [ ] `[M]` Write tests: `tests/unit/test_extraction_engine.py`:
  - Library hit path (pattern found)
  - Library miss path (LLM fallback)
  - Pattern saved after LLM extraction
  - Force LLM bypass

#### Stage 1.4.3 — REST API Completion

- [ ] `[M]` Implement `genie/api/v1/endpoints/config.py`:
  - `POST /api/v1/configs` — create extraction configuration
  - `GET /api/v1/configs/{config_id}` — retrieve configuration
  - `PUT /api/v1/configs/{config_id}` — update configuration
  - `DELETE /api/v1/configs/{config_id}` — delete configuration
- [ ] `[M]` Implement `genie/api/v1/endpoints/library.py`:
  - `GET /api/v1/library/patterns` — list all patterns
  - `GET /api/v1/library/patterns/{layout_id}` — get pattern details
  - `GET /api/v1/library/stats` — library statistics
- [ ] `[S]` Implement API router aggregation in `genie/api/v1/router.py`
- [ ] `[M]` Write tests: `tests/integration/test_api.py` — config CRUD, library endpoints

#### Stage 1.4.4 — End-to-End Validation

- [ ] `[L]` Write `tests/integration/test_end_to_end.py`:
  - Full flow: create config → extract from text → verify pattern saved → re-extract same layout → verify library hit
  - Full flow: extract from PDF → verify fingerprint → verify pattern storage
- [ ] `[M]` Manual validation: extract from 3+ different document layouts, verify Search Library grows
- [ ] `[S]` Run full test suite, verify 80%+ coverage

> **Quality Gate 1.4:** Complete extraction flow works (library lookup → LLM fallback → pattern save). Config CRUD and Library endpoints work. End-to-end test passes. Test coverage >= 80%.

---

## Phase 2: Search Library Enhancement (3-4 weeks)

### 2.1 Auto Pattern Creation

**Requires:** Phase 1 completed

#### Stage 2.1.1 — Pattern Generator

- [ ] `[L]` Implement `genie/search_library/pattern_generator.py`:
  - `PatternGenerator` — analyze LLM extraction context and generate REGEX patterns
  - Support for extraction methods: `regex`, `instruction`, `query`
  - Pattern template generation from content + extracted data pairs
- [ ] `[M]` Integrate `PatternGenerator` into `ExtractionEngine` — auto-create patterns after successful LLM extraction
- [ ] `[M]` Write tests: pattern generation from known content/data pairs

#### Stage 2.1.2 — Pattern Validation & Refinement

- [ ] `[M]` Implement pattern validation: test generated patterns against source content
- [ ] `[M]` Implement pattern refinement: re-extract with pattern, compare to LLM result, adjust if mismatch
- [ ] `[M]` Implement success rate threshold (`> 95%`) — auto-fallback to LLM when pattern degrades
- [ ] `[S]` Write tests: validation and refinement flows

> **Quality Gate 2.1:** Patterns are automatically created after LLM extraction. Generated patterns successfully extract data from same-layout documents. Pattern validation catches incorrect patterns.

---

### 2.2 Layout Fingerprinting Improvements

**Requires:** 2.1 completed

#### Stage 2.2.1 — Advanced Fingerprinting

- [ ] `[L]` Enhance `LayoutFingerprint`:
  - Multi-level hashing (structural + positional + label-based)
  - Configurable sensitivity per config (some layouts need strict matching, others loose)
  - Support for partial fingerprint matching (fuzzy)
- [ ] `[M]` Write tests: fuzzy matching, sensitivity levels, edge cases

#### Stage 2.2.2 — Smart Fallback Logic

- [ ] `[M]` Implement intelligent fallback in `ExtractionEngine`:
  - Success rate < 95% → re-extract with LLM, update pattern
  - Changed extraction instructions → invalidate patterns
  - Pattern age-based expiration (configurable)
- [ ] `[M]` Implement `layout/detector.py` — detect layout type (vertical, horizontal, tabular)
- [ ] `[S]` Write tests: fallback triggers, pattern invalidation

> **Quality Gate 2.2:** Fingerprinting handles layout variations gracefully. Smart fallback triggers correctly on pattern degradation.

---

### 2.3 SQLite Migration & Manual Corrections

**Requires:** 2.2 completed

#### Stage 2.3.1 — SQLite Storage Backend

- [ ] `[L]` Implement `genie/search_library/sqlite_storage.py`:
  - `SQLiteStorage` implementing `BaseStorage`
  - Tables: `layouts`, `extraction_patterns` (per SPEC schema)
  - Indexed queries on fingerprint, layout_id
  - Async operations with `aiosqlite`
- [ ] `[M]` Implement `scripts/migrate_library.py` — JSON → SQLite migration script
- [ ] `[M]` Update `genie/core/config.py` — `storage_type` setting (`json` | `sqlite`)
- [ ] `[M]` Write tests: SQLite CRUD, migration, query performance

#### Stage 2.3.2 — Manual Correction API

- [ ] `[M]` Implement `PUT /api/v1/library/patterns/{layout_id}/fields/{field_name}`:
  - Update pattern REGEX/instruction
  - Track correction metadata (corrected_by, corrected_at, reason)
- [ ] `[M]` Implement `POST /api/v1/library/patterns/{layout_id}/validate`:
  - Test pattern against sample content
  - Return match results and confidence
- [ ] `[S]` Write tests: correction API, validation endpoint

> **Quality Gate 2.3:** SQLite storage works as drop-in replacement for JSON. Migration script transfers all data. Manual corrections work via API.

---

## Phase 3: Multiple Formats (4-5 weeks)

### 3.1 Image & OCR Support

**Requires:** Phase 2 completed

#### Stage 3.1.1 — Image Preprocessing

- [ ] `[S]` Add dependencies: `pytesseract`, `Pillow`
- [ ] `[M]` Implement `genie/extraction/ocr/preprocessor.py`:
  - Image enhancement (contrast, threshold, deskew)
  - Resolution normalization
  - Noise reduction
- [ ] `[S]` Add sample images to `tests/fixtures/sample_images/`

#### Stage 3.1.2 — Tesseract OCR Integration

- [ ] `[L]` Implement `genie/extraction/ocr/tesseract.py`:
  - `TesseractOCR` — OCR extraction with language support
  - Confidence scoring per extracted region
  - Multi-page image support
- [ ] `[M]` Implement `genie/extraction/parsers/image.py`:
  - `ImageParser` — delegates to OCR, returns text
- [ ] `[M]` Write tests: OCR extraction from sample images

#### Stage 3.1.3 — Scanned PDF Detection & Processing

- [ ] `[M]` Enhance `PDFParser` — detect scanned PDFs (no selectable text)
- [ ] `[M]` Implement automatic OCR fallback for scanned PDFs
- [ ] `[M]` Update `ExtractionEngine` — OCR decision flow (per SPEC section 3.4)
- [ ] `[S]` Write tests: scanned vs native PDF detection

> **Quality Gate 3.1:** Images and scanned PDFs are processed via OCR. Native PDFs use direct text extraction. Correct method is auto-selected.

---

### 3.2 Spreadsheet & Structured Data

**Requires:** 3.1 completed

#### Stage 3.2.1 — XLSX & CSV Parsers

- [ ] `[S]` Add dependency: `openpyxl`
- [ ] `[M]` Implement `genie/extraction/parsers/spreadsheet.py`:
  - `SpreadsheetParser` — XLSX and CSV reading
  - Sheet selection, header detection, data type inference
- [ ] `[S]` Write tests: spreadsheet parsing with various structures

#### Stage 3.2.2 — JSON & XML Parsers

- [ ] `[M]` Implement `genie/extraction/parsers/json_parser.py`:
  - JSON/YAML structured data parsing
  - Nested structure flattening
- [ ] `[M]` Implement XML parsing support
- [ ] `[S]` Write tests: structured data parsing

#### Stage 3.2.3 — Database Parsers

- [ ] `[S]` Add dependency: `sqlalchemy`
- [ ] `[L]` Implement `genie/extraction/parsers/db_parser.py`:
  - PostgreSQL, MySQL, SQLite query-based extraction
  - MongoDB document extraction
- [ ] `[M]` Implement `genie/mcp/db_connector.py` — secure DB connections (no path exposure to LLM)
- [ ] `[M]` Write tests: DB extraction (SQLite fixture)

> **Quality Gate 3.2:** All input formats (PDF, image, XLSX, CSV, JSON, XML, DB) can be parsed and extracted from. Tests pass for each format.

---

### 3.3 Output Management & Schema Adaptation

**Requires:** 3.2 completed

#### Stage 3.3.1 — Output Formatters

- [ ] `[M]` Implement `genie/output/adapters/json_adapter.py`
- [ ] `[M]` Implement `genie/output/adapters/csv_adapter.py`
- [ ] `[M]` Implement `genie/output/adapters/xlsx_adapter.py`
- [ ] `[M]` Implement `genie/output/adapters/db_adapter.py`
- [ ] `[S]` Write tests: each formatter produces correct output

#### Stage 3.3.2 — Schema Adapter (Auto-Adaptation)

- [ ] `[L]` Implement `genie/output/schema_adapter.py`:
  - `SchemaAdapter` — detect new fields, infer types, auto-add columns
  - `adapt_to_existing()` — map data to existing schema
  - `handle_new_fields()` — add new columns to CSV/XLSX/DB
  - `create_from_data()` — generate schema from first extraction
- [ ] `[M]` Implement `genie/extraction/agents/schema_manager.py`:
  - Schema Manager Agent — orchestrates schema changes
  - Synonym dictionary for field normalization
- [ ] `[M]` Write tests: schema adaptation, new field detection, column addition

#### Stage 3.3.3 — Output Manager & MCP Integration

- [ ] `[M]` Implement `genie/output/manager.py`:
  - `OutputManager` — adapt data + format output
  - Existing output detection (schema reuse)
- [ ] `[M]` Implement `genie/mcp/file_reader.py` — MCP-based file reading
- [ ] `[S]` Write tests: output manager end-to-end

> **Quality Gate 3.3:** Auto schema adaptation works (new fields detected → columns added). All output formats produce correct results. MCP file reading works.

---

## Phase 4: Interoperability (3-4 weeks)

### 4.1 SDKs

**Requires:** Phase 3 completed

#### Stage 4.1.1 — JavaScript SDK

- [ ] `[L]` Implement `sdks/javascript/src/genie-client.js`:
  - `GenieClient` class with `extract()`, `createConfig()`, `getPatternStats()`
  - Error handling and retry logic
  - TypeScript type definitions
- [ ] `[M]` Create `sdks/javascript/package.json` with build/test scripts
- [ ] `[M]` Create `sdks/javascript/README.md` — usage documentation
- [ ] `[M]` Write SDK tests

#### Stage 4.1.2 — Python SDK

- [ ] `[M]` Implement `sdks/python/genie_sdk/client.py`:
  - `GenieClient` class mirroring JS SDK API
  - Async and sync variants
- [ ] `[S]` Create `sdks/python/pyproject.toml`
- [ ] `[S]` Create `sdks/python/README.md`
- [ ] `[M]` Write SDK tests

> **Quality Gate 4.1:** Both SDKs can connect to GENIE API, create configs, and perform extractions. SDK tests pass.

---

### 4.2 API Documentation & TabEx Integration

**Requires:** 4.1 completed

#### Stage 4.2.1 — OpenAPI Documentation

- [ ] `[M]` Generate `docs/api/openapi.yaml` from FastAPI auto-docs
- [ ] `[M]` Add detailed endpoint descriptions, examples, and error responses
- [ ] `[S]` Verify Swagger UI works at `/docs`

#### Stage 4.2.2 — TabEx Integration

- [ ] `[L]` Create TabEx integration example using JS SDK
- [ ] `[M]` Implement `genie/api/v1/endpoints/extract.py` — file upload support (multipart)
- [ ] `[M]` Validate: TabEx JS app extracts medical reports via GENIE API
- [ ] `[S]` Document integration guide at `docs/examples/tabex_integration.md`

#### Stage 4.2.3 — Load Testing

- [ ] `[M]` Write load test scripts (concurrent extractions)
- [ ] `[M]` Validate performance targets:
  - Simple extraction < 2s
  - API response (excluding processing) < 100ms
  - Search Library hit rate > 95%
- [ ] `[S]` Document performance results

> **Quality Gate 4.2:** OpenAPI docs are complete. TabEx integration works end-to-end. Performance targets met.

---

## Phase 5: Production (4-6 weeks)

### 5.1 Security & Authentication

**Requires:** Phase 4 completed

#### Stage 5.1.1 — API Key Authentication

- [ ] `[M]` Implement `genie/api/middleware/auth.py`:
  - API key validation middleware
  - Key generation and rotation
- [ ] `[M]` Complete `genie/core/security.py`:
  - `SecureKeyStore` — encrypted API key storage (Fernet)
  - `SecureFileAccess` — sandboxed file reading (allowed paths)
- [ ] `[S]` Write tests: auth middleware, key management

#### Stage 5.1.2 — Authorization & Rate Limiting

- [ ] `[M]` Implement per-key authorization (allowed configs, formats)
- [ ] `[M]` Implement `genie/api/middleware/rate_limit.py`:
  - Rate limiting per API key
  - Configurable limits
- [ ] `[S]` Write tests: authorization, rate limiting

> **Quality Gate 5.1:** All API endpoints require valid API key. Rate limiting prevents abuse. Unauthorized requests return 401/403.

---

### 5.2 Monitoring, Logging & Performance

**Requires:** 5.1 completed

#### Stage 5.2.1 — Structured Logging

- [ ] `[M]` Enhance `logging_config.py`:
  - JSON structured log format for production
  - Context fields: `extraction_id`, `config_id`, `layout_fingerprint`, `method_used`
  - Log rotation and retention
- [ ] `[S]` Implement extraction audit trail

#### Stage 5.2.2 — Metrics & Monitoring

- [ ] `[M]` Implement metrics endpoint: `GET /api/v1/metrics`
  - Extraction counts (by method, config, layout)
  - Average processing time
  - Search Library hit rate
  - LLM token usage
- [ ] `[M]` Add Prometheus-compatible metrics export (optional)
- [ ] `[S]` Write tests: metrics accuracy

#### Stage 5.2.3 — Performance Optimization

- [ ] `[M]` Implement Search Library caching (in-memory LRU for hot patterns)
- [ ] `[M]` Optimize fingerprint generation for large documents
- [ ] `[M]` Implement async batch extraction endpoint
- [ ] `[S]` Validate: 80%+ LLM token reduction after library is populated

> **Quality Gate 5.2:** Structured logs contain all required context. Metrics endpoint returns accurate data. Performance targets met.

---

### 5.3 Containerization & Deployment

**Requires:** 5.2 completed

#### Stage 5.3.1 — Docker

- [ ] `[M]` Create `Dockerfile` (multi-stage build, Python 3.11-slim)
- [ ] `[M]` Create `docker-compose.yml`:
  - `genie-api` service
  - `postgres` service (config storage)
  - `redis` service (cache, optional)
- [ ] `[S]` Create `config/docker.yaml` and `config/production.yaml`
- [ ] `[S]` Write tests: container builds and starts successfully

#### Stage 5.3.2 — CI/CD Pipeline

- [ ] `[M]` Create GitHub Actions workflow:
  - Lint (`ruff check`), format (`ruff format --check`), type check (`mypy`)
  - Run tests with coverage report
  - Build Docker image
- [ ] `[S]` Add branch protection rules documentation
- [ ] `[S]` Create release tagging strategy

#### Stage 5.3.3 — Documentation Completion

- [ ] `[M]` Create `README.md` — project overview, quickstart, architecture diagram
- [ ] `[M]` Create `docs/guides/quickstart.md` — step-by-step setup guide
- [ ] `[M]` Create `docs/guides/configuration.md` — complete configuration reference
- [ ] `[M]` Create `docs/guides/deployment.md` — production deployment guide
- [ ] `[S]` Create `docs/examples/custom_parser.md` — extending GENIE with custom parsers
- [ ] `[S]` Create `LICENSE` file (Phase 1-2: Open Source)

> **Quality Gate 5.3:** Docker image builds and runs. CI/CD pipeline passes. All documentation complete. Project is production-ready.

---

## Cross-Phase Standards Compliance Checklist

The **GenIE 10 Code Standards** must be verified at every Phase completion:

- [ ] **1. Type Hints** — ALL functions and methods have type hints
- [ ] **2. Async/Await** — ALL I/O operations are async
- [ ] **3. Pydantic v2** — ALL data models use Pydantic BaseModel
- [ ] **4. Dependency Injection** — FastAPI `Depends()` for all service dependencies
- [ ] **5. Custom Exceptions** — `GenieException` hierarchy used, never bare `Exception`
- [ ] **6. Search Library First** — Pattern lookup always attempted before LLM call
- [ ] **7. Auto Schema Adapt** — New fields detected → Schema Manager creates columns
- [ ] **8. Docstrings** — All public classes and methods (Google style)
- [ ] **9. Tests** — Every feature has unit tests, coverage >= 80%
- [ ] **10. Logging** — Structured logging with context (`extraction_id`, `config_id`)

---

## Licensing Milestones

| Phase | Deliverable | License | Milestone |
|-------|-------------|---------|-----------|
| 1 | GENIE Core (Extractor) | Open Source | MVP functional |
| 2 | GENIE Templates (Search Library) | Open Source | Pattern auto-creation works |
| 3 | GENIE Schema Manager | Commercial | Auto-adaptation production-ready |
| 4 | Integrations (TabEx Pro) | Product | SDKs and TabEx integration |

---

## Summary

| Phase | Sub-Phases | Stages | Items | Timeline |
|-------|-----------|--------|-------|----------|
| 1 — MVP Core | 4 | 11 | ~50 | 4-6 weeks |
| 2 — Search Library Enhancement | 3 | 6 | ~25 | 3-4 weeks |
| 3 — Multiple Formats | 3 | 9 | ~35 | 4-5 weeks |
| 4 — Interoperability | 2 | 5 | ~20 | 3-4 weeks |
| 5 — Production | 3 | 8 | ~30 | 4-6 weeks |
| **Total** | **15** | **39** | **~160** | **18-25 weeks** |
