# GENIE Development Checklist

**For developers working on GENIE**

---

## Before Starting Development

- [ ] Read `CLAUDE.md` (project guidelines)
- [ ] Read `README.md` (quick start)
- [ ] Read `HOMOLOGATION-CHECKLIST.md` (what's implemented)
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create `.env` from `.env.example`
- [ ] Start server: `uvicorn spec.main:app --reload`

---

## Code Standards (Non-Negotiable)

- [ ] **Type hints** on ALL functions (100% coverage)
- [ ] **Docstrings** on ALL public classes/methods (Google style)
- [ ] **Async/await** for ALL I/O operations
- [ ] **Custom exceptions** - use GenieException hierarchy
- [ ] **Pydantic v2** for ALL data models
- [ ] **FastAPI Depends()** for dependency injection
- [ ] **No hardcoded values** - use config/env
- [ ] **Logging** with context (extraction_id, config_id)

---

## Before Committing

- [ ] Run linter: `ruff format . && ruff check .`
- [ ] Check types: `mypy spec/`
- [ ] Run tests: `pytest -v`
- [ ] Check coverage: `pytest --cov=spec`
- [ ] Update documentation if needed
- [ ] Commit message follows format (see git history)

---

## Pull Request Checklist

- [ ] All tests pass
- [ ] Type hints complete
- [ ] Docstrings present
- [ ] Code formatted (ruff/black)
- [ ] New tests for new features
- [ ] Documentation updated
- [ ] No hardcoded values
- [ ] Error handling is comprehensive
- [ ] Logging is structured

---

## Common Commands

```bash
# Development
uvicorn spec.main:app --reload

# Testing
pytest -v
pytest --cov=spec --cov-report=html

# Code quality
ruff format .
ruff check .
mypy spec/

# Git workflow
git checkout -b feature/your-feature
git add -A
git commit -m "Your message"
git push origin feature/your-feature
# Then create PR via GitHub
```

---

## Architecture Reminders

**ExtractionEngine Pipeline:**
1. Read content (parser)
2. Generate fingerprint
3. Search library lookup
4. LLM extraction (fallback)
5. Auto-save pattern
6. Format output

**Key Classes:**
- `ExtractionEngine` - Main orchestrator
- `BaseLLMProvider` - LLM interface
- `BaseStorage` - Library storage interface
- `LayoutFingerprint` - Structure identification
- `PatternMatcher` - Pattern execution

---

## Testing Strategy

### Unit Tests
- Test individual classes/functions
- Mock external dependencies (LLM, storage)
- Test error cases

### Integration Tests
- Test API endpoints
- Test full pipelines
- Use test fixtures

### Fixtures
- Sample PDFs in `tests/fixtures/sample_pdfs/`
- Sample data in `conftest.py`
- Mock LLM responses

---

## Performance Checklist

- [ ] Fingerprinting is deterministic (no random variation)
- [ ] Library lookups use caching
- [ ] LLM calls are minimized
- [ ] Async operations prevent blocking
- [ ] Error handling doesn't retry indefinitely

---

## Security Checklist

- [ ] No secrets in code (use .env)
- [ ] API keys from environment
- [ ] Input validation via Pydantic
- [ ] Error messages are safe
- [ ] File access is restricted

---

## When Stuck

1. Check error logs: `tail logs/genie.log`
2. Run tests: `pytest -v --tb=short`
3. Read docstrings for the failing class
4. Check `docs/guides/` for examples
5. Review git history for similar changes

---

## Contributing to Phase 2+

When implementing new phases:

1. Read the spec (PHASE-1-PLAN.md etc.)
2. Create tests first (TDD)
3. Implement functionality
4. Update documentation
5. Get code review (use SEAL agent)
6. Test end-to-end

---

**Last Updated:** 2026-03-10
**Maintained by:** GENIE Team
