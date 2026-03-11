---
name: genie-dev
description: "Python 3.11+/FastAPI implementation patterns for GenIE data extraction framework. Provides code conventions, exception hierarchy, incremental testing workflow, and project structure. Use when: (1) Implementing new features or fixes, (2) Writing async code with type hints, (3) Creating Pydantic v2 models, (4) Integrating with Search Library or LLM providers, (5) Writing pytest tests, (6) Following GenIE's 10 code standards."
---

# genie-dev

Implementation skill for the **wish** agent. Apply GenIE coding conventions, patterns, and incremental testing when building features or fixing bugs.

## Implementation Workflow

Follow these phases for every task:

1. **Understand** — Read the task requirements and acceptance criteria
2. **Analyze** — Identify affected components using [project-map](references/project-map.md)
3. **Plan** — Define files to create/modify, tests to write, and expected behavior
4. **Implement** — Write code following [conventions](references/conventions.md) and [tech-stack](references/tech-stack.md)
5. **Refactor** — Apply the 10 code standards; remove duplication
6. **Test** — Run incremental tests (see table below)
7. **Verify** — Run full verification before marking complete

## Incremental Testing Rules

Run the minimum test scope matching your changes:

| Files changed                        | Command to run                          |
|--------------------------------------|-----------------------------------------|
| `genie/models/*.py`                  | `pytest tests/unit/ -v -k "model"`      |
| `genie/extraction/llm/*.py`          | `pytest tests/unit/test_llm_providers.py -v` |
| `genie/extraction/engine.py`         | `pytest tests/unit/test_extraction_engine.py -v` |
| `genie/search_library/*.py`          | `pytest tests/unit/test_search_library.py -v` |
| `genie/extraction/parsers/*.py`      | `pytest tests/unit/test_parsers.py -v`  |
| `genie/api/**/*.py`                  | `pytest tests/integration/test_api.py -v` |
| `genie/output/**/*.py`               | `pytest tests/unit/ -v -k "output"`     |
| Multiple areas or uncertain scope    | `pytest tests/unit/ -v`                 |
| Before final delivery                | `pytest --cov=genie --cov-report=term`  |

## Verification Before Completion

Run all of these before declaring a task done:

```bash
# 1. Type checking
mypy genie/

# 2. Linting and formatting
ruff check .
ruff format --check .

# 3. Full test suite
pytest --cov=genie --cov-report=term

# 4. Confirm no import errors
python -c "from genie.main import app; print('OK')"
```

All four commands must pass with zero errors.

## References

- [conventions.md](references/conventions.md) — Code standards, exception hierarchy, naming rules, design patterns
- [project-map.md](references/project-map.md) — Project structure with component descriptions
- [tech-stack.md](references/tech-stack.md) — Dependencies, versions, and tooling
