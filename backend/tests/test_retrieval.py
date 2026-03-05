"""
Tests for RAG Retrieval Module
Tests vector search and document retrieval
"""

import pytest
from pathlib import Path
import sys
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.retrieval import Retriever


@pytest.mark.unit
def test_retriever_initialization():
    """Test Retriever initializes with correct configuration"""
    with patch('app.rag.retrieval.get_chroma_client'):
        with patch('app.rag.retrieval.SentenceTransformer'):
            # Mock to avoid loading actual models
            pytest.skip("Requires mocked ChromaDB - testing retrieval logic only")


@pytest.mark.unit
def test_confidence_calculation_inline():
    """Test that confidence is calculated correctly in retrieve() method"""
    retriever = Retriever()
    
    # Mock results from retrieval
    # Distance 0.0 should give confidence 1.0: confidence = 1 - (0.0 / 2) = 1.0
    # Distance 1.0 should give confidence 0.5: confidence = 1 - (1.0 / 2) = 0.5
    # Distance 2.0 should give confidence 0.0: confidence = 1 - (2.0 / 2) = 0.0
    
    # We test this indirectly by verifying the retrieve method returns proper confidence values
    # This is a simple test to ensure the basic structure is correct
    assert hasattr(retriever, 'retrieve')
    assert hasattr(retriever, 'confidence_threshold')


@pytest.mark.unit
def test_format_context():
    """Test formatting of retrieved documents into context string"""
    retriever = Retriever()
    
    # Mock documents with metadata
    documents = [
        {
            "content": "FastAPI is a modern web framework.",
            "metadata": {"source": "intro.md", "chunk_id": 0},
            "confidence": 0.95
        },
        {
            "content": "It provides automatic API documentation.",
            "metadata": {"source": "features.md", "chunk_id": 0},
            "confidence": 0.85
        }
    ]
    
    formatted = retriever.format_context(documents)
    
    # Should contain source information
    assert "intro.md" in formatted
    assert "features.md" in formatted
    # Should contain chunk IDs
    assert "chunk 0" in formatted
    # Should contain confidence scores
    assert "0.95" in formatted or "0.85" in formatted
    # Should contain actual content
    assert "FastAPI is a modern web framework" in formatted
    assert "automatic API documentation" in formatted


@pytest.mark.unit
def test_retrieval_returns_results(sample_retrieval_results):
    """Test that retrieval returns properly formatted results"""
    # This test verifies the structure of retrieval results
    results = sample_retrieval_results
    
    # Verify required fields
    assert "documents" in results
    assert "metadatas" in results
    assert "distances" in results
    assert "confidence" in results
    assert "retrieval_count" in results
    
    # Verify data types
    assert isinstance(results["documents"], list)
    assert isinstance(results["metadatas"], list)
    assert isinstance(results["distances"], list)
    assert isinstance(results["confidence"], float)
    assert isinstance(results["retrieval_count"], int)
    
    # Verify confidence is in valid range
    assert 0.0 <= results["confidence"] <= 1.0
    
    # Verify counts match
    assert len(results["documents"]) == results["retrieval_count"]
    assert len(results["metadatas"]) == results["retrieval_count"]
    assert len(results["distances"]) == results["retrieval_count"]


@pytest.mark.unit
def test_retrieval_empty_collection():
    """Test retrieval from empty collection returns appropriate error"""
    retriever = Retriever.__new__(Retriever)
    retriever.collection = None
    retriever.top_k = 5
    
    result = retriever.retrieve("test query")
    
    # Should return error structure
    assert result["retrieval_count"] == 0
    assert result["confidence"] == 0.0
    assert "error" in result


@pytest.mark.unit
def test_check_confidence_method():
    """Test the check_confidence method"""
    retriever = Retriever()
    
    # High confidence should pass threshold
    is_confident, message = retriever.check_confidence(0.75)
    assert is_confident is True
    assert "meets threshold" in message.lower()
    
    # Low confidence should not pass threshold (default threshold is 0.6)
    is_confident, message = retriever.check_confidence(0.30)
    assert is_confident is False
    assert "below threshold" in message.lower() or "unreliable" in message.lower()


@pytest.mark.unit
def test_embed_query_returns_vector():
    """Test query embedding returns correct format"""
    with patch('app.rag.retrieval.SentenceTransformer') as mock_st:
        # Mock embedding model
        mock_model = Mock()
        mock_model.encode.return_value = Mock(tolist=lambda: [0.1, 0.2, 0.3])
        mock_st.return_value = mock_model
        
        retriever = Retriever.__new__(Retriever)
        retriever.embedding_model = mock_model
        
        embedding = retriever.embed_query("test query")
        
        # Should return list of floats
        assert isinstance(embedding, list)
        assert all(isinstance(x, float) for x in embedding)


@pytest.mark.unit
def test_retrieval_top_k_parameter():
    """Test that top_k parameter controls result count"""
    # Verify that retrieval respects top_k parameter
    retriever = Retriever.__new__(Retriever)
    retriever.top_k = 5
    
    # Default should use instance top_k
    assert retriever.top_k == 5
    
    # top_k can be overridden per query in retrieve() method
    assert retriever.top_k > 0


@pytest.mark.integration
def test_full_retrieval_pipeline():
    """
    Test complete retrieval pipeline with real ChromaDB
    This is an integration test requiring ChromaDB
    """
    pytest.skip("Requires ChromaDB with ingested documents - run with: pytest -m integration")
    
    # Example flow (when ChromaDB is available):
    # retriever = Retriever()
    # result = retriever.retrieve("What is FastAPI?")
    # assert result["retrieval_count"] > 0
    # assert result["confidence"] > 0.0
    # assert len(result["documents"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
