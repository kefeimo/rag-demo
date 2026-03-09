# RAG System — Technical Reference

> Grounded in the actual codebase.

---

## System Summary

> *"This project implements a Retrieval-Augmented Generation system that answers questions over two documentation corpora — FastAPI docs and Visa Chart Components (VCC) docs. The frontend is a React/Vite interface; the backend is a FastAPI service that orchestrates retrieval, prompt construction, and LLM calls. Documents are ingested into ChromaDB using embeddings from either OpenAI or sentence-transformers. At query time the system tries semantic-only retrieval first, and if confidence is below a threshold it falls back to hybrid search combining BM25 keyword scoring with vector similarity. The final prompt is domain-aware — it uses different context and instructions for VCC vs FastAPI queries. I also built a RAGAS-based evaluation pipeline to measure retrieval quality and answer faithfulness against a curated test set."*

---

## System Architecture

The system has two separate workflows that meet at ChromaDB.

### Ingestion Workflow (offline, prerequisite)

Must run before the system can answer any query. Triggered manually via `/api/v1/ingest` (FastAPI docs) or `/api/v1/ingest/visa-docs` (VCC docs), or pre-baked into the Docker image.

```
FastAPI docs                              VCC docs
────────────────────────────────          ──────────────────────────────────────
Markdown files  (data/documents/)         JSON files  (data-pipeline/data/raw/)
  │  load_documents()  glob *.md            │  load_json_documents()
  │  glob *.md recursively                  │  visa_repo_docs.json  (53 docs)
  │                                         │  visa_code_docs.json  (210 docs)
  │                                         │  visa_issue_qa.json   (13 docs)
  └──────────────────┬──────────────────────┘
                     ▼
         DocumentLoader.chunk_text()
         (chunk_size=500, overlap=50, sentence-boundary aware)
                     │
                     ▼
         EmbeddingProvider.encode(batch)
         OpenAI text-embedding-3-small  OR  sentence-transformers/all-MiniLM-L6-v2
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   fastapi_docs            vcc_docs
   collection              collection
   (ChromaDB)              (ChromaDB)
```

### Query Workflow (online, per request)

```
React Frontend (Vite + Tailwind)
  │  POST /api/v1/query  {query, collection, top_k=3}
  ▼
FastAPI Backend  (backend/app/main.py)
  │  Retriever / HybridRetriever
  ▼
ChromaDB  ◄─── reads embeddings written by ingestion
  │  top-k chunks  (frontend sends k=3, backend default k=5, threshold=0.65)
  ▼
PromptBuilder  (LangChain PromptTemplate, domain-aware)
  │  prompt = system instructions + context chunks + user query
  ▼
LLM  (OpenAI gpt-3.5-turbo / GPT4All mistral-7b local)
  │  QueryResponse {answer, sources, confidence, response_time}
  ▼
React Frontend  (ResponseDisplay component)
```

**Key files:**

| File | Role |
|---|---|
| `frontend/src/App.jsx` | Query dispatch, corpus toggle, client-side cache |
| `backend/app/main.py` | FastAPI app, lifespan startup, all routes |
| `backend/app/rag/ingestion.py` | `DocumentLoader` — load → chunk → embed → store |
| `backend/app/rag/embeddings.py` | `EmbeddingProvider` — OpenAI or sentence-transformers |
| `backend/app/rag/retrieval.py` | `Retriever` — semantic-only search via ChromaDB |
| `backend/app/rag/hybrid_retrieval.py` | `HybridRetriever` — BM25 + semantic fusion |
| `backend/app/rag/query_classifier.py` | Keyword-based query type → weight tuning |
| `backend/app/rag/generation.py` | `PromptBuilder`, `OpenAIClient`, `GPT4AllClient` |
| `backend/app/config.py` | `Settings` via pydantic-settings, all env vars |
| `evaluation/run_ragas_stage2_eval.py` | RAGAS evaluation pipeline |

---

## The 4 Core RAG Components

### 1 — Ingestion (`backend/app/rag/ingestion.py`)

**What it does:** Loads source documents → splits into overlapping chunks → generates embeddings → stores in ChromaDB.

Two corpora, two source formats, two entry-point functions — both share the same `DocumentLoader.chunk_text()` → `ChromaDBIngestion` pipeline:

**FastAPI docs (markdown → `fastapi_docs` collection):**
```
ingest_documents(document_path)
  └── DocumentLoader.load_documents()      # glob *.md recursively from directory
  └── DocumentLoader.chunk_text()          # overlapping character windows
  └── EmbeddingProvider.encode(batch)      # batch encode all chunks
  └── collection.add(ids, embeddings, documents, metadatas)
```

**VCC docs (JSON → `vcc_docs` collection):**
```
ingest_vcc_documents(repo_docs_path, code_docs_path, issue_qa_path)
  └── DocumentLoader.load_json_documents() # reads up to 3 JSON files, skips missing
  └── DocumentLoader.chunk_text()          # same chunking pipeline
  └── EmbeddingProvider.encode(batch)      # same embedding pipeline
  └── collection.add(ids, embeddings, documents, metadatas)
```

JSON files are pre-structured `[{"content": "...", "metadata": {...}}]` arrays produced by the data-pipeline extractors — no parsing step needed before chunking.

**Actual settings (from `config.py`):**
```python
chunk_size: int = 500        # characters per chunk
chunk_overlap: int = 50      # overlap between adjacent chunks
```

**Chunking algorithm — the key detail:**
- Tries to break at sentence boundaries (`. `, `.\n`, `! `, etc.) within the last 100 characters
- Falls back to word boundary (last space) within last 50 characters
- Only then allows a hard cut at exactly `chunk_size`
- Each chunk stores `chunk_id`, `start_char`, `end_char`, `chunk_count` in metadata

**Known asymmetry — end is snapped, start is not:**
The boundary-snapping logic only adjusts the *end* of each chunk. The *start* of the next chunk always advances by the fixed formula `chunk_size - chunk_overlap`, regardless of where the previous chunk actually ended. This means the overlap region can begin mid-sentence or mid-word, and the effective overlap may differ from `chunk_overlap`. A boundary-aware fix would base the advance on `len(actual_chunk_text) - chunk_overlap` instead.

**Design rationale:**

*Why chunk at all?*
> LLMs have token limits (typically 4k–128k). Chunking lets us retrieve only the relevant portion instead of sending the entire corpus. It also improves retrieval precision — a small, focused chunk scores higher against a specific query than a long document that only mentions the topic once.

*How did you choose chunk_size=500?*
> 500 characters is roughly 100–120 tokens, which fits comfortably inside the context window even when concatenating top_k=5 chunks. Smaller chunks reduce noise per chunk but risk splitting important explanations across chunk boundaries. Larger chunks improve contextual completeness but dilute the embedding signal.

*What if chunks are too small?*
> Context gets fragmented — the answer might span two chunks but only one is retrieved. Incomplete code examples, split across chunks, become useless.

*What if chunks are too large?*
> Each chunk covers too many topics. A query about one specific feature retrieves a chunk that mostly talks about unrelated things, lowering effective precision.

---

### 2 — Embedding (`backend/app/rag/embeddings.py`)

**What it does:** `EmbeddingProvider` is an abstraction over two backends, selected via `EMBEDDING_PROVIDER` env var.

**Actual backends:**

| `EMBEDDING_PROVIDER` | Model | Dimension | Cost |
|---|---|---|---|
| `openai` (default) | `text-embedding-3-small` | 1536 | ~$0.02/1M tokens |
| anything else | `sentence-transformers/all-MiniLM-L6-v2` | 384 | Free, local |

**Unified interface — both backends expose the same signature:**
```python
provider.encode("a string")          # → List[float]   (single vector)
provider.encode(["str1", "str2"])    # → List[List[float]]  (batch)
```

**Design rationale:**

*Why OpenAI embeddings over sentence-transformers?*
> For production on Render, OpenAI `text-embedding-3-small` gives higher quality embeddings and avoids loading a 90MB model into memory. Sentence-transformers is offered as the local/offline fallback — useful for development without API keys or for GPU-accelerated environments.

*Why this sentence-transformer model specifically?*
> `all-MiniLM-L6-v2` has a good quality/speed tradeoff — 80ms per batch on CPU, 384-dimension vectors. For a developer documentation corpus (relatively clean text) it performs well enough. Something like `all-mpnet-base-v2` would give better quality but at ~4× the inference time.

*What if embedding quality is poor?*
> Queries will retrieve semantically irrelevant chunks — the entire downstream pipeline degrades. Signs: low confidence scores across the board, answers that don't address the question, high RAGAS `context_recall` failures.

*Why must ingestion and query-time use the same embedding model?*
> Vector similarity is only meaningful within the same embedding space. Mixing models produces garbage similarity scores.

---

### 3 — Retrieval (`backend/app/rag/retrieval.py`, `hybrid_retrieval.py`)

#### Semantic-only path (`Retriever`)

```
Retriever.retrieve(query)
  └── embed_query(query)                # single .encode() call
  └── collection.query(                 # ChromaDB
        query_embeddings=[vector],
        n_results=top_k,                # default 5
        include=["documents","metadatas","distances"]
      )
  └── confidence = 1.0 - (distance / 2.0)   # cosine: 0=identical, 2=opposite
  └── overall_confidence = mean(top-k confidences)
```

**Confidence threshold:** `0.65` — queries below this threshold return a "not enough information" message rather than a hallucinated answer.

#### Hybrid path (`HybridRetriever`)

The system uses a **two-phase strategy** (visible in `main.py`):

1. Try semantic-only first (handles most queries well, cheaper)
2. If `confidence < 0.65`, try hybrid (handles exact API names, keywords)
3. Keep whichever result has higher confidence

**Hybrid fusion algorithm:**
```
BM25 ranking (rank_bm25.BM25Okapi)
  └── tokenize corpus at startup (expensive, done once in lifespan)
  └── score query against all docs
  └── normalize scores to [0, 1]

Semantic ranking (ChromaDB)
  └── same as Retriever above

Fusion:
  combined_score = (semantic_weight × semantic_score) + (bm25_weight × bm25_score)
```

**Adaptive weights via `query_classifier.py`:**

| Query type | Example | Semantic weight | BM25 weight |
|---|---|---|---|
| `api` | "What does IDataTableProps do?" | 0.4 | 0.6 |
| `how_to` | "How do I add a tooltip?" | 0.7 | 0.3 |
| `troubleshooting` | "Why is my chart not rendering?" | 0.6 | 0.4 |
| `general` | "What is VCC?" | 0.7 | 0.3 |

**API-name boosting in BM25 tokenizer:** Tokens that look like interface names (start with `I`, contain `_` or `-`) are repeated 5× in the BM25 index — giving exact keyword matches on things like `IDataTableProps` or `visa-charts-react` a significant weight boost.

**Design rationale:**

*What if retrieval returns irrelevant chunks?*
> Debugging order: (1) check embedding model consistency, (2) inspect the raw retrieved chunks with confidence scores, (3) adjust `chunk_size` — too large dilutes signal, (4) adjust `top_k` — more results may include relevant ones but increases noise in prompt, (5) improve with reranking (cross-encoder), (6) metadata filtering if documents have clear categorical structure, (7) query rewriting / HyDE (Hypothetical Document Embeddings).

*Why hybrid search instead of just semantic?*
> Semantic search struggles with exact identifiers — if a user types `IDataTableProps`, the embedding for that token is close to other API names, not specifically the interface they want. BM25 does exact keyword matching and handles this natively. The hybrid approach gets the best of both: BM25 for precision on exact names, semantic for intent/concept matching.

*Why build BM25 at startup instead of per request?*
> BM25 requires tokenizing the entire corpus (2696 chunks for VCC alone). Building that index takes a few seconds and significant memory. The `lifespan` context manager in `main.py` does this once, and `hybrid_retrievers` dict caches the result per collection for the lifetime of the process.

---

### 4 — Prompt Construction (`backend/app/rag/generation.py`)

**What it does:** `PromptBuilder` uses a LangChain `PromptTemplate` to assemble the final prompt from user query + retrieved chunks, with domain-specific instructions.

**Actual prompt structure:**
```
You are a helpful AI assistant specialized in {domain}.

IMPORTANT RULES:
1. Use the provided context to answer
2. Code examples with {{...}} are intentional placeholders
3. Cite sources when possible
4. Only say you don't know if context is truly unrelated

QUERY UNDERSTANDING:
- Handle spelling variations / typos
- Known acronyms: {known_acronyms}   ← domain-specific

DOMAIN-SPECIFIC GUIDANCE:
{domain_guidance}                    ← domain-specific

CONTEXT:
[Source 1: path/to/doc.md (relevance: 0.82)]
<chunk content>
---
[Source 2: path/to/other.md (relevance: 0.74)]
<chunk content>

QUESTION:
{query}

ANSWER:
```

**Domain routing (determined from collection name):**

| Collection name contains | Domain | Acronyms injected |
|---|---|---|
| `visa`, `vcc`, `chart` | `vcc` | VCC, WCAG, a11y |
| `fastapi` | `fastapi` | API, ASGI, ORM |
| anything else | `general` | — |

**Two LLM backends:**

| `LLM_PROVIDER` | Class | Model | Notes |
|---|---|---|---|
| `openai` | `OpenAIClient` | `gpt-3.5-turbo` (configurable) | Production default |
| `gpt4all` | `GPT4AllClient` | `mistral-7b-instruct-v0.1.Q4_0.gguf` | Local fallback, ~4GB |

**Fallback chain:** If OpenAI fails at generation time, `generate_answer()` automatically retries with `GPT4AllClient` and prefixes the answer with a warning banner.

**Design rationale:**

*How do you reduce hallucination?*
> Multiple layers: (1) the confidence threshold rejects queries where retrieved context is too weak — the system explicitly says "I don't have enough information" rather than fabricating an answer; (2) the prompt explicitly says "answer based on context only"; (3) sources are cited in the response so users can verify; (4) RAGAS `faithfulness` metric measures whether every claim in the answer is grounded in retrieved context.

*Why does the prompt handle `{{...}}` placeholders specifically?*
> The documentation corpus contains code examples with template literals and Jinja/Python format strings. Without the explicit instruction, LLMs sometimes try to "fill in" these placeholders, which confuses users who expect to see the actual template syntax from the docs.

---

## The Evaluation System

**Two-stage pipeline (in `evaluation/`):**

```
Stage 1: run_ragas_stage1_query.py
  └── Sends each test question to the live RAG API
  └── Records: query, answer, retrieved_contexts, response_time

Stage 1b: run_ragas_stage1b_generate_references.py
  └── Uses GPT-4 to generate reference answers for each test question
  └── Needed for metrics that require ground truth (ContextPrecision, AnswerCorrectness)

Stage 2: run_ragas_stage2_eval.py
  └── Runs RAGAS evaluation on Stage 1 output
  └── Produces per-question and aggregate metrics
```

**Metrics and what they measure:**

| Metric | What fails if this is low | Requires reference? |
|---|---|---|
| `faithfulness` | LLM generates claims not in retrieved context (hallucination) | No |
| `answer_relevancy` | Answer doesn't address the actual question | No |
| `context_precision` | Retrieved chunks contain irrelevant noise | Yes |
| `context_recall` | Retrieved chunks are missing information needed to answer | Yes |
| `answer_correctness` | Answer is factually wrong compared to ground truth | Yes |

**Test sets (in `data/test_queries/`):**
- `baseline_20.json` — 20 FastAPI questions, no references
- `baseline_20_with_refs.json` — same 20 with GPT-4-generated references
- `vcc_baseline_10.json` — 10 VCC questions

`faithfulness` and `answer_relevancy` don't need a reference corpus and can be run on any query. For `context_precision` and `context_recall`, reference answers are generated using GPT-4 in Stage 1b, enabling measurement of whether the retriever surfaces the right chunks. The two-stage design allows re-running evaluation on the same query results with different metrics without hitting the RAG system again.

---

## Design Tradeoffs

### Why two separate corpora instead of one unified index?

The collections were kept separate intentionally:

1. **Different document structures** — FastAPI docs are narrative tutorial markdown; VCC docs combine READMEs, auto-generated API docs from code, and GitHub issue Q&A. A single embedding space would mix these signals.
2. **Evaluation isolation** — RAGAS metrics can be measured per corpus. Mixing them would make it hard to tell which corpus is underperforming.
3. **Prompt differentiation** — VCC queries need `IDataTableProps`-style API name boosting and WCAG/a11y acronym handling; FastAPI queries don't. `PromptBuilder`'s domain config encodes this cleanly.
4. **Future flexibility** — A query router can be added later to auto-select the collection without restructuring ingestion.

### Why vector DB over traditional keyword search?

| | Traditional (Elasticsearch/BM25) | Vector (ChromaDB) |
|---|---|---|
| Matching | Exact keyword overlap | Semantic similarity |
| "How do I make a chart accessible?" | Needs "accessible" in docs | Finds WCAG-related chunks even if word differs |
| Exact API names | Strong | Weaker |
| Setup complexity | Higher | Lower |

This repo uses **both**: semantic for intent, BM25 for exact identifier precision.

### Why RAG instead of fine-tuning?

| | Fine-tuning | RAG |
|---|---|---|
| Knowledge update | Retrain (expensive, days) | Re-ingest (minutes) |
| Cost | High ($$$, GPU hours) | Low (embedding API only) |
| Source citation | Hard | Native (metadata on every chunk) |
| Hallucination control | Harder | Confidence threshold + prompt constraints |
| Appropriate for | Tone/style adaptation | Dynamic, updatable knowledge bases |

---

## Debugging Playbook

### "The system returns irrelevant answers"

```
1. Check embedding consistency
   → Are ingestion and query-time using the same EMBEDDING_PROVIDER?

2. Inspect retrieved chunks directly
   → Add logging: print retrieval_result["documents"] with confidence scores
   → Look at what actually came back — is it topically wrong?

3. Adjust chunk_size
   → Too large: many topics per chunk, diluted signal
   → Too small: answer spans multiple chunks, only one retrieved

4. Adjust top_k
   → Increase from 5 to 8 and see if relevant chunks appear further down

5. Check confidence threshold
   → If threshold=0.65 is too strict, legitimate answers are being rejected
   → If too loose, weak context passes through and LLM hallucinates

6. Check prompt template
   → Is domain routing correct? (collection name → domain → PromptBuilder config)
```

### "Confidence scores are consistently low"

```
1. Check collection name match
   → CHROMA_COLLECTION_NAME in .env must match the ingested collection

2. Verify ingestion ran successfully
   → collection.count() should be > 0

3. Embedding model mismatch
   → collection.query() silently returns garbage distances if embedding dimension differs
```

---

## End-to-End Request Flow

> *"A request enters `main.py` at `POST /api/v1/query`. The handler reads `collection` from the request (falling back to the env default). It instantiates a `Retriever` and calls `retrieve(query, top_k)`. If the returned `confidence` is below `0.65`, and a `HybridRetriever` was pre-built at startup for that collection, it runs hybrid search and keeps whichever result has higher confidence. If the collection has no documents or confidence is still too low, it returns an 'I don't have enough information' message. Otherwise it calls `generate_answer()`, which builds a domain-aware prompt via `PromptBuilder` and sends it to the configured LLM client. The `QueryResponse` includes the answer, source chunks, confidence score, and response time."*

---

## Future Roadmap

| Area | Improvement | Why |
|---|---|---|
| **Retrieval** | Reranking with a cross-encoder | BM25+semantic fusion improves recall; a cross-encoder improves precision by re-scoring top-k with full pair attention |
| **Retrieval** | Query rewriting / HyDE | Rephrase ambiguous queries before embedding; HyDE generates a hypothetical answer and embeds that instead of the raw query |
| **UX** | Automatic corpus routing | Remove the manual FastAPI/VCC toggle; classify the query and select the collection automatically |
| **Evaluation** | Continuous eval pipeline | Run RAGAS on each deployment to catch regressions; dashboard to track metric trends over time |
| **Scale** | Chunking strategy improvements | Sentence-aware splitting, semantic chunking (split at topic boundaries rather than character count) |
| **Reliability** | `app/dependencies.py` with `Depends()` | Enable mock retrievers in tests; decouple startup from route handlers |

---

## Development Notes

This project uses AI tools to accelerate implementation. The architecture decisions — hybrid retrieval strategy, confidence-gating logic, domain-aware prompt routing, two-stage evaluation pipeline — are deliberate design choices. The AI assisted with writing implementation code; the system design and tradeoff reasoning drove those choices.
