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
from app.rag.generation import get_llm_client, generate_answer, extract_sources

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    Query the RAG system
    
    Args:
        request: Query request with user question
        
    Returns:
        QueryResponse with answer, sources, and confidence
    """
    logger.info(f"Query received: {request.query}")
    
    try:
        # Initialize retriever
        retriever = Retriever()
        
        # Retrieve relevant documents
        retrieval_result = retriever.retrieve(request.query, top_k=request.top_k)
        
        # Check for errors
        if "error" in retrieval_result:
            logger.error(f"Retrieval error: {retrieval_result['error']}")
            return QueryResponse(
                query=request.query,
                answer=f"Error retrieving documents: {retrieval_result['error']}. Please ensure documents have been ingested first.",
                sources=[],
                confidence=0.0,
                model=settings.llm_provider
            )
        
        documents = retrieval_result.get("documents", [])
        overall_confidence = retrieval_result.get("confidence", 0.0)
        
        # Check confidence threshold
        is_confident, confidence_msg = retriever.check_confidence(overall_confidence)
        
        if not documents or not is_confident:
            logger.warning(f"Low confidence or no documents: {confidence_msg}")
            return QueryResponse(
                query=request.query,
                answer="I don't have enough information to answer that question based on the provided documentation. Please try rephrasing your question or ask about FastAPI features.",
                sources=[],
                confidence=overall_confidence,
                model=settings.llm_provider
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
        
        logger.info(f"Query completed successfully (confidence: {overall_confidence:.3f})")
        return QueryResponse(
            query=request.query,
            answer=answer,
            sources=sources,
            confidence=overall_confidence,
            model=settings.llm_provider
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
