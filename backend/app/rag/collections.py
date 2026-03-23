"""
Collection Management Utilities
Handles ChromaDB collection discovery and metadata
"""

import logging
from typing import List, Dict, Any
from app.rag.chromadb_store import get_chroma_client

logger = logging.getLogger(__name__)


def list_all_collections() -> List[Dict[str, Any]]:
    """
    List all available ChromaDB collections with metadata

    Returns:
        List of dictionaries with collection name and count

    Example:
        [
            {"name": "fastapi_docs", "count": 165},
            {"name": "at_docs", "count": 2408}
        ]
    """
    try:
        client = get_chroma_client()
        collections = client.list_collections()

        collection_info = []
        for collection in collections:
            collection_info.append({
                "name": collection.name,
                "count": collection.count()
            })

        logger.info(f"Listed {len(collection_info)} collections")
        return collection_info

    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}", exc_info=True)
        raise


def get_collection_names() -> List[str]:
    """
    Get list of collection names

    Returns:
        List of collection names
    """
    return [col["name"] for col in list_all_collections()]
