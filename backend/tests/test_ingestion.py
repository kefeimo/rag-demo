"""
Tests for Document Ingestion Pipeline
Tests document loading, chunking, and ChromaDB insertion
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.ingestion import DocumentLoader


@pytest.mark.unit
def test_document_loader_initialization():
    """Test DocumentLoader initializes with correct parameters"""
    loader = DocumentLoader(chunk_size=500, chunk_overlap=50)
    
    assert loader.chunk_size == 500
    assert loader.chunk_overlap == 50


@pytest.mark.unit
def test_load_documents(sample_markdown_files):
    """Test loading markdown documents from directory"""
    loader = DocumentLoader()
    docs = loader.load_documents(str(sample_markdown_files["docs_dir"]))
    
    # Should load all 3 markdown files
    assert len(docs) == 3
    
    # Each document should have content and metadata
    for doc in docs:
        assert "content" in doc
        assert "metadata" in doc
        assert len(doc["content"]) > 0
        assert "source" in doc["metadata"]
        assert "filename" in doc["metadata"]


@pytest.mark.unit
def test_load_documents_nonexistent_path():
    """Test loading from non-existent path raises error"""
    loader = DocumentLoader()
    
    with pytest.raises(FileNotFoundError):
        loader.load_documents("/nonexistent/path")


@pytest.mark.unit
def test_chunk_text_basic():
    """Test basic text chunking functionality"""
    loader = DocumentLoader(chunk_size=50, chunk_overlap=10)
    
    text = "This is a test document. " * 10  # 250 chars
    metadata = {"source": "test.md", "filename": "test.md"}
    
    chunks = loader.chunk_text(text, metadata)
    
    # Should create multiple chunks
    assert len(chunks) > 1
    
    # Each chunk should have content and metadata
    for i, chunk in enumerate(chunks):
        assert "content" in chunk
        assert "metadata" in chunk
        assert chunk["metadata"]["chunk_id"] == i  # Use chunk_id, not chunk_index
        assert len(chunk["content"]) <= 50 + 10  # chunk_size + overlap buffer


@pytest.mark.unit
def test_chunk_text_short_document():
    """Test chunking with document shorter than chunk size"""
    loader = DocumentLoader(chunk_size=500, chunk_overlap=50)
    
    text = "Short document."
    metadata = {"source": "short.md"}
    
    chunks = loader.chunk_text(text, metadata)
    
    # Should return single chunk
    assert len(chunks) == 1
    assert chunks[0]["content"] == text


@pytest.mark.unit
def test_chunk_text_preserves_metadata():
    """Test that chunking preserves document metadata"""
    loader = DocumentLoader(chunk_size=50, chunk_overlap=10)
    
    text = "x" * 200
    metadata = {"source": "test.md", "filename": "test.md", "custom_field": "value"}
    
    chunks = loader.chunk_text(text, metadata)
    
    for chunk in chunks:
        # Original metadata should be preserved
        assert chunk["metadata"]["source"] == "test.md"
        assert chunk["metadata"]["filename"] == "test.md"
        assert chunk["metadata"]["custom_field"] == "value"
        # New metadata should be added
        assert "chunk_id" in chunk["metadata"]  # Use chunk_id, not chunk_index
        assert "chunk_count" in chunk["metadata"]  # Use chunk_count, not total_chunks


@pytest.mark.unit

@pytest.mark.unit
def test_chunk_size_validation():
    """Test chunk size parameter validation"""
    # Valid configuration
    loader = DocumentLoader(chunk_size=500, chunk_overlap=50)
    assert loader.chunk_size == 500
    assert loader.chunk_overlap == 50
    
    # Chunk overlap larger than chunk size (edge case)
    loader = DocumentLoader(chunk_size=100, chunk_overlap=150)
    # Should still initialize (validation happens during chunking)
    assert loader.chunk_overlap == 150


@pytest.mark.integration
def test_full_ingestion_pipeline(sample_markdown_files, temp_dir):
    """
    Test complete document ingestion pipeline
    This is an integration test requiring ChromaDB
    """
    # This test would require ChromaDB setup
    # Mark as integration test to run separately
    pytest.skip("Requires ChromaDB integration - run with: pytest -m integration")
    
    # Example flow (when ChromaDB is available):
    # loader = DocumentLoader()
    # docs = loader.load_documents(str(sample_markdown_files["docs_dir"]))
    # chunks = loader.chunk_documents(docs)
    # ingestion = ChromaDBIngestion()
    # result = ingestion.ingest_chunks(chunks)
    # assert result["success"] == True
    # assert result["chunk_count"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
