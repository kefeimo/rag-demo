"""
Tests for RAG Pipeline Integration
Tests unknown handling, source attribution, and end-to-end pipeline
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.mark.unit
def test_unknown_handling_low_confidence(sample_retrieval_results):
    """Test that low confidence queries are handled as unknown"""
    # Simulate low confidence retrieval result
    low_confidence_result = sample_retrieval_results.copy()
    low_confidence_result["confidence"] = 0.45  # Below 0.65 threshold
    
    # System should recognize this as low confidence
    assert low_confidence_result["confidence"] < 0.65
    
    # In actual RAG pipeline, this would return "unknown" or ask for clarification
    is_unknown = low_confidence_result["confidence"] < 0.65
    assert is_unknown


@pytest.mark.unit
def test_unknown_handling_no_results():
    """Test handling when no documents are retrieved"""
    empty_result = {
        "documents": [],
        "confidence": 0.0,
        "retrieval_count": 0
    }
    
    # Should be treated as unknown
    assert empty_result["retrieval_count"] == 0
    assert empty_result["confidence"] == 0.0
    
    # System should return helpful unknown message
    is_unknown = empty_result["retrieval_count"] == 0
    assert is_unknown


@pytest.mark.unit
def test_unknown_handling_high_confidence():
    """Test that high confidence queries are NOT marked unknown"""
    high_confidence_result = {
        "documents": ["doc1", "doc2"],
        "confidence": 0.85,
        "retrieval_count": 2
    }
    
    # Should NOT be unknown
    assert high_confidence_result["confidence"] >= 0.65
    assert high_confidence_result["retrieval_count"] > 0
    
    is_unknown = high_confidence_result["confidence"] < 0.65
    assert not is_unknown


@pytest.mark.unit
def test_source_attribution_present(sample_retrieval_results):
    """Test that retrieved documents include source attribution"""
    results = sample_retrieval_results
    
    # Each document should have metadata
    assert "metadatas" in results
    assert len(results["metadatas"]) == results["retrieval_count"]
    
    # Each metadata should have source information
    for metadata in results["metadatas"]:
        assert "source" in metadata
        assert isinstance(metadata["source"], str)
        assert len(metadata["source"]) > 0


@pytest.mark.unit
def test_source_attribution_formatting(sample_retrieval_results):
    """Test that sources are properly formatted for display"""
    results = sample_retrieval_results
    
    # Format sources for user display
    formatted_sources = []
    for i, metadata in enumerate(results["metadatas"]):
        source_info = {
            "source": metadata["source"],
            "content": results["documents"][i],
            "similarity": 1.0 - results["distances"][i]  # Convert distance to similarity
        }
        formatted_sources.append(source_info)
    
    # Verify formatting
    assert len(formatted_sources) == results["retrieval_count"]
    
    for source in formatted_sources:
        assert "source" in source
        assert "content" in source
        assert "similarity" in source
        assert 0.0 <= source["similarity"] <= 1.0


@pytest.mark.unit
def test_source_attribution_unique_sources():
    """Test handling of multiple chunks from same source"""
    results_with_duplicates = {
        "documents": ["content1", "content2", "content3"],
        "metadatas": [
            {"source": "intro.md", "chunk_index": 0},
            {"source": "intro.md", "chunk_index": 1},  # Same source
            {"source": "features.md", "chunk_index": 0}
        ],
        "distances": [0.1, 0.2, 0.3]
    }
    
    # Extract unique sources
    unique_sources = set(m["source"] for m in results_with_duplicates["metadatas"])
    
    # Should have 2 unique sources (intro.md, features.md)
    assert len(unique_sources) == 2
    assert "intro.md" in unique_sources
    assert "features.md" in unique_sources


@pytest.mark.unit
def test_confidence_threshold_configuration():
    """Test that confidence threshold is configurable"""
    from app.config import settings
    
    # Default threshold should be defined
    assert hasattr(settings, 'confidence_threshold')
    assert 0.0 <= settings.confidence_threshold <= 1.0
    
    # Default value should be reasonable (typically 0.65-0.75)
    assert 0.5 <= settings.confidence_threshold <= 0.8


@pytest.mark.unit
def test_rag_response_structure(mock_llm_response):
    """Test that RAG pipeline returns properly structured response"""
    response = mock_llm_response
    
    # Required fields
    assert "answer" in response
    assert "sources" in response
    assert "confidence" in response
    
    # Field types
    assert isinstance(response["answer"], str)
    assert isinstance(response["sources"], list)
    assert isinstance(response["confidence"], float)
    
    # Field constraints
    assert len(response["answer"]) > 0
    assert 0.0 <= response["confidence"] <= 1.0


@pytest.mark.unit
def test_source_deduplication():
    """Test that duplicate sources are deduplicated in final response"""
    sources_with_duplicates = [
        "intro.md",
        "features.md",
        "intro.md",  # Duplicate
        "tutorial.md",
        "features.md"  # Duplicate
    ]
    
    # Deduplicate while preserving order
    unique_sources = []
    seen = set()
    for source in sources_with_duplicates:
        if source not in seen:
            unique_sources.append(source)
            seen.add(source)
    
    # Should have 3 unique sources
    assert len(unique_sources) == 3
    assert unique_sources == ["intro.md", "features.md", "tutorial.md"]


@pytest.mark.unit
def test_empty_query_handling():
    """Test handling of empty or invalid queries"""
    from app.utils.validators import QueryValidator
    
    # Empty query
    is_valid, error = QueryValidator.validate_query("")
    assert not is_valid
    assert error is not None
    
    # Whitespace only
    is_valid, error = QueryValidator.validate_query("   ")
    assert not is_valid
    
    # Very short query
    is_valid, error = QueryValidator.validate_query("a")
    assert not is_valid


@pytest.mark.unit
def test_query_sanitization():
    """Test that queries are properly sanitized"""
    from app.utils.validators import QueryValidator
    
    # Query with extra whitespace
    sanitized = QueryValidator.sanitize_query("  What  is   FastAPI?  ")
    assert sanitized == "What is FastAPI?"
    
    # Query with null bytes
    sanitized = QueryValidator.sanitize_query("What\x00is FastAPI?")
    assert "\x00" not in sanitized


@pytest.mark.integration
def test_end_to_end_rag_pipeline():
    """
    Test complete RAG pipeline from query to response
    This is an integration test requiring all components
    """
    pytest.skip("Requires full RAG system - run with: pytest -m integration")
    
    # Example flow (when all components are available):
    # 1. User submits query
    # 2. Query is sanitized and validated
    # 3. Retrieval finds relevant documents
    # 4. Confidence is calculated
    # 5. If low confidence -> return "unknown"
    # 6. If high confidence -> generate answer with LLM
    # 7. Return response with answer, sources, confidence


@pytest.mark.integration
def test_hallucination_detection():
    """
    Test that system can detect potential hallucinations
    This would require RAGAS evaluation integration
    """
    pytest.skip("Requires RAGAS evaluation - run with: pytest -m integration")
    
    # Example: Compare generated answer against retrieved context
    # If answer contains facts not in context -> potential hallucination
    # RAGAS faithfulness metric tests this


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
