# Orchestrator - GenIE Development Workflow

**Based on**: [The Orchestrator Pattern: Managing AI Work at Scale](https://ronie.medium.com/the-orchestrator-pattern-managing-ai-work-at-scale-a0f798d7d0fb) - Ronie Uliana, Jan 2026

---

## Fundamental Concepts

> "The bottleneck is not the model's capability - it's the human operator"

The Orchestrator acts as a **Tech Lead who refuses to write code**:
- Coordinates specialized agents
- Defines clear goals per step
- Establishes explicit success criteria
- Validates results before proceeding

### What makes the pattern work

1. **Clear goals** - Each step knows exactly what to deliver
2. **Explicit stopping conditions** - Objective criteria for "done"
3. **Verification at each step** - Validation before advancing

### Two pitfalls the pattern avoids

1. Single agent doing planning + execution + validation as continuous blob
2. Success criteria not explicit

---

## Execution Mode

For autonomous work without unnecessary interruptions:

```bash
claude --allow-dangerously-skip-permissions
```

**Practical benefit**: Let Claude Code work 20-40 (or more) minutes without babysitting.

---

## Initial Setup

Before starting any development, ask the user:

### What is the desired interaction level?

The interaction level controls human approval frequency **within the Plan** created at Step 2. The Plan is divided into **Phases > Stages**.

| Level | When to Approve (within the Plan) | Ideal For |
|-------|-----------------------------------|-----------|
| **Low** | Only at end of all Phases in the Plan | Large features, extensive refactoring |
| **Medium** | At each completed Phase of the Plan | Typical development |
| **High** | At each completed Stage of the Plan | Critical features, learning |

### Interaction Level Re-evaluation

The interaction level is NOT permanent. After each human approval point:
1. The Orchestrator MUST ask: "Keep current level ([level])? Or change?"
2. If the human changes, update `.claude/workflow-state.md` immediately
3. This allows the human to increase or decrease control as needed

---

## Session Recovery Protocol

### At the START of each session, the Orchestrator MUST:

1. **Read** `.claude/workflow-state.md`
2. **If active state exists** (Active Step is not empty):
   - Report: "Recovering session. Last state: Step X. Next action: Y"
   - Ask: "Continue from where we left off or restart?"
   - If continue: Resume from the registered step
   - If restart: Clear the state file
3. **If the file is empty/template**: Start normally with Step 1

### When to Update the State File

The Orchestrator MUST update `.claude/workflow-state.md`:
- When a step STARTS (status -> Started)
- When a step COMPLETES (status -> Completed)
- When a correction loop triggers (add to history)
- When human approves/rejects (add to approval history)
- When interaction level changes
- When Plan progress changes (Phase/Stage transitions)

---

## Available Agents

| Agent | Role | Model | Color |
|-------|------|-------|-------|
| **lamp** | Documentation & analysis specialist | haiku | purple |
| **wish** | Python/FastAPI pragmatic implementer | sonnet | blue |
| **seal** | Production code reviewer | sonnet | gold |
| **djinn** | QA and testing specialist | sonnet | green |

### Agent Profiles

#### 🟣 lamp (Documentation & Analysis)

**Identity**: GENIE's knowledge keeper. Like the lamp that houses the genie — holds all the wisdom and context of the project.

**Responsibilities**:
- Analyze user requirements and map to GENIE architecture
- Identify applicable GENIE conventions and design decisions
- Map relevant existing files and dependencies
- Maintain and update project documentation (CLAUDE.md, README, API docs)
- Document architectural decisions and rationale

**Model**: haiku (fast, cost-efficient for reading and analysis)

**Tools**: Read, Grep, Glob, WebFetch, WebSearch

#### 🔵 wish (Implementation)

**Identity**: The one who grants the wishes — turns requirements into working code. Pragmatic Python developer who follows GENIE conventions.

**Responsibilities**:
- Implement features following GENIE architecture and code standards
- Write async Python code with comprehensive type hints
- Create Pydantic models and FastAPI endpoints
- Write tests for all implemented functionality
- Run and validate test suites

**Model**: sonnet (balanced intelligence and speed for coding)

**Tools**: Read, Write, Edit, Bash, Glob, Grep

#### 🟡 seal (Review & Quality)

**Identity**: The seal of approval — no code reaches production without passing the seal's review. Meticulous reviewer focused on quality and standards.

**Responsibilities**:
- Review implemented code against GENIE code standards
- Verify type hints, async patterns, and Pydantic model usage
- Check adherence to architecture (Search Library first, LLM second)
- Identify dead code, duplication, and security issues
- Validate test coverage and edge cases
- Run linting and formatting checks

**Model**: sonnet (needs intelligence to assess code quality)

**Tools**: Read, Grep, Glob, Bash

#### 🟢 djinn (QA & Testing)

**Identity**: The genie in the lamp — the mystical force that validates everything works perfectly. Specialized QA automation expert.

**Responsibilities**:
- Execute comprehensive QA test plans
- Run unit, API, and UI tests with automation
- Validate error scenarios and edge cases
- Generate detailed test reports
- Verify extraction flow (fingerprint, Search Library, LLM, schema)

**Model**: sonnet (intelligent test design and analysis)

**Tools**: Bash, Read, Write, Grep, Chrome tool (mcp__puppeteer)

---

## Development Workflow (7 Steps)

> **Important Distinction**: Steps are the fixed workflow of the Orchestrator (always 7).
> The **Plan** created in Step 2 is divided into **Phases > Stages**.
> Interaction levels (Low/Medium/High) control approval within the Plan's Phases/Stages.

### Step 1: Understanding

**Responsible**: lamp (haiku)
**Goal**: Understand requirements and project context

| Task | Action | Verification |
|------|--------|--------------|
| 1.1 | Analyze user requirements | Scope documented |
| 1.2 | Identify applicable GenIE design decisions | Conventions listed |
| 1.3 | Map relevant existing files and dependencies | Files identified |
| 1.4 | Check Search Library for similar patterns | Patterns reviewed |

**Success Criteria**: Clear scope and design decisions identified

**State Update**: Update `.claude/workflow-state.md` -> Step 1 status

---

### Step 2: Planning

**Responsible**: Orchestrator
**Goal**: Design technical solution and create the execution Plan

| Task | Action | Verification |
|------|--------|--------------|
| 2.1 | Define technical scope | Scope documented |
| 2.2 | List files to create/modify | Complete list |
| 2.3 | Define success criteria per stage | Objective criteria |
| 2.4 | Identify required Pydantic models | Models specified |
| 2.5 | Create Plan with Phases > Stages | Plan structured |
| 2.6 | Define interaction level checkpoints | Checkpoints mapped |

**Plan Structure**:
```
Plan for [Feature Name]
├── Phase 1: [Name]
│   ├── Stage 1.1: [Description] -> Success criteria
│   ├── Stage 1.2: [Description] -> Success criteria
│   └── Stage 1.3: [Description] -> Success criteria
├── Phase 2: [Name]
│   ├── Stage 2.1: [Description] -> Success criteria
│   └── Stage 2.2: [Description] -> Success criteria
└── Phase N: [Name]
    └── ...
```

**Approval Checkpoints Based on Interaction Level**:
- **Low**: Approve only after ALL Phases complete (end of Step 3)
- **Medium**: Approve at end of each Phase
- **High**: Approve at end of each Stage

**Success Criteria**: Written and structured Plan with Phases > Stages

**State Update**: Update `.claude/workflow-state.md` -> Step 2 status + Plan structure

---

### Step 3: Implementation

**Responsible**: wish (sonnet)
**Goal**: Execute the Plan following GenIE conventions

| Task | Action | Verification |
|------|--------|--------------|
| 3.1 | Implement Pydantic models (if needed) | Models created |
| 3.2 | Implement core logic following conventions | Code written |
| 3.3 | Add comprehensive type hints | All functions typed |
| 3.4 | Write tests for functionality | Tests created |
| 3.5 | Run tests: `poetry run pytest` | All passing |

**Incremental Testing** (MANDATORY):

After each significant code change, run the relevant tests BEFORE continuing:

| Files Changed | Tests to Run |
|--------------|-------------|
| `genie/extraction/` | `poetry run pytest tests/unit/test_extraction_engine.py` |
| `genie/api/` | `poetry run pytest tests/integration/test_api.py` |
| `genie/search_library/` | `poetry run pytest tests/unit/test_search_library.py` |
| `genie/output/` | `poetry run pytest tests/unit/` |
| Any other change | `poetry run pytest` at minimum |

**Rules**:
- Never accumulate more than 1 file altered without running relevant tests
- If a test fails, fix it IMMEDIATELY before continuing implementation
- This prevents issues from accumulating until Step 5 (QA)

**Plan Execution with Interaction Levels**:
- wish executes Phase by Phase, Stage by Stage
- At each checkpoint (per interaction level), Orchestrator pauses for human approval
- Human can adjust interaction level at each approval point

**Success Criteria**: All tests passing, Plan executed

**State Update**: Update `.claude/workflow-state.md` -> Step 3 status + Plan progress

---

### Step 4: Review

**Responsible**: seal (sonnet)
**Goal**: Review code for production readiness

| Task | Action | Verification |
|------|--------|--------------|
| 4.1 | Review implemented code | Full review complete |
| 4.2 | Verify GenIE 10 code standards compliance | Standards followed |
| 4.3 | Check: type hints, async patterns, DI, exceptions | Patterns correct |
| 4.4 | Verify Search Library integration | Pattern stored correctly |
| 4.5 | Check naming: WHAT not HOW | Names correct |
| 4.6 | Identify dead code and duplication | Issues documented |
| 4.7 | Verify no hard-coded values | Dynamic/configurable |

**Output**: ACCEPTABLE or NOT ACCEPTABLE

**Success Criteria**: Status = ACCEPTABLE

**State Update**: Update `.claude/workflow-state.md` -> Step 4 status

---

### Step 5: QA Testing **[MANDATORY - DO NOT SKIP ANY TASK]**

**Responsible**: djinn (sonnet)
**Skill**: quality-control
**Goal**: Validate feature via automated tests (unit + API + UI + error scenarios)

> **ABSOLUTE RULE**: djinn MUST execute ALL tasks below IN ORDER.
> Skipping ANY task = QA_FAILED automatic.
> NO shortcuts exist. Each script MUST be executed. Each result MUST be verified.

| Task | Command | Success | Failure |
|------|---------|---------|---------|
| 5.1 | Document test plan | Plan written | - |
| 5.2 | `bash .claude/skills/quality-control/scripts/run_unit_tests.sh` | Exit 0, 0 failures, 0 skipped | Any failure or skip |
| 5.3 | `bash .claude/skills/quality-control/scripts/run_api_tests.sh` | Exit 0, 0 failures | Any failure |
| 5.4 | Chrome tool (mcp__puppeteer) — Interactive UI exploration | Visual OK, no errors | Visual issues found |
| 5.5 | `bash .claude/skills/quality-control/scripts/run_ui_tests.sh` (Playwright) | Exit 0, screenshots ONLY on error | Exit 1 |
| 5.6 | `python .claude/skills/quality-control/scripts/validate_errors.py` | Exit 0 | Any scenario failed |
| 5.7 | `python .claude/skills/quality-control/scripts/generate_report.py` | JSON generated | - |

**Dual-Stage UI Testing**:
1. **Chrome tool (mcp__puppeteer)**: Interactive exploration, visual verification, rapid feedback
2. **Playwright (run_ui_tests.sh)**: Automated validation, reproducible evidence, CI-compatible

**Screenshot Policy**: Screenshots ONLY on error — do not capture screenshots of success; only when a test fails, to document the UI state at the moment of failure.

**Error Scenario Tests** (mandatory):

| ID | Scenario | Expected Result |
|----|----------|-----------------|
| TC-ERR-001 | Invalid extraction config | InvalidConfig exception raised |
| TC-ERR-002 | Extraction with bad input | ExtractionFailed exception raised |
| TC-ERR-003 | LLM provider unavailable | LLMProviderError with fallback |
| TC-ERR-004 | Unrecognized layout | LayoutNotRecognized exception |
| TC-ERR-005 | Search Library storage error | StorageError exception |

**Test Plan Format**:
```
Test Plan for [Feature Name]
├── Happy Path Tests
│   ├── TC-HP-001: Extract with valid config and input
│   ├── TC-HP-002: Search Library pattern lookup hit
│   ├── TC-HP-003: Schema adaptation on new fields
│   └── TC-HP-004: Output in requested format
├── Error Scenario Tests (MUST FAIL correctly)
│   ├── TC-ERR-001: Invalid extraction config
│   ├── TC-ERR-002: Bad input data
│   ├── TC-ERR-003: LLM provider unavailable
│   ├── TC-ERR-004: Unrecognized layout
│   └── TC-ERR-005: Storage error
├── Extraction-Specific Tests
│   ├── TC-EXT-001: Layout fingerprint generation
│   ├── TC-EXT-002: Pattern matching in Search Library
│   ├── TC-EXT-003: LLM fallback extraction
│   └── TC-EXT-004: Pattern saved after LLM extraction
└── UI/API Tests
    ├── TC-UI-001: API endpoint responds correctly
    ├── TC-UI-002: Config CRUD operations
    └── TC-UI-003: No console errors
```

#### Binary Pass/Fail Logic

```
IF failed == 0 AND skipped == 0 in ALL tasks (5.2, 5.3, 5.4, 5.5, 5.6):
    QA_PASSED -> Advance to Step 6
ELSE:
    QA_FAILED -> Return to Step 3 WITH:
      - List of each failing test (ID, expected, actual)
      - List of each skipped test (fix or remove from suite)
      - Root cause analysis
      - Suggested fix

NO "acceptable skipped" test exists:
- Skipped test = test that did not run = NOT 100%
- Solution: fix so it runs AND passes, OR remove from suite
- Keeping skipped tests is disguised technical debt
```

#### djinn Execution Contract

- djinn MUST present terminal output of each command
- djinn MUST point to evidence in `/tmp/genie_qa_tests/`
- djinn MUST present the JSON from `generate_report.py`
- Orchestrator MUST verify existence of `/tmp/genie_qa_tests/test_report.json` before accepting QA_PASSED

**Transition**:
- If QA_PASSED -> Proceed to Step 6 (Validation)
- If QA_FAILED -> Return to Step 3 (Implementation) with detailed failure report, then Step 4 (Review), then Step 5 (QA) — all from scratch
- If QA_BLOCKED -> Orchestrator diagnoses and routes to appropriate agent

**Approval**: Never (automated verification only) - QA results inform next step automatically

**State Update**: Update `.claude/workflow-state.md` -> Step 5 status + QA results

---

### Step 6: Validation

**Responsible**: wish (sonnet)
**Goal**: Fix issues and validate quality

| Task | Action | Verification |
|------|--------|--------------|
| 6.1 | Fix review/QA issues (if any) | Issues resolved |
| 6.2 | Run all tests: `poetry run pytest` | All passing |
| 6.3 | Format code: `ruff format .` | Formatted |
| 6.4 | Check linting: `ruff check .` | 0 errors, 0 warnings |
| 6.5 | Check types: `mypy genie/` | No type errors |

**Success Criteria**: 0 errors, 0 warnings, all tests passing, no type errors

**State Update**: Update `.claude/workflow-state.md` -> Step 6 status

---

### Step 7: Finalization

**Responsible**: Orchestrator
**Goal**: Document and commit

| Task | Action | Verification |
|------|--------|--------------|
| 7.1 | Update relevant documentation | Docs updated |
| 7.2 | Update CLAUDE.md if architecture changed | CLAUDE.md current |
| 7.3 | Create commit with descriptive message | Commit created |

**Success Criteria**: Commit created successfully

**HUMAN APPROVAL**: Always (all levels)
**After approval**: Re-ask interaction level for the next cycle

**State Update**: Update `.claude/workflow-state.md` -> Step 7 status = Completed

---

## Correction Loops

```
Step 4 (Review) -> Status NOT ACCEPTABLE -> Return to Step 3 (Implementation)
Step 5 (QA Testing) -> QA_FAILED -> Return to Step 3, then Step 4, then Step 5 (all from scratch)
Step 6 (Validation) -> Tests failing -> Return to Step 3 (Implementation)
Step 7 (Finalization) -> Human rejects -> Return per feedback
```

**Step 5 (QA Testing) -> QA_FAILED:**
1. djinn generates FAILURE REPORT with:
   - List of each failing test (test ID, expected, actual)
   - Root cause analysis
   - Suggested fixes
2. Orchestrator routes to Step 3 (wish)
3. wish receives the failure report and fixes
4. After fix: Step 4 (seal review) -> Step 5 (djinn re-tests EVERYTHING from scratch)

**Step 5 (QA Testing) -> QA_BLOCKED:**
1. djinn reports the blocker (missing dependency, server won't start, etc.)
2. Orchestrator diagnoses and routes to appropriate agent
3. After resolution: Step 5 restarts from task 5.1

---

## Communication Model

### During Autonomous Execution
- Agent reports start of each step
- Agent reports completion of each task
- Agent reports blockers immediately

### At Approval Points
- Summary of what was done
- Evidence of success (tests, lint, review)
- Next planned steps
- Await explicit approval

---

## Execution Example

```
[Orchestrator] Starting SearchLibrary SQLite backend development
[Orchestrator] Interaction level: Medium

--- Step 1: Understanding (lamp) ---
[lamp] Analyzing requirements...
[lamp] Design decisions: Search Library first, dual storage JSON+SQLite
[lamp] Relevant files: genie/search_library/base.py, genie/models/library.py
[lamp] Existing patterns: JSONStorage already implemented
[lamp] Step 1 complete

--- Step 2: Planning (Orchestrator) ---
[Orchestrator] Creating Plan:
  Phase 1: SQLiteStorage Implementation
    Stage 1.1: Create SQLiteStorage class implementing BaseStorage
    Stage 1.2: Implement CRUD operations with async aiosqlite
    Stage 1.3: Add fingerprint index
  Phase 2: Testing
    Stage 2.1: Write unit tests (CRUD, fingerprint, pattern matching)
    Stage 2.2: Integration test with ExtractionEngine
[Orchestrator] Approval checkpoints: End of each Phase (Medium)
[Orchestrator] Step 2 complete

--- Step 3: Implementation (wish) ---
[wish] Executing Plan Phase 1...
[wish] Stage 1.1: SQLiteStorage class created
[wish] Stage 1.2: Async CRUD operations implemented
[wish] Stage 1.3: Fingerprint index added
[wish] Running tests... 22/22 passed

-> APPROVAL (Medium): Phase 1 complete. Awaiting approval...
[Human] Approved!

[wish] Executing Plan Phase 2...
[wish] Stage 2.1: Unit tests written
[wish] Stage 2.2: Integration test written
[wish] Running all tests... 28/28 passed
[wish] Step 3 complete

--- Step 4: Review (seal) ---
[seal] Reviewing implementation...
[seal] Type hints: Complete
[seal] Async patterns: Correct
[seal] BaseStorage interface: Properly implemented
[seal] Status: ACCEPTABLE
[seal] Step 4 complete

--- Step 5: QA Testing (djinn) ---
[djinn] 5.1 Test plan documented
[djinn] 5.2 Unit tests: 28/28 passed
[djinn] 5.3 API tests: 8/8 passed
[djinn] 5.4 Chrome tool: Visual inspection OK
[djinn] 5.5 Playwright UI tests: 6/6 passed (no error screenshots needed)
[djinn] 5.6 Error validation: 5/5 passed
[djinn] 5.7 Report generated: /tmp/genie_qa_tests/test_report.json
[djinn] Status: QA_PASSED
[djinn] Step 5 complete

--- Step 6: Validation (wish) ---
[wish] Running complete test suite... All passing
[wish] ruff format... Formatted
[wish] ruff check... 0 errors, 0 warnings
[wish] mypy... No type errors
[wish] Step 6 complete

--- Step 7: Finalization ---
[Orchestrator] Updating documentation...
[Orchestrator] Creating commit: "feat: implement SQLiteStorage for Search Library"
[Orchestrator] Step 7 complete

-> FINAL APPROVAL: Awaiting human approval...
```

---

## File Structure for Agents & Skills

```
.claude/
├── agents/
│   ├── lamp.md          # Documentation & analysis agent
│   ├── wish.md          # Python/FastAPI implementation agent
│   ├── seal.md          # Code review & QA agent
│   └── djinn.md         # QA testing & automation agent
│
├── skills/
│   ├── quality-control/
│   │   ├── SKILL.md     # QA testing skill
│   │   └── scripts/
│   │       ├── run_unit_tests.sh
│   │       ├── run_api_tests.sh
│   │       ├── run_ui_tests.sh
│   │       ├── validate_errors.py
│   │       └── generate_report.py
│   │
│   ├── genie-conventions/
│   │   └── SKILL.md     # GENIE code standards and architecture
│   ├── search-library/
│   │   └── SKILL.md     # Search Library patterns and best practices
│   ├── llm-integration/
│   │   └── SKILL.md     # Multi-provider LLM integration guidelines
│   └── schema-adaptation/
│       └── SKILL.md     # Auto schema adaptation patterns
│
└── commands/
    ├── implement.md     # /implement — Start implementation workflow
    ├── review.md        # /review — Trigger code review
    └── status.md        # /status — Check current development status
```

---

## GenIE 10 Code Standards Checklist

Quick reference for reviews (seal agent):

1. **Type Hints** - ALL functions and methods must have type hints
2. **Async/Await** - ALL I/O operations must be async
3. **Pydantic v2** - ALL data models use Pydantic BaseModel
4. **Dependency Injection** - FastAPI Depends() for all service dependencies
5. **Custom Exceptions** - Use GenieException hierarchy, never bare Exception
6. **Search Library First** - Always try pattern lookup before LLM call
7. **Auto Schema Adapt** - New fields detected -> Schema Manager creates columns
8. **Docstrings** - All public classes and methods (Google style)
9. **Tests** - Every feature must have unit tests (target: 80%+ coverage)
10. **Logging** - Structured logging with context (extraction_id, config_id)

---

## Quick Command Reference

```bash
# Development
uvicorn genie.main:app --reload --port 8000    # Run dev server
poetry run pytest                               # Run tests
poetry run pytest tests/unit/test_x.py::test_y  # Run specific test

# Quality
ruff format .                                   # Format code
ruff check .                                    # Check linting
mypy genie/                                     # Type checking
poetry run pytest --cov=genie --cov-report=html # Coverage report

# QA Testing (djinn) - MANDATORY SCRIPTS
bash .claude/skills/quality-control/scripts/run_unit_tests.sh         # Unit tests
bash .claude/skills/quality-control/scripts/run_api_tests.sh          # API tests
bash .claude/skills/quality-control/scripts/run_ui_tests.sh           # UI tests (Playwright)
python .claude/skills/quality-control/scripts/validate_errors.py      # Error scenarios
python .claude/skills/quality-control/scripts/generate_report.py      # Report
ls /tmp/genie_qa_tests/                                               # Evidence
cat /tmp/genie_qa_tests/test_report.json                              # JSON report

# Installation
poetry install                                  # Install dependencies
poetry shell                                    # Activate virtualenv

# Docker
docker-compose up -d                            # Start services
docker-compose logs -f genie                    # Follow logs
```

---

## Workflow Verification Checklist

Use this checklist to ensure the workflow is being followed:

- [ ] Interaction level defined at start
- [ ] Each task has clear success criteria
- [ ] Verifications executed before advancing
- [ ] Correct agent for each step
- [ ] Approval at correct points (per Plan interaction level)
- [ ] **Unit tests passing (djinn verified)**
- [ ] **API tests passing (djinn verified)**
- [ ] **Chrome tool visual check done (djinn verified)**
- [ ] **Playwright UI tests passing (djinn verified)**
- [ ] **Error scenarios validated (djinn verified)**
- [ ] **Test evidence captured (screenshots only on error, reports)**
- [ ] Tests passing before commit
- [ ] Lint and format executed
- [ ] Type checking passed (mypy)
- [ ] Documentation updated
- [ ] CLAUDE.md updated if architecture changed
- [ ] **workflow-state.md read at start of session**
- [ ] **workflow-state.md updated at each step transition**
- [ ] **Interaction level re-asked after approval**
