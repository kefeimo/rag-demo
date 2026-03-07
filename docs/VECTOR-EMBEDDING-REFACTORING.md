# Vector Embedding Refactoring

**Commit:** `9da94be`  
**Branch:** `develop`  
**Date:** March 7, 2026

---

## Summary

Switched the embedding backend from a **local sentence-transformers model** (`all-MiniLM-L6-v2`) to the **OpenAI Embeddings API** (`text-embedding-3-small`). This is the primary change in this refactor; the rest of the commit cleans up the heavy local dependencies that are no longer needed.

---

## Motivation

| Problem | Impact |
|---|---|
| `torch==2.10.0` (CUDA build) + 16 `nvidia-*` packages | ~8–9 GB of the 14 GB Docker image |
| `sentence-transformers`, `transformers`, `triton`, `gpt4all` | Additional ~2–3 GB |
| Local model requires GPU or slow CPU inference at startup | Poor cold-start on cloud deployments (Render, etc.) |
| Hard dependency on hardware | Prevents lightweight local dev and CI |

The project already uses OpenAI for LLM generation. Adding OpenAI embeddings eliminates all local ML inference dependencies entirely, reducing the image from **~14 GB → ~1 GB**.

---

## What Changed

### New: `EmbeddingProvider` abstraction

**File:** [`backend/app/rag/embeddings.py`](../backend/app/rag/embeddings.py)

A single class that wraps both backends behind a uniform `encode()` interface:

```python
provider = EmbeddingProvider()

# Single string → List[float]
vector = provider.encode("What is FastAPI?")

# List of strings → List[List[float]]
vectors = provider.encode(["chunk 1", "chunk 2", ...])
```

The backend is selected at startup via `EMBEDDING_PROVIDER` in `.env`:

| `EMBEDDING_PROVIDER` | Model used | Extra deps needed |
|---|---|---|
| `openai` *(default)* | `text-embedding-3-small` | none (uses existing `openai` package) |
| `sentence-transformers` | `all-MiniLM-L6-v2` | `sentence-transformers`, `torch` |

**Key implementation details:**
- Empty strings are replaced with `"."` to avoid OpenAI API 400 errors
- Each text is truncated to 6000 characters (~1500 tokens) before embedding
- Batches of up to 500 texts per API call (within OpenAI's 2048-input limit)

### Updated: `ingestion.py` and `retrieval.py`

Both modules now import `EmbeddingProvider` instead of `SentenceTransformer` directly:

```python
# Before
from sentence_transformers import SentenceTransformer
self.embedding_model = SentenceTransformer(self.embedding_model_name)
embeddings = self.embedding_model.encode(texts, convert_to_numpy=True).tolist()

# After
from app.rag.embeddings import EmbeddingProvider
self.embedding_model = EmbeddingProvider()
embeddings = self.embedding_model.encode(texts)
```

### Updated: `config.py`

Two new settings:

```python
embedding_provider: str  # "openai" | "sentence-transformers"  default: "openai"
openai_embedding_model: str  # default: "text-embedding-3-small"
```

The existing `embedding_model` field is retained for the `sentence-transformers` fallback path.

### Updated: `.env.example`

```bash
EMBEDDING_PROVIDER=openai                        # Options: openai, sentence-transformers
OPENAI_EMBEDDING_MODEL=text-embedding-3-small    # Used when EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2  # Used when EMBEDDING_PROVIDER=sentence-transformers
```

### Removed from `requirements.txt`

| Package | Reason removed |
|---|---|
| `torch==2.10.0` | No longer needed for local embeddings |
| `sentence-transformers==2.3.1` | Replaced by OpenAI embeddings |
| `transformers==4.57.6` | Pulled in by sentence-transformers |
| `triton==3.6.0` | GPU kernel compiler, torch dependency |
| `nvidia-cublas-cu12` … (16 packages) | CUDA runtime, no longer needed |
| `cuda-bindings==12.9.4` | CUDA Python bindings |
| `cuda-pathfinder==1.4.0` | CUDA path discovery |
| `gpt4all==2.8.2` | Local LLM removed (OpenAI is the default provider) |
| `huggingface_hub`, `tokenizers`, `safetensors`, `sentencepiece` | HuggingFace stack, no longer needed |
| `hf-xet`, `mpmath`, `sympy` | Transitive deps of the above |

---

## Embedding Model Comparison

| Property | `all-MiniLM-L6-v2` (old) | `text-embedding-3-small` (new) |
|---|---|---|
| Dimensions | 384 | 1536 |
| Provider | Local (HuggingFace) | OpenAI API |
| Inference location | On-device CPU/GPU | Remote API call |
| Cost | Free (compute only) | ~$0.02 / 1M tokens |
| Image size impact | ~3 GB (with torch) | None |
| Cold-start time | 10–30s (model load) | < 1s |
| Quality (MTEB) | Good | Better |

> **Note:** Switching embedding models requires **re-ingesting all documents** because the vector dimensions change (384 → 1536) and the vector space is different. Existing ChromaDB collections built with `all-MiniLM-L6-v2` are incompatible with `text-embedding-3-small`.

---

## Migration Steps (for existing deployments)

If you have an existing ChromaDB database built with `sentence-transformers`:

```bash
# 1. Delete the old vector database
rm -rf data/chroma_db/

# 2. Set the new env vars in backend/.env
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# 3. Re-ingest FastAPI docs
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"document_path": "../data/documents/", "force_reingest": true}'

# 4. Re-ingest VCC docs
curl -X POST http://localhost:8000/api/v1/ingest/visa-docs \
  -H "Content-Type: application/json" \
  -d '{
    "force_reingest": true,
    "repo_docs_path": "../data-pipeline/data/raw/visa_repo_docs.json",
    "code_docs_path": "../data-pipeline/data/raw/visa_code_docs.json",
    "issue_qa_path":  "../data-pipeline/data/raw/visa_issue_qa.json"
  }'
```

---

## Keeping sentence-transformers (opt-in fallback)

If you need to run without an OpenAI API key, you can opt back in to local embeddings:

```bash
# backend/.env
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

Then install the extra deps:

```bash
pip install sentence-transformers torch --index-url https://download.pytorch.org/whl/cpu
```

Re-ingest after switching so the vector dimensions are consistent.

---

## Image Size Impact

| Image | Before | After |
|---|---|---|
| `rag-backend` (Docker) | ~14 GB | ~1 GB |
| Local `venv` | ~7–8 GB (estimated) | **1.1 GB** (measured) |

The reduction comes almost entirely from dropping `torch` + the CUDA stack.
