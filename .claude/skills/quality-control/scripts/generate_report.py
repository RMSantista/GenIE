#!/usr/bin/env python3
"""GenIE QA - Test Report Generator.

Used by: djinn agent (Step 5.7)

Consolidates all test results into a single JSON report.
"""

import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

EVIDENCE_DIR = Path(os.environ.get("GENIE_TEST_EVIDENCE_DIR", "/tmp/genie_qa_tests"))
REPORT_FILE = EVIDENCE_DIR / "test_report.json"


def parse_junit_xml(xml_path: Path) -> dict:
    """Parse a JUnit XML file and extract results.

    Args:
        xml_path: Path to JUnit XML file.

    Returns:
        Dictionary with test results.
    """
    if not xml_path.exists():
        return {"status": "NOT_RUN", "message": f"File not found: {xml_path}"}

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Handle both <testsuites> and <testsuite> root elements
        if root.tag == "testsuites":
            suites = root.findall("testsuite")
        else:
            suites = [root]

        total = 0
        passed = 0
        failed = 0
        skipped = 0
        errors = 0
        tests = []

        for suite in suites:
            total += int(suite.get("tests", 0))
            failed += int(suite.get("failures", 0))
            errors += int(suite.get("errors", 0))
            skipped += int(suite.get("skipped", 0))

            for testcase in suite.findall("testcase"):
                test_info = {
                    "name": testcase.get("name", "unknown"),
                    "classname": testcase.get("classname", ""),
                    "time": float(testcase.get("time", 0)),
                }

                failure = testcase.find("failure")
                error = testcase.find("error")
                skip = testcase.find("skipped")

                if failure is not None:
                    test_info["status"] = "FAILED"
                    test_info["message"] = failure.get("message", "")
                elif error is not None:
                    test_info["status"] = "ERROR"
                    test_info["message"] = error.get("message", "")
                elif skip is not None:
                    test_info["status"] = "SKIPPED"
                    test_info["message"] = skip.get("message", "")
                else:
                    test_info["status"] = "PASSED"

                tests.append(test_info)

        passed = total - failed - errors - skipped

        return {
            "total": total,
            "passed": passed,
            "failed": failed + errors,
            "skipped": skipped,
            "tests": tests,
        }

    except ET.ParseError as e:
        return {"status": "PARSE_ERROR", "message": f"Failed to parse XML: {e}"}


def load_json_results(json_path: Path) -> dict:
    """Load results from a JSON file.

    Args:
        json_path: Path to JSON results file.

    Returns:
        Dictionary with results.
    """
    if not json_path.exists():
        return {"status": "NOT_RUN", "message": f"File not found: {json_path}"}

    try:
        with open(json_path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        return {"status": "PARSE_ERROR", "message": f"Failed to parse JSON: {e}"}


def determine_overall_status(dimensions: dict) -> str:
    """Determine overall QA status from all dimensions.

    Args:
        dimensions: Dictionary of test dimension results.

    Returns:
        Overall status string.
    """
    total_failed = 0
    total_skipped = 0
    has_not_run = False

    for dim_name, dim_results in dimensions.items():
        if isinstance(dim_results, dict):
            if dim_results.get("status") in ("NOT_RUN", "PARSE_ERROR"):
                has_not_run = True
                continue
            total_failed += dim_results.get("failed", 0)
            total_skipped += dim_results.get("skipped", 0)

    if total_failed > 0 or total_skipped > 0:
        return "QA_FAILED"
    if has_not_run:
        return "QA_BLOCKED"
    return "QA_PASSED"


def count_error_screenshots() -> list[str]:
    """Find error screenshots in evidence directory.

    Returns:
        List of screenshot file paths.
    """
    screenshot_dir = EVIDENCE_DIR / "screenshots"
    if not screenshot_dir.exists():
        return []

    return [
        str(f) for f in screenshot_dir.glob("error_*.png")
    ]


def generate_report() -> dict:
    """Generate consolidated test report.

    Returns:
        Complete test report dictionary.
    """
    # Parse all result files
    unit_results = parse_junit_xml(EVIDENCE_DIR / "unit_test_results.xml")
    api_results = parse_junit_xml(EVIDENCE_DIR / "api_test_results.xml")
    ui_results = parse_junit_xml(EVIDENCE_DIR / "ui_test_results.xml")
    error_results = load_json_results(EVIDENCE_DIR / "error_validation.json")

    dimensions = {
        "unit_tests": unit_results,
        "api_tests": api_results,
        "ui_tests": ui_results,
        "error_scenarios": error_results.get("summary", error_results),
    }

    # Calculate totals
    total = 0
    passed = 0
    failed = 0
    skipped = 0

    for dim in dimensions.values():
        if isinstance(dim, dict) and "total" in dim:
            total += dim.get("total", 0)
            passed += dim.get("passed", 0)
            failed += dim.get("failed", 0)
            skipped += dim.get("skipped", 0)

    overall_status = determine_overall_status(dimensions)
    error_screenshots = count_error_screenshots()

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": overall_status,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
        },
        "dimensions": dimensions,
        "evidence": {
            "report": str(REPORT_FILE),
            "error_screenshots": error_screenshots,
            "evidence_dir": str(EVIDENCE_DIR),
        },
    }

    return report


def main() -> int:
    """Main entry point."""
    print("=== GenIE QA Report Generator ===")
    print()

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    report = generate_report()

    # Write report
    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    # Print summary
    summary = report["summary"]
    print(f"Status: {report['status']}")
    print(f"Total:  {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Skipped: {summary['skipped']}")
    print()

    print("Dimensions:")
    for dim_name, dim_results in report["dimensions"].items():
        if isinstance(dim_results, dict) and "total" in dim_results:
            print(f"  {dim_name}: {dim_results.get('passed', 0)}/{dim_results.get('total', 0)} passed")
        elif isinstance(dim_results, dict) and "status" in dim_results:
            print(f"  {dim_name}: {dim_results['status']}")

    if report["evidence"]["error_screenshots"]:
        print()
        print(f"Error screenshots: {len(report['evidence']['error_screenshots'])}")
        for ss in report["evidence"]["error_screenshots"]:
            print(f"  - {ss}")

    print()
    print(f"Report saved: {REPORT_FILE}")

    return 0 if report["status"] == "QA_PASSED" else 1


if __name__ == "__main__":
    sys.exit(main())
