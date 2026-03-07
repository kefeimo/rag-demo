# Backend - RAG System API

FastAPI-based Retrieval-Augmented Generation (RAG) system for FastAPI documentation using ChromaDB, GPT4All, and sentence-transformers.

## 🚀 Quick Start

```bash
# 1. Setup environment
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Access Points:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## 📖 Usage Example

### 1. Ingest Documents

#### FastAPI Docs (`fastapi_docs` collection)
```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"document_path": "../data/documents/", "force_reingest": false}'
```

**Response:**
```json
{
  "status": "success",
  "documents_processed": 10,
  "chunks_created": 165,
  "time_elapsed": "3.06s"
}
```

#### VCC Docs (`vcc_docs` collection)

In Docker the raw JSON files are mounted automatically. Locally, pass the explicit host paths:

```bash
curl -X POST http://localhost:8000/api/v1/ingest/visa-docs \
  -H "Content-Type: application/json" \
  -d '{
    "force_reingest": false,
    "repo_docs_path": "../data-pipeline/data/raw/visa_repo_docs.json",
    "code_docs_path": "../data-pipeline/data/raw/visa_code_docs.json",
    "issue_qa_path":  "../data-pipeline/data/raw/visa_issue_qa.json"
  }'
```

> **Tip:** Use absolute paths if the server is not started from the project root, e.g.
> `"/home/<user>/project/ai-engineer-coding-exercise/data-pipeline/data/raw/visa_repo_docs.json"`

**Response:**
```json
{
  "status": "success",
  "documents_processed": 276,
  "chunks_created": 2696,
  "time_elapsed": "19.45s"
}
```

#### Verify Ingestion

After ingesting, confirm both collections are populated with a quick query:

```bash
# Verify FastAPI docs
curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is FastAPI?", "collection": "fastapi_docs", "top_k": 1}' \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print('confidence:', r['confidence'])"

# Verify VCC docs
curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Visa Chart Components?", "collection": "vcc_docs", "top_k": 1}' \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print('confidence:', r['confidence'])"
```

Expected: `confidence: 0.8+` for both. A score of `0.0` with an error answer means the collection is empty — re-run the matching ingest command above.

### 2. Query the System

The `collection` field selects which ChromaDB collection to search. If omitted, it defaults to the `CHROMA_COLLECTION_NAME` env var.

Available collections:
- `fastapi_docs` — FastAPI framework documentation
- `vcc_docs` — Visa Chart Components documentation

```bash
# Query FastAPI docs
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is FastAPI?", "top_k": 3, "collection": "fastapi_docs"}'

# Query VCC docs
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I use bar charts?", "top_k": 3, "collection": "vcc_docs"}'
```

**Response:**
```json
{
  "query": "What is FastAPI?",
  "answer": "FastAPI is an open-source web framework for building APIs with Python 3.6+ based on standard Python type hints. It provides a fast (high-performance), web-safe interface for creating APIs with Python...\n\nReference(s): tutorial/first-steps.md",
  "sources": [
    {
      "content": "author and team behind **FastAPI**...",
      "metadata": {
        "source": "tutorial/first-steps.md",
        "chunk_id": 27
      },
      "confidence": 0.8284
    }
  ],
  "confidence": 0.8099,
  "model": "gpt4all"
}
```

---

## 📁 Project Structure

```
backend/
├── app/                        # Application code
│   ├── __init__.py
│   ├── main.py                # FastAPI app & endpoints
│   ├── config.py              # Configuration management
│   ├── models.py              # Pydantic models
│   ├── rag/                   # RAG pipeline modules
│   │   ├── __init__.py
│   │   ├── ingestion.py       # Document loading & chunking
│   │   ├── retrieval.py       # Vector search & retrieval
│   │   └── generation.py      # LLM generation
│   └── utils/                 # Utility modules
│       ├── __init__.py
│       ├── logging.py         # Logging configuration
│       └── validators.py      # Input validation helpers
├── data/                      # Runtime data
│   ├── chroma_db/            # ChromaDB persistence (auto-created)
│   ├── results/              # Evaluation results
│   └── test_queries/         # Test query datasets
├── tests/                     # Unit tests
│   └── test_basic.py
├── venv/                      # Virtual environment (not in git)
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variable template
├── .env                      # Local configuration (not in git)
└── README.md                 # This file
```

## ⚙️ Configuration

Key settings in `.env`:

```bash
# LLM & Embeddings
LLM_PROVIDER=gpt4all
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# RAG Parameters
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RESULTS=5
CONFIDENCE_THRESHOLD=0.65

# ChromaDB
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
CHROMA_COLLECTION_NAME=fastapi_docs
```

**Note:** GPT4All model (~4GB) auto-downloads to `~/.cache/gpt4all/` on first run.

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app & endpoints
│   ├── config.py            # Configuration
│   ├── models.py            # Pydantic models
│   └── rag/
│       ├── utils.py         # ChromaDB singleton
│       ├── ingestion.py     # Document loading & chunking
│       ├── retrieval.py     # Vector search
│       └── generation.py    # LLM generation
├── data/
│   ├── documents/           # Source documents
│   └── chroma_db/           # Vector database (auto-created)
├── requirements.txt
└── .env
```
  "documents_processed": 12,
  "chunks_created": 245,
  "time_elapsed": "3.2s"
}
```

### **Interactive API Documentation**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🧪 Testing

### **Run Unit Tests**

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_basic.py

# Run with verbose output
pytest -v
```

### **Manual Testing with curl**

```bash
# Health check
curl http://localhost:8000/health

# Query endpoint (collection defaults to CHROMA_COLLECTION_NAME if omitted)
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is FastAPI?", "collection": "fastapi_docs"}'

# Ingest documents
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"document_path": "../data/documents/"}'
```

### **Manual Testing with Python**

```python
import requests

# Query
response = requests.post(
    "http://localhost:8000/api/v1/query",
## 🧪 Testing

```bash
# Health check
curl http://localhost:8000/health

# Python test script
python test_rag.py

# Unit tests
pytest tests/
```

## 🔧 Development

```bash
# Format code
black app/

# Run with auto-reload
uvicorn app.main:app --reload
```

##  Troubleshooting

**Port already in use:**
```bash
lsof -i :8000
kill -9 <PID>
```

**Clear ChromaDB:**
```bash
rm -rf data/chroma_db/
# Restart server and re-ingest
```

**GPT4All model location:**
- Auto-downloads to `~/.cache/gpt4all/` (~4GB)
- First query takes extra time for download

## 🏗️ Architecture

**RAG Pipeline:**
1. Query → Embedding (sentence-transformers)
2. Vector Search (ChromaDB) → Top-K retrieval
3. Confidence check (≥0.65)
4. LLM Generation (GPT4All) with context
5. Response with sources

**Stack:**
- FastAPI + uvicorn (API)
- ChromaDB (vector database)
- sentence-transformers (embeddings)
- GPT4All mistral-7b-instruct (LLM)

---

**Status:** Stage 1A Complete ✅  
**Version:** 1.0.0
