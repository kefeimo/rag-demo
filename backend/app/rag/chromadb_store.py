"""
ChromaDB Vector Store

Single abstraction layer for all ChromaDB interactions.

If the vector store backend is ever replaced (Pinecone, Weaviate, Qdrant, etc.),
only this file needs to change — ingestion.py, retrieval.py, and
hybrid_retrieval.py remain untouched.

Responsibilities:
  - ChromaDB client singleton
  - Collection creation with HNSW config
  - Write path: batch insert (add)
  - Read paths: ANN query (query), bulk fetch (get_all)
  - HNSW_SPACE constant — single source of truth for the distance metric
"""

import logging
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

logger = logging.getLogger(__name__)


# ── Distance metric ──────────────────────────────────────────────────────────
# ChromaDB accepts this via metadata={"hnsw:space": ...} at collection creation
# time (a ChromaDB API quirk — hnsw:* keys in the metadata dict are HNSW index
# config, not document metadata; they are extracted by HnswParams and passed to
# hnswlib at index build time).
#
# Valid values: "cosine" | "l2" | "ip"
# Default in ChromaDB is "l2" — explicit setting here is required.
# IMPORTANT: retrieval.py distance→relevance formula only holds for "cosine":
#   relevance = 1.0 - (distance / 2.0)   # cosine distance ∈ [0, 2] → [0, 1]
# Changing HNSW_SPACE requires recreating all collections (force_reingest=True).
HNSW_SPACE = "cosine"


# ── Client singleton ─────────────────────────────────────────────────────────
# One PersistentClient per process to avoid SQLite lock conflicts when ingestion
# and retrieval both run in the same FastAPI process.
_chroma_client: Optional[chromadb.ClientAPI] = None


def get_chroma_client() -> chromadb.ClientAPI:
    """
    Get or create ChromaDB client singleton.

    Returns:
        Persistent ChromaDB client (chromadb.ClientAPI).
    """
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        logger.info(f"ChromaDB client initialised: {settings.chroma_persist_directory}")
    return _chroma_client


# ── Store abstraction ─────────────────────────────────────────────────────────

class ChromaDBStore:
    """
    Vector store abstraction over a single ChromaDB collection.

    Owns all ChromaDB collection operations — creation, insertion, querying,
    and bulk retrieval.  Ingestion and retrieval modules import this class
    rather than calling chromadb directly, so swapping the vector store
    backend only requires changes here.

    Usage pattern:
      # Write path (ingestion):
      store = ChromaDBStore("fastapi_docs")
      store.get_or_create_collection(reset=False)
      store.add(ids, embeddings, documents, metadatas)

      # Read path (retrieval):
      store = ChromaDBStore("fastapi_docs")
      store.get_collection()          # opens existing collection
      results = store.query(vec, n_results=5, include=["documents", ...])
    """

    def __init__(self, collection_name: str) -> None:
        self.collection_name = collection_name
        self.client = get_chroma_client()
        self._collection: Optional[chromadb.Collection] = None

    # ── Collection management ─────────────────────────────────────────────────

    def get_or_create_collection(self, reset: bool = False) -> chromadb.Collection:
        """
        Get or create the collection with the cosine similarity metric.

        Args:
            reset: If True, delete the existing collection before creating.

        Returns:
            ChromaDB Collection object.
        """
        if reset:
            try:
                self.client.delete_collection(name=self.collection_name)
                logger.info(f"Deleted collection: {self.collection_name}")
            except Exception as e:
                logger.debug(f"No existing collection to delete: {e}")

        # hnsw:space is index config smuggled via the metadata parameter
        # (ChromaDB API quirk — see module docstring).  Must stay in sync with
        # HNSW_SPACE; retrieval.py's distance formula depends on it.
        self._collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": HNSW_SPACE},
        )
        logger.info(
            f"Collection ready: {self.collection_name} (count: {self._collection.count()})"
        )
        return self._collection

    def get_collection(self) -> Optional[chromadb.Collection]:
        """
        Open an existing collection.  Returns None if not found.

        Returns:
            ChromaDB Collection or None.
        """
        try:
            self._collection = self.client.get_collection(name=self.collection_name)
            return self._collection
        except Exception as e:
            logger.error(f"Failed to get collection '{self.collection_name}': {e}")
            return None

    # ── Write path ────────────────────────────────────────────────────────────

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> None:
        """
        Batch-insert chunks into the collection.

        Args:
            ids:        Unique ID for each chunk.
            embeddings: Pre-computed embedding vectors.
            documents:  Raw text for each chunk.
            metadatas:  Metadata dicts for each chunk.
            batch_size: Number of chunks per ChromaDB insert call (default 100).
        """
        if self._collection is None:
            raise RuntimeError(
                "Collection not initialised. Call get_or_create_collection() first."
            )
        total = len(ids)
        for i in range(0, total, batch_size):
            end = min(i + batch_size, total)
            self._collection.add(
                ids=ids[i:end],
                documents=documents[i:end],
                metadatas=metadatas[i:end],
                embeddings=embeddings[i:end],
            )
            logger.debug(f"Inserted batch {i // batch_size + 1} ({end}/{total})")

    # ── Read path ─────────────────────────────────────────────────────────────

    def query(
        self,
        query_embedding: List[float],
        n_results: int,
        include: List[str],
    ) -> Dict[str, Any]:
        """
        Query the collection for approximate nearest neighbours.

        Args:
            query_embedding: Dense query vector (must match the embedding space
                             used at ingest time).
            n_results:       Number of nearest neighbours to return.
            include:         Fields to return — any of "documents", "metadatas",
                             "distances", "embeddings".

        Returns:
            ChromaDB QueryResult dict.  All values are lists-of-lists
            (outer list = one entry per query; always unwrap with [0]
            for single-query calls).
        """
        if self._collection is None:
            raise RuntimeError(
                "Collection not initialised. Call get_collection() first."
            )
        return self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=include,
        )

    def get_all(self, include: List[str]) -> Dict[str, Any]:
        """
        Fetch every document from the collection.

        Used by HybridRetriever to build the in-memory BM25 index at startup.

        Args:
            include: Fields to return — any of "documents", "metadatas",
                     "embeddings", "ids".

        Returns:
            ChromaDB GetResult dict.
        """
        if self._collection is None:
            raise RuntimeError(
                "Collection not initialised. Call get_collection() first."
            )
        return self._collection.get(include=include)

    # ── Utility ───────────────────────────────────────────────────────────────

    def count(self) -> int:
        """Return document count (0 if collection not yet opened)."""
        if self._collection is None:
            return 0
        return self._collection.count()
