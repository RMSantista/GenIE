# QA Test Checklist for GenIE Features

## Pre-Testing

- [ ] Requirements understood and scope defined
- [ ] Test plan documented with all dimensions
- [ ] Test environment ready (server running, dependencies installed)
- [ ] Evidence directory exists (`/tmp/genie_qa_tests/`)

## Unit Tests

- [ ] Extraction engine logic tested
- [ ] Pydantic models validated (valid + invalid inputs)
- [ ] Search Library CRUD operations tested
- [ ] Layout fingerprint generation tested
- [ ] Output adapters tested (JSON, CSV, XLSX, etc.)
- [ ] Custom exception hierarchy tested
- [ ] All async operations tested with pytest-asyncio
- [ ] Edge cases covered (empty input, large input, malformed data)

## API Tests

- [ ] POST /api/v1/extract — Valid extraction request
- [ ] POST /api/v1/extract — Invalid config returns 400
- [ ] POST /api/v1/extract — Bad input returns appropriate error
- [ ] GET /api/v1/config — List configurations
- [ ] POST /api/v1/config — Create configuration
- [ ] GET /api/v1/library — Search Library patterns
- [ ] Error responses follow standard format (`error`, `message`, `details`)
- [ ] Content-Type headers correct

## Extraction Flow Tests

- [ ] Layout fingerprint generated correctly for document
- [ ] Search Library lookup returns cached pattern (if exists)
- [ ] LLM extraction triggered when no pattern found
- [ ] Pattern saved to Search Library after successful LLM extraction
- [ ] Schema Manager detects new fields
- [ ] Schema Manager creates columns for new fields
- [ ] Output formatted in requested format
- [ ] Multi-provider fallback works (Anthropic -> OpenAI -> Google)

## Error Scenario Tests

- [ ] TC-ERR-001: InvalidConfig raised for bad config
- [ ] TC-ERR-002: ExtractionFailed raised for bad input
- [ ] TC-ERR-003: LLMProviderError raised when provider unavailable
- [ ] TC-ERR-004: LayoutNotRecognized raised for unknown layout
- [ ] TC-ERR-005: StorageError raised for library errors
- [ ] All errors include descriptive messages
- [ ] HTTP status codes match exception types

## UI Tests (Chrome tool + Playwright)

- [ ] Application starts without errors
- [ ] API documentation page loads (FastAPI /docs)
- [ ] Key pages render correctly
- [ ] No console errors
- [ ] Forms and controls are interactive
- [ ] Playwright automated tests all pass
- [ ] Screenshots captured ONLY on error

## Performance

- [ ] Simple extraction < 2s
- [ ] Complex extraction < 10s
- [ ] Search Library hit rate measured
- [ ] API response times acceptable

## Post-Testing

- [ ] All tests passing (0 failed, 0 skipped)
- [ ] Test report generated (`/tmp/genie_qa_tests/test_report.json`)
- [ ] Evidence timestamps are current session
- [ ] QA status determined: QA_PASSED or QA_FAILED
