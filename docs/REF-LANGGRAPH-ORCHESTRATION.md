# REF: LangGraph Orchestration Essentials

> Practical reference for designing, implementing, and operating LangGraph workflows in production-style RAG systems.

---

## 1) Core Principle

Model orchestration as a **state machine**:

- **State** is the single source of truth for request lifecycle data.
- **Nodes** perform one focused unit of work and return partial state updates.
- **Edges** define flow; **conditional edges** branch by state.
- Keep orchestration separate from domain logic.

**Terminology note:**
- An **edge** is a connection from one node to another.
- A **branch** is the decision point where one of several **conditional edges** is chosen.

So in practice, a branch is implemented using `add_conditional_edges(...)`.

In practice:
- Use LangChain for LLM/retrieval primitives.
- Use LangGraph for control flow, routing, retries, and traceability.

---

## 2) Mental Model

```
START
  ↓
planner
  ├─ semantic path
  └─ hybrid path
  ↓
evaluate
  ├─ generate
  └─ finish (graceful reject)
  ↓
END
```

This pattern scales naturally to retry loops, tool-use branches, and human-in-the-loop checkpoints.

---

## 3) Minimum Building Blocks

### A. Typed State

Define state with only fields needed for flow decisions + outputs.

```python
from typing import TypedDict, List, Dict, Any

class RAGState(TypedDict, total=False):
    query: str
    collection: str
    top_k: int

    planned_strategy: str
    query_type: str
    decision_path: List[str]

    retrieval_result: Dict[str, Any]
    documents: List[Dict[str, Any]]
    relevance_score: float
    is_relevant: bool

    answer: str
    sources: List[Dict[str, Any]]
    error: str
```

### B. Node Contract

Each node:
- reads state
- performs one task
- returns partial updates (do not mutate global state)

### C. Routing Functions

Routing functions read state and return branch labels. Keep deterministic where possible.

Example:

```python
graph.add_conditional_edges(
  "evaluate",
  route_after_evaluate,
  {
    "generate": "generate",
    "finish": END,
  },
)
```

Here:
- the **branch** happens at `evaluate`
- the outgoing **conditional edges** are `generate` and `finish`
- the router decides which edge to follow

---

## 4) Canonical Workflow to Implement

1. Define state schema (`TypedDict`).
2. Implement nodes (`planner`, `retrieve`, `evaluate`, `generate`).
3. Add `START -> first_node` edge.
4. Add conditional edges for branch decisions.
5. Compile graph.
6. Invoke with initial state per request.
7. Log decision path and key metrics.
8. Add retries/fallbacks only where needed.

---

## 5) Minimal Skeleton

```python
from langgraph.graph import StateGraph, START, END


graph = StateGraph(RAGState)
graph.add_node("planner", planner_node)
graph.add_node("retrieve", retrieve_node)
graph.add_node("evaluate", evaluate_node)
graph.add_node("generate", generate_node)

graph.add_edge(START, "planner")
graph.add_edge("planner", "retrieve")
graph.add_edge("retrieve", "evaluate")

graph.add_conditional_edges(
    "evaluate",
    route_after_evaluate,   # returns "generate" or "finish"
    {
        "generate": "generate",
        "finish": END,
    },
)

graph.add_edge("generate", END)
app = graph.compile()

result = app.invoke({
    "query": "What is IDataTableProps?",
    "collection": "vcc_docs",
    "top_k": 5,
    "decision_path": [],
})
```

---

## 6) Planner Design Options

### Rule-based planner (recommended first)

Pros:
- deterministic
- low latency/cost
- easy to test

Use for:
- query-shape routing (`api_like` vs `general`)
- first-pass strategy selection (`semantic_first` vs `hybrid_first`)

### LLM-based planner (next step)

Pros:
- handles fuzzy intent and ambiguous queries better

Trade-offs:
- non-determinism
- extra latency/cost
- requires stricter output schema and guardrails

Migration pattern:
- keep node interface stable (`planner_node(state) -> partial_state`)
- swap internals from rules to structured LLM output

---

## 7) Reliability Patterns

- Add explicit `error` in state and route to `finish` safely.
- Add capped retry counter (`attempts < N`) for loops.
- Prefer graceful rejection over low-confidence hallucination.
- Keep fallback logic as graph edges, not scattered `try/except` branches.

---

## 8) Observability Checklist

Track and log at minimum:

- `planned_strategy`
- `query_type`
- `relevance_score`
- `decision_path`
- response time per request

Optional:
- per-node duration
- token/cost metrics
- branch distribution over time

---

## 9) Testing Strategy

- Unit-test each node with mocked dependencies.
- Unit-test each routing function with branch cases.
- Integration-test full graph for representative query classes.
- Add regression tests for edge cases (exact API tokens, low-confidence rejects).

---

## 10) Common Anti-Patterns

- Overloading one node with multiple concerns.
- Storing non-essential data in state (state bloat).
- Hidden side effects inside routing functions.
- LLM planner without structured output constraints.
- No explicit low-confidence path.

---

## 11) Mapping to Current Repository

Implemented pattern in this repository:

- Graph pipeline class: `backend/app/rag/agent_graph.py`
- Query entrypoint invoking graph: `backend/app/main.py`
- Mermaid graph endpoint: `/api/v1/rag/graph/mermaid`
- Frontend graph viewer: `frontend/src/components/GraphViewer.jsx`

Current graph shape:
- `planner` → `semantic_retrieve` / `hybrid_retrieve` → `evaluate` → `generate` or finish.

---

## 12) Practical Interview Summary

“LangGraph is the orchestration control plane: typed state + nodes + conditional routing. LangChain provides model/retrieval primitives. I start with a deterministic planner, add traceability (`decision_path`), and evolve toward retries/memory only when metrics justify added complexity.”

---

**Last Updated:** March 12, 2026
