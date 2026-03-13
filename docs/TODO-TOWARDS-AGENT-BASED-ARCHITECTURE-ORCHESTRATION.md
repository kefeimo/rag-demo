# TODO: Towards an Agent-Based Architecture & Orchestration

> **Status:** In progress — minimal LangGraph implementation is live.  
> **Related:** [`REFERENCE-RAG.md`](./REFERENCE-RAG.md) · [`ARCHITECTURE.md`](./ARCHITECTURE.md)

---

## Current Architecture — Accurate Characterisation

The current system is a **minimal stateful LangGraph RAG pipeline** with a rule-based planner.

```
User Query
   ↓
Planner node  (query-shape routing: semantic-first vs hybrid-first)
   ↓
Retrieval node(s)  (Retriever / HybridRetriever via ChromaDBStore)
   ↓
Confidence gate  (threshold=0.65)
   ├─ relevant → generate
   └─ not relevant → graceful reject
   ↓
Prompt construction  (LangChain PromptTemplate, domain-aware)
   ↓
LLM generation  (OpenAI GPT-3.5 primary / GPT4All fallback)
   ↓
Guardrails  (confidence banner, source citation, "I don't know" path)
```

**Characteristics of the current design:**

| Property | Current state |
|---|---|
| Workflow | Graph-based, stateful per request |
| Decision rules | Planner + threshold rules (`0.65`) |
| Request lifecycle | Single pass — one retrieval, one generation, one response |
| Orchestration | LangGraph `StateGraph` in `agent_graph.py` |
| LangChain role | Prompt templates + LLM client abstraction |
| State | `RAGAgentState` tracks strategy, path, scores |

This is a pragmatic first step toward agent-based architecture: routing and control flow are now explicit graph nodes and edges.

### Implemented in this iteration

- `backend/app/rag/agent_graph.py` added (`LangGraphRAGPipeline` + `RAGAgentState`)
- `main.py` query handler now invokes graph execution instead of manual orchestration
- `planner` node added (rule-based query-shape strategy selection)
- Decision trace persisted in state (`decision_path`) and logged
- Mermaid graph endpoint added: `/api/v1/rag/graph/mermaid`
- Frontend graph viewer added (`GraphViewer`) to render orchestration diagram in-app

---

## Limitations of the Current Approach

### 1. Static Workflow

The pipeline follows a fixed sequence. It cannot dynamically choose a different retrieval strategy based on query content beyond the binary semantic/hybrid gate.

*Concrete example:* A query about `IDataTableProps` that scores 0.66 (just above threshold) returns semantic-only results even though hybrid would score higher — the gate never runs.

### 2. Single Retrieval Cycle

The system performs **one** retrieval → generation cycle with no ability to:
- detect that retrieved context is insufficient *after* inspecting it
- rephrase the query and retry
- gather additional evidence from a second collection or corpus

### 3. No Iterative Reasoning

If the first retrieval returns context that is technically above threshold but still leads to a weak answer, there is no mechanism to re-evaluate and try again. The gap shows up in RAGAS `faithfulness` scores for edge-case queries.

### 4. Query Classifier is Rule-Based

`classify_query()` uses keyword counting — it has no understanding of query intent beyond surface-level token matching. Misclassification silently sets wrong BM25/semantic weights with no feedback mechanism.

### 5. Stateless — No Conversation Memory

Each request is fully independent. Multi-turn clarification ("follow up on the last answer about accessibility") is not supported.

---

## Proposed Future Architecture: Agent-Based System

### Target Workflow

```
User Query
   ↓
Planner Agent  ← decides strategy: which retriever(s), which collection(s)
   ↓
Retrieval Agent  ← executes ChromaDBStore.query via Retriever
   ↓
Confidence Evaluator  ← inspects results, decides: sufficient / retry / escalate
   ├─ Sufficient → Prompt Construction → LLM Generation → Response
   └─ Insufficient → Query Refinement Agent
                         ↓
                     Rephrase query / widen search
                         ↓
                     Retrieval Agent (second pass)
                         ↓
                     Evidence Aggregator
                         ↓
                     LLM Generation → Response
```

### Key Improvements Over Current System

| Capability | Current | Agent-based |
|---|---|---|
| Retrieval strategy selection | Binary gate (semantic / hybrid) | Planner decides per query |
| Query rephrasing on low confidence | ❌ None | ✅ Query Refinement Agent |
| Multi-pass retrieval | ❌ Single pass | ✅ Iterative until sufficient |
| Collection routing | Manual toggle (frontend) | ✅ Automatic |
| Decision traceability | Limited (logs only) | ✅ Graph state captures each node decision |
| Conversation memory | ❌ Stateless | ✅ State persisted across turns |

---

## Role of LangGraph

[LangGraph](https://langchain-ai.github.io/langgraph/) maps directly onto this design:

- **Nodes** — each agent capability (`retrieve`, `evaluate_confidence`, `refine_query`, `generate`)
- **Edges** — conditional routing (`confidence >= 0.65 → generate`, else `→ refine_query`)
- **State** — typed dict tracking query, retrieved docs, confidence, attempt count, final answer
- **Checkpointing** — durable execution; human-in-the-loop approval on low-confidence paths

The existing `Retriever`, `HybridRetriever`, `PromptBuilder`, and `ChromaDBStore` become **node implementations** — the LangGraph graph replaces the `main.py` control flow, not the domain logic itself.

**Sketch of the LangGraph state type:**

```python
class RAGAgentState(TypedDict):
    query: str
    collection: str
    retrieval_attempts: int
    retrieved_docs: List[Dict]
    confidence: float
    refined_query: Optional[str]
    answer: Optional[str]
    sources: List[Dict]
```

**Sketch of graph construction:**

```python
graph = StateGraph(RAGAgentState)

graph.add_node("retrieve",         retrieval_node)       # wraps Retriever
graph.add_node("evaluate",         confidence_node)      # checks threshold
graph.add_node("refine_query",     refinement_node)      # LLM rephrases query
graph.add_node("hybrid_retrieve",  hybrid_node)          # wraps HybridRetriever
graph.add_node("generate",         generation_node)      # wraps PromptBuilder + LLM

graph.add_conditional_edges(
    "evaluate",
    route_on_confidence,     # returns "generate" | "refine_query" | "hybrid_retrieve"
)
```

---

## Transition Roadmap

### Phase 1 — Introduce State Management

- [x] Add `LangGraph` dependency (`langgraph`)
- [x] Define `RAGAgentState` typed dict
- [x] Wrap existing `Retriever` / `HybridRetriever` / generation steps as graph nodes
- [x] Replace `main.py` query handler with graph invocation
- [x] Verify parity with focused backend test suite

### Phase 2 — Add Planning / Routing Agent

- [x] Implement `planner_node` that selects retrieval strategy from query characteristics
- [ ] Replace hard-coded `classify_query()` with LLM-based intent classification (or a richer rule engine)
- [ ] Implement automatic collection routing (removes frontend toggle requirement)

### Phase 3 — Enable Iterative Retrieval

- [ ] Implement `query_refinement_node` — uses LLM to rephrase low-confidence queries
- [ ] Add loop back from `evaluate` → `refine_query` → `retrieve` (capped at N attempts)
- [ ] Track attempt count in state to prevent infinite loops

### Phase 4 — Conversation Memory

- [ ] Add LangGraph `MemorySaver` checkpoint to persist state across turns
- [ ] Surface conversation history in the frontend (`App.jsx`)
- [ ] Implement multi-turn context window management (trim old turns)

---

## What to Keep

These parts of the current system remain valid in an agent architecture and map directly to graph nodes with minimal change:

- `ChromaDBStore` — retrieval node implementation
- `EmbeddingProvider` — used inside retrieval node
- `PromptBuilder` — used inside generation node
- `HybridRetriever` — becomes the hybrid retrieval node
- RAGAS evaluation pipeline — unchanged; evaluates graph output the same way

---

## What Is Out of Scope

The following are **not** warranted for the VCC/FastAPI documentation use case and were excluded from this roadmap:

- Code execution agents — no code execution required for documentation Q&A
- Knowledge graph agents — no structured KG in the corpus
- External API agents — the corpus is self-contained; web search adds noise for a private docs system

These could be relevant if the system is extended to a more general-purpose assistant, but should not be added speculatively.

---

**Last Updated:** March 12, 2026
