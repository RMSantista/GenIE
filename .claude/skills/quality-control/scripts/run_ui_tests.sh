#!/usr/bin/env bash
# GenIE QA - UI Tests Runner (Playwright)
# Used by: djinn agent (Step 5.5)
# Screenshots captured ONLY on error

set -euo pipefail

EVIDENCE_DIR="${GENIE_TEST_EVIDENCE_DIR:-/tmp/genie_qa_tests}"
SCREENSHOT_DIR="${EVIDENCE_DIR}/screenshots"
RESULTS_FILE="${EVIDENCE_DIR}/ui_test_results.xml"
SERVER_PORT="${GENIE_TEST_PORT:-8000}"
SERVER_HOST="${GENIE_TEST_HOST:-localhost}"
SERVER_PID=""

echo "=== GenIE UI Tests (Playwright) ==="
echo "Evidence directory: ${EVIDENCE_DIR}"
echo "Screenshot policy: ONLY on error"
echo ""

# Create evidence directories
mkdir -p "${SCREENSHOT_DIR}"

# Function to clean up server on exit
cleanup() {
    if [ -n "${SERVER_PID}" ] && kill -0 "${SERVER_PID}" 2>/dev/null; then
        echo "Stopping test server (PID: ${SERVER_PID})..."
        kill "${SERVER_PID}" 2>/dev/null || true
        wait "${SERVER_PID}" 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Check if server is already running
if curl -s "http://${SERVER_HOST}:${SERVER_PORT}/docs" > /dev/null 2>&1; then
    echo "Server already running on port ${SERVER_PORT}"
else
    echo "Starting test server on port ${SERVER_PORT}..."
    poetry run uvicorn genie.main:app --host "${SERVER_HOST}" --port "${SERVER_PORT}" &
    SERVER_PID=$!

    # Wait for server to start (max 30 seconds)
    RETRIES=30
    while [ ${RETRIES} -gt 0 ]; do
        if curl -s "http://${SERVER_HOST}:${SERVER_PORT}/docs" > /dev/null 2>&1; then
            echo "Server started successfully"
            break
        fi
        RETRIES=$((RETRIES - 1))
        sleep 1
    done

    if [ ${RETRIES} -eq 0 ]; then
        echo "ERROR: Server failed to start within 30 seconds"
        exit 1
    fi
fi

echo ""
echo "Running Playwright tests (headless)..."

# Run Playwright UI tests
# Screenshots only on failure (--screenshot only-on-failure)
poetry run pytest tests/ui/ \
    -v \
    --tb=short \
    --junitxml="${RESULTS_FILE}" \
    --screenshot only-on-failure \
    --output "${SCREENSHOT_DIR}" \
    "$@" 2>&1 || true

EXIT_CODE=${PIPESTATUS[0]:-$?}

echo ""
echo "=== Results ==="
echo "Exit code: ${EXIT_CODE}"
echo "JUnit XML: ${RESULTS_FILE}"
echo "Screenshots (errors only): ${SCREENSHOT_DIR}/"

if [ ${EXIT_CODE} -eq 0 ]; then
    echo "Status: PASSED"
else
    echo "Status: FAILED"
    echo "Check error screenshots in: ${SCREENSHOT_DIR}/"
fi

exit ${EXIT_CODE}
