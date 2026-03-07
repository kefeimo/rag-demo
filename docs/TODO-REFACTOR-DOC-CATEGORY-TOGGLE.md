# TODO: Refactor Doc Category Toggle

## Background

The current implementation separates the FastAPI and VCC corpora primarily by **collection name** (`fastapi_docs` vs `vcc_docs`), not by embedding strategy. Both corpora share the same embedding model (`sentence-transformers/all-MiniLM-L6-v2`). The separation is mostly a **metadata and schema concern**, not an embedding concern.

### Current Metadata Richness (Asymmetry)

| Field | FastAPI docs | VCC docs |
|---|---|---|
| `source` | ✅ | ✅ |
| `filename` / `file_path` | ✅ | ✅ |
| `file_size` | ✅ | — |
| `chunk_id`, `start_char`, `end_char` | ✅ | — |
| `repo_name` | — | ✅ |
| `file_extension`, `commit_hash` | — | ✅ |
| `doc_type`, `audience` | — | ✅ |
| `api_type`, `api_name`, `package` | — | ✅ (code-docs) |
| `component`, `source_language` | — | ✅ (code-docs) |
| `generation_method` | — | ✅ (code-docs) |

FastAPI metadata is significantly thinner than VCC metadata. This gap is a refactor target.

---

## Known Bug: Domain/Corpus Mismatch in Prompt Construction

**This is the highest-priority correctness fix.**

- The query endpoint correctly selects the collection from the request (falling back to the default setting) and passes it into retrieval. ([`backend/app/main.py`](../backend/app/main.py))
- However, prompt construction infers the "domain" from `settings.chroma_collection_name` — a **global setting** — not from the actual request collection. ([`backend/app/rag/generation.py`](../backend/app/rag/generation.py))

**Consequence:** If the default env collection is `vcc_docs` and the user queries `fastapi_docs`, retrieval uses the correct collection while prompt construction still thinks it is in the VCC domain (or vice versa). Retrieval and generation are out of sync.

---

## Problem: The Toggle Is Doing Too Many Jobs

The current frontend toggle in [`frontend/src/App.jsx`](../frontend/src/App.jsx) simultaneously acts as:

1. **Corpus selector** — switches between `fastapi_docs` and `vcc_docs`
2. **App identity switch** — changes the page title and subtitle
3. **UX mode switch** — changes placeholder text and example queries
4. **Evaluation control** — implicitly drives which collection is tested

This is why the toggle feels like two separate apps stapled together rather than a scope filter within one product.

---

## Recommended Refactor Plan

### Phase 1 — Fix Correctness (High Priority) 🔴

**File:** [`backend/app/rag/generation.py`](../backend/app/rag/generation.py)

Pass the **actual request collection or corpus** into prompt generation, instead of inferring domain from `settings.chroma_collection_name`.

- Add a `corpus` or `collection_name` parameter to the prompt-construction function
- Derive domain (`fastapi` | `vcc` | `general`) from that parameter at request time
- Remove the global settings dependency for domain selection

**File:** [`backend/app/main.py`](../backend/app/main.py)

- Ensure the resolved `collection_name` from the request is threaded through to `generation.py`, not just to retrieval

---

### Phase 2 — Stop Changing the App Title (UX Fix) 🟡

**File:** [`frontend/src/App.jsx`](../frontend/src/App.jsx)

- Keep one **stable app title**, e.g., `"Documentation RAG Assistant"`
- Rename the toggle label from something that implies identity switching to something that implies scope, e.g.:
  - `Search scope`
  - `Documentation scope`
  - `Knowledge base filter`
- The title flip is what makes the toggle feel jarring; removing it makes the product feel cohesive

---

### Phase 3 — Add a Neutral Default Scope (UX Improvement) 🟡

**File:** [`frontend/src/App.jsx`](../frontend/src/App.jsx)

Change the toggle from a binary `FastAPI ↔ VCC` switch to a three-option scope selector:

| Option | Collection / Behavior |
|---|---|
| All docs *(default)* | Search both corpora (auto-route or merged) |
| FastAPI only | Filter to `fastapi_docs` |
| VCC only | Filter to `vcc_docs` |

This answers the UX concern without losing evaluation isolation. Normal review/demo usage defaults to `All docs`; targeted evaluation scripts can still explicitly request a corpus.

---

### Phase 4 — Normalize FastAPI Metadata 🟢

**File:** [`backend/app/rag/ingestion.py`](../backend/app/rag/ingestion.py)

Enrich FastAPI doc metadata to match the spirit of the VCC side, adding:

| Field | Value |
|---|---|
| `corpus` | `fastapi` |
| `doc_family` | `markdown_docs` |
| `framework` | `fastapi` |
| `section_title` | extracted from heading, if available |
| `url_path` / `source_url` | if available |

This enables metadata-driven filtering and better source display in the frontend, and puts both corpora on equal footing for future reranking or routing.

---

## Backend Architecture Options (Longer Term)

### Option 1: Unified Collection with Shared Metadata Schema

Merge both corpora into a single collection with a normalized metadata schema:

```
corpus:          fastapi | vcc
doc_family:      repo_docs | code_docs | api_docs | markdown_docs
doc_type:        (existing values)
api_type:        (vcc-specific)
api_name:        (vcc-specific)
package:         (vcc-specific)
source_language: (vcc-specific)
framework:       fastapi | (empty for vcc)
```

**Pros:** Single retrieval path, simpler routing, easier `All docs` default  
**Cons:** Requires re-ingestion of both corpora; higher risk of cross-corpus noise

### Option 2: Keep Separate Collections, Add Routing + Optional Scope Filter ✅ Recommended next step

Preserve the existing `fastapi_docs` / `vcc_docs` split (low risk, no re-ingestion needed) and:

- Default UX = `All docs` (auto-route or fan-out to both collections)
- Advanced option = `FastAPI only` / `VCC only` scope filters
- Evaluation scripts continue to run corpus-specific tests cleanly

**Option 2 is the better immediate next step** because it preserves the existing evaluation separation while eliminating the weirdness for normal users.

---

## Files Affected

| File | Change |
|---|---|
| [`backend/app/rag/generation.py`](../backend/app/rag/generation.py) | Pass corpus/collection into prompt construction; remove global settings dependency |
| [`backend/app/main.py`](../backend/app/main.py) | Thread resolved `collection_name` through to generation, not just retrieval |
| [`frontend/src/App.jsx`](../frontend/src/App.jsx) | Fix title, redesign toggle as scope selector, add `All docs` default |
| [`backend/app/rag/ingestion.py`](../backend/app/rag/ingestion.py) | Enrich FastAPI metadata schema |

---

## Interview Framing

> I originally used the toggle to keep FastAPI and VCC evaluation isolated, because the corpora have different structures and different metadata richness. In the current implementation they are separated mostly by collection, not by embedding strategy. The next refactor would be to make the user-facing control a search scope filter instead of switching the app identity, and to pass corpus/domain explicitly through the backend so prompt construction and retrieval stay aligned. Longer term I'd either unify the corpora under a shared metadata schema or keep separate indexes with automatic routing plus optional corpus filters.

---

## Summary of Priorities

| Phase | Area | Priority |
|---|---|---|
| Phase 1 | Fix domain/corpus mismatch in prompt construction | 🔴 High (correctness bug) |
| Phase 2 | Stop changing app title on toggle | 🟡 Medium (UX) |
| Phase 3 | Add neutral `All docs` default scope | 🟡 Medium (UX) |
| Phase 4 | Normalize FastAPI metadata | 🟢 Low (future-proofing) |
