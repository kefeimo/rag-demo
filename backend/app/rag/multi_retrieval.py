"""
Multi-Collection Retrieval
Queries multiple ChromaDB collections and merges results by relevance
"""

import logging
import time
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models import Source

logger = logging.getLogger(__name__)


class MultiCollectionRetriever:
    """
    Query multiple collections and merge results by relevance score.

    This orchestrator runs the RAG pipeline multiple times (once per collection)
    and merges the results, selecting the top-K most relevant documents across
    all collections.

    The graph pipeline itself remains unchanged - multi-collection logic is
    implemented as an orchestration layer above the graph.
    """

    def __init__(self, rag_pipeline, known_collections: List[str]):
        """
        Initialize multi-collection retriever

        Args:
            rag_pipeline: LangGraph RAG pipeline instance
            known_collections: List of collection names to query
        """
        self.rag_pipeline = rag_pipeline
        self.known_collections = known_collections
        logger.info(f"MultiCollectionRetriever initialized with {len(known_collections)} collections")

    def query_all(
        self,
        query: str,
        top_k: int = None,
    ) -> Dict[str, Any]:
        """
        Query all known collections and merge results by relevance score.

        Algorithm:
        1. Query each collection independently (run graph for each)
        2. Collect all documents with their relevance scores
        3. Sort all documents by relevance (distance)
        4. Take top-K documents across all collections
        5. Calculate overall relevance score
        6. Generate answer using merged documents

        Args:
            query: User query string
            top_k: Number of top results to return (default from settings)

        Returns:
            Dictionary with:
                - documents: List of top-K documents across all collections
                - relevance_score: Overall relevance score
                - sources: Formatted source objects
                - answer: Generated answer (if relevant)
                - error: Error message (if any)
                - collection_results: Per-collection statistics
        """
        logger.info(f"Executing multi-collection query across {len(self.known_collections)} collections")

        top_k = top_k or settings.top_k_results
        all_documents = []
        collection_results = {}

        # Query each collection
        for collection_name in self.known_collections:
            try:
                logger.info(f"Querying collection: {collection_name}")

                pipeline_state = self.rag_pipeline.run(
                    query=query,
                    top_k=top_k,
                    collection=collection_name,
                )

                if pipeline_state.get("error"):
                    logger.warning(f"Error querying {collection_name}: {pipeline_state['error']}")
                    continue

                documents = pipeline_state.get("documents", [])
                relevance_score = pipeline_state.get("relevance_score", 0.0)

                # Tag documents with collection name
                for doc in documents:
                    doc["collection"] = collection_name

                all_documents.extend(documents)
                collection_results[collection_name] = {
                    "count": len(documents),
                    "relevance": relevance_score
                }

                logger.info(
                    f"✓ {collection_name}: {len(documents)} docs, "
                    f"relevance={relevance_score:.3f}"
                )

            except Exception as e:
                logger.error(f"Error querying collection {collection_name}: {str(e)}")
                continue

        # No documents found across any collection
        if not all_documents:
            return {
                "documents": [],
                "relevance_score": 0.0,
                "sources": [],
                "answer": None,
                "error": "No documents found in any collection",
                "collection_results": collection_results,
            }

        # Sort all documents by relevance (distance field, lower is better)
        all_documents.sort(key=lambda x: x.get("distance", 1.0))

        # Take top K documents across all collections
        top_documents = all_documents[:top_k]

        # Calculate overall relevance score (average of top K)
        # Convert distance to similarity: similarity = 1.0 - (distance / 2.0)
        overall_relevance = (
            sum(doc.get("distance", 0.0) for doc in top_documents) / len(top_documents)
            if top_documents else 0.0
        )
        overall_relevance = 1.0 - (overall_relevance / 2.0)

        logger.info(
            f"Merged results: {len(top_documents)} docs from "
            f"{len(collection_results)} collections, relevance={overall_relevance:.3f}"
        )

        # Format sources
        sources = []
        for doc in top_documents:
            distance = doc.get("distance", 1.0)
            relevance = 1.0 - (distance / 2.0)
            sources.append(
                Source(
                    content=doc.get("content", ""),
                    metadata=doc.get("metadata", {}),
                    relevance_score=relevance
                )
            )

        # Check relevance threshold
        is_relevant = overall_relevance >= settings.relevance_threshold

        # Generate answer only if relevant
        answer = None
        if is_relevant:
            from app.rag.generation import generate_answer
            # Pass collection names for domain-aware prompt construction
            answer = generate_answer(query, top_documents, collections=self.known_collections)

        return {
            "documents": top_documents,
            "relevance_score": overall_relevance,
            "sources": sources,
            "answer": answer,
            "is_relevant": is_relevant,
            "error": None,
            "collection_results": collection_results,
        }
