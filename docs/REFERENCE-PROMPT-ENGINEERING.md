# REFERENCE: Prompt Engineering (Project-Oriented)

> Practical reference for implementation, based on this project's RAG prompt design.

---

## 1) Core Prompt Techniques

### Role-based prompting
Define:

- **Persona**: who the model is
- **Scope**: what domain/tasks it should handle
- **Behavior constraints**: how it must respond

In this project, role-based prompting is implemented in [backend/app/rag/generation.py](backend/app/rag/generation.py) via `PromptBuilder`.

### Few-shot prompting
Provide 1-3 examples of desired behavior/output format before the actual query.

Use when:
- output style is inconsistent
- model needs examples for edge behaviors (e.g., unknown handling)

### Chain-of-thought-style guidance (production-safe)
Use structured reasoning instructions, but keep final output concise.

Note: `CoT` means *Chain of Thought*.

Use when:
- answers need better reasoning discipline
- you want reliable grounded answers without verbose reasoning dumps

---

## 2) Mapping to Current Project Prompt

Current anchor line:

"You are a helpful AI assistant specialized in {domain}."

### What is what?

- **Persona**: "helpful AI assistant"
- **Scope**: "specialized in {domain}" + domain-specific guidance blocks (FastAPI/FastAPI/general)
- **Behavior constraints**: rules such as
  - answer from provided context
  - cite sources when possible
  - only use insufficient-info response when context is truly unrelated
  - handle minor typos/variations
  - interpret placeholders like `{{...}}` as intentional

---

## 3) Clarification: Is "helpful AI assistant" too general?

Yes, by itself it is generic.

But it is still a valid **base role**. In practice, role is layered:

1. base role: helpful assistant
2. domain role: FastAPI/FastAPI specialist
3. optional task role: API doc explainer, troubleshooting assistant, etc.

This project already strengthens the generic role with domain scope and explicit behavior constraints.

---

## 4) Prompt Techniques: When to Use Which

| Technique | Best for | Risk | Mitigation |
|---|---|---|---|
| Role-based | Consistent tone + domain alignment | Too generic role | Add precise scope + constraints |
| Few-shot | Enforcing answer format and edge-case behavior | Longer prompt/cost | Keep examples short and high-value |
| Chain-of-thought-style guidance | Better reasoning discipline | Verbose or off-format output | Ask for concise final answer only |

---

## 5) Project-Ready Examples

### A) Role-based (current style)

Use domain-specialist role + context-grounding rules.

Example wording:

- Persona: "You are a helpful AI assistant"
- Scope: "specialized in FastAPI documentation"
- Constraints: "Answer from provided context; cite sources; if context is insufficient, say so clearly."

### B) Few-shot (recommended extension)

Add short examples inside prompt template:

- Example 1: API term question -> concise grounded answer + source mention
- Example 2: unrelated query -> explicit insufficient-context response

### C) Chain-of-thought-style (implemented)

Instruct the model to reason step-by-step inside `<thinking>...</thinking>` tags before the final answer:

```
<thinking>
1. The context mentions X...
2. The relevant facts are...
3. Therefore the answer is...
</thinking>
Final answer here.
```

The backend parses the tags — reasoning goes to `cot_reasoning` in state, clean answer goes to `answer`. Reasoning is streamed to the frontend as a separate `{"type": "cot"}` SSE event and displayed in the ThinkingPanel as a **Model Reasoning** block.

**Important:** Do not add hard output-length constraints (`concise answer only`) — this caused quality regression on `gpt-3.5-turbo` by truncating complete prop listings. Let the model decide response depth based on context richness.

---

## 6) Implementation Summary

This project uses role-based prompting with domain-specific scope and explicit behavior constraints, plus chain-of-thought-style reasoning via visible `<thinking>` tags. CoT is controlled by the `prompt_cot_enabled` feature flag (default: `True`). The model's reasoning is surfaced in the ThinkingPanel as a **Model Reasoning · CoT · demo** block. It can be further extended with few-shot examples for output consistency.

---

## 7) CoT vs HyDE (Important Distinction)

These techniques operate at different layers:

- **CoT (Chain of Thought)**: generation-time reasoning style
  - Applied after retrieval, during answer generation
  - Goal: improve reasoning quality over retrieved context

- **HyDE (Hypothetical Document Embeddings)**: retrieval-time query expansion
  - Applied before retrieval
  - Goal: improve recall by embedding a synthetic hypothetical answer/document

They can both appear in multi-step workflows, but they solve different problems:

- HyDE improves **what context you retrieve**
- CoT improves **how you reason over retrieved context**

---

## 8) Live Thinking UI vs Prompt Improvement

The frontend `ThinkingPanel` shows **live pipeline observability** -- not prompt engineering.

### How it works

- The backend exposes `POST /api/v1/query/stream` -- a Server-Sent Events (SSE) endpoint.
- As LangGraph executes each node (`planner` -> `semantic_retrieve` / `hybrid_retrieve` -> `evaluate` -> `generate`), the server emits a `{"type":"thinking","step":"..."}` event.
- The frontend reads these via `fetch` + `ReadableStream` (`queryRAGStream` in [frontend/src/utils/api.js](frontend/src/utils/api.js)).
- `ThinkingPanel` ([frontend/src/components/ThinkingPanel.jsx](frontend/src/components/ThinkingPanel.jsx)) renders steps as they arrive, auto-collapses after the final answer lands, and exposes expand/dismiss controls -- the same UX pattern as Copilot agent's "Thinking..." display.

### CoT blueprint vs orchestration steps

A key architectural reflection: **CoT and orchestration steps are independent layers**, but they are conceptually aligned:

- **CoT** is the reasoning blueprint inside the prompt — it shapes how the `generate` node reasons over retrieved context within a single LLM call.
- **Orchestration steps** (planner → retrieve → evaluate → generate) are the pipeline execution path — they are emitted as SSE events and shown as pipeline observability in the ThinkingPanel.

CoT does not drive orchestration, and orchestration does not expose CoT. But they mirror the same underlying intent: structured, disciplined reasoning from evidence.

| | Live Thinking UI | Chain-of-Thought |
|---|---|---|
| Layer | UX / observability | Prompt / generation |
| Happens | While graph nodes execute | Inside single LLM call (`generate`) |
| Purpose | Show pipeline progress + state summaries | Improve reasoning quality over context |
| User-visible? | ✅ Yes — orchestration steps + state summaries | ✅ Yes (demo) — `<thinking>` block in Model Reasoning panel |
| Affects answer quality? | No | Yes (when effective) |

The panel shows two distinct things:
1. **Orchestration thoughts** — state-derived summaries per node (e.g. relevance score, retrieval strategy chosen)
2. **Model Reasoning** — the model's own `<thinking>` output from the CoT-prompted `generate` call

### What does affect quality

- Prompt changes: role, few-shot examples, CoT-style structure
- Retrieval changes: hybrid strategy, HyDE, re-ranking
- Model changes

### Lesson learned: avoid hard output constraints with CoT

Adding `Return concise final answer only` alongside CoT instructions caused `gpt-3.5-turbo` to truncate complete prop listings to 4 lines (125 chars). The model obeyed the constraint literally, ignoring evidence richness. Removing the constraint restored full answers. **Let the model decide response depth based on context.**

---

## 9) File Reference

- Prompt implementation: [backend/app/rag/generation.py](backend/app/rag/generation.py)
- SSE streaming endpoint: [backend/app/main.py](backend/app/main.py) (`POST /api/v1/query/stream`)
- Streaming client helper: [frontend/src/utils/api.js](frontend/src/utils/api.js) (`queryRAGStream`)
- Live thinking component: [frontend/src/components/ThinkingPanel.jsx](frontend/src/components/ThinkingPanel.jsx)
- Response schema: [backend/app/models.py](backend/app/models.py)

---

**Last Updated:** March 13, 2026
