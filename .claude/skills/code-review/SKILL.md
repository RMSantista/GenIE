---
name: code-review
description: "Production-ready code review for GenIE Python/FastAPI projects. Verify compliance with 10 GenIE code standards, enforce naming conventions (WHAT not HOW), detect dead code and duplication, check async patterns and Pydantic usage, validate Search Library integration flow, and assess production readiness. Use when: (1) Code has been written and needs review, (2) Verifying architecture alignment, (3) Checking code standard compliance, (4) Hunting dead code or duplication, (5) Pre-production quality gate."
---

# Code Review

## Review Workflow

Execute each step in sequence. Stop early and mark NOT ACCEPTABLE if any critical violation is found.

### Step 1 — Quick Scan
- Read all changed/new files
- Identify scope: new feature, bugfix, refactor, or test
- Note file count and lines changed

### Step 2 — Standard Check
- Verify all 10 GenIE code standards (see [references/standards.md](references/standards.md))
- Record pass/fail for each standard
- Any fail on standards 1-6 → NOT ACCEPTABLE

### Step 3 — Architecture Alignment
- Verify extraction flow: fingerprint → library lookup → LLM fallback → save pattern
- Confirm dependency injection via `Depends()`
- Confirm exception hierarchy uses `GenieException` subtypes
- Confirm Pydantic v2 models for all data structures

### Step 4 — Deep Analysis
- Check async/await correctness (no blocking calls in async context)
- Verify error handling (no bare `except`, no swallowed exceptions)
- Validate structured logging includes context (extraction_id, config_id)
- Confirm Search Library is checked before LLM calls

### Step 5 — Dead Code Detection
- Identify unused imports, unreachable branches, commented-out code
- Flag functions/classes with zero callers (unless public API)
- Check for TODO/FIXME/HACK without linked issue

### Step 6 — Duplication Detection
- Find copy-pasted logic (3+ similar lines across files)
- Identify repeated patterns that should be abstracted
- Flag duplicated constants or magic numbers

### Step 7 — Naming Conventions
- Enforce WHAT-not-HOW naming (see [references/naming-conventions.md](references/naming-conventions.md))
- Verify no implementation details leak into function/method names
- Check constant definitions and config usage

### Step 8 — Hard Code Detection
- Find hardcoded values: URLs, paths, credentials, magic numbers
- Verify all configurable values use config/env vars
- Flag string literals that should be constants

### Step 9 — Synthesis
- Aggregate all findings
- Classify each issue: CRITICAL / WARNING / SUGGESTION
- Determine final verdict: ACCEPTABLE or NOT ACCEPTABLE

## Decision Criteria

### ACCEPTABLE
- All 10 standards pass (or non-critical standards have minor warnings only)
- No hardcoded values
- Naming follows WHAT-not-HOW convention
- No dead code or significant duplication
- Architecture alignment confirmed

### NOT ACCEPTABLE
- Any standard 1-6 fails (type hints, async, Pydantic, DI, exceptions, Search Library First)
- Hardcoded credentials, URLs, or paths
- Blocking I/O in async context
- Bare `except Exception` without re-raise
- Missing tests for new functionality
- Function names expose implementation details

## Output Format

```
# Code Review — [scope description]

## Verdict: [ACCEPTABLE | NOT ACCEPTABLE]

## Standards Compliance
| # | Standard                  | Status | Notes |
|---|---------------------------|--------|-------|
| 1 | Type hints                | ✅/❌  |       |
| 2 | Async/await               | ✅/❌  |       |
| 3 | Pydantic v2               | ✅/❌  |       |
| 4 | Dependency Injection      | ✅/❌  |       |
| 5 | Custom exceptions         | ✅/❌  |       |
| 6 | Search Library First      | ✅/❌  |       |
| 7 | Auto Schema Adapt         | ✅/❌  |       |
| 8 | Google-style docstrings   | ✅/❌  |       |
| 9 | Tests (80%+ coverage)     | ✅/❌  |       |
|10 | Structured logging        | ✅/❌  |       |

## Issues Found
[List each issue with classification: CRITICAL / WARNING / SUGGESTION]

## Recommendations
[Actionable items to resolve issues]
```

## Automated Checks

Run `scripts/run_checks.sh` to execute ruff format, ruff lint, and mypy before manual review.

## References

- [Code Standards](references/standards.md) — 10 GenIE standards with pass/fail criteria
- [Naming Conventions](references/naming-conventions.md) — WHAT-not-HOW rules and examples
