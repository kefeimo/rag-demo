"""
Pydantic Models for API Request/Response
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class QueryRequest(BaseModel):
    """Request model for RAG query endpoint"""
    query: str = Field(..., description="User query", min_length=1, max_length=1000)
    top_k: Optional[int] = Field(default=5, description="Number of results to retrieve", ge=1, le=20)
    collection: Optional[str] = Field(default=None, description="ChromaDB collection to query (e.g. 'fastapi_docs'). Defaults to CHROMA_COLLECTION_NAME env var.")


class Source(BaseModel):
    """Source document with metadata"""
    content: str = Field(..., description="Document content/chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    relevance_score: float = Field(..., description="Retrieval relevance score (cosine similarity, computed before LLM generation)", ge=0.0, le=1.0)



class QueryResponse(BaseModel):
    """Response model for RAG query endpoint"""
    query: str = Field(..., description="Original user query")
    answer: str = Field(..., description="Generated answer")
    sources: List[Source] = Field(default_factory=list, description="Source documents used")
    relevance_score: float = Field(..., description="Overall retrieval relevance score — average cosine similarity of top-k retrieved chunks to the query, computed before LLM generation", ge=0.0, le=1.0)
    model: str = Field(..., description="LLM model used for generation")
    response_time: Optional[float] = Field(None, description="Response time in seconds")
    api_version: Optional[str] = Field(None, description="API version")


class IngestRequest(BaseModel):
    """Request model for document ingestion endpoint"""
    document_path: str = Field(..., description="Path to documents directory")
    collection_name: str = Field(default="fastapi_docs", description="Collection name for ingested documents")
    force_reingest: bool = Field(default=False, description="Force re-ingestion even if exists")


class IngestResponse(BaseModel):
    """Response model for document ingestion endpoint"""
    status: str = Field(..., description="Ingestion status")
    documents_processed: int = Field(..., description="Number of documents processed")
    chunks_created: int = Field(..., description="Number of chunks created")
    time_elapsed: str = Field(..., description="Time elapsed for ingestion")


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    model: str = Field(..., description="Active LLM provider (e.g. openai, gpt4all)")
