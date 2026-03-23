# Multi-Collection Architecture & Remaining Work

## Status Overview

✅ **Phase 1 Complete** - Domain/corpus mismatch in prompt construction FIXED
✅ **Phase 2 Complete** - Collections API endpoint
✅ **Phase 3 Complete** - Multi-collection query with automatic routing
🟢 **Phase 4 Future** - Metadata normalization

---

## Background

The system now supports multiple documentation collections (`fastapi_docs`, `at_docs`) with automatic query routing. Collections are separated by **collection name**, not by embedding strategy. Both use the same embedding model (`sentence-transformers/all-MiniLM-L6-v2`).

### Current Collections

| Collection | Documents | Description |
|------------|-----------|-------------|
| `fastapi_docs` | 165 | FastAPI framework documentation |
| `at_docs` | 2408 | Asset Score / Audit Template documentation |
| `tspr_docs` | ~200 | HVAC System Performance (HSP) documentation |

---

## ✅ Completed Work

### Phase 1 — Fix Domain/Corpus Mismatch (Complete)

**Problem Fixed:**
Prompt generation was using `settings.chroma_collection_name` (global setting) to infer domain, causing retrieval and generation to be out of sync.

**Implementation:**
- `infer_domain_from_collections()` - Dynamically determine domain from actual collections used
- Updated `construct_prompt()` and `generate_answer()` to accept collections parameter
- Threaded collection context through `agent_graph.py` and `multi_retrieval.py`

**Domain Mapping:**
- `["fastapi_docs"]` → `"fastapi"` (FastAPI-specific prompts)
- `["at_docs"]` → `"asset_score"` (Asset Score/Audit Template prompts)
- `["tspr_docs"]` → `"tspr"` (HVAC System Performance prompts)
- Multiple collections → `"general"` (domain-neutral prompts)

**New Domain Configuration:**
Added `"asset_score"` domain config with:
- Docker Compose development guidance
- Customizable enum fields context
- Rails application specifics
- Energy calculations and database models

**Files Modified:**
- `backend/app/rag/generation.py` - Domain inference and new asset_score config
- `backend/app/rag/multi_retrieval.py` - Pass collections to generation
- `backend/app/rag/agent_graph.py` - Thread collection through to generation

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
- Example questions target specific collections for accurate results
- Collection name displayed in source metadata
- App title changed to "Documentation RAG Assistant" (neutral, not corpus-specific)

**Files Modified:**
- `backend/app/main.py` - Refactored to thin API layer (522 lines, down from ~650)
- `backend/app/rag/multi_retrieval.py` - New module
- `backend/app/rag/collections.py` - New module
- `backend/app/rag/ingestion.py` - Added collection metadata and unique ID generation
- `frontend/src/App.jsx` - Collection-aware query routing from example questions
- `frontend/src/components/DocumentationGuide.jsx` - Collection-specific example questions
- `frontend/src/components/SourceCard.jsx` - Display collection metadata

---

## ✅ Recent Enhancements (March 2026)

### Collection-Specific Query Routing

**Implementation:**
- `DocumentationGuide` component passes `{question, collection}` object
- `App.jsx` uses `selectedCollection` state to target specific collections
- Example questions now query their specific collection instead of all collections
- Prevents cross-corpus contamination (e.g., AT questions returning FastAPI results)

### Collection Metadata in Sources

**Implementation:**
- Backend adds `collection` field to metadata during ingestion
- `SourceCard` component displays collection name before document path
- Unique chunk IDs using format: `{collection}_{source}_{chunk_id}`
- Fixes duplicate chunk IDs when force re-ingesting

**Files Modified:**
- `backend/app/rag/ingestion.py:294` - Add collection to metadata, generate unique IDs
- `frontend/src/components/SourceCard.jsx:54-61` - Display collection field
- `frontend/src/components/DocumentationGuide.jsx:6-37` - Add collection_name to each collection
- `frontend/src/App.jsx:18-29` - Add selectedCollection state and routing

### TSPR Collection Support

**Implementation:**
- Added `tspr_docs` collection with HVAC System Performance documentation
- Added "tspr" domain configuration in `generation.py`
- 3 example questions covering local setup, simulation caching, and monitoring
- `docker-compose-dev.yml` auto-ingests all 3 collections on startup

---

## 🟢 Future Work

### Phase 4 — Extended Metadata (Low Priority)

**Potential Enhancement:**
Further enrich metadata with:
- `doc_family`: `"markdown_docs"` | `"api_docs"` | `"how_to"`
- `framework`: `"fastapi"` | `"asset_score"` | `"openstudio"`
- `section_title`: Extracted from headings
- `source_url`: If available

**Benefit:** Advanced filtering and reranking capabilities

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

**Completed (All Core Phases):**
- ✅ Phase 1: Domain/corpus mismatch fixed - prompts now collection-aware
- ✅ Phase 2: Collections API for dynamic discovery
- ✅ Phase 3: Multi-collection query with automatic routing
- ✅ Clean architecture refactor (API layer separated from business logic)
- ✅ Frontend visual guide instead of manual selector

**Future (Phase 4):**
- Normalize metadata schemas across collections
- Enhanced filtering and source display

---

**Last Updated:** March 22, 2026
- Phase 1, 2 & 3 implementation complete
- Collection-specific query routing from frontend
- Collection metadata display in sources
- TSPR collection support added
- Unique chunk ID generation fix
