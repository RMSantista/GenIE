# UI Testing Reference — Mandatory Interactive Validation Protocol

## 1. Anti-Shallow-Testing Rules

These rules are NON-NEGOTIABLE. Violating any rule invalidates the entire test run.

1. **"Visual OK" is NOT a test result.** Every assertion requires evidence of interaction — a click, a submission, a value read. "Page loaded without errors" proves nothing.
2. **NEVER report a button works without clicking it** and verifying the downstream result (API call, navigation, modal, state change).
3. **NEVER report a form works without submitting it** with BOTH valid AND invalid data. A form that accepts everything is broken.
4. **NEVER report a field value is correct without reading the actual value** from the DOM and comparing it to the expected value.
5. **EVERY interactive element on the page MUST be tested.** If there are 5 buttons, test all 5. If there are 8 inputs, test all 8. No exceptions.
6. **Screenshots ONLY on error or failure.** Logs of every interaction are mandatory regardless of outcome.
7. **Testing only the happy path is a test failure.** You MUST test error states, empty states, and invalid inputs.
8. **"No console errors" is a hygiene check, not a test.** It proves the page loaded. It does not prove the page works.

---

## 2. Chrome Tool (mcp__puppeteer) — Systematic Exploration Protocol

Follow these phases IN ORDER. Do not skip any phase. Do not proceed to the next phase until the current phase is complete.

### Phase A: Page Inventory

1. Navigate to the target page.
2. Wait for the page to fully load (network idle, no pending spinners).
3. Enumerate ALL interactive elements on the page:
   - Buttons (including icon buttons and submit buttons)
   - Links (internal and external)
   - Input fields (text, number, email, password, date, file)
   - Select dropdowns
   - Checkboxes and radio buttons
   - Toggles/switches
   - Tabs and accordions
   - Modals/dialogs (trigger elements)
4. For EACH element, record: **label/text**, **type**, **visible state** (enabled/disabled, checked/unchecked, selected value).
5. Count total interactive elements. This number defines the testing scope. Write it down. You will report against it.

### Phase B: Element-by-Element Testing

Test EACH element from Phase A. No element is exempt.

#### Buttons

1. Click the button.
2. Verify the expected action occurred — check for: API request fired, navigation happened, modal opened, state changed, data updated.
3. Verify the UI updated correctly after the action (loading indicator during action, result displayed after).
4. If the button triggers a destructive action (delete, reset, overwrite), verify a confirmation dialog appears BEFORE the action executes.
5. Log: "Clicked [button label] -> [what happened] -> [UI state after]".

#### Form Fields (inputs, selects, textareas)

For EACH field, run ALL of these tests:

| Test | Action | Verify |
|------|--------|--------|
| Valid data | Enter well-formed expected value | Field accepts it, no error shown |
| Empty data | Clear field, trigger validation | Validation error appears if field is required |
| Invalid data | Enter wrong-type data (letters in number field, malformed email) | Rejection with specific error message |
| Boundary — max length | Enter string exceeding max length | Truncation or error |
| Boundary — special chars | Enter `<script>alert(1)</script>`, `'; DROP TABLE --`, unicode `"`, accented chars | Proper escaping, no crash |
| Boundary — zero/negative | For numeric fields: 0, -1, 999999999 | Appropriate handling |

Also verify:
- Field label matches its purpose.
- Placeholder text (if present) describes expected input.
- Required indicator is visible for mandatory fields.

#### Links / Navigation

1. Click the link.
2. Verify the destination page loaded correctly.
3. Verify browser back navigation returns to the original page.
4. For external links, verify they open in a new tab (if expected).

#### Tables / Lists

1. Verify data rows are displayed (not empty when data exists).
2. Read and verify column headers match the expected schema.
3. Read at least one row and verify cell values match expected data.
4. If pagination exists: click next, verify new data loads, click previous, verify return.
5. If sorting exists: click each sortable column header, verify order changes.
6. If filtering exists: apply a filter with valid criteria, verify results narrow. Clear filter, verify all results return. Apply filter with no-match criteria, verify empty state message.

#### Dropdowns / Selects

1. Open the dropdown.
2. Verify all expected options are listed.
3. Select each option and verify the selection registers.
4. If the dropdown drives dependent UI (cascading selects, conditional fields), verify the dependent elements update.

### Phase C: Form Submission Testing

For EVERY form on the page, run ALL of these scenarios:

| # | Scenario | Steps | Verify |
|---|----------|-------|--------|
| 1 | All fields valid | Fill every field with correct data, submit | Success response (toast, redirect, or data update) |
| 2 | All fields empty | Clear every field, submit | Every required field shows a validation error |
| 3 | One field invalid at a time | For each field: set it to invalid, keep others valid, submit | Only that field shows an error; others remain valid |
| 4 | Boundary values | Fill fields with boundary data (max length, min value, special chars), submit | Proper handling — accept or reject with clear message |
| 5 | Duplicate submission | Submit valid data that already exists (if applicable) | Duplicate/conflict error, not silent success |
| 6 | Persistence check | After successful submit, reload the page | Submitted data persists and displays correctly |

After each submission:
- Verify success/error feedback is visible to the user (toast notification, inline message, or redirect).
- Verify the form resets or retains data as expected.
- Verify no loading spinner is stuck.

### Phase D: Error State Testing

**This phase is the most critical. Agents consistently skip this. DO NOT SKIP THIS.**

| # | Scenario | How to trigger | Verify |
|---|----------|----------------|--------|
| 1 | API returns 400 (Bad Request) | Submit malformed data the frontend does not validate | UI shows user-friendly error, NOT raw JSON |
| 2 | API returns 404 (Not Found) | Request a nonexistent resource ID | UI shows "not found" message |
| 3 | API returns 500 (Server Error) | If possible, trigger server error; otherwise note as untestable | UI shows "service unavailable" or equivalent |
| 4 | Network error | If simulable, disconnect; otherwise note as untestable | UI shows connectivity error, does not crash |
| 5 | Unauthorized (401/403) | If token manipulation is possible, test; otherwise note | UI redirects to login or shows permission error |
| 6 | Double-click submit | Click submit button twice rapidly | Only one request fires, OR second is gracefully handled |
| 7 | Rapid navigation | Navigate away during an in-progress API call | No crash, no orphan state |

For EACH error scenario tested:
- Verify the UI does NOT crash.
- Verify the UI does NOT show raw error objects, stack traces, or blank screens.
- Verify the UI does NOT enter an unrecoverable state (stuck spinner, dead buttons).
- Verify the user can recover (retry, navigate away, refresh).

### Phase E: State Verification

After ALL interactions from Phases B-D:

1. Open the browser console. Check for JavaScript errors. Log any found.
2. Check the network tab for failed requests (4xx, 5xx) that were NOT part of intentional error testing.
3. Verify no loading indicators are stuck.
4. Verify the page is still fully functional — click a button, confirm it still works.
5. Verify data integrity: data currently displayed matches what was last submitted/expected.

---

## 3. Playwright — Automated Validation Rules

When writing Playwright tests for UI validation:

1. **Assert on values, not existence.** Use `expect(locator).toHaveText('Expected Text')`, NOT just `expect(locator).toBeVisible()`.
2. **Assert API response bodies.** Intercept requests and check payloads and response data, not just status codes.
3. **Mock error states.** Use `page.route()` to intercept API calls and return 400, 404, 500 responses. Verify UI handles each.
4. **Test every form scenario.** Translate Phase C scenarios into parameterized tests.
5. **Test field-level validation.** For each required field, submit with that field empty and assert the specific error message text.
6. **Use strict locators.** Prefer `getByRole`, `getByLabel`, `getByTestId`. Avoid fragile CSS selectors.
7. **No `page.waitForTimeout()` as an assertion.** Waiting is not testing. Wait for a specific condition, then assert.
8. **Assert post-action state.** After every action (click, submit, navigate), assert the resulting state explicitly.

Playwright test structure per form:

```typescript
test.describe('Form: [FormName]', () => {
  test('submits successfully with valid data', async ({ page }) => { /* ... */ });
  test('shows all validation errors when submitted empty', async ({ page }) => { /* ... */ });
  test('shows specific error for invalid [field]', async ({ page }) => { /* ... */ });
  test('handles API 500 gracefully', async ({ page }) => {
    await page.route('**/api/endpoint', route => route.fulfill({ status: 500 }));
    // fill and submit, then assert error message
  });
  test('prevents double submission', async ({ page }) => { /* ... */ });
});
```

---

## 4. Evidence Requirements

A test without evidence is not a test. Every interaction MUST produce a log entry.

**Reporting rule: report ONLY genuine defects.**

Every element and scenario must be TESTED, but only REPORT what is broken:
- If a button works correctly → do not report it. Silence means pass.
- If a validation correctly rejects bad input → do not report it. That's expected behavior.
- If a button does NOT work → REPORT with full evidence.
- If a validation ACCEPTS bad input that should be rejected → REPORT with full evidence.
- If the UI crashes, shows raw errors, or enters an unrecoverable state → REPORT with screenshot.

**Valid defect evidence formats:**

- **Broken button:** `Clicked 'Submit' -> No API call fired -> Button unresponsive -> DEFECT`
- **Missing validation:** `Field 'config_id' = "" (required) -> No error shown, form submitted -> DEFECT`
- **Wrong error:** `Field 'email' = "invalid" -> Error says "Required" instead of "Invalid format" -> DEFECT`
- **Crash:** `Mocked API 500 on /extract -> UI showed raw JSON stack trace -> DEFECT [screenshot attached]`
- **Accepts bad input:** `Field 'name' = "<script>alert(1)</script>" -> Accepted without sanitization -> DEFECT`

**Summary line:** `Page has 12 interactive elements. All 12 tested. 2 defects found.`

**Invalid evidence (automatic test failure):**

- "Page looks correct"
- "No errors observed"
- "Form appears to work"
- "UI is functional"
- Any statement without a specific interaction and its specific result
- Reporting something that works correctly as if it were evidence
- Reporting expected errors as if they were defects

---

## 5. UI Test Report Format

Use this exact format. Do not abbreviate or omit sections.

```
## UI Test Report — [Page/Feature Name]

### Page Inventory
- URL: [full URL]
- Total interactive elements found: N
- Elements: [list each with type]

### Coverage
- Elements tested: N/N (must be 100%)
- Form scenarios tested: N
- Error states tested: N

### Defects Found (only list what is genuinely broken)
| # | Element/Scenario | Expected | Actual | Evidence |
|---|------------------|----------|--------|----------|
| 1 | Config ID (empty submit) | Validation error shown | No error, form submitted | DEFECT |
| 2 | Network timeout | Error message or retry | Loading spinner stuck forever | DEFECT [screenshot] |
| 3 | Double-click submit | Single request | Two requests fired, duplicate data | DEFECT |

If no defects: "No defects found. All N elements and M scenarios tested."

### Summary
- Console errors found: N
- Total defects: N
- Verdict: **UI_PASSED** (0 defects) / **UI_FAILED** (1+ defects)
```

If ANY element is untested, the verdict MUST be **UI_FAILED** with reason "Incomplete coverage."

---

## 6. Trigger Rules

Apply this FULL protocol when:

- A new UI page or component is created.
- An existing UI page receives functional changes (new fields, buttons, workflows, state logic).
- An API endpoint consumed by the UI changes its request/response contract.
- A UI bug fix is implemented (re-test the fixed flow AND regression-test surrounding flows).

Do NOT apply this protocol when:

- Changes are purely backend with no UI consumer.
- Changes are documentation-only.
- Changes are styling-only (colors, fonts, spacing) with zero functional impact.

When in doubt, apply the protocol. Under-testing is always worse than over-testing.
