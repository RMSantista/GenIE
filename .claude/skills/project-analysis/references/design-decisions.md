# GenIE Design Decisions

The 5 key decisions that define GenIE's architecture. Every feature and change must align with these.

## 1. Generic, not General

GenIE requires configuration per use case. It does not auto-extract everything from a document.

**What it means:**
- The user defines fields, extraction instructions, and output format.
- GenIE adapts to any document layout within that configuration.
- Without configuration, GenIE does nothing.

**Analogy:** A universal mold — it can make anything, but you must provide the recipe.

**When analyzing:** Flag any requirement that assumes automatic extraction without user-defined configuration.

## 2. Search Library First, LLM Second

Cost efficiency is a core principle. Always try stored patterns before invoking an LLM.

**Flow:**
1. Generate layout fingerprint (SHA256, 16-char hex).
2. Look up matching patterns in Search Library.
3. If found → apply REGEX/query extraction (zero LLM cost).
4. If not found → use LLM → save resulting pattern to library for future reuse.

**Impact:**
- After initial extraction, subsequent documents with the same layout cost zero LLM tokens.
- Target: >95% Search Library hit rate after library is built.
- Target: >80% LLM token reduction over time.

**When analyzing:** Ensure new features preserve the lookup-before-LLM flow. Any feature that bypasses the Search Library needs strong justification.

## 3. Auto Schema Adaptation

The Schema Manager Agent adds new columns/fields automatically when new data fields are detected.

**How it works:**
- During extraction, if the LLM returns fields not in the current output schema, Schema Manager creates new columns.
- Synonym dictionaries normalize field names (e.g., "Hemoglobin" = "Hb" = "HGB").
- No manual intervention required for schema evolution.

**When analyzing:** Verify that new features involving data models support dynamic field addition. Static, rigid schemas violate this decision.

## 4. Layout-Independent Extraction

Extract the same data regardless of document layout. Different source formats produce the same structured output.

**How it works:**
- Layout fingerprinting identifies the source format.
- Each fingerprint maps to specific extraction patterns.
- The output schema remains consistent across layouts.

**Example:** Lab A's PDF and Lab B's PDF both produce the same structured medical report data.

**When analyzing:** Ensure extraction logic does not hardcode assumptions about a specific layout.

## 5. Independent Library

GenIE is a standalone framework. TabEx is the first consumer, not the owner.

**What it means:**
- GenIE has no dependency on TabEx or any specific client.
- Communication happens via REST API and/or SDKs.
- GenIE's roadmap is independent of any single consumer.

**When analyzing:** Reject any requirement that couples GenIE to a specific client application. All client-specific logic belongs in the client SDK or the consuming application.
