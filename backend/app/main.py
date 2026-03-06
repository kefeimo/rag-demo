"""
FastAPI Main Application
RAG System API with health check and query endpoints
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import settings
from app.models import (
    HealthResponse,
    QueryRequest,
    QueryResponse,
    IngestRequest,
    IngestResponse,
    Source
)
from app import __version__
from app.rag.ingestion import ingest_documents
from app.rag.retrieval import Retriever
from app.rag.hybrid_retrieval import HybridRetriever
from app.rag.generation import get_llm_client, generate_answer, extract_sources

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
    
    if "visa" in collection_name or "vcc" in collection_name or "chart" in collection_name:
        return "Please try rephrasing your question or asking about specific Visa Chart Components features, such as: chart types, accessibility features, data props, or integration guides."
    elif "fastapi" in collection_name:
        return "Please try rephrasing your question or ask about FastAPI features."
    else:
        return "Please try rephrasing your question with more specific terms."


# Create FastAPI app
app = FastAPI(
    title="RAG System API",
    description="Retrieval-Augmented Generation system for FastAPI documentation",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize hybrid retriever (global instance to cache BM25 index)
hybrid_retriever = None

@app.on_event("startup")
async def startup_event():
    """Initialize hybrid retriever on startup"""
    global hybrid_retriever
    logger.info("Initializing hybrid retriever...")
    try:
        hybrid_retriever = HybridRetriever(auto_classify=True)
        logger.info("✓ Hybrid retriever initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize hybrid retriever: {e}")
        logger.warning("Falling back to semantic-only retrieval")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Returns service status and version
    """
    logger.info("Health check requested")
    return HealthResponse(
        status="healthy",
        version=__version__
    )


@app.post("/api/v1/query", response_model=QueryResponse, tags=["RAG"])
async def query_rag(request: QueryRequest):
    """
    Query the RAG system with hybrid search (semantic + keyword)
    
    Args:
        request: Query request with user question
        
    Returns:
        QueryResponse with answer, sources, confidence, and metadata
    """
    import time
    start_time = time.time()
    
    logger.info(f"Query received: {request.query}")
    
    try:
        # Strategy: Try semantic-only first (handles most queries well)
        # If confidence is low, try hybrid search (handles edge cases like exact API names)
        retriever = Retriever()
        logger.info("Trying semantic-only search first")
        retrieval_result = retriever.retrieve(request.query, top_k=request.top_k)
        
        # If confidence is low and hybrid is available, try hybrid as fallback
        if retrieval_result.get("confidence", 0.0) < 0.65 and hybrid_retriever is not None:
            logger.info(f"Semantic confidence {retrieval_result['confidence']:.3f} < 0.65, trying hybrid search")
            hybrid_result = hybrid_retriever.search(request.query, top_k=request.top_k)
            
            # Use whichever has higher confidence
            if hybrid_result.get("confidence", 0.0) > retrieval_result.get("confidence", 0.0):
                logger.info(f"Using hybrid search (conf={hybrid_result['confidence']:.3f} > semantic={retrieval_result['confidence']:.3f})")
                retrieval_result = hybrid_result
            else:
                logger.info(f"Keeping semantic-only (conf={retrieval_result['confidence']:.3f} >= hybrid={hybrid_result['confidence']:.3f})")
        elif retrieval_result.get("confidence", 0.0) >= 0.65:
            logger.info(f"Semantic confidence {retrieval_result['confidence']:.3f} >= 0.65, using semantic-only")
        else:
            logger.info("Hybrid retriever not available, using semantic-only result")
        
        # Check for errors
        if "error" in retrieval_result:
            logger.error(f"Retrieval error: {retrieval_result['error']}")
            response_time = time.time() - start_time
            return QueryResponse(
                query=request.query,
                answer=f"Error retrieving documents: {retrieval_result['error']}. Please ensure documents have been ingested first.",
                sources=[],
                confidence=0.0,
                model=settings.llm_provider,
                response_time=response_time,
                api_version=__version__
            )
        
        documents = retrieval_result.get("documents", [])
        overall_confidence = retrieval_result.get("confidence", 0.0)
        
        # Check confidence threshold (use Retriever for consistency)
        temp_retriever = Retriever()
        is_confident, confidence_msg = temp_retriever.check_confidence(overall_confidence)
        
        if not documents or not is_confident:
            logger.warning(f"Low confidence or no documents: {confidence_msg}")
            help_text = get_help_text_for_collection()
            response_time = time.time() - start_time
            return QueryResponse(
                query=request.query,
                answer=f"I don't have enough information to answer that question based on the provided documentation. {help_text}",
                sources=[],
                confidence=overall_confidence,
                model=settings.llm_provider,
                response_time=response_time,
                api_version=__version__
            )
        
        # Generate answer using LLM
        logger.info("Generating answer with LLM...")
        llm_client = get_llm_client()
        answer = generate_answer(
            query=request.query,
            retrieved_documents=documents,
            llm_client=llm_client
        )
        
        # Format sources for response
        sources = extract_sources(documents)
        
        response_time = time.time() - start_time
        logger.info(f"Query completed successfully (confidence: {overall_confidence:.3f}, time: {response_time:.2f}s)")
        return QueryResponse(
            query=request.query,
            answer=answer,
            sources=sources,
            confidence=overall_confidence,
            model=settings.llm_provider,
            response_time=response_time,
            api_version=__version__
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


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
            force_reingest=request.force_reingest
        )
        
        # Return result
        return IngestResponse(**result)
        
    except Exception as e:
        logger.error(f"Error ingesting documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error ingesting documents: {str(e)}")


@app.post("/api/v1/ingest/visa-docs", response_model=IngestResponse, tags=["Admin"])
async def ingest_visa_docs_endpoint(force_reingest: bool = True):
    """
    Ingest Visa Chart Components documentation into ChromaDB
    
    This endpoint ingests all extracted Visa documentation:
    - Repository docs (53): README, CONTRIBUTING, CHANGELOGs
    - Code docs (210): Auto-generated API documentation
    - Issue Q&A (13): GitHub issue discussions
    
    Args:
        force_reingest: If True, reset collection before ingestion (default: True)
        
    Returns:
        IngestResponse with ingestion statistics
    """
    logger.info(f"Visa docs ingestion requested (force_reingest={force_reingest})")
    
    try:
        # Import the visa docs ingestion function
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from ingest_visa_docs import ingest_visa_docs
        
        # Call ingestion pipeline
        result = ingest_visa_docs(force_reingest=force_reingest)
        
        # Return result
        return IngestResponse(**result)
        
    except Exception as e:
        logger.error(f"Error ingesting Visa docs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error ingesting Visa docs: {str(e)}")


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
