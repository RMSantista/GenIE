# Test Plan Template

## Structure

```
Test Plan for [Feature Name]
|
+-- Happy Path Tests (must PASS)
|   +-- TC-HP-001: Extract with valid config and input
|   +-- TC-HP-002: Search Library pattern lookup hit
|   +-- TC-HP-003: Schema adaptation on new fields
|   +-- TC-HP-004: Output in requested format
|
+-- Error Scenario Tests (must FAIL correctly)
|   +-- TC-ERR-001: Invalid extraction config -> InvalidConfig
|   +-- TC-ERR-002: Bad input data -> ExtractionFailed
|   +-- TC-ERR-003: LLM provider unavailable -> LLMProviderError
|   +-- TC-ERR-004: Unrecognized layout -> LayoutNotRecognized
|   +-- TC-ERR-005: Storage error -> StorageError
|
+-- Extraction-Specific Tests
|   +-- TC-EXT-001: Layout fingerprint generation
|   +-- TC-EXT-002: Pattern matching in Search Library
|   +-- TC-EXT-003: LLM fallback extraction
|   +-- TC-EXT-004: Pattern saved after LLM extraction
|
+-- Edge Case Tests
|   +-- TC-EDGE-001: Unicode/special characters in extraction
|   +-- TC-EDGE-002: Very large document processing
|   +-- TC-EDGE-003: Empty document
|   +-- TC-EDGE-004: Malformed PDF/image input
|
+-- UI/API Tests
    +-- TC-UI-001: API endpoint responds correctly
    +-- TC-UI-002: Config CRUD operations
    +-- TC-UI-003: No console errors
```

## Test Case Format

Each test case follows this format:

```
ID:       TC-[CATEGORY]-[NUMBER]
Title:    Short description
Input:    What goes in
Expected: What should happen
Status:   PASS | FAIL | SKIP | BLOCKED
Evidence: Path to log/screenshot (screenshots only on error)
```

## Pre-Testing Checklist

- [ ] Requirements understood and scope defined
- [ ] Test environment ready (server running, dependencies installed)
- [ ] Evidence directory exists (`/tmp/genie_qa_tests/`)
- [ ] Test plan documented with all dimensions

## Post-Testing Checklist

- [ ] All tests executed (0 skipped unless justified)
- [ ] Test report generated at `/tmp/genie_qa_tests/test_report.json`
- [ ] Evidence timestamps match current session
- [ ] QA status determined: QA_PASSED or QA_FAILED

## GenieException Hierarchy

Map each error scenario to the correct exception:

```
GenieException (base)
+-- InvalidConfig          -> 400 Bad Request
+-- ExtractionFailed       -> 422 Unprocessable Entity
+-- LLMProviderError       -> 502 Bad Gateway
+-- LayoutNotRecognized    -> 422 Unprocessable Entity
+-- StorageError           -> 500 Internal Server Error
```

## Naming Convention

- `TC-HP-XXX` -- Happy path
- `TC-ERR-XXX` -- Error scenarios
- `TC-EXT-XXX` -- Extraction-specific
- `TC-EDGE-XXX` -- Edge cases
- `TC-UI-XXX` -- UI/API tests
- `TC-FP-XXX` -- Fingerprint tests
- `TC-SL-XXX` -- Search Library tests
- `TC-LLM-XXX` -- LLM provider tests
- `TC-SA-XXX` -- Schema adaptation tests
- `TC-OUT-XXX` -- Output formatting tests
