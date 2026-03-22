# Multi-Collection Architecture & Remaining Work

## Status Overview

✅ **Phase 2 Complete** - Collections API endpoint
✅ **Phase 3 Complete** - Multi-collection query with automatic routing
🔴 **Phase 1 Pending** - Domain/corpus mismatch in prompt construction
🟢 **Phase 4 Future** - Metadata normalization

---

## Background

The system now supports multiple documentation collections (`fastapi_docs`, `at_docs`) with automatic query routing. Collections are separated by **collection name**, not by embedding strategy. Both use the same embedding model (`sentence-transformers/all-MiniLM-L6-v2`).

### Current Collections

| Collection | Documents | Description |
|------------|-----------|-------------|
| `fastapi_docs` | 165 | FastAPI framework documentation |
| `at_docs` | 2408 | Asset Score / Audit Template documentation |

---

## ✅ Completed Work

### Phase 2 — Collections API (Complete)

**Implementation:**
- `GET /api/v1/collections` endpoint lists all available collections with counts
- `backend/app/rag/collections.py` - Collection management utilities (52 lines)
- `CollectionsResponse` and `CollectionInfo` models

**Benefit:** Dynamic collection discovery without hardcoding collection names

### Phase 3 — Multi-Collection Query (Complete)

**Implementation:**
- `backend/app/rag/multi_retrieval.py` - `MultiCollectionRetriever` class (171 lines)
- Queries all collections automatically when no specific collection is requested
- Merges results by relevance score, returns top-K across all collections
- Multi-collection logic is orchestration layer **above** the graph pipeline

**Architecture Decision:**
- Graph remains unchanged (single-collection pipeline)
- Multi-collection retriever calls graph multiple times and merges results
- Clean separation: graph = single query logic, multi-retriever = orchestration

**Frontend Updates:**
- Removed manual collection dropdown selector
- Added collapsible `DocumentationGuide` component
- Shows available collections with 3 example questions each
- Queries all collections by default (unified search experience)
- App title changed to "Documentation RAG Assistant" (neutral, not corpus-specific)

**Files Modified:**
- `backend/app/main.py` - Refactored to thin API layer (522 lines, down from ~650)
- `backend/app/rag/multi_retrieval.py` - New module
- `backend/app/rag/collections.py` - New module
- `frontend/src/App.jsx` - Remove selector, add guide component
- `frontend/src/components/DocumentationGuide.jsx` - New component

---

## 🔴 Remaining Work

### Phase 1 — Fix Domain/Corpus Mismatch in Prompt Construction (High Priority)

**Current Bug:**

The query endpoint correctly passes the collection to retrieval, but prompt construction still infers domain from `settings.chroma_collection_name` (a global setting).

**Files:**
- [`backend/app/rag/generation.py`](../backend/app/rag/generation.py) - Uses global setting for domain
- [`backend/app/main.py`](../backend/app/main.py) - Should thread collection through to generation

**Consequence:**
When using multi-collection query, retrieval is correct but prompt construction doesn't know which collection(s) were used.

**Solution:**
1. Add `collection` or `corpus` parameter to `generate_answer()` function
2. Map collection to domain dynamically:
   - `fastapi_docs` → `"fastapi"`
   - `at_docs` → `"asset_score"` or `"general"`
   - Multiple collections → `"general"` or domain-neutral prompts
3. Remove dependency on `settings.chroma_collection_name` for domain inference

**Impact:** Medium - Multi-collection query works well, but prompts could be more domain-aware

---

### Phase 4 — Normalize Metadata (Low Priority / Future)

**Current State:**
Collections have different metadata schemas:
- `fastapi_docs`: Basic metadata (source, filename, chunk_id, etc.)
- `at_docs`: Similar basic metadata

**Potential Enhancement:**
Enrich both collections with normalized metadata:
- `corpus`: `"fastapi"` | `"at_docs"`
- `doc_family`: `"markdown_docs"` | `"api_docs"` | `"how_to"`
- `framework`: `"fastapi"` | `"asset_score"` | etc.
- `section_title`: Extracted from headings
- `source_url`: If available

**Benefit:** Better filtering, source display, and future reranking capabilities

---

## Architecture

### Clean Separation of Concerns

```
API Layer (main.py - 522 lines)
    ├── Routing and validation
    └── Delegates to business logic

Business Logic Layer (app/rag/)
    ├── collections.py (52 lines)      → Collection discovery
    ├── multi_retrieval.py (171 lines) → Multi-collection orchestration
    ├── retrieval.py                   → Single-collection retrieval
    ├── generation.py                  → Answer generation
    ├── agent_graph.py                 → Graph pipeline
    └── hybrid_retrieval.py            → Hybrid search (BM25 + semantic)
```

### Multi-Collection Query Flow

```
User Query (no collection specified)
    ↓
MultiCollectionRetriever.query_all()
    ↓
For each collection:
    Graph.run(query, collection)
    ↓
Merge results by relevance score
    ↓
Return top-K documents
    ↓
Generate answer from merged documents
```

**Key Design:** Graph remains simple and unchanged. Multi-collection is an orchestration layer that calls the graph multiple times.

---

## Backend Architecture Options (Future Consideration)

### Option 1: Unified Collection with Shared Metadata Schema

Merge all corpora into a single collection with normalized metadata.

**Pros:** Single retrieval path, simpler routing
**Cons:** Requires re-ingestion, potential cross-corpus noise

### Option 2: Keep Separate Collections ✅ Current Implementation

Preserve separate collections with multi-collection orchestration layer.

**Pros:**
- Low risk, no re-ingestion needed
- Clear separation for evaluation
- Can add more collections easily

**Cons:**
- Multiple retrievals per query (mitigated by parallelization potential)
- Slightly higher latency

**Verdict:** Option 2 is working well. No immediate need to change.

---

## Testing & Validation

**Collections API:**
```bash
curl http://localhost:8000/api/v1/collections
# Returns: {"collections": [{"name": "fastapi_docs", "count": 165}, ...]}
```

**Multi-Collection Query:**
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -d '{"query": "What is FastAPI?", "top_k": 3}'
# Queries both collections, returns best matches
```

**Test Cases:**
- ✅ "What is FastAPI?" → Returns FastAPI docs
- ✅ "How to add customizable enum field?" → Returns AT docs
- ✅ "How to set up Docker?" → Merges relevant results from both

---

## Files Affected

| File | Status | Lines | Description |
|------|--------|-------|-------------|
| `backend/app/main.py` | ✅ Refactored | 522 | Thin API layer |
| `backend/app/rag/collections.py` | ✅ New | 52 | Collection management |
| `backend/app/rag/multi_retrieval.py` | ✅ New | 171 | Multi-collection orchestration |
| `frontend/src/App.jsx` | ✅ Updated | - | Removed selector, added guide |
| `frontend/src/components/DocumentationGuide.jsx` | ✅ New | 99 | Collapsible collection guide |
| `backend/app/rag/generation.py` | 🔴 Needs update | - | Fix domain inference |
| `backend/app/models.py` | ✅ Updated | - | Added collection models |

---

## Summary

**Completed (Phase 2 & 3):**
- Collections API for dynamic discovery
- Multi-collection query with automatic routing
- Clean architecture refactor (API layer separated from business logic)
- Frontend visual guide instead of manual selector

**Remaining (Phase 1):**
- Fix domain mismatch in prompt construction
- Pass collection context through to generation layer
- Make prompts collection-aware or domain-neutral

**Future (Phase 4):**
- Normalize metadata schemas across collections
- Enhanced filtering and source display

---

**Last Updated:** March 22, 2026 - Phase 2 & 3 implementation complete
