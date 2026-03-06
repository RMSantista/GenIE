#!/usr/bin/env bash
# GenIE QA - API Integration Tests Runner
# Used by: djinn agent (Step 5.3)

set -euo pipefail

EVIDENCE_DIR="${GENIE_TEST_EVIDENCE_DIR:-/tmp/genie_qa_tests}"
RESULTS_FILE="${EVIDENCE_DIR}/api_test_results.xml"

echo "=== GenIE API Tests ==="
echo "Evidence directory: ${EVIDENCE_DIR}"
echo ""

# Create evidence directory
mkdir -p "${EVIDENCE_DIR}"

# Run API integration tests with JUnit XML output
poetry run pytest tests/integration/test_api.py \
    -v \
    --tb=short \
    --junitxml="${RESULTS_FILE}" \
    "$@"

EXIT_CODE=$?

echo ""
echo "=== Results ==="
echo "Exit code: ${EXIT_CODE}"
echo "JUnit XML: ${RESULTS_FILE}"

if [ ${EXIT_CODE} -eq 0 ]; then
    echo "Status: PASSED"
else
    echo "Status: FAILED"
fi

exit ${EXIT_CODE}
