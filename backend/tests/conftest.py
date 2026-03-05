"""
Pytest Configuration and Fixtures
Shared test setup, fixtures, and utilities
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import Settings


@pytest.fixture(scope="session")
def test_settings():
    """Create test configuration settings"""
    return Settings(
        # Use test-specific settings
        llm_provider="gpt4all",
        chroma_collection_name="test_collection",
        chunk_size=200,  # Smaller for testing
        chunk_overlap=20,
        top_k_results=3,
        confidence_threshold=0.65,
        log_level="DEBUG"
    )


@pytest.fixture(scope="function")
def temp_dir():
    """Create temporary directory for test files"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture(scope="function")
def sample_markdown_files(temp_dir):
    """Create sample markdown files for testing"""
    docs_dir = temp_dir / "docs"
    docs_dir.mkdir()
    
    # Sample document 1: Simple
    doc1 = docs_dir / "intro.md"
    doc1.write_text("""# Introduction to FastAPI

FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints.

## Key Features
- Fast: Very high performance, on par with NodeJS and Go
- Fast to code: Increase the speed of development
- Easy: Designed to be easy to use and learn
""")
    
    # Sample document 2: Code examples
    doc2 = docs_dir / "tutorial" / "first_steps.md"
    doc2.parent.mkdir(parents=True)
    doc2.write_text("""# First Steps

## Create a Path Operation

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

This creates a GET endpoint at the root path.
""")
    
    # Sample document 3: Advanced
    doc3 = docs_dir / "advanced" / "security.md"
    doc3.parent.mkdir(parents=True)
    doc3.write_text("""# Security

FastAPI provides several tools for security.

## OAuth2
OAuth2 is a specification that defines several ways to handle authentication and authorization.

## API Keys
You can use API keys for authentication.
""")
    
    return {
        "docs_dir": docs_dir,
        "files": [doc1, doc2, doc3],
        "count": 3
    }


@pytest.fixture(scope="function")
def sample_chunks():
    """Sample text chunks for testing"""
    return [
        {
            "content": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+.",
            "metadata": {
                "source": "intro.md",
                "chunk_index": 0,
                "file_size": 100
            }
        },
        {
            "content": "Key features include high performance, fast development, and easy to use.",
            "metadata": {
                "source": "intro.md",
                "chunk_index": 1,
                "file_size": 100
            }
        },
        {
            "content": "OAuth2 is a specification for authentication and authorization.",
            "metadata": {
                "source": "advanced/security.md",
                "chunk_index": 0,
                "file_size": 80
            }
        }
    ]


@pytest.fixture(scope="function")
def sample_retrieval_results():
    """Sample retrieval results for testing"""
    return {
        "documents": [
            "FastAPI is a modern web framework for Python.",
            "It provides automatic API documentation.",
            "FastAPI uses standard Python type hints."
        ],
        "metadatas": [
            {"source": "intro.md", "chunk_index": 0},
            {"source": "features.md", "chunk_index": 0},
            {"source": "intro.md", "chunk_index": 1}
        ],
        "distances": [0.15, 0.25, 0.30],
        "confidence": 0.85,
        "retrieval_count": 3
    }


@pytest.fixture(scope="function")
def sample_query():
    """Sample user query for testing"""
    return "What is FastAPI?"


@pytest.fixture(scope="function")
def sample_context():
    """Sample context for prompt testing"""
    return """
Source: intro.md
FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+.

Source: features.md
Key features include automatic API documentation, data validation, and async support.
"""


@pytest.fixture(scope="function")
def mock_llm_response():
    """Mock LLM response for testing"""
    return {
        "answer": "FastAPI is a modern web framework for building APIs with Python 3.7+. It provides high performance and automatic documentation.",
        "sources": ["intro.md", "features.md"],
        "confidence": 0.85
    }


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration between tests"""
    import logging
    # Remove all handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    yield


@pytest.fixture(scope="session")
def test_data_dir():
    """Path to test data directory"""
    return Path(__file__).parent / "test_data"


# Markers for test categorization
def pytest_configure(config):
    """Add custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")
