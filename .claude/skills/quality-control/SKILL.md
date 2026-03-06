---
name: quality-control
description: |
  QA testing skill for GenIE with test planning, execution via scripts, Chrome tool (mcp__puppeteer),
  and Playwright, happy path and error scenario validation, extraction-specific testing, and report generation.
  Use when: (1) Creating QA test plans, (2) Executing unit/integration tests,
  (3) Running API tests, (4) Running UI tests via Chrome tool + Playwright,
  (5) Validating error scenarios with GenieException hierarchy,
  (6) Testing extraction flow (fingerprint, Search Library, LLM, schema adaptation),
  (7) Producing test reports.
  Used by Orchestrator for test planning and by agent djinn for test execution.
---

# Quality Control - QA Testing Skill

## Overview

This skill provides QA testing capabilities for GenIE:
- **Test Planning**: Create structured test plans (happy path + error + extraction-specific)
- **Test Execution**: Run tests via pytest (unit, API) and Playwright (UI)
- **Chrome Tool**: Interactive UI exploration via mcp__puppeteer
- **Error Validation**: Ensure GenieException hierarchy is properly raised
- **Extraction Testing**: Validate Search Library, fingerprint, LLM providers, schema adaptation
- **Test Reports**: Produce structured JSON reports with evidence

## Quick Reference

| Action | Command |
|--------|---------|
| Run unit tests | `bash .claude/skills/quality-control/scripts/run_unit_tests.sh` |
| Run API tests | `bash .claude/skills/quality-control/scripts/run_api_tests.sh` |
| Run UI tests (Playwright) | `bash .claude/skills/quality-control/scripts/run_ui_tests.sh` |
| Validate error scenarios | `python .claude/skills/quality-control/scripts/validate_errors.py` |
| Generate test report | `python .claude/skills/quality-control/scripts/generate_report.py` |
| Chrome tool exploration | Use mcp__puppeteer tools directly |

## Test Planning

### Test Plan Structure

```
Test Plan for [Feature Name]
├── Happy Path Tests (must PASS)
│   ├── TC-HP-001: Extract with valid config and input
│   ├── TC-HP-002: Search Library pattern lookup hit
│   ├── TC-HP-003: Schema adaptation on new fields
│   └── TC-HP-004: Output in requested format
├── Error Scenario Tests (must FAIL correctly)
│   ├── TC-ERR-001: Invalid extraction config -> InvalidConfig
│   ├── TC-ERR-002: Bad input data -> ExtractionFailed
│   ├── TC-ERR-003: LLM provider unavailable -> LLMProviderError
│   ├── TC-ERR-004: Unrecognized layout -> LayoutNotRecognized
│   └── TC-ERR-005: Storage error -> StorageError
├── Extraction-Specific Tests
│   ├── TC-EXT-001: Layout fingerprint generation
│   ├── TC-EXT-002: Pattern matching in Search Library
│   ├── TC-EXT-003: LLM fallback extraction
│   └── TC-EXT-004: Pattern saved after LLM extraction
├── Non-Standard Tests (edge cases)
│   ├── TC-EDGE-001: Unicode/special characters in extraction
│   ├── TC-EDGE-002: Very large document processing
│   ├── TC-EDGE-003: Empty document
│   └── TC-EDGE-004: Malformed PDF/image input
└── UI/API Tests
    ├── TC-UI-001: API endpoint responds correctly
    ├── TC-UI-002: Config CRUD operations
    └── TC-UI-003: No console errors
```

## Test Execution

### Unit Tests (pytest)

```bash
bash .claude/skills/quality-control/scripts/run_unit_tests.sh
```

### API Tests

```bash
bash .claude/skills/quality-control/scripts/run_api_tests.sh
```

### UI Tests (Dual-Stage)

**Stage 1 — Chrome tool (mcp__puppeteer)**:
Use mcp__puppeteer for interactive UI exploration. Check page loads, visual layout, console errors.

**Stage 2 — Playwright (automated)**:
```bash
bash .claude/skills/quality-control/scripts/run_ui_tests.sh
```

**Screenshot Policy**: Screenshots ONLY on error — not on success.

### Error Scenario Validation

```bash
python .claude/skills/quality-control/scripts/validate_errors.py
```

## Test Results

### Status Codes

| Status | Meaning | Next Action |
|--------|---------|-------------|
| `QA_PASSED` | All tests pass | Proceed to next step |
| `QA_FAILED` | Test(s) failed | Return to implementation with details |
| `QA_ERROR` | Test execution error | Debug test infrastructure |
| `QA_BLOCKED` | Cannot run tests | Resolve blockers first |

### Report Format

Reports saved to `/tmp/genie_qa_tests/`:
- `test_report.json` — Consolidated results
- `unit_test_results.xml` — JUnit XML
- `api_test_results.xml` — API test results
- `error_validation.json` — Error scenario results
- `screenshots/` — ONLY error screenshots

### Report Structure

```json
{
  "timestamp": "2026-03-05T10:30:00Z",
  "status": "QA_PASSED",
  "summary": {
    "total": 30,
    "passed": 30,
    "failed": 0,
    "skipped": 0
  },
  "dimensions": {
    "unit_tests": {"passed": 15, "failed": 0, "skipped": 0},
    "api_tests": {"passed": 8, "failed": 0, "skipped": 0},
    "ui_tests": {"passed": 4, "failed": 0, "skipped": 0},
    "error_scenarios": {"passed": 5, "failed": 0, "skipped": 0},
    "chrome_tool": "visual_ok"
  },
  "tests": [...],
  "evidence": {
    "report": "/tmp/genie_qa_tests/test_report.json",
    "error_screenshots": []
  }
}
```

## Integration with Orchestrator

### Step 5: QA Testing

1. **Orchestrator** invokes quality-control skill
2. **Agent djinn** executes tests using this skill
3. **djinn** returns results to Orchestrator:
   - `QA_PASSED` -> Proceed to Step 6
   - `QA_FAILED` -> Return to Step 3 with failure details

### Orchestrator Flow

```
Step 3 (Implementation) -> Step 4 (Review) -> Step 5 (QA Testing)
                                                     |
                                          +----------+-----------+
                                          v                      v
                                    QA_PASSED               QA_FAILED
                                          |                      |
                                          v                      v
                                    Step 6                Return to Step 3
                                  (Validation)            (then Step 4, then Step 5)
```

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/run_unit_tests.sh` | Execute pytest unit tests |
| `scripts/run_api_tests.sh` | Execute API integration tests |
| `scripts/run_ui_tests.sh` | Execute Playwright UI tests headless |
| `scripts/validate_errors.py` | Validate GenieException error scenarios |
| `scripts/generate_report.py` | Generate consolidated JSON report |

## Best Practices

1. **Always test both success AND failure paths**
2. **Capture evidence (logs, reports; screenshots only on error)**
3. **Test extraction-specific dimensions (fingerprint, library, LLM, schema)**
4. **Run regression tests after any code change**
5. **Report specific failure details for debugging**
6. **Use Chrome tool for exploration, Playwright for automation**
7. **Never simulate — always execute**
