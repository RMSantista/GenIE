# GENIE - Generic Extractor of Information Engine

A Python framework for intelligent data extraction using LLMs.

## Quick Start

### Prerequisites
- Python 3.11+
- Poetry (or pip)

### Installation

**Using Poetry (recommended):**
```bash
poetry install
poetry shell
```

**Using pip:**
```bash
pip install -r requirements.txt
```

### Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Add your API keys to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
```

### Running the Server

```bash
uvicorn spec.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/api/v1/health

## Project Structure

```
spec/
├── api/                    # REST API endpoints
│   └── v1/
│       ├── endpoints/      # Endpoint implementations
│       ├── router.py       # Route aggregator
│       └── dependencies.py # Dependency injection
├── core/                   # Core infrastructure
│   ├── config.py          # Settings management
│   ├── exceptions.py      # Custom exceptions
│   ├── logging_config.py  # Logging setup
│   └── security.py        # Security utilities
├── models/                 # Pydantic data models
├── extraction/             # Extraction engine
│   ├── engine.py          # Main orchestrator
│   ├── llm/               # LLM providers
│   ├── parsers/           # Content parsers
│   └── layout/            # Layout fingerprinting
├── search_library/        # Pattern storage
├── output/                # Output management
└── main.py                # FastAPI entry point
```

## API Endpoints

### Health Check
```http
GET /api/v1/health
```

### Extract Data
```http
POST /api/v1/extract
Content-Type: application/json

{
    "config_id": "config_001",
    "source": {
        "type": "text",
        "content": "Document content here..."
    },
    "force_llm": false,
    "options": {
        "auto_create_patterns": true
    }
}
```

## Testing

Run all tests:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/unit/test_models.py -v
```

Run with coverage:
```bash
pytest --cov=spec --cov-report=html
```

## Development

### Code Style
- **Formatter:** Black (88 chars line length)
- **Linter:** Ruff
- **Type Checker:** Mypy

Format code:
```bash
black spec/ tests/
ruff check . --fix
```

Type checking:
```bash
mypy spec/
```

## Documentation

- [Architecture Guide](./docs/guides/GENIE-ARCHITECTURE.md)
- [Phase 1 Plan](./docs/guides/PHASE-1-PLAN.md)
- [Specification v2](./docs/guides/GENIE-SPEC-v2.md)

## License

MIT

## Project Status

**Phase 1: MVP Core** - In Development

- ✓ Project setup and tooling
- ✓ Core infrastructure
- ✓ Pydantic models
- ✓ LLM provider interface (Anthropic)
- ✓ Text and PDF parsers
- ✓ Layout fingerprinting
- ✓ Search library (JSON storage)
- ✓ Extraction engine
- ✓ REST API endpoints
- ⏳ Comprehensive testing
- ⏳ End-to-end validation

See [PHASE-1-PLAN.md](./docs/guides/PHASE-1-PLAN.md) for detailed roadmap.
