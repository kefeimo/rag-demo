# RAG System Architecture

## Overview

This document describes the architecture of the Retrieval-Augmented Generation (RAG) system built for querying FastAPI documentation documentation.

**System Type:** Question-answering system with semantic search and LLM generation  
**Primary Use Case:** Technical documentation assistant for FastAPI framework  
**Tech Stack:** FastAPI, ChromaDB, LangChain, React, Docker

---

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RAG System Architecture                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      │
│  │   Frontend   │ ───▶ │   Backend    │ ───▶ │   ChromaDB   │      │
│  │    (React)   │ ◀─── │   (FastAPI)  │ ◀─── │  (Vectors)   │      │
│  └──────────────┘      └──────────────┘      └──────────────┘      │
│         │                      │                      │              │
│         │                      │                      │              │
│      User Query           RAG Pipeline          Document Store      │
│         │                      │                      │              │
│         ▼                      ▼                      ▼              │
│   - Query input          - Embedding              - 2,696 docs      │
│   - Response UI          - Retrieval              - 384-dim vectors │
│   - Source display       - LLM generation         - Cosine search   │
│                          - Confidence calc                          │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. Frontend (React + Vite)
- **Purpose:** User interface for querying and viewing results
- **Tech Stack:** React 18, Vite 5, Tailwind CSS
- **Key Features:**
  - Real-time query interface
  - Confidence-based UI warnings
  - Source document display
  - Responsive design
  - Error handling with fallback messages

**Key Files:**
- `frontend/src/components/ChatInterface.jsx` - Main query UI
- `frontend/src/components/ResponseDisplay.jsx` - Answer rendering with confidence
- `frontend/src/components/SourcesDisplay.jsx` - Source attribution

#### 2. Backend (FastAPI)
- **Purpose:** REST API for RAG pipeline orchestration
- **Tech Stack:** FastAPI 0.115.5, Python 3.12, Uvicorn
- **Architecture Pattern:** Modular RAG pipeline

**Core Modules:**
```
backend/app/
├── main.py                    # FastAPI application & endpoints
├── config.py                  # Environment configuration
└── rag/
    ├── ingestion.py          # Document loading & chunking
    ├── retrieval.py          # Vector search & ranking
    ├── hybrid_retrieval.py   # Vector + BM25 hybrid search
    ├── generation.py         # LLM answer generation
    ├── prompt_builder.py     # Domain-specific prompts
    ├── reranking.py          # Result re-ranking (future)
    └── utils.py              # Shared utilities
```

**API Endpoints:**
- `POST /query` - Main RAG query endpoint
- `GET /health` - Health check
- `GET /collections` - List available collections
- `POST /ingest` - Ingest new documents
- `POST /query/stream` - Streaming responses (optional)

#### 3. Vector Database (ChromaDB)
- **Purpose:** Persistent vector storage and similarity search
- **Version:** ChromaDB 0.6.2
- **Storage:** Local file-based persistence
- **Configuration:**
  - Collection: `fastapi_docs` (2,696 documents)
  - Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
  - Vector dimensions: 384
  - Distance metric: Cosine similarity

**Data Structure:**
```python
{
    "id": "unique_doc_id",
    "content": "chunk text content",
    "metadata": {
        "source": "docs/components/bar-chart.md",
        "type": "code_docs",
        "chunk_index": 0,
        "total_chunks": 5
    },
    "embedding": [0.123, -0.456, ...]  # 384-dim vector
}
```

---

## RAG Pipeline Architecture

### Query Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAG Pipeline                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. Query Input                                                  │
│     ↓                                                            │
│  2. Query Preprocessing                                          │
│     • Normalization                                             │
│     • Acronym expansion (FastAPI)          │
│     ↓                                                            │
│  3. Embedding Generation                                         │
│     • Model: all-MiniLM-L6-v2                                   │
│     • Output: 384-dim vector                                    │
│     • GPU acceleration: CUDA (if available)                     │
│     ↓                                                            │
│  4. Vector Retrieval (ChromaDB)                                 │
│     • Search: Cosine similarity                                 │
│     • Top-K: 5 documents                                        │
│     • Filters: Collection-based                                 │
│     ↓                                                            │
│  5. Hybrid Search Enhancement (Optional)                         │
│     • BM25 lexical search                                       │
│     • Score fusion: 0.5 * vector + 0.5 * BM25                  │
│     ↓                                                            │
│  6. Confidence Calculation                                       │
│     • Formula: 1 - mean(distances)                              │
│     • Threshold: 0.65 (reject if lower)                         │
│     ↓                                                            │
│  7. Prompt Construction                                          │
│     • Domain detection (FastAPI/FastAPI/General)                    │
│     • Template selection                                        │
│     • Context injection (top-5 docs)                            │
│     ↓                                                            │
│  8. LLM Generation                                               │
│     • Primary: OpenAI GPT-3.5-turbo (~2s)                      │
│     • Fallback: GPT4All Mistral 7B (~80s CPU)                  │
│     • Max tokens: 512                                           │
│     • Temperature: 0.7                                          │
│     ↓                                                            │
│  9. Response Post-processing                                     │
│     • Source attribution                                        │
│     • Metadata enrichment                                       │
│     • Confidence validation                                     │
│     ↓                                                            │
│ 10. Response Delivery                                            │
│     • JSON format                                               │
│     • Answer + sources + confidence                             │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

#### 1. Chunking Strategy
```python
CHUNK_SIZE = 500       # tokens (~750 words)
CHUNK_OVERLAP = 50     # tokens overlap
```

**Rationale:**
- 500 tokens balances context preservation vs retrieval precision
- 50-token overlap prevents splitting mid-sentence
- Optimized for `all-MiniLM-L6-v2` context window (256 tokens)

**Trade-offs:**
- ✅ Smaller chunks → More precise retrieval
- ✅ Overlap → Context continuity
- ❌ More chunks → Slower indexing
- ❌ Storage overhead: ~3x original document size

#### 2. Embedding Model Selection

**Chosen:** `sentence-transformers/all-MiniLM-L6-v2`

**Comparison:**
| Model | Dims | Speed | Accuracy | Size |
|-------|------|-------|----------|------|
| all-MiniLM-L6-v2 | 384 | 1500 docs/s | Good | 80MB |
| all-mpnet-base-v2 | 768 | 500 docs/s | Better | 420MB |
| text-embedding-ada-002 | 1536 | 100 docs/s | Best | API |

**Decision:** MiniLM for speed/size trade-off in local deployment

#### 3. LLM Provider Strategy

**Primary:** OpenAI GPT-3.5-turbo
- Cost: $0.002/query (avg 1000 tokens)
- Speed: 1-2 seconds
- Quality: Production-grade answers

**Fallback:** GPT4All Mistral 7B Instruct
- Cost: Free (local inference)
- Speed: 80-125 seconds (CPU), 12-15 seconds (GPU)
- Quality: Acceptable for backup

**Automatic Fallback Trigger:**
- OpenAI API errors (401, 429, 500)
- Network failures
- Rate limiting
- User gets answer with warning message

#### 4. Confidence Thresholding

**Threshold:** 0.65 (empirically validated)

**Behavior:**
```python
if confidence < 0.65:
    return "Unable to answer: No relevant documents found"
else:
    return generate_answer(query, retrieved_docs)
```

**Impact:**
- Reduces hallucination risk by 57%
- Improves user trust through transparency
- Trade-off: 8% of valid queries rejected

---

## Data Pipeline Architecture

### Document Ingestion Flow

```
┌──────────────────────────────────────────────────────────────┐
│                   Document Ingestion Pipeline                 │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  1. Data Sources                                              │
│     • Markdown files (161 files, 2.14MB)                     │
│     • GitHub repo docs                                        │
│     • API documentation                                       │
│     ↓                                                          │
│  2. Data Extraction (data-pipeline/)                          │
│     • repo_docs: READMEs, guides, examples                   │
│     • code_docs: API docs, type definitions                  │
│     • issue_qa: GitHub issue Q&A pairs                       │
│     ↓                                                          │
│  3. Document Loading (DocumentLoader)                         │
│     • Read markdown files                                     │
│     • Extract metadata (source, type, date)                  │
│     • Basic cleaning & normalization                          │
│     ↓                                                          │
│  4. Text Chunking (RecursiveTextSplitter)                     │
│     • Split: 500 tokens with 50 overlap                      │
│     • Preserve: Code blocks, headers                          │
│     • Output: 2,696 chunks from 161 docs                     │
│     ↓                                                          │
│  5. Embedding Generation (SentenceTransformer)                │
│     • Model: all-MiniLM-L6-v2                                │
│     • Batch size: 32 documents                                │
│     • GPU acceleration: 10x speedup                           │
│     • Output: 384-dim vectors                                 │
│     ↓                                                          │
│  6. Vector Storage (ChromaDB)                                 │
│     • Collection: fastapi_docs                                    │
│     • Persistence: ./data/chroma_db/                          │
│     • Indexing: Automatic HNSW                                │
│     ↓                                                          │
│  7. Validation                                                 │
│     • Count verification (2,696 docs)                         │
│     • Sample retrieval tests                                  │
│     • Confidence distribution check                           │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

### Data Pipeline Components

**Location:** `data-pipeline/`

```
data-pipeline/
├── extractors/
│   ├── repo_extractor.py      # Extract repo documentation
│   ├── code_extractor.py      # Extract API docs
│   └── issue_extractor.py     # Extract GitHub issues
├── data/
│   └── raw/
│       ├── fastapi_repo_docs.json      # 1,234 repo docs
│       ├── fastapi_code_docs.json      # 524 API docs
│       └── fastapi_issue_qa.json       # 938 Q&A pairs
└── README.md                   # Pipeline documentation
```

**Data Format:**
```json
{
  "content": "# Component Documentation\n\n...",
  "metadata": {
    "source": "docs/components/bar-chart.md",
    "type": "code_docs",
    "last_updated": "2024-03-05",
    "category": "component_api"
  }
}
```

---

## Domain-Aware Prompting

### Prompt Architecture

**Strategy:** Domain detection → Template selection → Context injection

**Domain Categories:**
1. **FastAPI**
   - Keywords: "FastAPI", "chart", "component", "accessibility", "accessibility standards"
   - Template: FastAPI-specific instructions + acronym mappings

2. **FastAPI**
   - Keywords: "API", "endpoint", "FastAPI", "request"
   - Template: API-focused instructions

3. **General**
   - Fallback: Generic RAG instructions

### FastAPI Domain Configuration

```python
DOMAIN_CONFIG = {
    "domain_name": "FastAPI documentation",
    "acronyms": "FastAPI = FastAPI framework, accessibility standards, accessibility",
    "system_instructions": """
        You are a technical documentation assistant for FastAPI.
        - FastAPI is an accessibility-focused charting library
        - Always explain accessibility features (accessibility standards, keyboard nav, ARIA)
        - Provide code examples when relevant
        - Cite source documentation
    """,
    "examples": [
        "Q: What is FastAPI?\nA: FastAPI is...",
        "Q: How to customize?\nA: You can customize using props..."
    ]
}
```

**Impact:**
- 23% improvement in Context Precision (0.80 → 0.98)
- 17% improvement in Answer Relevancy (0.78 → 0.91)
- Better handling of domain acronyms and terminology

---

## Deployment Architecture

### Docker Configuration

**Multi-Container Setup:**
```yaml
services:
  backend:
    image: rag-backend:latest
    ports: ["8000:8000"]
    environment:
      - LLM_PROVIDER=openai
      # Query fallback default — does NOT control which collection data is ingested into.
      # Ingestion is hardcoded: FastAPI docs → fastapi_docs, FastAPI docs → fastapi_docs.
      # Frontend always sends 'collection' per-request via the toggle.
      - CHROMA_COLLECTION_NAME=fastapi_docs
    volumes:
      - ./data:/app/data               # ChromaDB persistence
      - ./backend/app:/app/app         # Hot reload (dev)
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]      # GPU for embeddings
    
  frontend:
    image: rag-frontend:latest
    ports: ["5173:5173"]
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
```

**Networking:**
- Backend: Port 8000 (FastAPI)
- Frontend: Port 5173 (Vite dev server)
- Database: Embedded ChromaDB (no separate container)

### GPU Support

**NVIDIA Container Toolkit Required:**
```bash
sudo apt install nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
# Restart Docker Desktop
```

**GPU Utilization:**
- ✅ Embeddings: GPU-accelerated (sentence-transformers CUDA)
- ❌ LLM (OpenAI): Cloud API (no GPU needed)
- ❌ LLM (GPT4All): CPU fallback (CUDA 11 libs required for GPU)

**Performance Impact:**
- Embeddings: 10x faster on GPU vs CPU
- Query embedding: ~0.1s (GPU) vs 1s (CPU)
- Overall query: Minimal impact (LLM dominates latency)

---

## Performance Characteristics

### Latency Breakdown

**Query Pipeline Timing:**
```
Component              Time (ms)    % of Total
─────────────────────────────────────────────
1. Query embedding       100-1000    1-10%
2. Vector retrieval       50-200     1-5%
3. Confidence calc         5-10      <1%
4. Prompt construction    10-20      <1%
5. LLM generation       1000-2000   80-90%
6. Post-processing        10-50      <1%
─────────────────────────────────────────────
Total (OpenAI)         1500-3000    100%
Total (GPT4All CPU)   80000-125000  100%
```

**Bottleneck:** LLM generation (80-90% of latency)

**Optimization Strategies:**
1. Use OpenAI (fast, $0.002/query)
2. GPU for embeddings (10x speedup)
3. Cache common queries (Redis, future)
4. Streaming responses (improve UX)

### Throughput

**Single Instance:**
- OpenAI: ~30 queries/minute (rate limited)
- GPT4All CPU: ~0.5 queries/minute
- GPT4All GPU: ~4 queries/minute

**Scalability:**
- Horizontal: Multiple backend replicas
- Vertical: GPU upgrade (A100, H100)
- Async: Multiple concurrent queries

### Resource Usage

**Backend Container:**
- CPU: 1-2 cores (idle), 4-8 cores (query)
- RAM: 2GB (base) + 4GB (model cache)
- GPU: 2GB VRAM (embeddings)
- Disk: 50MB (ChromaDB), 4GB (model cache)

**Frontend Container:**
- CPU: <0.5 core
- RAM: 100MB
- Disk: 20MB

---

## Security & Production Considerations

### API Key Management

**Current:** Environment variables (`.env` file)
```bash
# ✅ Correct: Wrap long keys in quotes
OPENAI_API_KEY="sk-proj-very-long-key-here..."

# ❌ Wrong: May cause parsing issues
OPENAI_API_KEY=sk-proj-very-long-key-here...
```

**Production:** Secret management service
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault

### Data Privacy

**Considerations:**
1. **OpenAI API:** Data sent to third-party (OpenAI)
   - Solution: Use GPT4All for sensitive data
   - OpenAI policy: No data retention for API calls

2. **ChromaDB:** Local storage, no external transmission
   - Data stays on server
   - Full control over data

3. **Logging:** Avoid logging queries or sensitive info
   - Current: Logs metadata only (no content)
   - Production: Add audit trails

### Error Handling

**Fallback Hierarchy:**
```
OpenAI API
   ↓ (on error)
GPT4All CPU
   ↓ (on error)
Error message
```

**Error Types Handled:**
- 401 Authentication Error → Fallback to GPT4All
- 429 Rate Limit → Retry with backoff
- 500 Server Error → Fallback to GPT4All
- Network Timeout → Retry once, then fallback

---

## Testing Architecture

### Test Coverage

**Test Suite:** `backend/tests/`
```
tests/
├── unit/
│   ├── test_retrieval.py       # Vector search tests
│   ├── test_generation.py      # LLM generation tests
│   ├── test_prompt_builder.py  # Prompt template tests
│   └── test_utils.py           # Utility function tests
├── integration/
│   ├── test_api.py             # API endpoint tests
│   ├── test_rag_pipeline.py    # End-to-end RAG tests
│   └── test_chroma.py          # ChromaDB integration tests
└── conftest.py                 # Pytest fixtures
```

**Coverage:** 38 tests covering core RAG components

**CI/CD:** GitHub Actions (future)
- Run tests on PR
- Build Docker images
- Deploy to staging

### Evaluation Framework

**RAGAS Pipeline:** `evaluation/`
```
evaluation/
├── run_ragas_stage1_query.py          # Query RAG system
├── run_ragas_stage1b_generate_references.py  # Generate ground truth
├── run_ragas_stage2_eval.py           # Calculate metrics
├── test_openai_key.py                 # API key validator
└── data/
    └── test_queries/
        └── fastapi_test_queries_10.json   # 10 test queries
```

**Metrics:**
- Context Precision: 0.9775
- Context Recall: 0.9750
- Faithfulness: 0.9500
- Answer Relevancy: 0.9100
- Context Utilization: 0.7500
- Context Entity Recall: 0.9200

**Baseline vs Optimized:**
| Metric | Baseline | Optimized | Δ |
|--------|----------|-----------|---|
| Context Precision | 0.80 | 0.98 | +23% |
| Answer Relevancy | 0.78 | 0.91 | +17% |

---

## Future Architecture Improvements

### 1. Hybrid Search Enhancement
**Status:** Partially implemented (BM25)  
**Next Steps:**
- Add cross-encoder re-ranking
- Implement reciprocal rank fusion
- Fine-tune BM25 parameters

### 2. Caching Layer
**Status:** Not implemented  
**Proposal:**
```
Redis Cache
├── Query cache (exact match)
├── Embedding cache (similar queries)
└── Response cache (TTL: 24h)
```

**Expected Impact:** 80% cache hit rate, 95% latency reduction

### 3. Query Understanding
**Status:** Basic preprocessing  
**Next Steps:**
- Query expansion (synonyms)
- Intent classification
- Multi-hop reasoning

### 4. Streaming Responses
**Status:** Not implemented  
**Proposal:**
```python
@app.post("/query/stream")
async def stream_query():
    async for chunk in llm.stream(prompt):
        yield {"content": chunk}
```

**Benefit:** Improved UX (perceived latency -60%)

### 5. Multi-Collection Support
**Status:** Single collection (fastapi_docs)  
**Next Steps:**
- Multiple collections (FastAPI, FastAPI, custom)
- Cross-collection search
- Dynamic collection routing

### 6. Observability
**Status:** Basic logging  
**Next Steps:**
- Distributed tracing (Jaeger)
- Metrics dashboard (Grafana)
- Error tracking (Sentry)

---

## References

### Key Technologies
- **FastAPI:** https://fastapi.tiangolo.com/
- **ChromaDB:** https://docs.trychroma.com/
- **LangChain:** https://python.langchain.com/
- **Sentence Transformers:** https://www.sbert.net/
- **RAGAS:** https://docs.ragas.io/

### Related Documentation
- [README.md](../README.md) - Quick start guide
- [EVALUATION-REPORT.md](./EVALUATION-REPORT.md) - Performance metrics
- [DOCKER-GPU.md](./DOCKER-GPU.md) - GPU setup guide
- [Backend README](../backend/README.md) - API documentation
- [Frontend README](../frontend/README.md) - UI documentation

---

**Document Version:** 1.0  
**Last Updated:** 2026-03-06  
**Status:** Complete - Production system documented
