# Confidence → Relevance Score Refactoring

**Status: ✅ COMPLETED — March 9, 2026**  
**Version:** 1.0.0 → 1.1.0 (breaking API change)  
**Deployed:** Backend (Render) + Frontend (Vercel) both live and verified.

---

## Background

The term `confidence` was used throughout the codebase and UI, but it was **not** answer-level confidence. It is a **retrieval relevance score** — a measure of how closely the retrieved chunks match the query, computed before the LLM ever runs.

### What the value actually is

```
relevance_score = 1.0 - (cosine_distance / 2.0)
                = average across top-k retrieved chunks
                = computed from ChromaDB distances, before generation
```

This measures **query-chunk similarity in embedding space**. It answers: "how relevant are the retrieved documents to the question?" — not "how correct or trustworthy is the generated answer?"

### Why the distinction matters

| | What was called "confidence" | True answer-level confidence |
|---|---|---|
| Computed | Before LLM is called | After generation |
| Measures | Retrieval relevance (chunk ↔ query similarity) | Answer correctness / faithfulness |
| Used for | Gating: reject query if retrieval too weak | Telling the user how much to trust the answer |
| Influenced by | Embedding quality, chunk content, query wording | LLM reasoning, context faithfulness, factual accuracy |

True answer-level confidence would require one of:
- LLM self-assessment (unreliable; LLMs are poorly calibrated)
- RAGAS `faithfulness` check post-generation (requires a second LLM call)
- Cross-encoder scoring (answer, context) similarity

None of these are implemented at request time. The RAGAS evaluation pipeline (`evaluation/`) runs offline against a test set only.

---

## Breaking Changes (v1.1.0)

| Change | Old | New |
|---|---|---|
| API JSON field | `"confidence"` | `"relevance_score"` |
| Env var | `CONFIDENCE_THRESHOLD` | `RELEVANCE_THRESHOLD` |

---

## Files Changed

### Backend

| File | Change |
|---|---|
| `app/__init__.py` | `__version__` `"1.0.0"` → `"1.1.0"` |
| `app/models.py` | `Source.confidence` → `Source.relevance_score`; `QueryResponse.confidence` → `QueryResponse.relevance_score`; descriptions clarified as "Retrieval relevance score (cosine similarity, computed before LLM generation)" |
| `app/config.py` | `confidence_threshold` → `relevance_threshold`; `CONFIDENCE_THRESHOLD` env var → `RELEVANCE_THRESHOLD` |
| `app/rag/retrieval.py` | `check_confidence()` → `check_relevance()`; `confidence_threshold` attr → `relevance_threshold`; all `"confidence"` dict keys → `"relevance_score"`; log messages updated |
| `app/rag/hybrid_retrieval.py` | `total_confidence`/`avg_confidence` → `total_relevance`/`avg_relevance`; `"confidence"` dict key → `"relevance_score"` |
| `app/rag/generation.py` | `extract_sources()` dict key `"confidence"` → `"relevance_score"` |
| `app/main.py` | All `overall_confidence` → `overall_relevance`; all `.get("confidence", 0.0)` → `.get("relevance_score", 0.0)`; `check_confidence()` → `check_relevance()` |
| `app/utils/validators.py` | `validate_confidence_threshold()` → `validate_relevance_threshold()` |
| `backend/.env` | `CONFIDENCE_THRESHOLD=0.65` → `RELEVANCE_THRESHOLD=0.65` |
| `backend/.env.example` | Same |
| `tests/conftest.py` | `confidence_threshold=0.65` → `relevance_threshold=0.65` |
| `tests/test_retrieval.py` | All test function names, mock dict keys, assertions updated |
| `tests/test_rag_pipeline.py` | `test_confidence_threshold_configuration` → `test_relevance_threshold_configuration`; all `settings.confidence_threshold` → `settings.relevance_threshold` |

### Frontend

| File | Change |
|---|---|
| `src/App.jsx` | `confidence: data.confidence` → `relevance_score: data.relevance_score`; history display refs updated |
| `src/components/ResponseDisplay.jsx` | `response.confidence` → `response.relevance_score`; "Low Confidence Response" → "Low Relevance Score"; badge labels updated |
| `src/components/SourceCard.jsx` | `source.confidence` → `source.relevance_score`; `getConfidenceColor`/`getConfidenceLabel` → `getRelevanceColor`/`getRelevanceLabel` |

### Evaluation Pipeline

| File | Change |
|---|---|
| `evaluation/run_ragas_stage1_query.py` | `rag_response.get('confidence')` → `rag_response.get('relevance_score')`; output JSON key and print updated |

### Docs

| File | Change |
|---|---|
| `docs/REFERENCE-RAG.md` | Threshold note clarified as retrieval relevance gate, not answer confidence |
| `backend/README.md` | Updated (user-edited) |
| `docs/REFERENCE-BACKEND-FASTAPI.md` | Updated (user-edited) |

**Archive files left unchanged** (`evaluation/archive/`).

---

## What This Is NOT

- ❌ Not adding answer-level confidence (would require post-generation LLM evaluation)
- ❌ Not changing the threshold value (0.65 stays the same)
- ❌ Not changing the computation formula
- ❌ Not changing retrieval logic — purely a naming/labelling fix

---

## Deployment

- **Backend:** `mynameismo/rag-backend:latest` rebuilt from `backend/Dockerfile.render` and pushed to Docker Hub. Render redeployed from the new image. Render env var updated: `CONFIDENCE_THRESHOLD` → `RELEVANCE_THRESHOLD`.
- **Frontend:** Deployed via Vercel GitHub integration (auto-deploy on push). No env var changes needed for frontend.
- **Verification:** Both endpoints confirmed live post-deploy.
