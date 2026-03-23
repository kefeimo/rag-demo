# TODO — Extract RAG Pipeline Logic from main.py

**Status:** 📋 PLANNED  
**Priority:** Medium (tech debt, no functional blocker)  
**Estimated effort:** 2–3 hours

---

## Problem

The `query_rag()` endpoint in `main.py` contains ~80 lines of RAG orchestration logic that doesn't belong in a route handler:

```python
@app.post("/api/v1/query", ...)
async def query_rag(request: QueryRequest):
    # ❌ RAG strategy logic in the HTTP layer
    retriever = Retriever(collection_name=collection)
    retrieval_result = retriever.retrieve(...)
    
    # ❌ Business rules in the HTTP layer
    if retrieval_result.get("relevance_score") < 0.65 and hybrid_retriever:
        hybrid_result = hybrid_retriever.search(...)
        if hybrid_result["relevance_score"] > retrieval_result["relevance_score"]:
            retrieval_result = hybrid_result
    
    # ❌ Rejection/validation logic in the HTTP layer
    is_relevant, relevance_msg = temp_retriever.check_relevance(...)
    if not documents or not is_relevant:
        help_text = get_help_text_for_collection()
        return QueryResponse(answer=f"I don't have enough information...")
    
    # ❌ LLM generation in the HTTP layer
    llm_client = get_llm_client()
    answer = generate_answer(query, documents, llm_client)
    sources = extract_sources(documents)
    return QueryResponse(...)
```

**What should be in `main.py`:** HTTP concerns — request validation, response serialization, error → HTTPException mapping.

**What should NOT be in `main.py`:** Retrieval strategy selection, relevance gating, LLM orchestration, collection-specific help text.

---

## Why This Matters

### 1. Code duplication
`evaluation/run_ragas_stage1_query.py` **duplicates this logic via HTTP calls**:

```python
def run_rag_query(query: str, api_url: str = "http://localhost:8000/api/v1/query") -> Dict:
    response = requests.post(api_url, json={"query": query})
    return response.json()
```

This forces the evaluation pipeline to:
- Start the FastAPI server (or hit a deployed endpoint)
- Make HTTP round-trips for every test query
- Parse JSON → dict → JSON on both sides

If the pipeline logic were extracted to `app/rag/pipeline.py`, the evaluation script could import and call it directly:

```python
from app.rag.pipeline import RAGPipeline

pipeline = RAGPipeline(collection_name="fastapi_docs")
result = pipeline.query(query="What is BarChart?", top_k=5)
```

**Benefits:**
- ✅ No server required for evaluation runs
- ✅ No HTTP overhead (10–50 ms per query saved)
- ✅ Direct access to internal metrics (BM25 scores, semantic weights, etc.)
- ✅ Same logic path for API and evaluation → no drift

### 2. Testability
The RAG orchestration logic is currently **untestable without FastAPI**. To unit-test the "try semantic, fall back to hybrid" strategy, you must:
- Spin up the full FastAPI app with lifespan handlers
- Mock ChromaDB, LLM client, and retriever instances
- Send HTTP requests via `TestClient`

With extraction, you can unit-test `RAGPipeline.query()` in isolation:

```python
def test_hybrid_fallback_when_semantic_low_relevance(mock_chroma, mock_llm):
    pipeline = RAGPipeline(collection_name="test")
    result = pipeline.query(query="What is uvicorn?", top_k=3)
    
    assert result.retrieval_strategy == "hybrid"
    assert result.relevance_score > 0.65
```

### 3. Future extensibility
Any new endpoint that needs RAG logic will duplicate `main.py` code:
- `/api/v1/query/stream` (streaming responses)
- `/api/v1/explain` (return retrieval strategy reasoning)
- `/api/v1/compare` (compare semantic vs hybrid side-by-side)

With a `RAGPipeline` class, these all call the same `.query()` method.

---

## Proposed Structure

### New file: `backend/app/rag/pipeline.py`

```python
class RAGPipeline:
    """
    Orchestrates the full RAG flow: retrieval strategy selection,
    relevance gating, LLM generation, and source formatting.
    """
    
    def __init__(
        self,
        collection_name: str,
        semantic_retriever: Retriever = None,
        hybrid_retriever: HybridRetriever = None,
        llm_client = None,
        relevance_threshold: float = 0.65,
    ):
        self.collection_name = collection_name
        self.semantic_retriever = semantic_retriever or Retriever(collection_name)
        self.hybrid_retriever = hybrid_retriever  # optional
        self.llm_client = llm_client or get_llm_client()
        self.relevance_threshold = relevance_threshold
    
    def query(
        self,
        query: str,
        top_k: int = 5,
    ) -> RAGResult:
        """
        Run the full RAG pipeline:
        1. Try semantic-only retrieval
        2. If relevance < threshold and hybrid available, try hybrid
        3. Compare and pick best result
        4. Check relevance gate
        5. Generate answer or rejection message
        
        Returns:
            RAGResult with answer, sources, relevance_score, metadata
        """
        # Strategy: semantic-only first
        semantic_result = self.semantic_retriever.retrieve(query, top_k)
        
        # If low relevance and hybrid available, try it
        if semantic_result["relevance_score"] < self.relevance_threshold and self.hybrid_retriever:
            hybrid_result = self.hybrid_retriever.search(query, top_k)
            
            # Use whichever has higher relevance
            if hybrid_result["relevance_score"] > semantic_result["relevance_score"]:
                retrieval_result = hybrid_result
                strategy_used = "hybrid"
            else:
                retrieval_result = semantic_result
                strategy_used = "semantic"
        else:
            retrieval_result = semantic_result
            strategy_used = "semantic"
        
        # Check relevance gate
        is_relevant = retrieval_result["relevance_score"] >= self.relevance_threshold
        
        if not is_relevant:
            # Rejection path
            return RAGResult(
                query=query,
                answer=self._get_rejection_message(),
                sources=[],
                relevance_score=retrieval_result["relevance_score"],
                strategy_used=strategy_used,
                model=settings.llm_provider,
            )
        
        # Generation path
        documents = retrieval_result["documents"]
        answer = generate_answer(query, documents, self.llm_client)
        sources = extract_sources(documents)
        
        return RAGResult(
            query=query,
            answer=answer,
            sources=sources,
            relevance_score=retrieval_result["relevance_score"],
            strategy_used=strategy_used,
            model=settings.llm_provider,
        )
    
    def _get_rejection_message(self) -> str:
        """Collection-specific help text for rejected queries."""
        collection = self.collection_name.lower()
        if "component" in collection or "fastapi" in collection or "chart" in collection:
            return "I don't have enough information... Please try asking about specific FastAPI features..."
        elif "fastapi" in collection:
            return "I don't have enough information... Please try asking about FastAPI features."
        else:
            return "I don't have enough information... Please try rephrasing your question."
```

### New dataclass: `app/models.py`

```python
@dataclass
class RAGResult:
    """Internal result from RAGPipeline (before HTTP serialization)."""
    query: str
    answer: str
    sources: List[Source]
    relevance_score: float
    strategy_used: str  # "semantic" or "hybrid"
    model: str
    response_time: Optional[float] = None
```

### Simplified `main.py`

```python
# Global pipeline instances (initialized in lifespan)
rag_pipelines: dict[str, RAGPipeline] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize RAG pipelines for all known collections."""
    for cname in KNOWN_COLLECTIONS:
        try:
            semantic = Retriever(collection_name=cname)
            hybrid = HybridRetriever(collection_name=cname, auto_classify=True)
            rag_pipelines[cname] = RAGPipeline(
                collection_name=cname,
                semantic_retriever=semantic,
                hybrid_retriever=hybrid,
            )
            logger.info(f"✓ RAG pipeline ready: {cname}")
        except Exception as e:
            logger.warning(f"Could not init pipeline for '{cname}': {e}")
    yield

@app.post("/api/v1/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Query the RAG system with hybrid search (semantic + keyword)"""
    import time
    start_time = time.time()
    
    logger.info(f"Query received: {request.query}")
    collection = request.collection or settings.chroma_collection_name
    
    try:
        # Get pipeline for this collection
        pipeline = rag_pipelines.get(collection)
        if not pipeline:
            raise HTTPException(status_code=404, detail=f"Collection '{collection}' not found")
        
        # Run pipeline
        result = pipeline.query(query=request.query, top_k=request.top_k)
        
        # Convert to HTTP response
        response_time = time.time() - start_time
        return QueryResponse(
            query=result.query,
            answer=result.answer,
            sources=result.sources,
            relevance_score=result.relevance_score,
            model=result.model,
            response_time=response_time,
            api_version=__version__,
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
```

**Line count:** `query_rag` goes from ~90 lines → ~25 lines (HTTP concerns only).

---

## Migration Plan

### Phase 1: Extract without breaking changes
1. Create `backend/app/rag/pipeline.py` with `RAGPipeline` class
2. Add `RAGResult` dataclass to `models.py`
3. Update `main.py` to use `RAGPipeline` internally (no API changes)
4. Run existing tests (`backend/tests/`, `evaluation/` via HTTP)
5. Verify no regressions

### Phase 2: Update evaluation scripts
1. Update `evaluation/run_ragas_stage1_query.py` to import `RAGPipeline` directly
2. Remove `run_rag_query()` HTTP call, replace with `pipeline.query()`
3. Measure performance improvement (expect 10–50 ms saved per query)
4. Update `evaluation/README.md` with new usage

### Phase 3 (optional): Add new endpoints
- `/api/v1/query/stream` — streaming responses using the same `RAGPipeline`
- `/api/v1/explain` — return retrieval strategy reasoning (`strategy_used`, BM25 scores, etc.)

---

## Testing Strategy

### Unit tests (`backend/tests/test_pipeline.py`)
```python
def test_semantic_only_when_high_relevance(mock_chroma, mock_llm):
    """If semantic relevance >= 0.65, don't call hybrid."""
    pipeline = RAGPipeline(collection_name="test")
    result = pipeline.query("What is FastAPI?", top_k=3)
    
    assert result.strategy_used == "semantic"
    assert result.relevance_score >= 0.65

def test_hybrid_fallback_when_low_relevance(mock_chroma, mock_llm):
    """If semantic relevance < 0.65, try hybrid."""
    pipeline = RAGPipeline(collection_name="test")
    result = pipeline.query("What is uvicorn?", top_k=3)
    
    assert result.strategy_used == "hybrid"

def test_rejection_when_relevance_below_threshold(mock_chroma):
    """If both strategies < 0.65, return rejection message."""
    pipeline = RAGPipeline(collection_name="test")
    result = pipeline.query("asdfasdf", top_k=3)
    
    assert "I don't have enough information" in result.answer
    assert result.sources == []
```

### Integration tests
- Existing `backend/tests/test_rag_pipeline.py` should pass unchanged (HTTP layer still works)
- `evaluation/run_ragas_stage1_query.py` output should be identical before/after

---

## Benefits Summary

| Before | After |
|---|---|
| RAG logic in HTTP handler | RAG logic in reusable `RAGPipeline` class |
| Evaluation scripts call API via HTTP | Evaluation scripts import pipeline directly |
| 90-line route handler | 25-line route handler |
| Untestable without FastAPI | Unit-testable in isolation |
| Code duplication risk for new endpoints | Single source of truth |

---

## Related Files

- `backend/app/main.py` — current location of pipeline logic (lines 110–230)
- `evaluation/run_ragas_stage1_query.py` — duplicates logic via HTTP (line 26)
- `backend/app/rag/retrieval.py` — semantic search component
- `backend/app/rag/hybrid_retrieval.py` — BM25 + semantic component
- `backend/app/rag/generation.py` — LLM generation component
- `backend/tests/test_rag_pipeline.py` — existing integration tests

---

## Decision Log

**Date:** March 9, 2026  
**Decision:** Deferred to future iteration. No immediate functional blocker, but justified by:
1. Evaluation script (`run_ragas_stage1_query.py`) already reuses the logic via HTTP
2. 90-line route handler violates single-responsibility principle
3. Testability improvement for RAG strategy logic

**Estimated ROI:**
- ~50% reduction in route handler complexity
- ~10–50 ms per evaluation query saved (×20 queries = 200–1000 ms total)
- New endpoints (streaming, explain) can reuse pipeline immediately
