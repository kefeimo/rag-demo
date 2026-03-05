"""
Tests for RAG Generation Module
Tests prompt construction and LLM integration
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.generation import construct_prompt


@pytest.mark.unit
def test_construct_prompt_with_context():
    """Test building prompt with query and context documents"""
    query = "What is FastAPI?"
    context_docs = [
        {
            "content": "FastAPI is a modern, fast web framework for Python.",
            "metadata": {"source": "intro.md"},
            "confidence": 0.85
        },
        {
            "content": "FastAPI provides automatic API documentation.",
            "metadata": {"source": "features.md"},
            "confidence": 0.78
        }
    ]
    
    prompt = construct_prompt(query, context_docs)
    
    # Prompt should contain the query
    assert query in prompt
    
    # Prompt should contain the context
    assert "FastAPI" in prompt
    assert "modern, fast web framework" in prompt
    
    # Prompt should have system instructions
    assert any(keyword in prompt for keyword in ['context', 'CONTEXT', 'provided'])
    
    # Prompt should include sources
    assert "intro.md" in prompt
    assert "features.md" in prompt


@pytest.mark.unit
def test_prompt_includes_instructions():
    """Test that prompt includes proper instructions for LLM"""
    query = "What is FastAPI?"
    context_docs = [{"content": "FastAPI is a web framework.", "metadata": {"source": "intro.md"}, "confidence": 0.8}]
    
    prompt = construct_prompt(query, context_docs)
    
    # Should include instructions about using context
    assert any(keyword in prompt for keyword in ['ONLY', 'only', 'provided', 'context'])
    
    # Should mention handling unknown cases
    assert any(keyword in prompt for keyword in ["don't have", 'enough information'])


@pytest.mark.unit
def test_prompt_construction_empty_context():
    """Test prompt construction with empty context"""
    query = "What is FastAPI?"
    context_docs = []
    
    prompt = construct_prompt(query, context_docs)
    
    # Should still return a valid prompt
    assert len(prompt) > 0
    assert query in prompt
    assert "No relevant context found" in prompt or "CONTEXT" in prompt


@pytest.mark.unit
def test_prompt_format_consistency():
    """Test that prompts follow consistent format"""
    queries = [
        "What is FastAPI?",
        "How do I create an endpoint?",
        "Explain path parameters"
    ]
    
    context_docs = [{"content": "Context text here.", "metadata": {"source": "test.md"}, "confidence": 0.8}]
    
    prompts = []
    for query in queries:
        prompt = construct_prompt(query, context_docs)
        prompts.append(prompt)
    
    # All prompts should have similar structure
    for prompt in prompts:
        assert len(prompt) > 0
        # Should have CONTEXT and QUESTION sections
        assert "CONTEXT" in prompt or "context" in prompt.lower()
        assert "QUESTION" in prompt or "question" in prompt.lower()


@pytest.mark.unit
def test_prompt_with_multiple_sources():
    """Test prompt construction with multiple source documents"""
    query = "What is FastAPI?"
    context_docs = [
        {"content": "Doc 1 content", "metadata": {"source": "doc1.md"}, "confidence": 0.9},
        {"content": "Doc 2 content", "metadata": {"source": "doc2.md"}, "confidence": 0.8},
        {"content": "Doc 3 content", "metadata": {"source": "doc3.md"}, "confidence": 0.7}
    ]
    
    prompt = construct_prompt(query, context_docs)
    
    # Should include all sources
    assert "doc1.md" in prompt
    assert "doc2.md" in prompt
    assert "doc3.md" in prompt
    
    # Should include confidence scores
    assert "0.90" in prompt or "0.9" in prompt
    
    # Should maintain source order or show relevance
    assert len(prompt) > 200  # Should be substantive


@pytest.mark.unit
def test_prompt_length_reasonable():
    """Test that generated prompts are reasonable length"""
    query = "What is FastAPI?"
    context_docs = [{"content": "FastAPI is a web framework. " * 50, "metadata": {"source": "long.md"}, "confidence": 0.8}]
    
    prompt = construct_prompt(query, context_docs)
    
    # Prompt should exist but not be excessively long
    assert 100 < len(prompt) < 20000
    
    # Should include query
    assert query in prompt


@pytest.mark.unit
def test_prompt_special_characters():
    """Test prompt handles special characters correctly"""
    query = "How do I use @app.get('/') decorator?"
    context_docs = [{"content": "Use @app.get('/') to define a GET endpoint.", "metadata": {"source": "tutorial.md"}, "confidence": 0.85}]
    
    prompt = construct_prompt(query, context_docs)
    
    # Special characters should be preserved
    assert "@app.get" in prompt
    assert "('/')" in prompt or "('/')" in prompt.replace('"', "'")


@pytest.mark.unit
def test_construct_prompt_confidence_display():
    """Test that confidence scores are properly formatted"""
    query = "Test query"
    context_docs = [
        {"content": "Content", "metadata": {"source": "test.md"}, "confidence": 0.8543}
    ]
    
    prompt = construct_prompt(query, context_docs)
    
    # Confidence should be formatted (2 decimal places)
    assert "0.85" in prompt


@pytest.mark.unit
def test_construct_prompt_missing_metadata():
    """Test prompt construction with missing metadata fields"""
    query = "Test query"
    # Document with minimal metadata
    context_docs = [
        {"content": "Test content"}
    ]
    
    prompt = construct_prompt(query, context_docs)
    
    # Should still work with defaults
    assert len(prompt) > 0
    assert query in prompt
    assert "Test content" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

