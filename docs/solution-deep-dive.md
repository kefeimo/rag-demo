# RAG System: Solution Deep-Dive

**A technical companion to [`docs/technical-report.md`](./technical-report.md)**  
**Author:** Kefei Mo · **Date:** March 5–6, 2026

This document consolidates the four supporting references into one readable deep-dive:  
[ARCHITECTURE.md](./ARCHITECTURE.md) · [HYBRID-SEARCH-CASE-STUDY.md](./HYBRID-SEARCH-CASE-STUDY.md) · [EVALUATION-REPORT.md](./EVALUATION-REPORT.md) · [lesson-learned.md](./lesson-learned.md)

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Hybrid Search: Case Study](#2-hybrid-search-case-study)
3. [Full RAGAS Evaluation](#3-full-ragas-evaluation)
4. [Engineering Process & Lessons Learned](#4-engineering-process--lessons-learned)

---

## 1. System Architecture

### 1.1 High-Level Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RAG System Architecture                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐       ┌──────────────┐       ┌──────────────┐     │
│  │   Frontend   │ ----> │   Backend    │ ----> │   ChromaDB   │     │
│  │    (React)   │ <---- │   (FastAPI)  │ <---- │  (Vectors)   │     │
│  └──────────────┘       └──────────────┘       └──────────────┘     │
│                                                                     │
│   User Query input       RAG Pipeline           2,696 doc chunks    │
│   Confidence UI          Embedding + Retrieval  384-dim cosine      │
│   Source display         LLM generation         2 collections       │
│   Query history          Confidence calc        (vcc_docs,          │
│                          Hybrid fallback         fastapi_docs)      │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Evaluation Pipeline (offline)              │  │
│  │                                                               │  │
│  │  Stage 1A            Stage 1B               Stage 2           │  │
│  │  Query RAG    ---->  Generate Ground  ----> RAGAS Metrics     │  │
│  │  (JSON out)          Truth Answers          Faithfulness      │  │
│  │  run once per        via OpenAI             Answer Relevancy  │  │
│  │  configuration       run once ($0.50)       Context Precision │  │
│  │                      reuse for free         iterate freely    │  │
│  │                                             (~$0.04/run)      │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Tech stack summary:**

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | React + Vite + Tailwind CSS | React 18, Vite 5 |
| Backend | FastAPI + Python | 0.115.5 / 3.12 |
| Vector DB | ChromaDB | 0.6.2 |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | 384-dim |
| LLM (primary) | OpenAI GPT-3.5-turbo | cloud API |
| LLM (fallback) | GPT4All Mistral 7B | local CPU |
| Orchestration | Docker Compose | — |

### 1.2 RAG Pipeline Flow

```
 1. Query Input
    ↓
 2. Domain Detection  (VCC / FastAPI / General — triggers template selection)
    ↓
 3. Query Embedding   (all-MiniLM-L6-v2 → 384-dim vector)
    ↓
 4. Semantic Retrieval (`ChromaDBStore` abstraction over ChromaDB cosine similarity, top-5)
    ↓
 5. Confidence Check  (1 − mean(distances), threshold 0.65)
    │
    ├─ ≥ 0.65 → use semantic results
    └─ < 0.65 → Hybrid Fallback (BM25 + semantic, choose best)
    ↓
 6. Prompt Construction (LangChain template + domain config + acronym map)
    ↓
 7. LLM Generation     (OpenAI GPT-3.5 primary / GPT4All fallback)
    ↓
 8. Response Delivery  (answer + sources + confidence + response_time)
```

### 1.3 Key Design Decisions

#### Vector Store Abstraction

ChromaDB access is centralized in `backend/app/rag/chromadb_store.py` (`ChromaDBStore`).
This module owns client singleton initialization, collection lifecycle, batched inserts,
ANN query, and bulk reads for BM25 index building. `ingestion.py`, `retrieval.py`, and
`hybrid_retrieval.py` now depend on this abstraction instead of calling ChromaDB directly.

This narrows the backend swap surface: if the vector store changes in the future, most
changes are isolated to one module.

#### Embedding Model

| Model | Dims | Speed | Accuracy | Size |
|-------|------|-------|----------|------|
| **all-MiniLM-L6-v2** ← chosen | 384 | 1,500 docs/s | Good | 80 MB |
| all-mpnet-base-v2 | 768 | 500 docs/s | Better | 420 MB |
| text-embedding-ada-002 | 1,536 | 100 docs/s (API) | Best | cloud |

**Decision:** MiniLM for speed/size trade-off in local deployment. 10× GPU speedup with NVIDIA CUDA for batch ingestion.

#### Chunking Strategy

```python
CHUNK_SIZE    = 500   # tokens — balances context vs retrieval precision
CHUNK_OVERLAP = 50    # tokens — prevents mid-sentence splits
```

2,696 output chunks from 161 markdown files (≈ 3× storage expansion). The overlap is critical: without it, cross-chunk answers lose sentence-boundary context.

#### LLM Strategy: Graceful Degradation

```
OpenAI GPT-3.5-turbo  →  2.3s, $0.002/query, production-grade quality
        ↓ (on 401 / 429 / 500 / network error)
GPT4All Mistral 7B    →  80–125s CPU, $0, acceptable backup
        ↓ (on failure)
Error message with guidance
```

#### Confidence Thresholding

Threshold **0.65** (empirically validated). Below this:
- System returns explicit `"Unable to answer with high confidence"`
- Reduces hallucination risk by **57%**
- Trade-off: ~18% of queries are rejected, but users receive transparent guidance

### 1.4 Domain-Aware Prompting

VCC documentation contains domain-specific acronyms that confuse generic embedding search:

```
"What is VCC?"                  → 52.7% confidence
"What is Visa Chart Components?" → 74.4% confidence  (+21%)
```

**Solution:** LangChain `PromptTemplate` with per-domain configuration:

```python
DOMAIN_CONFIGS = {
    "vcc": {
        "domain_name": "Visa Chart Components (VCC)",
        "acronyms": "VCC = Visa Chart Components, WCAG = Web Content "
                    "Accessibility Guidelines, a11y = accessibility",
        "key_concepts": "accessibility, customization, data visualization",
        "prompt_template": """You are an expert on {domain_name}.

Common acronyms: {acronyms}
Key concepts: {key_concepts}

Context from documentation:
{context}

User question: {question}

Provide a clear, accurate answer based ONLY on the context above.
Do NOT infer or add details not present in the context."""
    }
}
```

**Impact:** +15% Answer Relevancy, +23% Context Precision for VCC-specific queries.

---

## 2. Hybrid Search: Case Study

*For the full implementation walkthrough, see [HYBRID-SEARCH-CASE-STUDY.md](./HYBRID-SEARCH-CASE-STUDY.md).*

### 2.1 The Problem

During VCC baseline evaluation, Query 9 consistently failed:

```
Query: "What is IDataTableProps?"

Semantic-only result:
  Retrieved: IAccessibilityType ❌, IDataLabelType ❌, IDataDisplayType ❌
  Confidence: 0.687
```

**Root cause:** Semantic embeddings prioritized *conceptual* similarity ("accessibility" ≈ "table", "label" ≈ "data"). All 6 IDataTableProps chunks existed in ChromaDB — direct lookup succeeded. The model simply couldn't distinguish the exact technical term from similarly-named interfaces.

### 2.2 Solution: Semantic-First + Hybrid Fallback

```
❌ Naive approach: Run hybrid search on ALL queries
   Problem: Degraded general queries (hybrid confidence: 0.3–0.4)

✅ Final strategy: Semantic-first, hybrid as fallback
   1. Try semantic-only (handles 90% of queries well)
   2. If confidence < 0.65 → try hybrid (BM25 + semantic)
   3. Return whichever result has higher confidence
```

### 2.3 Implementation Highlights

#### BM25 Tokenization with Stopword Filtering

```python
STOPWORDS = {'what', 'is', 'the', 'how', 'do', 'can', 'i', 'in',
             'with', 'to', 'a', 'an', 'for', 'of', 'this', 'that', ...}

def tokenize_with_stopword_filter(text):
    tokens = [w for w in text.lower().split() if w not in STOPWORDS]
    # 5× boost for camelCase/PascalCase API names (e.g. IDataTableProps)
    return [token * 5 if token.startswith('i') and len(token) > 2
            else token for token in tokens]
```

**Before filtering:**  
`"What is IDataTableProps?"` → tokens `['what', 'is', 'idatatableprops']`  
→ BM25 ranks generic READMEs first ("what" and "is" appear everywhere)

**After filtering + boosting:**  
→ tokens `['idatatableprops'] × 5`  
→ BM25 ranks IDataTableProps chunks with scores **0.995–1.000** ✅

#### Query Classification for Adaptive Weights

```python
def get_search_weights(query_type):
    return {
        'api':             (0.4, 0.6),  # Favor BM25 — exact keyword match
        'how_to':          (0.7, 0.3),  # Favor semantic — conceptual
        'troubleshooting': (0.6, 0.4),
        'general':         (0.7, 0.3),
    }[query_type]
```

### 2.4 Results

| Query | Strategy Used | Semantic Conf | Hybrid Conf | Result |
|-------|--------------|---------------|-------------|--------|
| 1–8: general how_to | Semantic ✓ | 0.77–0.89 | 0.55–0.78 | No change |
| **9. IDataTableProps** | **Hybrid ✅** | **0.687** | **0.898** | **+31%** |
| 10. Integrate React | Semantic ✓ | 0.886 | 0.771 | No change |

**9/10 queries:** Semantic-only works fine — no regression from hybrid path.  
**1/10 queries:** Hybrid fallback rescued a critical API lookup — **all 5 top results were IDataTableProps** (BM25 score 0.995–1.000).

**Performance overhead:** Hybrid adds ~2.5s when triggered. At 10% trigger rate → weighted average latency **2.75s** (vs 2.5s semantic-only). Acceptable.

---

## 3. Full RAGAS Evaluation

*For complete metric tables, per-query breakdown, and cost analysis, see [EVALUATION-REPORT.md](./EVALUATION-REPORT.md).*

### 3.1 Evaluation Framework

Three-stage pipeline separating expensive and cheap operations:

```
Stage 1A: Query RAG System          — run once per configuration
    ↓  save: baseline_results.json
Stage 1B: Generate Reference Answers — run once ($0.50–$1 OpenAI)
    ↓  save: queries_with_refs.json
Stage 2:  RAGAS Evaluation           — iterate freely (~$0.04 / run)
    ↓  output: metric scores (0–1)
```

**Why this matters:** Stage 1A+1B are the expensive steps. Once references exist, re-evaluation after any code change costs ~$0.04 and takes ~1 minute, enabling rapid iteration.

### 3.2 Baseline vs. Optimized

| Metric | Baseline (GPT4All) | Optimized (GPT-3.5) | Change |
|--------|-------------------|---------------------|--------|
| **Faithfulness** | 0.52 | **0.87** | +67% ✅ |
| **Answer Relevancy** | 0.68 | **0.89** | +31% ✅ |
| **Context Precision** | 0.71 | **0.84** | +18% ✅ |
| **Overall** | 0.64 | **0.87** | +36% ✅ |
| Response Time | 85s | **2.3s** | −97% ✅ |
| Confidence ≥ 0.65 | 58% | **82%** | +40% ✅ |

### 3.3 Improvement Breakdown

**LLM upgrade (GPT4All → GPT-3.5): +35% Faithfulness**  
GPT-3.5 is superior at instruction following — it stays grounded in the retrieved context and avoids fabricating API details. Example of baseline failure:

```
Query: "How do I improve the group focus indicator in VCC?"
Retrieved context: "VCC supports WCAG 2.1 Level AA compliance. Focus
  indicators can be customized using CSS properties..."

GPT4All answer: "Use the `focusIndicatorStyle` prop with
  `borderWidth: 3px` and `borderColor: '#0066CC'`..."
    → Faithfulness: 0.40 ❌  (prop name not in context — hallucinated)

GPT-3.5 answer: "According to the VCC documentation, focus indicators
  can be customized via CSS properties. For WCAG 2.1 compliance..."
    → Faithfulness: 0.91 ✅
```

**Domain-aware prompts: +15% Answer Relevancy**  
Acronym mappings (VCC, WCAG, a11y) and domain instructions eliminate the confidence gap between expanded and contracted queries.

**Confidence thresholding: −57% low-confidence responses**  
Rather than returning a hallucinated answer, the system now responds:  
`"Unable to answer with high confidence. Confidence: 0.51. Please verify with the official VCC documentation."`  
This is especially important for deployment-related queries that lack source coverage.

**Retrieval improvements: +18% Context Precision**  
Better document type diversity (79.5% repo docs, 19.4% API docs, 1.1% GitHub issue Q&A), improved metadata, and hybrid fallback for edge cases.

### 3.4 Cost-Performance Analysis

```
Baseline (GPT4All local):
  Cost: $0 per query
  Time: 85s
  Quality: 0.64 overall
  42% of queries below confidence threshold

Optimized (GPT-3.5-turbo):
  Cost: $0.002 per query
  Time: 2.3s
  Quality: 0.87 overall
  18% of queries below confidence threshold

ROI: 97% faster · 36% higher quality · ~$60/month at 1,000 queries/day
```

### 3.5 Query-Level Patterns

**High-confidence (≥ 0.80):**
- "What is Visa Chart Components?" — Confidence 0.889, Faithfulness 0.95
- "How do I implement accessibility features?" — Confidence 0.847, Faithfulness 0.91

**Medium-confidence (0.65–0.79):**
- "What is VCC?" (acronym without expansion) — Confidence 0.687, handled by domain prompt
- "How do I work with frequency values in Alluvial Chart?" — Confidence 0.724, specific API detail

**Low-confidence (< 0.65) — correctly rejected:**
- "How do I deploy VCC to production?" — Confidence 0.512, documentation lacks deployment guide → prevented hallucinated answer

---

## 4. Engineering Process & Lessons Learned

*For the full retrospective including dev timeline and transferable strategies, see [lesson-learned.md](./lesson-learned.md).*

### 4.1 Evaluation-Driven Development

Rather than guessing at improvements, we built a 3-stage evaluation pipeline *before* optimizing — and ran it at every change. This revealed critical issues early:

```
Early evaluation finding:
  Context Precision: 0.948  ✅ (retrieval is excellent)
  Faithfulness:      0.634  ❌ (generation has hallucination issues)
  Answer Relevancy:  0.772  ✅ (query alignment good)

Without evaluation: we would have shipped a system with 0.634 faithfulness
and assumed it worked because manual testing looked fine.
```

**Key insight:** Faithfulness < 0.7 means the LLM is injecting facts not present in the retrieved context. This is invisible to manual testing — you'd need to cross-reference every claim against every source to catch it. RAGAS catches it automatically at $0.04/run.

### 4.2 AI-Assisted Testing

We used GitHub Copilot to scaffold 38 unit tests from implementation descriptions — a process that would take 3–4 hours manually was done in ~30 minutes.

| Metric | Manual Approach | AI-Driven Approach |
|--------|----------------|-------------------|
| Time to write 38 tests | ~4 hours | ~30 minutes |
| Test coverage | Variable (<60%) | Comprehensive (>80%) |
| Edge case identification | Developer-dependent | AI suggests many |

**Critical caveat — "test what exists, not what you imagine":**

```python
# AI confidently generated:
def test_prompt_builder_initialization():
    pb = PromptBuilder()  # ← class doesn't exist
    assert pb is not None

# Actual code has:
construct_prompt(query, context, domain)  # ← standalone function

# Fix: human verification rewrote tests to match reality
```

AI generates tests for abstractions it *imagines* from the code. The human must verify every generated test runs against the actual implementation — not assumed interfaces.

### 4.3 Development Velocity

Time breakdown across the 2-day, ~22-hour project:

| Stage | Time | Value |
|-------|------|-------|
| Backend core RAG | 3.0h (14%) | Working system |
| Frontend + Docker | 3.5h (16%) | Full-stack demo |
| **Evaluation framework** | **5.0h (23%)** | **Highest value** |
| Tests (AI-assisted) | 2.0h (9%) | Confidence |
| Improvements (hybrid, prompts) | 1.5h (7%) | Quality gains |
| Documentation | 2.0h (9%) | Professional polish |
| Debugging | 4.5h (20%) | Reality tax |

The evaluation framework was the highest single time investment — and the highest ROI. It caught the faithfulness problem, quantified the LLM upgrade impact, and enabled confident iteration.

### 4.4 Key Transferable Lessons

**Technical:**
1. **Cloud LLMs are better for production RAG** — 37× faster, 36% higher quality, minimal cost ($60/month at 1K queries/day). Local LLMs only for privacy-critical or offline deployments.
2. **Confidence thresholding prevents hallucination** more reliably than prompt tweaking alone — explicit "I don't know" builds more user trust than a wrong answer.
3. **Hybrid search is not one-size-fits-all** — applying BM25 to all queries degrades general performance. Semantic-first + hybrid-fallback at a confidence threshold is the correct pattern.
4. **Stopword filtering matters as much as the BM25 algorithm** — without it, generic tokens dominate scores and exact technical terms rank last.

**Process:**
1. **Build evaluation infrastructure before optimizing** — you need a feedback loop to know if a change actually helped.
2. **Distribution analysis > mean metrics** — P10 at 0.0 faithfulness reveals catastrophic failure modes that a mean of 0.63 masks.
3. **Ship working software with 80% test coverage** > perfect software that ships late.
4. **AI assistance requires human oversight** — for tests, for code, for everything. The AI is a fast scaffolding tool, not a correctness guarantee.

---

## Quick Reference

| Topic | Where to go |
|-------|------------|
| Full architecture diagrams | [`ARCHITECTURE.md`](./ARCHITECTURE.md) |
| Hybrid search implementation code | [`HYBRID-SEARCH-CASE-STUDY.md`](./HYBRID-SEARCH-CASE-STUDY.md) |
| RAGAS pipeline & all query results | [`EVALUATION-REPORT.md`](./EVALUATION-REPORT.md) |
| Full lessons & dev timeline | [`lesson-learned.md`](./lesson-learned.md) |
| Setup & running | [`../README.md`](../README.md) |
| Technical summary (2–3 pages) | [`technical-report.md`](./technical-report.md) |

---

**Document Version:** 1.0  
**Last Updated:** March 10, 2026  
**Status:** Complete — standalone deep-dive companion
