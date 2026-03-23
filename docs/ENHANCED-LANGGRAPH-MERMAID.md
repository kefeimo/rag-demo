# ENHANCED LangGraph Mermaid

## Purpose

This document explains the design and implementation of the **enhanced Mermaid graph** for the LangGraph RAG workflow.

Goal: keep runtime orchestration unchanged while making graph visualization clearer and more stable for demos, docs, and debugging.

---

## Problem We Solved

Default `draw_mermaid()` output is structurally correct, but conditional branch intent can be hard to read.

Typical brittle workaround is post-processing Mermaid text with string replacement. We avoided that.

---

## Design Strategy

### 1) Keep execution semantics in LangGraph

- Orchestration remains implemented with nodes + conditional edges.
- No change to routing behavior.

### 2) Keep labels synchronized with routing logic

In [backend/app/rag/agent_graph.py](backend/app/rag/agent_graph.py), we added:

- helper methods used by actual routers (for example planner/semantic/evaluate route checks)
- `_get_branch_labels()` to generate Mermaid labels from those same rules/constants
- `get_mermaid_enhanced()` to render the custom Mermaid graph

This means the enhanced graph is not a disconnected static label table. It is generated from the same decision criteria used during execution.

This provides explicit labels like:

- `strategy == hybrid_first AND has_hybrid`
- `relevance < 0.65 AND has_hybrid`
- `is_relevant == true/false`

### 3) Support both enhanced and raw views

In [backend/app/main.py](backend/app/main.py), endpoint behavior:

- `GET /api/v1/rag/graph/mermaid?view=enhanced` (default)
- `GET /api/v1/rag/graph/mermaid?view=raw`

So we preserve raw LangGraph output for inspection while using enhanced for readability.

### 4) Add frontend view toggle

In [frontend/src/components/GraphViewer.jsx](frontend/src/components/GraphViewer.jsx):

- Added **Enhanced / Raw** toggle buttons.
- Fetches selected view via API.
- Caches rendered SVG per view for fast switching.

In [frontend/src/utils/api.js](frontend/src/utils/api.js):

- `getRagGraphMermaid(view = "enhanced")` now passes query params.

---

## Why This Approach

- **Reliable**: no fragile text patching of generated Mermaid.
- **Readable**: explicit branch conditions shown directly in diagram.
- **Compatible**: raw graph still available.
- **Sync-safe**: branch labels are generated from routing helpers/constants to reduce drift risk.

---

## Sync Concern: Is this true source-of-truth?

Execution source-of-truth remains router behavior in [backend/app/rag/agent_graph.py](backend/app/rag/agent_graph.py).

The enhanced Mermaid labels are now derived from helper methods/constants used by those routers, so label updates happen alongside logic updates.

What we implemented to reduce drift:

- shared helper logic for routing decisions
- `_get_branch_labels()` generated from those same criteria/constants
- unit tests that assert route behavior and Mermaid labels remain aligned

Added tests:

- [backend/tests/test_agent_graph_mermaid_sync.py](backend/tests/test_agent_graph_mermaid_sync.py)

---

## Current Enhanced Graph Semantics

- `planner` branches to `hybrid_retrieve` or `semantic_retrieve`
- `semantic_retrieve` branches to `finish`, `hybrid_retrieve`, or `evaluate`
- `hybrid_retrieve` flows to `evaluate`
- `evaluate` branches to `generate` or `finish`
- `generate` flows to `finish`

Important distinction in labels:

1. **Hybrid fallback gate** (`HYBRID_GATE_THRESHOLD`, default 0.65)
   - Used in semantic→hybrid fallback decision.
2. **Final relevance gate** (`settings.relevance_threshold`)
   - Used in evaluate→generate/finish decision.

---

## API Examples

Enhanced (default):

- `GET /api/v1/rag/graph/mermaid`
- `GET /api/v1/rag/graph/mermaid?view=enhanced`

Raw:

- `GET /api/v1/rag/graph/mermaid?view=raw`

Response shape:

```json
{
  "graph": "langgraph",
  "view": "enhanced",
  "mermaid": "..."
}
```

---

## Future Improvements

- Add optional `theme`/`direction` query params for diagram styling.
- Version graph schema in response (e.g., `graph_version`).
- Build the full Mermaid topology from a declarative edge spec (single-rule DSL).
- Add endpoint-level tests for `view=enhanced|raw` responses.

---

## Files Changed (Implementation)

- [backend/app/rag/agent_graph.py](backend/app/rag/agent_graph.py)
  - Added route helper methods used by both routing and label generation
  - Added `_get_branch_labels()`
  - Added `get_mermaid_enhanced()`
- [backend/app/main.py](backend/app/main.py)
  - Added `view` query param support on Mermaid endpoint
- [frontend/src/utils/api.js](frontend/src/utils/api.js)
  - Added `view` argument to graph API helper
- [frontend/src/components/GraphViewer.jsx](frontend/src/components/GraphViewer.jsx)
  - Added Raw/Enhanced toggle + per-view SVG cache
- [backend/tests/test_agent_graph_mermaid_sync.py](backend/tests/test_agent_graph_mermaid_sync.py)
  - Added sync tests between routing criteria and enhanced Mermaid labels

---

**Last Updated:** March 13, 2026
