# Case Study: Chain-of-Thought Evolution

> How CoT prompt engineering was introduced, regressed, recovered, and made user-visible in this RAG system.

---

## 1) Background

This project uses a LangGraph-based RAG pipeline. The generation layer uses `PromptBuilder` in [backend/app/rag/generation.py](backend/app/rag/generation.py), which constructs prompts with role, domain-specific guidance, and retrieved context chunks. Before this evolution, only role-based prompting was active.

---

## 2) Initial Design Decision: Keep CoT Internal

### Rationale
Chain-of-thought prompting was identified as a recommended extension in [REFERENCE-PROMPT-ENGINEERING.md](REFERENCE-PROMPT-ENGINEERING.md). The initial specification called for:

1. Identify relevant context chunks
2. Extract answer-supporting facts
3. Draft answer from evidence only
4. If support is weak, state insufficient context

Accompanied by hard output constraints:
- `Return concise final answer only`
- `Do not reveal internal reasoning steps`

### Intent
The model reasons internally; only the final clean answer is shown. This mirrors "hidden scratchpad" patterns used in production RAG systems.

---

## 3) Quality Regression: The Lesson Learned

### Symptom
After activating CoT with output constraints, the answer to _"What are the props for IDataTableProps?"_ degraded from a full prop listing to 4 bullets (125 chars):

```
The props for IDataTableProps are:
- uniqueID: string
- data: object[]
- secondaryData: object[]
- tableColumns: object[]
```

The context had full documentation at relevance `0.90`. The answer was correct but severely truncated.

### Root Cause (from logs)
`gpt-3.5-turbo` obeyed `Return concise final answer only` literally. It treated the constraint as a token budget instruction and cut the response early, regardless of context richness.

```
2026-03-13 18:09:28 — Prompt preview shows full IDataTableProps doc in Source 1 (relevance: 0.90)
2026-03-13 18:09:29 — Received response (125 chars)
```

### Fix
Removed both hard constraints. The model decides response depth based on context. The CoT guidance was made feature-flagged (`prompt_cot_enabled`) and disabled by default until further refinement.

### Lesson
> Hard output-length constraints (`concise answer only`) conflict with evidence-rich context. The model prioritises the constraint over completeness. Do not over-constrain output format alongside reasoning structure instructions.

---

## 4) Rethink: Visible CoT for Demo

### Reflection
A key architectural question arose:

> *"CoT is the blueprint in prompt engineering to indicate RAG workflow principle. It is not coupled with orchestration steps, but is reflected by the orchestration steps."*

This led to a clearer separation:

| Concept | What it is | Layer |
|---|---|---|
| **CoT** | Reasoning discipline blueprint | Prompt / `generate` node |
| **Orchestration steps** | Pipeline execution path | LangGraph nodes → SSE |
| **ThinkingPanel** | User-visible observability | Frontend UI |

CoT shapes *how the model reasons*. Orchestration steps reflect *what the pipeline decided* (strategy, retrieval scores, evidence quality). They are independent but complementary.

### Decision
For demo purposes, make CoT reasoning user-visible. Instruct the model to output reasoning inside `<thinking>` tags:

```
REASONING FORMAT:
Think through the question step by step before answering.
Output your reasoning inside <thinking>...</thinking> tags, then provide your final answer after the closing tag.
```

---

## 5) Implementation

### 5.1 Prompt Change (`generation.py`)

The `_get_cot_guidance()` method (active when `prompt_cot_enabled=True`) now outputs:

```
REASONING FORMAT:
Think through the question step by step before answering.
Output your reasoning inside <thinking>...</thinking> tags, then provide your final answer after the closing tag.
Example:
<thinking>
1. The context mentions X...
2. The relevant facts are...
3. Therefore the answer is...
</thinking>
Final answer here.
```

No hard output-length constraints. The model decides depth.

### 5.2 Response Parsing (`generation.py`)

```python
def parse_cot_response(text: str) -> tuple:
    """
    Parse <thinking>...</thinking> block from model output.
    Returns: (cot_text, answer_text)
    """
    import re
    match = re.search(r'<thinking>(.*?)</thinking>', text, re.DOTALL)
    if match:
        cot = match.group(1).strip()
        answer = text[match.end():].strip()
        return cot, answer
    return "", text
```

### 5.3 Agent State (`agent_graph.py`)

`RAGAgentState` now carries `cot_reasoning` separately from `answer`:

```python
answer: str
cot_reasoning: str   # parsed <thinking> content, empty if CoT disabled
sources: List[Dict[str, Any]]
```

`_generate_node` calls `parse_cot_response()` after LLM generation to split them.

### 5.4 SSE Streaming (`main.py`)

After the `generate` node ends, a separate `cot` event is emitted:

```json
{"type": "cot", "content": "1. The context mentions...\n2. The relevant fact..."}
```

This is distinct from `thinking` events (orchestration step summaries).

### 5.5 Frontend (`ThinkingPanel.jsx`)

The panel now renders two distinct sections:

1. **Orchestration thoughts** — per-node state summaries (strategy, retrieval score, generate completion)
2. **Model Reasoning · CoT · demo** — the raw `<thinking>` text in an indigo-accented monospace block, clearly labelled as a demo feature

---

## 6) Architecture Summary

```
User query
    │
    ▼
LangGraph pipeline
    ├── planner         ──► SSE: {"type":"thinking", "step":"Planning...", "thought":"Classified as api_like; hybrid-first path."}
    ├── hybrid_retrieve ──► SSE: {"type":"thinking", "step":"Running hybrid search", "thought":"Found 5 chunks, relevance 0.88."}
    ├── evaluate        ──► SSE: {"type":"thinking", "step":"Evaluating...", "thought":"Score 0.88 > 0.65; proceed to generate."}
    └── generate
            │
            ├── PromptBuilder builds prompt with CoT guidance
            ├── LLM outputs: <thinking>...</thinking> + final answer
            ├── parse_cot_response() splits them
            ├── SSE: {"type":"thinking", "step":"Generating answer", "thought":"Generated 512 chars, 3 sources."}
            └── SSE: {"type":"cot", "content":"1. Context mentions...\n2. Relevant facts..."}
    │
    ▼
SSE: {"type":"result", "data": {...answer, sources, relevance_score...}}
    │
    ▼
ThinkingPanel
    ├── Orchestration thoughts (gray cards, per-node)
    └── Model Reasoning block (indigo, monospace, CoT · demo label)
```

---

## 7) Feature Flag

Controlled by `prompt_cot_enabled` in [backend/app/config.py](backend/app/config.py):

```python
prompt_cot_enabled: bool = Field(
    default=True,
    description="Enable internal CoT-style reasoning guidance in prompt template"
)
```

Set `PROMPT_COT_ENABLED=false` in `.env` to disable CoT and revert to baseline role-based prompting.

---

## 8) Key Takeaways

| # | Takeaway |
|---|---|
| 1 | CoT is a **prompt-layer blueprint** — independent from orchestration, but aligned in spirit |
| 2 | Orchestration steps **reflect** the pipeline's structural reasoning (plan → retrieve → evaluate → generate) |
| 3 | Hard output constraints conflict with evidence-rich context — avoid `concise answer only` |
| 4 | `<thinking>` tag format lets the model express structured reasoning **and** produce a full answer |
| 5 | Separating `cot_reasoning` from `answer` in state keeps the response API clean regardless of CoT mode |
| 6 | No session/query history is stored — each query is stateless; CoT operates within a single LLM call |

---

## 9) File Reference

| File | Role |
|---|---|
| [backend/app/rag/generation.py](backend/app/rag/generation.py) | `PromptBuilder._get_cot_guidance()`, `parse_cot_response()` |
| [backend/app/rag/agent_graph.py](backend/app/rag/agent_graph.py) | `RAGAgentState.cot_reasoning`, `_generate_node` parsing |
| [backend/app/main.py](backend/app/main.py) | SSE `cot` event emission |
| [backend/app/config.py](backend/app/config.py) | `prompt_cot_enabled` feature flag |
| [frontend/src/utils/api.js](frontend/src/utils/api.js) | `onCot` callback in `queryRAGStream` |
| [frontend/src/App.jsx](frontend/src/App.jsx) | `cotReasoning` state |
| [frontend/src/components/ThinkingPanel.jsx](frontend/src/components/ThinkingPanel.jsx) | Model Reasoning block rendering |
| [docs/REFERENCE-PROMPT-ENGINEERING.md](docs/REFERENCE-PROMPT-ENGINEERING.md) | Prompt engineering reference |

---

**Last Updated:** March 13, 2026
