# Report Format

## Output Directory

All test artifacts go to `/tmp/genie_qa_tests/`:

| File | Contents |
|------|----------|
| `test_report.json` | Consolidated results (see schema below) |
| `unit_test_results.xml` | JUnit XML from pytest |
| `api_test_results.xml` | API test results |
| `error_validation.json` | Error scenario validation results |
| `screenshots/` | Error screenshots ONLY (never success) |

## Report JSON Schema

```json
{
  "timestamp": "ISO-8601 timestamp",
  "status": "QA_PASSED | QA_FAILED | QA_ERROR | QA_BLOCKED",
  "summary": {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0
  },
  "dimensions": {
    "unit_tests": {"passed": 0, "failed": 0, "skipped": 0},
    "api_tests": {"passed": 0, "failed": 0, "skipped": 0},
    "ui_tests": {"passed": 0, "failed": 0, "skipped": 0},
    "error_scenarios": {"passed": 0, "failed": 0, "skipped": 0},
    "chrome_tool": "visual_ok | visual_fail | not_tested"
  },
  "tests": [
    {
      "id": "TC-HP-001",
      "title": "Test description",
      "status": "PASS | FAIL | SKIP",
      "duration_ms": 0,
      "error": null
    }
  ],
  "evidence": {
    "report": "/tmp/genie_qa_tests/test_report.json",
    "error_screenshots": []
  }
}
```

## Status Determination

- `QA_PASSED`: `summary.failed == 0 && summary.skipped == 0`
- `QA_FAILED`: `summary.failed > 0`
- `QA_ERROR`: test infrastructure failure (scripts did not run)
- `QA_BLOCKED`: prerequisites not met (server down, dependencies missing)

Rule: 100% pass = QA_PASSED. Any single failure = QA_FAILED.

## Generate Report

```bash
python .claude/skills/quality-control/scripts/generate_report.py
```

This script reads all result files from `/tmp/genie_qa_tests/` and produces
the consolidated `test_report.json`.
