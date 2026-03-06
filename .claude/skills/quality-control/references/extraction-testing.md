# Extraction-Specific Testing Guide for GenIE

## Overview

GenIE's core value is intelligent data extraction. Testing must cover the full extraction pipeline, not just generic CRUD operations.

## Extraction Pipeline

```
Document Input -> Parser -> Layout Fingerprint -> Search Library Lookup
    |                                                      |
    |                                          +-----------+-----------+
    |                                          |                       |
    |                                    Pattern Found           Not Found
    |                                          |                       |
    |                                    Apply Pattern          LLM Extraction
    |                                          |                       |
    |                                          |              Save Pattern to Library
    |                                          |                       |
    |                                          +----------+------------+
    |                                                     |
    |                                              Schema Adaptation
    |                                                     |
    |                                              Output Formatting
    v                                                     v
  Input                                              Structured Output
```

## Test Dimensions

### 1. Layout Fingerprint

**What to test**:
- Same document layout generates same fingerprint
- Different layouts generate different fingerprints
- Fingerprint is deterministic (no randomness)
- Fingerprint handles edge cases (empty doc, single-page, multi-page)

**Test cases**:
```python
# TC-FP-001: Deterministic fingerprint
fingerprint1 = generate_fingerprint(doc_a)
fingerprint2 = generate_fingerprint(doc_a)
assert fingerprint1 == fingerprint2

# TC-FP-002: Different docs, different fingerprints
fp_lab_a = generate_fingerprint(lab_a_report)
fp_lab_b = generate_fingerprint(lab_b_report)
assert fp_lab_a != fp_lab_b

# TC-FP-003: Empty document
with pytest.raises(ExtractionFailed):
    generate_fingerprint(empty_doc)
```

### 2. Search Library

**What to test**:
- Store and retrieve patterns by fingerprint
- Pattern CRUD operations (create, read, update, delete)
- Dual storage consistency (JSON + SQLite)
- Pattern matching with fingerprint lookup
- Performance with many patterns

**Test cases**:
```python
# TC-SL-001: Store and retrieve
await library.store(fingerprint="abc123", pattern=extraction_pattern)
result = await library.lookup(fingerprint="abc123")
assert result == extraction_pattern

# TC-SL-002: Miss returns None
result = await library.lookup(fingerprint="nonexistent")
assert result is None

# TC-SL-003: Dual storage consistency
json_result = await json_storage.lookup("abc123")
sqlite_result = await sqlite_storage.lookup("abc123")
assert json_result == sqlite_result
```

### 3. LLM Provider Integration

**What to test**:
- Primary provider (Anthropic) extraction works
- Fallback to secondary provider (OpenAI) on failure
- Fallback to tertiary provider (Google) on failure
- All providers return consistent format
- Rate limiting and timeout handling
- API key validation

**Test cases**:
```python
# TC-LLM-001: Primary provider extraction
result = await extractor.extract(text=ocr_text, config=config)
assert result.fields is not None

# TC-LLM-002: Fallback on primary failure
with mock_provider_failure("anthropic"):
    result = await extractor.extract(text=ocr_text, config=config)
    assert result.provider == "openai"

# TC-LLM-003: All providers fail
with mock_all_providers_failure():
    with pytest.raises(LLMProviderError):
        await extractor.extract(text=ocr_text, config=config)
```

### 4. Schema Adaptation

**What to test**:
- New field detected in extraction result
- Schema Manager creates column for new field
- Existing fields preserved
- Field normalization via synonyms
- Multiple new fields in single extraction

**Test cases**:
```python
# TC-SA-001: New field detection
result = {"name": "John", "new_field": "value"}
changes = await schema_manager.detect_changes(result, existing_schema)
assert "new_field" in changes.new_fields

# TC-SA-002: Column creation
await schema_manager.adapt(result, existing_schema)
updated_schema = await schema_manager.get_schema()
assert "new_field" in updated_schema.columns

# TC-SA-003: Synonym normalization
result = {"hemoglobin": "14.5"}  # synonym for "hgb"
normalized = await schema_manager.normalize(result)
assert "hgb" in normalized
```

### 5. Output Formatting

**What to test**:
- JSON output matches expected structure
- CSV output has correct headers and delimiters
- XLSX output has correct sheets and columns
- DB insert creates correct records
- Schema changes reflected in output format

**Test cases**:
```python
# TC-OUT-001: JSON output
output = await manager.format(result, format="json")
parsed = json.loads(output)
assert parsed["fields"] == expected_fields

# TC-OUT-002: CSV output
output = await manager.format(result, format="csv")
reader = csv.reader(io.StringIO(output))
headers = next(reader)
assert headers == expected_headers
```

## Integration Test Scenarios

### End-to-End: New Document Type
1. Submit document with unknown layout
2. Verify fingerprint generated
3. Verify Search Library miss
4. Verify LLM extraction triggered
5. Verify pattern saved to library
6. Verify schema adapted (if new fields)
7. Verify output in requested format
8. Submit SAME document again
9. Verify Search Library HIT (no LLM cost)

### End-to-End: Known Document Type
1. Pre-populate Search Library with pattern
2. Submit document with known layout
3. Verify fingerprint matches
4. Verify Search Library hit
5. Verify NO LLM call made
6. Verify output matches expected

### End-to-End: Provider Failover
1. Configure primary provider to fail
2. Submit extraction request
3. Verify fallback to secondary provider
4. Verify extraction succeeds
5. Verify pattern still saved to library

## Performance Benchmarks

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Fingerprint generation | < 100ms | `time.perf_counter()` |
| Search Library lookup | < 50ms | `time.perf_counter()` |
| LLM extraction (simple) | < 2s | End-to-end timer |
| LLM extraction (complex) | < 10s | End-to-end timer |
| Schema adaptation | < 200ms | `time.perf_counter()` |
| Output formatting | < 500ms | `time.perf_counter()` |
