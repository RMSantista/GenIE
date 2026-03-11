---
name: quality-control
description: |
  QA testing skill for GenIE. Plan, execute, and report on all test dimensions.
  Use when: creating test plans, running unit/API/UI tests, validating GenieException
  error scenarios, testing extraction flow (fingerprint, Search Library, LLM, schema
  adaptation), exploring UI via Chrome tool (mcp__puppeteer), running Playwright
  automated tests, or generating test reports.
  Used by agent djinn for test execution. Invoked by Orchestrator at Step 5.
---

# Quality Control

QA testing for GenIE: plan, execute, report.

## Commands

| Action | Command |
|--------|---------|
| Unit tests | `bash .claude/skills/quality-control/scripts/run_unit_tests.sh` |
| API tests | `bash .claude/skills/quality-control/scripts/run_api_tests.sh` |
| UI tests (Playwright) | `bash .claude/skills/quality-control/scripts/run_ui_tests.sh` |
| Error validation | `python .claude/skills/quality-control/scripts/validate_errors.py` |
| Generate report | `python .claude/skills/quality-control/scripts/generate_report.py` |
| Chrome tool | Use `mcp__puppeteer` tools directly |

## Workflow

### 1. Plan

Create a test plan covering all dimensions. Use the template at
`references/test-plan-template.md` for structure.

Test dimensions:
- **Happy path** -- valid config, valid input, expected output
- **Error scenarios** -- each GenieException subclass raised correctly
- **Extraction-specific** -- fingerprint, Search Library, LLM fallback, schema adaptation
- **Edge cases** -- unicode, large docs, empty docs, malformed input
- **UI/API** -- endpoints respond, pages render, no console errors

### 2. Execute

Run tests in order: unit -> API -> error validation -> UI.

**Unit tests (pytest)**
```bash
bash .claude/skills/quality-control/scripts/run_unit_tests.sh
```

**API tests**
```bash
bash .claude/skills/quality-control/scripts/run_api_tests.sh
```

**Error scenario validation**
```bash
python .claude/skills/quality-control/scripts/validate_errors.py
```

Validate the full GenieException hierarchy:
```
GenieException (base)
+-- InvalidConfig
+-- ExtractionFailed
+-- LLMProviderError
+-- LayoutNotRecognized
+-- StorageError
```

**UI tests (dual-stage)**
1. Chrome tool (`mcp__puppeteer`) -- interactive exploration, visual checks, console errors
2. Playwright (automated):
```bash
bash .claude/skills/quality-control/scripts/run_ui_tests.sh
```

**Screenshot policy**: capture ONLY on unexpected failures. Never on success or expected errors.

**IMPORTANT**: Follow the full interactive testing protocol in `references/ui-testing-guide.md` when any UI is created or functionally changed. Test what MUST work AND what MUST fail. Report ONLY what is genuinely broken — not successes, not expected errors.

### 3. Evaluate

| Status | Meaning | Next action |
|--------|---------|-------------|
| `QA_PASSED` | 100% tests pass | Proceed to next step |
| `QA_FAILED` | Any test failed | Return to implementation with details |
| `QA_ERROR` | Test infra error | Debug test infrastructure |
| `QA_BLOCKED` | Cannot run tests | Resolve blockers first |

Approval rule: 100% pass = `QA_PASSED`. Any failure = `QA_FAILED`.

### 4. Report

Generate the consolidated report:
```bash
python .claude/skills/quality-control/scripts/generate_report.py
```

Output goes to `/tmp/genie_qa_tests/`. See `references/report-format.md` for
JSON structure and file layout.

## Anti-Simulation Rule

NEVER simulate test execution. Always run real commands and capture real output.
Every test result must come from actual execution, not fabricated data.

## Orchestrator Integration

```
Step 3 (Implementation) -> Step 4 (Review) -> Step 5 (QA Testing)
                                                     |
                                          +----------+-----------+
                                          |                      |
                                    QA_PASSED               QA_FAILED
                                          |                      |
                                    Step 6                Return to Step 3
                                  (Validation)
```

## Evidence Policy

Test BOTH what must work AND what must fail. Report ONLY genuine defects:
- **Do NOT report** things that work correctly — silence means pass.
- **Do NOT report** expected errors that correctly fail — that's correct behavior.
- **DO report** with evidence anything that is genuinely broken: something that should work but doesn't, or something that should fail but passes.
- Screenshots and detailed output ONLY for genuine defects.

## References

- `references/ui-testing-guide.md` -- **MANDATORY** interactive UI testing protocol (Chrome tool + Playwright)
- `references/test-plan-template.md` -- test plan structure and test case IDs
- `references/report-format.md` -- report JSON schema and output files
- `references/extraction-testing.md` -- extraction pipeline test details and benchmarks
