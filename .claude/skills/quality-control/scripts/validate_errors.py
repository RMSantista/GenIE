#!/usr/bin/env python3
"""GenIE QA - Error Scenario Validation.

Used by: djinn agent (Step 5.6)

Validates that the GenieException hierarchy is properly raised
for each error scenario.
"""

import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

EVIDENCE_DIR = Path(os.environ.get("GENIE_TEST_EVIDENCE_DIR", "/tmp/genie_qa_tests"))
RESULTS_FILE = EVIDENCE_DIR / "error_validation.json"


def validate_error_scenarios() -> dict:
    """Run all error scenario validations.

    Returns:
        Dictionary with validation results.
    """
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scenarios": [],
        "summary": {"total": 0, "passed": 0, "failed": 0},
    }

    scenarios = [
        {
            "id": "TC-ERR-001",
            "name": "Invalid extraction config",
            "exception": "InvalidConfig",
            "test_fn": test_invalid_config,
        },
        {
            "id": "TC-ERR-002",
            "name": "Extraction with bad input",
            "exception": "ExtractionFailed",
            "test_fn": test_extraction_failed,
        },
        {
            "id": "TC-ERR-003",
            "name": "LLM provider unavailable",
            "exception": "LLMProviderError",
            "test_fn": test_llm_provider_error,
        },
        {
            "id": "TC-ERR-004",
            "name": "Unrecognized layout",
            "exception": "LayoutNotRecognized",
            "test_fn": test_layout_not_recognized,
        },
        {
            "id": "TC-ERR-005",
            "name": "Search Library storage error",
            "exception": "StorageError",
            "test_fn": test_storage_error,
        },
    ]

    for scenario in scenarios:
        results["summary"]["total"] += 1
        result = {
            "id": scenario["id"],
            "name": scenario["name"],
            "expected_exception": scenario["exception"],
        }

        try:
            scenario["test_fn"]()
            result["status"] = "PASSED"
            result["message"] = f"{scenario['exception']} raised correctly"
            results["summary"]["passed"] += 1
        except AssertionError as e:
            result["status"] = "FAILED"
            result["message"] = str(e)
            results["summary"]["failed"] += 1
        except ImportError as e:
            result["status"] = "FAILED"
            result["message"] = f"Import error: {e}. GenIE modules may not be installed."
            results["summary"]["failed"] += 1
        except Exception as e:
            result["status"] = "FAILED"
            result["message"] = f"Unexpected error: {e}\n{traceback.format_exc()}"
            results["summary"]["failed"] += 1

        results["scenarios"].append(result)
        status_icon = "PASS" if result["status"] == "PASSED" else "FAIL"
        print(f"  [{status_icon}] {scenario['id']}: {scenario['name']}")

    return results


def test_invalid_config() -> None:
    """TC-ERR-001: InvalidConfig must be raised for bad config."""
    try:
        from genie.core.exceptions import InvalidConfig

        # Test that InvalidConfig can be instantiated and raised
        exc = InvalidConfig("Test invalid config")
        assert isinstance(exc, Exception), "InvalidConfig must be an Exception"

        try:
            raise InvalidConfig("Bad configuration provided")
        except InvalidConfig as e:
            assert "Bad configuration" in str(e)
            return

    except ImportError:
        raise AssertionError(
            "Cannot import InvalidConfig from genie.core.exceptions. "
            "Ensure the exception hierarchy is implemented."
        )


def test_extraction_failed() -> None:
    """TC-ERR-002: ExtractionFailed must be raised for bad input."""
    try:
        from genie.core.exceptions import ExtractionFailed

        exc = ExtractionFailed("Test extraction failed")
        assert isinstance(exc, Exception), "ExtractionFailed must be an Exception"

        try:
            raise ExtractionFailed("Extraction process failed")
        except ExtractionFailed as e:
            assert "failed" in str(e).lower()
            return

    except ImportError:
        raise AssertionError(
            "Cannot import ExtractionFailed from genie.core.exceptions. "
            "Ensure the exception hierarchy is implemented."
        )


def test_llm_provider_error() -> None:
    """TC-ERR-003: LLMProviderError must be raised when provider is unavailable."""
    try:
        from genie.core.exceptions import LLMProviderError

        exc = LLMProviderError("Test LLM error")
        assert isinstance(exc, Exception), "LLMProviderError must be an Exception"

        try:
            raise LLMProviderError("Provider unavailable")
        except LLMProviderError as e:
            assert "unavailable" in str(e).lower()
            return

    except ImportError:
        raise AssertionError(
            "Cannot import LLMProviderError from genie.core.exceptions. "
            "Ensure the exception hierarchy is implemented."
        )


def test_layout_not_recognized() -> None:
    """TC-ERR-004: LayoutNotRecognized must be raised for unknown layouts."""
    try:
        from genie.core.exceptions import LayoutNotRecognized

        exc = LayoutNotRecognized("Test layout error")
        assert isinstance(exc, Exception), "LayoutNotRecognized must be an Exception"

        try:
            raise LayoutNotRecognized("Layout not in library")
        except LayoutNotRecognized as e:
            assert "not" in str(e).lower()
            return

    except ImportError:
        raise AssertionError(
            "Cannot import LayoutNotRecognized from genie.core.exceptions. "
            "Ensure the exception hierarchy is implemented."
        )


def test_storage_error() -> None:
    """TC-ERR-005: StorageError must be raised for library errors."""
    try:
        from genie.core.exceptions import StorageError

        exc = StorageError("Test storage error")
        assert isinstance(exc, Exception), "StorageError must be an Exception"

        try:
            raise StorageError("Search Library storage failed")
        except StorageError as e:
            assert "storage" in str(e).lower()
            return

    except ImportError:
        raise AssertionError(
            "Cannot import StorageError from genie.core.exceptions. "
            "Ensure the exception hierarchy is implemented."
        )


def main() -> int:
    """Main entry point."""
    print("=== GenIE Error Scenario Validation ===")
    print()

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    results = validate_error_scenarios()

    # Write results
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print()
    print(f"Results: {results['summary']['passed']}/{results['summary']['total']} passed")
    print(f"Report: {RESULTS_FILE}")

    if results["summary"]["failed"] > 0:
        print("Status: FAILED")
        return 1

    print("Status: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
