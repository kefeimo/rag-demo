"""
Shared RAG Utilities
Common resources like ChromaDB client singleton
"""

import logging
from typing import Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

logger = logging.getLogger(__name__)

# Global ChromaDB client (singleton pattern to avoid conflicts)
_chroma_client: Optional[chromadb.PersistentClient] = None


def get_chroma_client() -> chromadb.PersistentClient:
    """
    Get or create ChromaDB client singleton
    
    Returns:
        ChromaDB PersistentClient instance
    """
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        logger.info(f"ChromaDB client initialized: {settings.chroma_persist_directory}")
    return _chroma_client
