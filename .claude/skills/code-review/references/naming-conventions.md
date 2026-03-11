# GenIE Naming Conventions

## Core Rule: Name After WHAT, Not HOW

Function and method names describe the **outcome** or **purpose**, never the **implementation mechanism**.

---

## Functions and Methods

### Good (WHAT it does)
```python
extract()
lookup_pattern()
generate_fingerprint()
adapt_schema()
save_pattern()
read_content()
format_output()
validate_config()
encrypt_key()
normalize_field()
```

### Bad (HOW it does it)
```python
regex_extract()            # Leaks implementation (regex)
sqlite_lookup_pattern()    # Leaks storage backend (sqlite)
hash_generate_fingerprint()# Leaks algorithm (hash)
json_save_pattern()        # Leaks format (json)
pdf_read_content()         # Leaks parser type (pdf)
pandas_format_output()     # Leaks library (pandas)
```

### Why
- Implementation changes should not force rename
- Callers should not know or care about internals
- If storage moves from SQLite to PostgreSQL, `lookup_pattern()` still works; `sqlite_lookup_pattern()` becomes a lie

---

## Variables and Parameters

- Use descriptive names: `extraction_id`, `config_id`, `layout_fingerprint`
- Avoid single letters except in comprehensions or lambdas: `[f.name for f in fields]`
- Boolean variables start with `is_`, `has_`, `should_`, `can_`: `is_cached`, `has_pattern`

---

## Constants

- ALL_CAPS with underscores: `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT_SECONDS`
- Define in config module or at module level, never inline
- No magic numbers or string literals in logic

```python
# Good
MAX_RETRY_COUNT = settings.max_retries
DEFAULT_TIMEOUT_SECONDS = settings.timeout

# Bad
for i in range(3):          # What is 3?
    await asyncio.sleep(5)  # What is 5?
```

---

## Classes

- PascalCase, noun-based: `ExtractionEngine`, `SchemaManager`, `SearchLibrary`
- Agent classes end with `Agent`: `ExtractorAgent`, `SchemaManagerAgent`
- Storage classes end with `Storage`: `JsonStorage`, `SqliteStorage`
- Adapter classes end with `Adapter`: `CsvAdapter`, `XlsxAdapter`

---

## Files and Modules

- snake_case: `extraction_engine.py`, `schema_manager.py`
- Name after primary class or purpose
- One primary class per module

---

## No Hardcoded Values

All configurable values must come from config files or environment variables.

```python
# Good
settings = get_settings()
timeout = settings.llm_timeout
base_url = settings.api_base_url

# Bad
timeout = 30
base_url = "http://localhost:8000"
```
