"""
Configuration Management
Loads and validates environment variables
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # LLM Configuration
    llm_provider: str = Field(default="gpt4all", description="LLM provider: gpt4all or openai")
    gpt4all_model: str = Field(
        default="mistral-7b-instruct-v0.1.Q4_0.gguf",
        description="GPT4All model name"
    )
    openai_api_key: str = Field(default="", description="OpenAI API key (optional)")
    
    # Embedding Configuration
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model for vector search"
    )
    
    # ChromaDB Configuration
    chroma_persist_directory: str = Field(
        default="../data/chroma_db",
        description="ChromaDB persistence directory (relative to backend/)"
    )
    chroma_collection_name: str = Field(
        default="fastapi_docs",
        description="ChromaDB collection name"
    )
    
    # RAG Configuration
    chunk_size: int = Field(default=500, description="Text chunk size in characters")
    chunk_overlap: int = Field(default=50, description="Overlap between chunks")
    top_k_results: int = Field(default=5, description="Number of results to retrieve")
    confidence_threshold: float = Field(
        default=0.65,
        description="Minimum confidence for known answers"
    )
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_reload: bool = Field(default=True, description="Auto-reload on code changes")
    
    # CORS Configuration
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Comma-separated list of allowed origins"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Evaluation (RAGAS)
    ragas_metrics: str = Field(
        default="context_precision,faithfulness,answer_relevancy",
        description="Comma-separated list of RAGAS metrics"
    )
    
    @property
    def ragas_metrics_list(self) -> List[str]:
        """Parse RAGAS metrics into a list"""
        return [metric.strip() for metric in self.ragas_metrics.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
