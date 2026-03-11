---
name: project-analysis
description: "Requirements analysis, architecture mapping, and documentation for GenIE data extraction framework. Analyze user requirements against GenIE's 5 design decisions, map affected components and files, identify applicable code standards, and produce structured analysis summaries. Use when: (1) Analyzing new feature requirements, (2) Mapping file dependencies, (3) Identifying architecture impact, (4) Documenting design decisions, (5) Preparing context for implementation agents."
---

# Project Analysis

Analyze requirements, map architecture impact, and produce structured context for GenIE development.

## Analysis Workflow

Execute these 4 steps sequentially for every analysis request.

### Step 1 — Analyze Requirements

1. Parse the user request into discrete functional requirements.
2. Classify each requirement: new feature | enhancement | bug fix | refactor | documentation.
3. Evaluate against the 5 design decisions (see [references/design-decisions.md](references/design-decisions.md)):
   - Does it preserve "Generic, not General"?
   - Does it respect "Search Library First, LLM Second"?
   - Does it support "Auto Schema Adaptation"?
   - Does it maintain "Layout-Independent Extraction"?
   - Does it keep GenIE as an "Independent Library"?
4. Flag any requirement that conflicts with a design decision.

### Step 2 — Map Files

1. Identify all components affected by each requirement.
2. List concrete file paths using the architecture reference (see [references/architecture.md](references/architecture.md)).
3. Trace dependencies: upstream callers and downstream consumers.
4. Note files that need creation vs. modification.

### Step 3 — Identify Conventions

1. Match each affected file against applicable code standards (see [references/code-standards.md](references/code-standards.md)).
2. Call out standards critical to the change (e.g., async I/O for new endpoints, Pydantic v2 for new models).
3. Identify required test coverage and testing strategy.

### Step 4 — Document Results

Produce the analysis summary using the output template below. Deliver it directly — do not wrap in a code block unless requested.

## Output Template

```
# Analysis Summary

## Requirements
- [R1] <requirement description> — <classification>
- [R2] ...

## Design Decision Alignment
| Requirement | Decision | Status | Notes |
|-------------|----------|--------|-------|
| R1 | Generic, not General | OK/CONFLICT | ... |

## Affected Components
| Component | File Path | Action | Reason |
|-----------|-----------|--------|--------|
| ExtractionEngine | spec/extraction/engine.py | modify | ... |

## Dependency Map
- <component> → depends on → <component>

## Code Standards Checklist
- [ ] Type hints on all new functions
- [ ] Async/await for I/O operations
- [ ] Pydantic v2 models for data structures
- [ ] Custom exceptions (GenieException hierarchy)
- [ ] Google-style docstrings
- [ ] Tests (80%+ coverage target)

## Risks & Recommendations
- <risk or recommendation>

## Implementation Notes
- <context for the implementation agent (wish)>
```

## References

- [Architecture](references/architecture.md) — component diagram, extraction pipeline, file locations
- [Design Decisions](references/design-decisions.md) — the 5 key decisions with rationale
- [Code Standards](references/code-standards.md) — the 10 mandatory standards
