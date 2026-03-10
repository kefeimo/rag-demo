"""
RAG Retrieval Module
Vector search and document retrieval from ChromaDB
"""

import logging
from typing import List, Dict, Any, Tuple
from app.config import settings
from app.rag.embeddings import EmbeddingProvider
from app.rag.utils import get_chroma_client

logger = logging.getLogger(__name__)


class Retriever:
    """Retrieve relevant documents from ChromaDB"""
    
    def __init__(self, collection_name: str = None):
        """Initialize retriever with ChromaDB connection and embedding model"""
        self.persist_directory = settings.chroma_persist_directory
        self.collection_name = collection_name or settings.chroma_collection_name
        self.embedding_model_name = settings.embedding_model
        self.top_k = settings.top_k_results
        self.relevance_threshold = settings.relevance_threshold
        
        # Use singleton ChromaDB client
        self.client = get_chroma_client()
        
        # Load embedding model
        logger.info(f"Loading embedding model: {self.embedding_model_name}")
        self.embedding_model = EmbeddingProvider()
        
        # Get collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Retriever initialized (collection={self.collection_name}, count={self.collection.count()})")
        except Exception as e:
            logger.error(f"Failed to get collection {self.collection_name}: {str(e)}")
            self.collection = None
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for query text
        
        Args:
            query: Query text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        return self.embedding_model.encode(query)
    
    def retrieve(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """
        Retrieve relevant documents for query
        
        Args:
            query: User query text
            top_k: Number of results to retrieve (overrides default)
            
        Returns:
            Dictionary with retrieved documents, relevance_score, and metadata
        """
        if self.collection is None:
            logger.error("Collection not initialized. Run document ingestion first.")
            return {
                "documents": [],
                "relevance_score": 0.0,
                "retrieval_count": 0,
                "error": "Collection not initialized"
            }
        
        if self.collection.count() == 0:
            logger.error("Collection is empty. Run document ingestion first.")
            return {
                "documents": [],
                "relevance_score": 0.0,
                "retrieval_count": 0,
                "error": "Collection is empty"
            }
        
        k = top_k or self.top_k
        
        logger.info(f"Retrieving top-{k} documents for query: {query[:100]}...")
        
        try:
            # Generate query embedding
            query_embedding = self.embed_query(query)
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            documents = []
            if results['documents'] and len(results['documents'][0]) > 0:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    # Convert distance to similarity score (cosine: 0=identical, 2=opposite)
                    # relevance_score = 1 - (distance / 2)
                    relevance_score = max(0.0, 1.0 - (distance / 2.0))
                    
                    documents.append({
                        "content": doc,
                        "metadata": metadata,
                        "relevance_score": round(relevance_score, 4),
                        "distance": round(distance, 4),
                        "rank": i + 1
                    })
            
            # Calculate overall relevance score (average of top results)
            if documents:
                overall_relevance = sum(d["relevance_score"] for d in documents) / len(documents)
            else:
                overall_relevance = 0.0
            
            logger.info(f"Retrieved {len(documents)} documents (avg relevance score: {overall_relevance:.3f})")
            
            return {
                "documents": documents,
                "relevance_score": round(overall_relevance, 4),
                "retrieval_count": len(documents),
                "query": query
            }
            
        except Exception as e:
            logger.error(f"Retrieval error: {str(e)}", exc_info=True)
            return {
                "documents": [],
                "relevance_score": 0.0,
                "retrieval_count": 0,
                "error": str(e)
            }
    
    def format_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Format retrieved documents into context string for LLM
        
        Args:
            documents: List of retrieved document dictionaries
            
        Returns:
            Formatted context string with source attribution
        """
        if not documents:
            return ""
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc["metadata"].get("source", "unknown")
            chunk_id = doc["metadata"].get("chunk_id", 0)
            relevance_score = doc.get("relevance_score", 0.0)
            
            context_parts.append(
                f"[Source {i}: {source} (chunk {chunk_id}, relevance: {relevance_score:.2f})]\n"
                f"{doc['content']}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def check_relevance(self, relevance_score: float) -> Tuple[bool, str]:
        """
        Check if retrieval relevance score meets threshold
        
        Args:
            relevance_score: Retrieval relevance score to check
            
        Returns:
            Tuple of (is_relevant, message)
        """
        is_relevant = relevance_score >= self.relevance_threshold
        
        if is_relevant:
            message = f"Relevance score {relevance_score:.3f} meets threshold {self.relevance_threshold}"
        else:
            message = f"Relevance score {relevance_score:.3f} below threshold {self.relevance_threshold} - retrieved documents too weakly matched"
        
        logger.info(message)
        return is_relevant, message
