# Workflow State - GenIE

> Maintained automatically by the Orchestrator. Read this file at the start of each session.

## Active Feature

- **Feature**: [Feature name]
- **Description**: [Brief description]
- **Started at**: [timestamp]

## Interaction Level

- **Current Level**: [Low | Medium | High]
- **Set at**: [timestamp]
- **Re-ask after**: Next human approval point

## Step Status

| Step | Name | Agent | Status | Started | Completed | Notes |
|------|------|-------|--------|---------|-----------|-------|
| 1 | Understanding | lamp | Pending | | | |
| 2 | Planning | Orchestrator | Pending | | | |
| 3 | Implementation | wish | Pending | | | |
| 4 | Review | seal | Pending | | | |
| 5 | QA Testing | djinn | Pending | | | |
| 6 | Validation | wish | Pending | | | |
| 7 | Finalization | Orchestrator | Pending | | | |

## Current Position

- **Active Step**: [Number and name]
- **Active Task**: [Task number, e.g., 5.3]
- **Active Agent**: [Agent name]
- **Last Action**: [What was done last]
- **Next Action**: [What should be done now]

## Plan Progress (Step 2 output)

| Phase | Name | Status | Stages Completed | Total Stages |
|-------|------|--------|-----------------|--------------|
| | | | | |

### Current Plan Position
- **Active Phase**: [Phase number and name]
- **Active Stage**: [Stage number and description]

## QA Results (Step 5)

- **Unit Tests**: [Not run | X/X passed (100%) | X/Y failed]
- **API Tests**: [Not run | X/X passed (100%) | X/Y failed]
- **Chrome Tool**: [Not run | Visual OK | Issues found]
- **Playwright UI Tests**: [Not run | X/X passed (100%) | X/Y failed]
- **Error Validation**: [Not run | X/X passed (100%) | X/Y failed]
- **Overall Status**: [Not run | QA_PASSED | QA_FAILED | QA_BLOCKED]
- **Note**: 0 skipped tolerated. Test that doesn't run = fix or remove
- **Report**: /tmp/genie_qa_tests/test_report.json

## Correction Loop History

| # | From Step | To Step | Reason | Timestamp |
|---|-----------|---------|--------|-----------|
| | | | | |

## Approval History

| # | Step | Decision | Notes | Timestamp |
|---|------|---------|-------|-----------|
| | | | | |

## Recovery Instructions

If you are reading this file at the start of a new session:
1. See "Current Position" to know exactly where to resume
2. "Active Step" and "Active Task" indicate the exact point
3. "Next Action" tells you what to do
4. DO NOT restart from Step 1 if the feature is the same
5. Confirm the interaction level with the human
