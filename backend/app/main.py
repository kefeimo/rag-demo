"""
FastAPI Main Application
RAG System API with health check and query endpoints
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from contextlib import asynccontextmanager
from typing import Optional
import json
import logging

from app.config import settings
from app.models import (
    HealthResponse,
    QueryRequest,
    QueryResponse,
    IngestRequest,
    IngestResponse,
    Source,
    CollectionsResponse,
    CollectionInfo
)
from app import __version__
from app.rag.ingestion import ingest_documents
from app.rag.hybrid_retrieval import HybridRetriever
from app.rag.agent_graph import HYBRID_GATE_THRESHOLD, LangGraphRAGPipeline
from app.rag.collections import list_all_collections
from app.rag.multi_retrieval import MultiCollectionRetriever

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_help_text_for_collection() -> str:
    """
    Get context-appropriate help text based on the current collection name

    Returns:
        Help text string with relevant suggestions
    """
    collection_name = settings.chroma_collection_name.lower()

    if "fastapi" in collection_name:
        return "Please try rephrasing your question or ask about FastAPI features."
    else:
        return "Please try rephrasing your question with more specific terms."


# Known collections — extend this list if you add more
KNOWN_COLLECTIONS = ["fastapi_docs", "at_docs", "tspr_docs"]

# Per-collection HybridRetriever cache (building BM25 index is expensive)
hybrid_retrievers: dict = {}

# Minimal LangGraph orchestration wrapper around current RAG flow
rag_pipeline = LangGraphRAGPipeline(hybrid_retrievers=hybrid_retrievers)

# Multi-collection retriever (initialized in lifespan)
multi_retriever: Optional[MultiCollectionRetriever] = None

# Human-readable labels for each graph node — used by the SSE streaming endpoint
_NODE_THINKING: dict[str, str] = {
    "planner": "Planning retrieval strategy",
    "semantic_retrieve": "Searching vector index",
    "hybrid_retrieve": "Running hybrid search",
    "evaluate": "Evaluating document relevance",
    "generate": "Generating answer",
}

_NODE_THINKING_START: dict[str, str] = {
    "planner": "Inspecting query shape and collection capabilities to choose retrieval flow.",
    "semantic_retrieve": "Running semantic similarity search over embedded documentation chunks.",
    "hybrid_retrieve": "Combining semantic similarity and keyword/BM25 matching to improve recall.",
    "evaluate": "Checking document support strength against the configured relevance threshold.",
    "generate": "Synthesizing a grounded answer from selected evidence and source snippets.",
}


def _summarize_node_thought(node_name: str, output: dict, state: dict) -> str:
    """Create concise, user-visible reasoning summary for a completed graph node."""
    if node_name == "planner":
        query_type = output.get("query_type", "unknown")
        strategy = output.get("planned_strategy", "unknown").replace("_", "-")
        return f"Classified query as {query_type}; selected {strategy} retrieval path."

    if node_name in {"semantic_retrieve", "hybrid_retrieve"}:
        method = output.get("retrieval_method") or state.get("retrieval_method") or "retrieval"
        docs = output.get("documents", state.get("documents", [])) or []
        score = output.get("relevance_score", state.get("relevance_score", 0.0))
        if output.get("error"):
            return f"{method.capitalize()} encountered an error; proceeding with available fallback behavior."
        return f"{method.capitalize()} found {len(docs)} candidate chunks with relevance {float(score):.2f}."

    if node_name == "evaluate":
        score = output.get("relevance_score", state.get("relevance_score", 0.0))
        is_relevant = output.get("is_relevant", state.get("is_relevant", False))
        decision = "sufficient support; proceed to answer generation" if is_relevant else "support too weak; return insufficient-context response"
        return f"Evidence score {float(score):.2f} vs threshold {settings.relevance_threshold:.2f}; {decision}."

    if node_name == "generate":
        answer = output.get("answer", state.get("answer", ""))
        sources = output.get("sources", state.get("sources", [])) or []
        return f"Generated grounded response ({len(str(answer))} chars) using {len(sources)} source snippet(s)."

    return "Completed pipeline stage."


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize hybrid retrievers and multi-collection retriever on startup"""
    global multi_retriever

    logger.info("Initializing hybrid retrievers for all collections...")
    for cname in KNOWN_COLLECTIONS:
        try:
            hr = HybridRetriever(collection_name=cname, auto_classify=True)
            hybrid_retrievers[cname] = hr
            logger.info(f"✓ Hybrid retriever ready: {cname}")
        except Exception as e:
            logger.warning(f"Could not init hybrid retriever for '{cname}': {e} (collection may not exist yet)")

    # Initialize multi-collection retriever
    multi_retriever = MultiCollectionRetriever(rag_pipeline, KNOWN_COLLECTIONS)
    logger.info("✓ Multi-collection retriever ready")

    yield
    # shutdown — nothing to release currently


# Create FastAPI app
app = FastAPI(
    title="RAG System API",
    description="Retrieval-Augmented Generation system for FastAPI documentation",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Returns service status and version
    """
    logger.info("Health check requested")
    return HealthResponse(
        status="healthy",
        version=__version__,
        model=settings.llm_provider
    )


@app.get("/api/v1/collections", response_model=CollectionsResponse, tags=["Admin"])
async def list_collections():
    """
    List all available ChromaDB collections with document counts

    Returns:
        CollectionsResponse with list of collections and their metadata
    """
    try:
        collections_data = list_all_collections()
        collection_info = [
            CollectionInfo(name=col["name"], count=col["count"])
            for col in collections_data
        ]
        return CollectionsResponse(collections=collection_info)

    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing collections: {str(e)}")


async def query_all_collections(request: QueryRequest, start_time: float) -> QueryResponse:
    """
    Query all known collections and merge results by relevance score.

    Delegates to MultiCollectionRetriever for the actual multi-collection logic.

    Args:
        request: Query request
        start_time: Request start time for response_time calculation

    Returns:
        QueryResponse with merged results from all collections
    """
    import time

    # Delegate to multi-collection retriever
    result = multi_retriever.query_all(query=request.query, top_k=request.top_k)

    # Handle error case
    if result["error"] or not result["is_relevant"]:
        help_text = get_help_text_for_collection()
        response_time = time.time() - start_time
        return QueryResponse(
            query=request.query,
            answer=f"I don't have enough information to answer that question based on the provided documentation. {help_text}",
            sources=result["sources"],
            relevance_score=result["relevance_score"],
            model=settings.llm_provider,
            response_time=response_time,
            api_version=__version__,
        )

    # Success case
    response_time = time.time() - start_time
    return QueryResponse(
        query=request.query,
        answer=result["answer"],
        sources=result["sources"],
        relevance_score=result["relevance_score"],
        model=settings.llm_provider,
        response_time=response_time,
        api_version=__version__,
    )


@app.post("/api/v1/query", response_model=QueryResponse, tags=["RAG"])
async def query_rag(request: QueryRequest):
    """
    Query the RAG system with hybrid search (semantic + keyword)
    
    Args:
        request: Query request with user question
        
    Returns:
        QueryResponse with answer, sources, relevance_score, and metadata
    """
    import time
    start_time = time.time()
    
    logger.info(f"Query received: {request.query}")

    # Resolve collection: request override → env default → query all
    collection = request.collection or None  # None means query all collections

    # If no specific collection requested, query all known collections and merge results
    if collection is None:
        logger.info(f"Querying all collections: {KNOWN_COLLECTIONS}")
        return await query_all_collections(request, start_time)

    logger.info(f"Using collection: {collection}")

    try:
        pipeline_state = rag_pipeline.run(
            query=request.query,
            top_k=request.top_k,
            collection=collection,
        )

        logger.info(
            "Orchestration trace: strategy=%s, query_type=%s, path=%s",
            pipeline_state.get("planned_strategy", "unknown"),
            pipeline_state.get("query_type", "unknown"),
            " -> ".join(pipeline_state.get("decision_path", [])),
        )

        # Check for retrieval/generation errors
        if pipeline_state.get("error"):
            logger.error(f"RAG pipeline error: {pipeline_state['error']}")
            response_time = time.time() - start_time
            return QueryResponse(
                query=request.query,
                answer=f"Error retrieving documents: {pipeline_state['error']}. Please ensure documents have been ingested first.",
                sources=[],
                relevance_score=0.0,
                model=settings.llm_provider,
                response_time=response_time,
                api_version=__version__,
            )

        documents = pipeline_state.get("documents", [])
        overall_relevance = pipeline_state.get("relevance_score", 0.0)
        
        # Debug: Log document details
        logger.info(f"Retrieved {len(documents)} documents with relevance score {overall_relevance:.3f}")
        if documents:
            logger.info(f"First document keys: {list(documents[0].keys())}")
            logger.info(f"First document content length: {len(documents[0].get('content', ''))} chars")
        
        is_relevant = pipeline_state.get("is_relevant", False)
        logger.info(f"Relevance check: is_relevant={is_relevant}, score={overall_relevance:.3f}")
        
        if not documents or not is_relevant:
            logger.warning(f"Rejecting query - documents: {len(documents)}, is_relevant: {is_relevant}, relevance_score: {overall_relevance:.3f}")
            help_text = get_help_text_for_collection()
            response_time = time.time() - start_time
            return QueryResponse(
                query=request.query,
                answer=f"I don't have enough information to answer that question based on the provided documentation. {help_text}",
                sources=[],
                relevance_score=overall_relevance,
                model=settings.llm_provider,
                response_time=response_time,
                api_version=__version__,
            )
        
        answer = pipeline_state.get("answer", "")
        sources = pipeline_state.get("sources", [])
        
        response_time = time.time() - start_time
        logger.info(f"Query completed successfully (relevance_score: {overall_relevance:.3f}, time: {response_time:.2f}s)")
        return QueryResponse(
            query=request.query,
            answer=answer,
            sources=sources,
            relevance_score=overall_relevance,
            model=settings.llm_provider,
            response_time=response_time,
            api_version=__version__,
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.post("/api/v1/query/stream", tags=["RAG"])
async def query_rag_stream(request: QueryRequest):
    """
    Streaming SSE query endpoint.

    Emits server-sent events as LangGraph nodes run so the frontend can show a
    live "thinking" panel.  Each event is a JSON object:
      {"type": "thinking", "step": "<human-readable label>"}   — one per node
      {"type": "result",   "data": <QueryResponse as dict>}    — final answer
      {"type": "error",    "message": "<error text>"}          — on failure
    """
    import time
    start_time = time.time()
    collection = request.collection or settings.chroma_collection_name

    async def event_stream():
        try:
            initial_state = {
                "query": request.query,
                "top_k": request.top_k or 5,
                "collection": collection,
                "decision_path": [],
            }

            accumulated: dict = {}
            seen_start_events: set = set()

            async for event in rag_pipeline._compiled_graph.astream_events(initial_state, version="v2"):
                etype = event.get("event", "")
                ename = event.get("name", "")
                edata = event.get("data", {})

                # Emit one thought item per node when it starts
                if etype == "on_chain_start" and ename in _NODE_THINKING and ename not in seen_start_events:
                    seen_start_events.add(ename)
                    yield f"data: {json.dumps({'type': 'thinking', 'step': _NODE_THINKING[ename], 'thought': _NODE_THINKING_START.get(ename, '')})}\n\n"

                # Accumulate each node's output so we can reconstruct final state
                elif etype == "on_chain_end" and ename in _NODE_THINKING:
                    output = edata.get("output", {})
                    if isinstance(output, dict):
                        accumulated.update(output)
                        thought = _summarize_node_thought(ename, output, {**initial_state, **accumulated})
                        yield f"data: {json.dumps({'type': 'thinking', 'step': _NODE_THINKING[ename], 'thought': thought})}\n\n"
                        # Emit visible CoT reasoning from generate node (demo)
                        if ename == "generate" and output.get("cot_reasoning"):
                            yield f"data: {json.dumps({'type': 'cot', 'content': output['cot_reasoning']})}\n\n"

                # Prefer the graph-level final state when available
                elif etype == "on_chain_end" and ename == "LangGraph":
                    graph_out = edata.get("output", {})
                    if isinstance(graph_out, dict) and graph_out:
                        accumulated.update(graph_out)

            final_state = {**initial_state, **accumulated}
            response_time = time.time() - start_time

            error_text = final_state.get("error")
            if error_text:
                resp = {
                    "query": request.query,
                    "answer": f"Error retrieving documents: {error_text}. Please ensure documents have been ingested first.",
                    "sources": [],
                    "relevance_score": 0.0,
                    "model": settings.llm_provider,
                    "response_time": response_time,
                    "api_version": __version__,
                }
                yield f"data: {json.dumps({'type': 'result', 'data': resp})}\n\n"
                yield "data: [DONE]\n\n"
                return

            documents = final_state.get("documents", [])
            overall_relevance = final_state.get("relevance_score", 0.0)
            is_relevant = final_state.get("is_relevant", False)

            if not documents or not is_relevant:
                help_text = get_help_text_for_collection()
                resp = {
                    "query": request.query,
                    "answer": f"I don't have enough information to answer that question based on the provided documentation. {help_text}",
                    "sources": [],
                    "relevance_score": overall_relevance,
                    "model": settings.llm_provider,
                    "response_time": response_time,
                    "api_version": __version__,
                }
                yield f"data: {json.dumps({'type': 'result', 'data': resp})}\n\n"
                yield "data: [DONE]\n\n"
                return

            sources = [
                {
                    "content": s.get("content", "") if isinstance(s, dict) else "",
                    "metadata": s.get("metadata", {}) if isinstance(s, dict) else {},
                    "relevance_score": float(s.get("relevance_score", 0.0)) if isinstance(s, dict) else 0.0,
                }
                for s in final_state.get("sources", [])
            ]

            resp = {
                "query": request.query,
                "answer": final_state.get("answer", ""),
                "sources": sources,
                "relevance_score": overall_relevance,
                "model": settings.llm_provider,
                "response_time": response_time,
                "api_version": __version__,
            }
            yield f"data: {json.dumps({'type': 'result', 'data': resp})}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as exc:
            logger.error("Streaming query error: %s", str(exc), exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/v1/rag/graph/mermaid", tags=["RAG"])
async def rag_graph_mermaid(view: str = "enhanced"):
    """
    Return the RAG graph as Mermaid source for demos.

    Query params:
    - view=enhanced (default): custom, explicitly labeled branch diagram
    - view=raw: direct LangGraph draw_mermaid() output
    """
    use_enhanced = view.lower() != "raw"
    return {
        "graph": "langgraph",
        "view": "enhanced" if use_enhanced else "raw",
        "mermaid": rag_pipeline.get_mermaid_enhanced() if use_enhanced else rag_pipeline.get_mermaid(),
    }


@app.post("/api/v1/ingest", response_model=IngestResponse, tags=["Admin"])
async def ingest_endpoint(request: IngestRequest):
    """
    Ingest documents into ChromaDB
    
    Args:
        request: Ingest request with document path
        
    Returns:
        IngestResponse with ingestion statistics
    """
    logger.info(f"Ingest requested for path: {request.document_path}")
    
    try:
        # Call ingestion pipeline
        result = ingest_documents(
            document_path=request.document_path,
            collection_name=request.collection_name,
            force_reingest=request.force_reingest
        )
        
        # Return result
        return IngestResponse(**result)
        
    except Exception as e:
        logger.error(f"Error ingesting documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error ingesting documents: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
