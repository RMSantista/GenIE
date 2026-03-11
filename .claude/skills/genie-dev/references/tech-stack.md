# GenIE Tech Stack

## Runtime

| Dependency        | Version   | Purpose                              |
|-------------------|-----------|--------------------------------------|
| Python            | 3.11+     | Runtime language                     |
| FastAPI           | 0.110.0   | REST API framework                   |
| Uvicorn           | 0.27.0    | ASGI server                          |
| Pydantic          | 2.6.0     | Data validation and settings (v2)    |
| pydantic-settings | 2.1.0     | Environment-based configuration      |

## LLM Providers

| Dependency        | Version   | Purpose                              |
|-------------------|-----------|--------------------------------------|
| anthropic         | latest    | Anthropic Claude SDK (primary)       |
| openai            | latest    | OpenAI GPT SDK                       |
| google-generativeai | latest  | Google Gemini SDK                    |

## Async I/O

| Dependency        | Version   | Purpose                              |
|-------------------|-----------|--------------------------------------|
| aiofiles          | latest    | Async file read/write                |
| aiosqlite         | latest    | Async SQLite access                  |
| httpx             | latest    | Async HTTP client                    |

## Document Processing

| Dependency        | Version   | Purpose                              |
|-------------------|-----------|--------------------------------------|
| PyPDF2            | latest    | PDF text extraction                  |
| openpyxl          | latest    | XLSX read/write                      |
| pytesseract       | latest    | OCR (image → text)                   |

## Development & Testing

| Dependency        | Version   | Purpose                              |
|-------------------|-----------|--------------------------------------|
| pytest            | 8.0.0     | Test runner                          |
| pytest-asyncio    | 0.23.0    | Async test support                   |
| pytest-cov        | latest    | Coverage reporting                   |
| ruff              | 0.2.0     | Linting and formatting (replaces black + isort + flake8) |
| mypy              | 1.8.0     | Static type checking                 |

## Infrastructure

| Tool              | Purpose                              |
|-------------------|--------------------------------------|
| Poetry            | Package management and virtualenv    |
| Docker            | Containerization                     |
| Docker Compose    | Multi-service orchestration          |

## Common Commands

```bash
# Package management
poetry install                        # Install all dependencies
poetry add <package>                  # Add a runtime dependency
poetry add --group dev <package>     # Add a dev dependency
poetry shell                          # Activate virtualenv

# Run server
uvicorn genie.main:app --reload --port 8000

# Testing
pytest                                # Run all tests
pytest tests/unit/ -v                # Unit tests only
pytest tests/integration/ -v         # Integration tests only
pytest --cov=genie --cov-report=term # With coverage

# Code quality
ruff check .                         # Lint
ruff format .                        # Format
ruff check --fix .                   # Auto-fix lint issues
mypy genie/                          # Type checking

# Docker
docker-compose up -d                 # Start services
docker-compose logs -f genie         # Follow logs
```
