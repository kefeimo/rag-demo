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
    openai_model: str = Field(
        default="gpt-3.5-turbo",
        description="OpenAI model name (gpt-3.5-turbo, gpt-4, etc.)"
    )
    openai_api_key: str = Field(default="", description="OpenAI API key (optional)")
    
    # Embedding Configuration
    embedding_provider: str = Field(
        default="openai",
        description="Embedding provider: openai or sentence-transformers"
    )
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence-transformers model (used when embedding_provider=sentence-transformers)"
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model (used when embedding_provider=openai)"
    )
    
    # ChromaDB Configuration
    chroma_persist_directory: str = Field(
        default="./data/chroma_db",
        description="ChromaDB persistence directory (relative to backend/)"
    )
    chroma_collection_name: str = Field(
        default="fastapi_docs",
        description="ChromaDB collection name"
    )
    anonymized_telemetry: bool = Field(
        default=False,
        description="Enable/disable ChromaDB telemetry"
    )
    
    # RAG Configuration
    chunk_size: int = Field(default=500, description="Text chunk size in characters")
    chunk_overlap: int = Field(default=50, description="Overlap between chunks")
    top_k_results: int = Field(default=5, description="Number of results to retrieve")
    relevance_threshold: float = Field(
        default=0.65,
        description="Minimum retrieval relevance score to attempt answer generation (below this the query is rejected)"
    )
    prompt_cot_enabled: bool = Field(
        default=True,
        description="Enable internal CoT-style reasoning guidance in prompt template"
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
