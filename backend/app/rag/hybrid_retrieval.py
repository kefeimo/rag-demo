"""
Hybrid Retrieval Module
Combines semantic search (ChromaDB) with keyword search (BM25) for improved relevance
"""

from rank_bm25 import BM25Okapi
from typing import List, Dict, Any, Optional
import numpy as np
import logging
import re

from app.rag.retrieval import Retriever
from app.rag.query_classifier import classify_query, get_search_weights
from app.config import settings

logger = logging.getLogger(__name__)

# Common English stopwords to filter from BM25 (reduces noise from common words)
STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he',
    'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'will',
    'with', 'what', 'how', 'do', 'does', 'can', 'could', 'should', 'would'
}


def tokenize_with_stopword_filter(text: str, remove_stopwords: bool = True) -> List[str]:
    """
    Tokenize text with optional stopword filtering and API-term boosting
    
    Args:
        text: Text to tokenize
        remove_stopwords: Whether to filter out common stopwords
        
    Returns:
        List of tokens
    """
    # Convert to lowercase and remove punctuation
    text_lower = text.lower()
    # Remove common punctuation but keep underscores and hyphens (used in API names)
    text_clean = re.sub(r'[^\w\s\-_]', ' ', text_lower)
    
    # Basic whitespace tokenization
    tokens = text_clean.split()
    
    # Filter stopwords if enabled
    if remove_stopwords:
        tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    
    # Boost API-specific terms (camelCase, PascalCase, contains 'I' prefix for interfaces)
    boosted_tokens = []
    for token in tokens:
        boosted_tokens.append(token)
        
        # Boost if it looks like an API name (starts with I, has underscores/hyphens)
        # Check if token contains patterns like "idatatable", "iaccessibility", etc.
        if (token.startswith('i') and len(token) > 2) or \
           '_' in token or '-' in token:
            # Repeat token 4 more times for 5x total weight on API names
            boosted_tokens.extend([token] * 4)
    
    return boosted_tokens



class HybridRetriever:
    """
    Hybrid retrieval combining semantic and keyword search
    
    Features:
    - Semantic search via ChromaDB embeddings
    - Keyword search via BM25 algorithm
    - Adaptive weight adjustment based on query type
    - Metadata-based boosting
    """
    
    def __init__(
        self,
        collection_name: Optional[str] = None,
        auto_classify: bool = True
    ):
        """
        Initialize hybrid retriever
        
        Args:
            collection_name: ChromaDB collection name (defaults to settings)
            auto_classify: Automatically classify queries and adjust weights
        """
        self.auto_classify = auto_classify
        
        # Initialize semantic retriever with the specified collection
        self.semantic_retriever = Retriever(collection_name=collection_name)
        
        # Initialize BM25 index
        self.bm25_index = None
        self.documents = []
        self.document_ids = []
        self.metadatas = []
        self._build_bm25_index()
        
        logger.info(f"HybridRetriever initialized (collection={self.semantic_retriever.collection_name}, auto_classify={auto_classify})")
    
    def _build_bm25_index(self):
        """Build BM25 index from ChromaDB documents with metadata enrichment and smart tokenization"""
        logger.info("Building BM25 index with stopword filtering...")

        try:
            # Get all documents from ChromaDB
            all_docs = self.semantic_retriever.store.get_all(
                include=['documents', 'metadatas']
            )

            if not all_docs or not all_docs.get('documents'):
                logger.warning("No documents found in collection for BM25 index")
                return

            self.documents = all_docs['documents']
            self.document_ids = all_docs['ids']
            self.metadatas = all_docs.get('metadatas', [{}] * len(self.documents))

            # Enrich documents with metadata for better BM25 matching
            # Combine document content with important metadata fields
            enriched_docs = []
            for doc, metadata in zip(self.documents, self.metadatas):
                # Start with original document
                enriched = doc

                # Add api_name if present (important for API queries)
                # Repeat api_name 5 times to HEAVILY boost its importance
                api_name = metadata.get('api_name', '')
                if api_name and api_name != 'N/A':
                    enriched = f"{api_name} {api_name} {api_name} {api_name} {api_name} {enriched}"

                # Add doc_type for context
                doc_type = metadata.get('doc_type', '')
                if doc_type:
                    enriched = f"{doc_type} {enriched}"

                enriched_docs.append(enriched)

            # Tokenize enriched documents with stopword filtering and API boosting
            tokenized_docs = [
                tokenize_with_stopword_filter(doc, remove_stopwords=True)
                for doc in enriched_docs
            ]
            self.bm25_index = BM25Okapi(tokenized_docs)

            logger.info(f"✓ BM25 index built: {len(self.documents)} documents (metadata enriched + stopword filtered)")

        except Exception as e:
            logger.error(f"Failed to build BM25 index: {e}")
            raise
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        semantic_weight: Optional[float] = None,
        bm25_weight: Optional[float] = None,
        boost_config: Optional[Dict[str, Dict[str, float]]] = None
    ) -> Dict[str, Any]:
        """
        Hybrid search combining semantic and keyword matching
        
        Args:
            query: Search query
            top_k: Number of results to return
            semantic_weight: Weight for semantic search scores (0-1)
            bm25_weight: Weight for BM25 scores (0-1)
            boost_config: Metadata-based boost configuration
        
        Returns:
            Dict with documents, relevance_score, and metadata (same format as Retriever.retrieve)
        """
        logger.info(f"Hybrid search: query='{query}', top_k={top_k}")
        
        # Auto-classify query if enabled
        if self.auto_classify and (semantic_weight is None or bm25_weight is None):
            query_type = classify_query(query)
            weights = get_search_weights(query_type)
            
            if semantic_weight is None:
                semantic_weight = weights['semantic_weight']
            if bm25_weight is None:
                bm25_weight = weights['bm25_weight']
            if boost_config is None:
                boost_config = weights['boost_config']
            
            logger.info(f"Query classified as '{query_type}' → semantic={semantic_weight}, bm25={bm25_weight}")
        else:
            # Default weights if not provided
            semantic_weight = semantic_weight or 0.6
            bm25_weight = bm25_weight or 0.4
            boost_config = boost_config or {}
        
        # 1. Semantic search
        semantic_result = self.semantic_retriever.retrieve(
            query=query,
            top_k=top_k * 2  # Get more for fusion
        )
        
        if "error" in semantic_result:
            return semantic_result
        
        semantic_docs = semantic_result.get("documents", [])
        
        # 2. BM25 keyword search with stopword filtering
        if self.bm25_index is None:
            logger.warning("BM25 index not available, falling back to semantic-only search")
            return semantic_result
        
        # Tokenize query with stopword filtering and API boosting
        tokenized_query = tokenize_with_stopword_filter(query, remove_stopwords=True)
        bm25_scores = self.bm25_index.get_scores(tokenized_query)
        
        # Get top BM25 results
        bm25_top_indices = np.argsort(bm25_scores)[::-1][:top_k * 2]
        
        # 3. Score fusion with normalization
        combined_scores = {}
        
        # Add semantic scores (convert distance to similarity)
        if semantic_docs:
            distances = [doc.get('distance', 1.0) for doc in semantic_docs]
            max_distance = max(distances) if distances else 1.0
            
            for idx, doc in enumerate(semantic_docs):
                # Use rank as doc_id if not present (semantic retriever doesn't return id)
                doc_id = doc.get('id', f"semantic_{idx}")
                distance = doc.get('distance', 1.0)
                # Convert distance to similarity (lower distance = higher similarity)
                similarity = 1.0 - (distance / max_distance) if max_distance > 0 else 0.0
                combined_scores[doc_id] = {
                    'score': semantic_weight * similarity,
                    'semantic_score': similarity,
                    'bm25_score': 0.0,
                    'metadata': doc.get('metadata', {}),
                    'content': doc.get('content', '')
                }
        
        # Add BM25 scores (normalized)
        max_bm25_score = max(bm25_scores) if len(bm25_scores) > 0 else 1.0
        
        for idx in bm25_top_indices:
            doc_id = self.document_ids[idx]
            bm25_score_raw = bm25_scores[idx]
            bm25_normalized = bm25_score_raw / max_bm25_score if max_bm25_score > 0 else 0.0
            
            if doc_id in combined_scores:
                combined_scores[doc_id]['score'] += bm25_weight * bm25_normalized
                combined_scores[doc_id]['bm25_score'] = bm25_normalized
            else:
                combined_scores[doc_id] = {
                    'score': bm25_weight * bm25_normalized,
                    'semantic_score': 0.0,
                    'bm25_score': bm25_normalized,
                    'metadata': self.metadatas[idx],
                    'content': self.documents[idx]
                }
        
        # 4. Apply metadata boosting
        if boost_config:
            for doc_id, doc_data in combined_scores.items():
                metadata = doc_data['metadata']
                
                for meta_key, boost_values in boost_config.items():
                    meta_value = metadata.get(meta_key)
                    if meta_value in boost_values:
                        boost_factor = boost_values[meta_value]
                        doc_data['score'] *= boost_factor
                        logger.debug(f"Boosted doc {doc_id[:8]}... by {boost_factor}x ({meta_key}={meta_value})")
        
        # 5. Sort by combined score and return top-k
        sorted_docs = sorted(
            combined_scores.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )[:top_k]
        
        # 6. Format results in same format as Retriever.retrieve()
        final_documents = []
        total_relevance = 0.0
        
        for doc_id, doc_data in sorted_docs:
            final_documents.append({
                'id': doc_id,
                'content': doc_data['content'],
                'metadata': doc_data['metadata'],
                'relevance_score': doc_data['score'],
                'semantic_score': doc_data['semantic_score'],
                'bm25_score': doc_data['bm25_score'],
                'distance': 1.0 - doc_data['semantic_score']  # For compatibility
            })
            total_relevance += doc_data['score']
        
        # Calculate average relevance score
        avg_relevance = total_relevance / len(final_documents) if final_documents else 0.0
        
        result = {
            "documents": final_documents,
            "relevance_score": avg_relevance,
            "retrieval_method": "hybrid",
            "weights": {
                "semantic": semantic_weight,
                "bm25": bm25_weight
            }
        }
        
        logger.info(f"Hybrid search returned {len(final_documents)} documents (avg relevance score: {avg_relevance:.3f})")
        
        return result
    
    def _apply_metadata_boost(
        self,
        combined_scores: Dict[str, Dict],
        boost_config: Dict[str, Dict[str, float]]
    ) -> None:
        """
        Apply metadata-based score boosting (in-place)
        
        Args:
            combined_scores: Dict of doc_id -> score_data to boost
            boost_config: Configuration for metadata boosting
                Example: {'doc_type': {'api': 1.5, 'readme': 1.0}}
        """
        for doc_id, doc_data in combined_scores.items():
            metadata = doc_data['metadata']
            
            for meta_key, boost_values in boost_config.items():
                meta_value = metadata.get(meta_key)
                if meta_value in boost_values:
                    boost_factor = boost_values[meta_value]
                    doc_data['score'] *= boost_factor
                    logger.debug(f"Boosted {doc_id[:8]}... by {boost_factor}x ({meta_key}={meta_value})")
