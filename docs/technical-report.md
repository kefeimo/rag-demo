# Technical Report: RAG System for Visa Chart Components Documentation

**Author:** Kefei Mo  
**Date:** March 2026  

---

## 1. Approach

### Dataset & Problem Framing

The system was built to answer developer questions against two corpora:

- **FastAPI docs** (12 markdown files, ~500KB) — used for initial pipeline validation
- **Visa Chart Components (VCC) docs** (161 markdown files, 2,696 chunks) — the primary production dataset, sourced from the [visa/visa-chart-components](https://github.com/visa/visa-chart-components) GitHub repo

VCC was chosen because it represents a real Visa production codebase with diverse content types: README prose, API interface definitions, accessibility guides, and closed GitHub issue Q&A. This variety exercises the RAG system more rigorously than generic documentation would.

### Architecture

The system is a standard RAG pipeline with two noteworthy design choices:

```
Query → Planner Node (LangGraph, rule-based query-shape routing)
        → Retrieval Node(s) (`Retriever` / `HybridRetriever` via `ChromaDBStore`)
            → Confidence Evaluation (threshold: 0.65 — reject or proceed)
            → Domain-Aware Prompt (LangChain template with VCC acronym mappings)
            → LLM Generation (OpenAI GPT-3.5-turbo)
            → Response with sources + confidence score
```

**Key design decisions:**

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Embedding model | `all-MiniLM-L6-v2` | Fast (1500 docs/sec), compact (384-dim), good semantic quality |
| Vector DB | ChromaDB | Simple, file-based, no extra infra |
| LLM | OpenAI GPT-3.5-turbo | 37× faster than local GPT4All, 36% higher quality |
| Confidence threshold | 0.65 (empirically tuned) | Rejects unanswerable queries rather than hallucinating |
| Hybrid search | BM25 + semantic | Catches exact-name lookups (API method names, props) that pure embedding misses |

*For the full architecture diagram and module breakdown, see [ARCHITECTURE.md](ARCHITECTURE.md).*

---

## 2. Implementation

### Notable: Domain-Aware Prompt Engineering

Early testing revealed that acronym-heavy queries degraded retrieval quality:

- `"What is VCC?"` → 52.7% confidence  
- `"What is Visa Chart Components?"` → 74.4% confidence

The fix was a `PromptBuilder` backed by LangChain `PromptTemplate`, injecting domain context (acronym mappings, key concepts) before the retrieved context block. This yielded **+15% answer relevancy** on VCC-specific queries.

```python
DOMAIN_CONFIGS = {
    "vcc": {
        "domain_name": "Visa Chart Components (VCC)",
        "acronyms": "VCC = Visa Chart Components, WCAG = Web Content Accessibility Guidelines, a11y = accessibility",
        "prompt_template": """You are an expert on {domain_name}.
Common acronyms: {acronyms}
Context: {context}
Question: {question}
Answer ONLY from the context above."""
    }
}
```

*For full details and iteration history, see [REFACOTRING-PROMPT-IMPROVEMENT.md](REFACOTRING-PROMPT-IMPROVEMENT.md).*

### Notable: Hybrid Search for API Queries

Semantic search alone struggled with exact API names (e.g. `IDataTableProps`, `barChart.getAccessibilityDesc`). A BM25 lexical index was added as a fallback, fused with semantic scores (0.5 weight each) when the initial confidence was below threshold.

```
Query: "What is IDataTableProps?"
Semantic-only confidence: 0.61 (below threshold → would reject)
Hybrid confidence:         0.78 (above threshold → answered correctly)
```

*For the full case study and benchmarks, see [HYBRID-SEARCH-CASE-STUDY.md](HYBRID-SEARCH-CASE-STUDY.md).*

### Production-Readiness Features

- **Stateful orchestration graph** — query flow runs through `LangGraphRAGPipeline` (`planner` → retrieval → evaluate → generate/reject), with node-path traceability in logs
- **Graph visualization endpoint + UI** — backend exposes `/api/v1/rag/graph/mermaid`; frontend renders graph for demo/debug
- **Confidence-gated rejection** — queries below 0.65 receive an explicit "unable to answer" rather than a hallucinated response
- **UI transparency** — confidence score displayed per response with colour-coded warnings; collapsible source attribution
- **Query-result caching** — in-memory cache in the React frontend keyed by `collection:query`, eliminating repeat API calls
- **Docker Compose stack** — single `docker compose up` brings up backend + frontend; GPU passthrough configured for NVIDIA runtime
- **RAGAS evaluation pipeline** — three-stage automated evaluation (query → generate ground truth → score) reproducible via CLI scripts

*For UI cache design details, see [UI-QUERY-CACHE.md](UI-QUERY-CACHE.md). For Docker setup, see [DOCKER.md](DOCKER.md).*

### Code Quality & Organization

The backend follows a clean modular structure under `backend/app/rag/` — each concern (ingestion, retrieval, hybrid retrieval, generation, prompt building) is a separate module with no cross-cutting dependencies. ChromaDB access is centralized in `backend/app/rag/chromadb_store.py` (`ChromaDBStore`), which encapsulates client/collection operations for both ingestion and retrieval paths. Configuration is fully environment-driven via `backend/app/config.py` (Pydantic `BaseSettings`), making the same codebase work locally, in Docker, and with either LLM provider without code changes.

Test coverage: **38 pytest tests** covering the core pipeline, with a dedicated `tests/` directory and `conftest.py` fixtures. Key coverage numbers: `config.py` 93%, `retrieval.py` 58%, `ingestion.py` 51%.

**Creativity highlights worth noting:**

- **VCC dataset choice** — Rather than a generic public corpus, the system was built against a real Visa production repository (`visa/visa-chart-components`), making the demo directly relevant to Visa's own tooling.
- **Custom data pipeline** — A `data-pipeline/` module extracts documentation from GitHub Issues (closed Q&A pairs) in addition to markdown files, enriching the corpus with real developer questions and resolutions. See [data-pipeline/README.md](../data-pipeline/README.md).
- **2-collection routing** — The UI exposes a toggle between `fastapi_docs` and `vcc_docs` collections, and the `collection` field in the API allows per-request targeting. This patterns toward a multi-tenant knowledge base rather than a single-purpose chatbot.
- **Graceful degradation** — If retrieval confidence is below threshold, the system returns a structured "unable to answer" with a hint to rephrase, rather than silently hallucinating. This is a deliberate product decision, not just a technical guard.

*For module layout, see [ARCHITECTURE.md](ARCHITECTURE.md). For the data pipeline, see [data-pipeline/README.md](../data-pipeline/README.md). For tech stack rationale, see [TECH-STACK-RATIONALE.md](TECH-STACK-RATIONALE.md).*

---

## 3. Evaluation Results

### Baseline vs. Optimized

| Metric | Baseline (GPT4All, local) | Optimized (GPT-3.5-turbo) | Change |
|--------|--------------------------|---------------------------|--------|
| **Faithfulness** | 0.52 | **0.87** | +67% ✅ |
| **Answer Relevancy** | 0.68 | **0.89** | +31% ✅ |
| **Context Precision** | 0.71 | **0.84** | +18% ✅ |
| **Overall** | 0.64 | **0.87** | +36% ✅ |
| **Avg Response Time** | ~85s (CPU) | **2.3s** | -97% ✅ |
| **Queries above confidence threshold** | 58% | **82%** | +40% ✅ |

The biggest single lever was **LLM quality**: GPT4All Mistral 7B hallucinated specific prop names and API details not present in the retrieved context (faithfulness 0.52). GPT-3.5-turbo's stronger instruction-following brought this to 0.87.

**Concrete hallucination example (baseline):**

```
Query: "How do I improve the group focus indicator in VCC?"
GPT4All answer: "Use the `focusIndicatorStyle` prop with borderWidth: 3px..."
Issue: `focusIndicatorStyle` does not exist in the documentation — hallucinated.
GPT-3.5 answer: Correctly cited the actual WCAG CSS approach from context.
```

### Cost-Performance

```
GPT4All (local):   $0/query,    85s,  quality 0.64
GPT-3.5-turbo:     $0.002/query, 2.3s, quality 0.87

At 1000 queries/day → ~$60/month for production-grade answers
```

*For full metric tables, per-query breakdown, and iteration log, see [EVALUATION-REPORT.md](EVALUATION-REPORT.md).*

---

## 4. Key Takeaways

1. **Cloud LLM over local for production** — The 37× speed and 36% quality improvement far outweighs the ~$60/month cost at moderate load.

2. **Prompt engineering matters at the domain level** — Generic prompts lose VCC acronyms; a domain config object injected into LangChain templates recovered 15% relevancy.

3. **Confidence thresholding builds trust** — Rejecting low-confidence queries explicitly is better UX than a confident wrong answer. Users rephrase and succeed on retry.

4. **Hybrid search is necessary for API doc corpora** — Exact token matches (method names, interface names) are poorly handled by embeddings alone; BM25 fills the gap.

5. **Evaluation pipeline is a force multiplier** — The 3-stage RAGAS CLI made it fast to quantify each change rather than relying on manual spot-checks.

*For broader reflections on the development process, see [lesson-learned.md](lesson-learned.md).*
