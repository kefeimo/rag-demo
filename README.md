# AI Engineer Coding Exercise - RAG System

![Frontend Preview](docs/img/rag-system-frontend.gif)

---

## 🎯 Project Overview

A production-ready Retrieval-Augmented Generation (RAG) system built with FastAPI, ChromaDB, and OpenAI GPT-3.5-turbo, demonstrating enterprise-grade GenAI engineering with comprehensive evaluation framework and domain-aware prompt engineering.

**Dataset:** Visa Chart Components (VCC) technical documentation (161 markdown files, 2.14MB)

### **Key Features**

- ✅ **FastAPI Backend** with production patterns (error handling, logging, config management)
- ✅ **Vector Database** (ChromaDB) for semantic search with sentence-transformers embeddings
- ✅ **OpenAI GPT-3.5-turbo** with LangChain prompt templates and domain awareness
- ✅ **React Frontend** (Vite + Tailwind CSS) with query history and confidence indicators
- ✅ **LangChain** orchestration for RAG pipeline with domain-specific prompts
- ✅ **RAGAS Evaluation** framework with 3 metrics (faithfulness, answer relevancy, context precision)
- ✅ **Production Differentiation:**
  - Source attribution in all responses with document metadata
  - "Unknown" handling for out-of-scope queries (confidence threshold <0.65)
  - Domain-aware prompt templates (VCC, FastAPI, general) with acronym mappings
  - Query history tracking with last 10 queries
  - Response time monitoring and API versioning
  - Confidence indicators with visual feedback (green/yellow/red)
  - Agent-style multi-step pipeline with validation (semantic search → confidence check → hybrid BM25 fallback → LLM generation or graceful rejection)

---

## 🚀 Quick Start

### **Prerequisites**

- **Docker & Docker Compose** (recommended)
- **LLM backend** — choose one:
  - **OpenAI** (recommended): set `LLM_PROVIDER=openai` + `OPENAI_API_KEY` in `backend/.env`
  - **GPT4All** (no API key needed): set `LLM_PROVIDER=gpt4all` — the model (`mistral-7b-instruct`, ~4GB) is downloaded automatically on first run and cached at `~/.cache/gpt4all/` on your host

### **Installation**

#### **Option 1: Docker Compose** ✅ Recommended

No Python or Node.js setup needed. Source code is volume-mounted so edits to `backend/` and `frontend/src/` reflect instantly without rebuilding.

```bash
git clone https://github.com/kefeimo/ai-engineer-coding-exercise.git
cd ai-engineer-coding-exercise

# Copy and configure environment
cp backend/.env.example backend/.env
# Edit backend/.env and set OPENAI_API_KEY=sk-your-key-here

# Start with hot reload (documents auto-ingested on startup)
docker compose -f docker-compose-dev.yml up --build
```

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

See **[DOCKER.md](docs/DOCKER.md)** for GPU support, common commands, and troubleshooting.

#### **Option 2: Local Development**

<details>
<summary>Expand for manual setup steps</summary>

**Prerequisites:** Python 3.11+, Node.js 20+

```bash
# 1. Clone
git clone https://github.com/kefeimo/ai-engineer-coding-exercise.git
cd ai-engineer-coding-exercise

# 2. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add OPENAI_API_KEY
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. Frontend (new terminal)
cd frontend
npm install && npm run dev
```

</details>

---

## 📖 Usage Guide

### **Basic Query Flow**

1. **Open the Frontend:** Navigate to http://localhost:5173
2. **Enter Your Question:** Type a question about VCC (e.g., "What is Visa Chart Components?")
3. **View Response:** The system will:
   - Retrieve relevant documents from ChromaDB
   - Generate answer using OpenAI GPT-3.5-turbo with domain-aware prompts
   - Display answer with confidence score, sources, and metadata
4. **Check Query History:** View your last 10 queries in the sidebar
5. **Review Sources:** Click on source cards to see full document content

### **Example Queries**

**VCC-Specific Queries:**
```
- What is Visa Chart Components?
- What is VCC?  (system handles acronyms)
- How do I implement accessibility in VCC?
- What are the main features of VCC?
- How do I customize chart components?
```

**FastAPI Documentation (Alternative Dataset):**
```
- How do I create a FastAPI application?
- What is dependency injection in FastAPI?
- How do I handle authentication in FastAPI?
```

### **Understanding Confidence Scores**

The system uses confidence scores to indicate answer quality:

- 🟢 **High (≥80%)**: Strong match, highly relevant sources
- 🟡 **Medium (65-79%)**: Acceptable match, review sources
- 🔴 **Low (<65%)**: Weak match, answer may be uncertain

**Low Confidence Warning:**
When confidence < 65%, you'll see a warning banner:
> ⚠️ Low Confidence Answer - This response is based on limited or less relevant information. Please verify with source documents.

### **Using the API Directly**

**Query Endpoint:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Visa Chart Components?",
    "collection_name": "visa_chart_components",
    "top_k": 5
  }'
```

**Response Format:**
```json
{
  "answer": "Visa Chart Components (VCC) is...",
  "confidence": 0.847,
  "sources": [
    {
      "content": "VCC provides...",
      "metadata": {
        "source": "docs/README.md",
        "chunk_id": "chunk_0",
        "doc_type": "repo_docs"
      },
      "confidence": 0.889
    }
  ],
  "model": "gpt-3.5-turbo",
  "response_time": 1.234,
  "api_version": "0.2.0"
}
```

**Health Check:**
```bash
curl http://localhost:8000/health

# Response: {"status": "healthy"}
```

**API Documentation:**
Interactive API docs at http://localhost:8000/docs (Swagger UI)

### **Switching Datasets**

To query different documentation:

1. **Ingest New Dataset:**
```bash
cd backend
source venv/bin/activate

# Ingest FastAPI docs
python ingest_fastapi_docs.py

# Or ingest VCC docs
python ingest_visa_docs.py
```

2. **Update Query Collection:**
   - In Frontend: The collection name is automatically detected
   - In API: Set `collection_name` parameter in request body

### **Query History**

The frontend tracks your last 10 queries:
- Click any previous query to re-run it
- See confidence scores and response times
- Helps track your exploration pattern

---

## 📚 Documentation

**📄 Technical Report (start here):**
- [docs/technical-report.md](docs/technical-report.md) — 2-3 page summary: approach, implementation highlights, and evaluation results

**Setup & Deployment:**
- [DOCKER.md](docs/DOCKER.md) — Docker commands, GPU support, container management
- [docs/DOCKER-COMPOSE.md](docs/DOCKER-COMPOSE.md) — dev vs production compose comparison
- [docs/DOCKER-GPU.md](docs/DOCKER-GPU.md) — GPU acceleration setup
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — common issues and full reset guide

**Architecture & Design:**
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system design, data flow, component overview
- [docs/TECH-STACK-RATIONALE.md](docs/TECH-STACK-RATIONALE.md) — why each technology was chosen

**Evaluation:**
- [docs/EVALUATION-REPORT.md](docs/EVALUATION-REPORT.md) — RAGAS metrics results and analysis
- [docs/HYBRID-SEARCH-CASE-STUDY.md](docs/HYBRID-SEARCH-CASE-STUDY.md) — BM25 + semantic search improvement study
- [docs/RAGAS-METRICS-REFERENCE.md](docs/RAGAS-METRICS-REFERENCE.md) — metrics definitions and interpretation
- [docs/VCC-BASELINE-SUMMARY.md](docs/VCC-BASELINE-SUMMARY.md) — VCC query baseline results
- [data-pipeline/GOLDEN-TEST-CASES.md](data-pipeline/GOLDEN-TEST-CASES.md) — curated high-quality test queries

**Lessons & Notes:**
- [docs/lesson-learned.md](docs/lesson-learned.md) — development retrospective
- [docs/PROMPT-IMPROVEMENT.md](docs/PROMPT-IMPROVEMENT.md) — prompt engineering notes

---

## 🏗️ Project Structure

```
ai-engineer-coding-exercise/
├── backend/          # FastAPI app, RAG pipeline, ingestion scripts
├── frontend/         # React + Vite + Tailwind CSS UI
├── evaluation/       # RAGAS evaluation framework
├── data-pipeline/    # VCC document extraction tools
├── data/             # ChromaDB persistence, source docs, test queries
├── docs/             # Architecture, planning, and evaluation reports
├── docker-compose.yml
└── docker-compose-dev.yml
```

For a detailed breakdown of components and data flow, see **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

---

---

## 🛠️ Technology Stack

**Backend:**
- **FastAPI 0.115.6** - Modern async REST API framework
- **ChromaDB 0.4.24** - Vector database for semantic search
- **OpenAI GPT-3.5-turbo** - Production LLM for generation
- **LangChain 0.3.14** - Prompt templates and RAG orchestration
- **sentence-transformers** - all-MiniLM-L6-v2 embeddings (384 dimensions)
- **RAGAS 0.2.8** - Evaluation framework for RAG systems
- **Pydantic 2.10.5** - Data validation and settings management
- **Uvicorn 0.34.0** - ASGI server for async handling

**Frontend:**
- **React 18.3.1** - UI library with hooks
- **Vite 6.0.11** - Fast build tool and dev server
- **Tailwind CSS 3.4.17** - Utility-first CSS framework
- **Axios 1.7.9** - HTTP client for API requests
- **React Markdown** - Markdown rendering with syntax highlighting

**Infrastructure:**
- **Docker 24.0+** - Containerization
- **Docker Compose V2** - Multi-container orchestration
- **Python 3.11+** - Backend runtime
- **Node.js 20+** - Frontend build toolchain

**Key Libraries:**
- `langchain_core.prompts.PromptTemplate` - Structured prompt engineering
- `chromadb.Client` - Vector database client
- `sentence_transformers.SentenceTransformer` - Embedding generation
- `openai.OpenAI` - OpenAI API client
- `pytest` - Testing framework with 98%+ coverage

---

## 🧪 Testing & Evaluation

### Unit Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

### RAGAS Evaluation

Measures RAG quality across three metrics: **faithfulness**, **answer relevancy**, and **context precision**.

```bash
# Step 1: Query the RAG system
cd evaluation
python run_ragas_stage1_query.py --input ../data/test_queries/baseline_20.json

# Step 2: Generate reference answers
python run_ragas_stage1b_generate_references.py

# Step 3: Compute RAGAS metrics (requires OPENAI_API_KEY)
python run_ragas_stage2_eval.py
```

See [evaluation/README.md](evaluation/README.md) and [docs/EVALUATION-REPORT.md](docs/EVALUATION-REPORT.md) for results and full documentation.

---

## 🔧 Troubleshooting

| Issue | Quick Fix |
|-------|-----------|
| "OpenAI API key not found" | `cp backend/.env.example backend/.env` and set `OPENAI_API_KEY` |
| Collection not found | Restart the stack — documents are auto-ingested on startup |
| Frontend can't connect | Check `curl http://localhost:8000/health` and `docker compose logs backend` |
| Port already in use | `lsof -ti :8000 \| xargs kill -9` / `lsof -ti :5173 \| xargs kill -9` |
| Docker build fails | `docker compose down -v && docker compose up --build --no-cache` |
| Slow responses (>60s) | Set `LLM_PROVIDER=openai` in `.env`; reduce `TOP_K=3` |
| Low confidence scores | Re-ingest docs; rephrase query; verify correct collection toggle |

For detailed solutions and full reset instructions, see **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)**.

---

## 👤 Author

**Kefei Mo**  
Full-Stack AI Engineer Candidate  
[GitHub](https://github.com/kefeimo) | [LinkedIn](https://linkedin.com/in/kefei-mo)

---

## 📄 License

This project is created as a coding exercise for the **Visa Full-Stack AI Engineer** position.  
All code is original work by Kefei Mo, March 2026.

---

## 🙏 Acknowledgments

- **Visa Chart Components Team** for the excellent documentation that served as the dataset
- **FastAPI Community** for the comprehensive tutorials and guides
- **LangChain** for prompt template abstractions
- **RAGAS** for the evaluation framework
- **ChromaDB** for the vector database solution

---

*Last Updated: March 6, 2026 - README restructure: Docker-first quickstart, simplified sections*
