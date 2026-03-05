# AI Engineer Coding Exercise - RAG System

**Status:** 🔨 In Development  
**Timeline:** March 4-5, 2026 (2 Days)  
**Submission For:** Visa Full-Stack AI Engineer Position

---

## 🎯 Project Overview

A production-ready Retrieval-Augmented Generation (RAG) system built with FastAPI, ChromaDB, and Ollama, demonstrating enterprise-grade GenAI engineering with comprehensive evaluation framework.

### **Key Features**

- ✅ **FastAPI Backend** with production patterns (error handling, logging, config management)
- ✅ **Vector Database** (ChromaDB) for semantic search
- ✅ **Local LLM** (Ollama llama3:8b) with OpenAI-ready configuration
- ✅ **React Frontend** for user interaction
- ✅ **RAGAS Evaluation** framework with 5 metrics
- ✅ **Production Differentiation:**
  - Source attribution in all responses
  - "Unknown" handling for out-of-scope queries
  - Confidence thresholding and hallucination detection
  - Agent-style multi-step pipeline

---

## 📋 Assignment Requirements

This project fulfills the following deliverables:

1. ✅ **Data Preparation** - FastAPI documentation dataset (50 test queries)
2. ✅ **Backend Development** - FastAPI + ChromaDB + Ollama RAG system
3. ✅ **Evaluation Framework** - RAGAS metrics + custom metrics (response time, cost)
4. ✅ **Frontend Development** - React UI with query input and response display
5. ✅ **Documentation** - README + 2-3 page report + architecture docs

---

## 🚀 Quick Start

### **Prerequisites**

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Ollama (for local LLM)

### **Installation**

```bash
# Clone repository
git clone git@github.com:kefeimo/ai-engineer-coding-exercise.git
cd ai-engineer-coding-exercise

# Start with Docker Compose
docker-compose up -d

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### **Manual Setup (Without Docker)**

See [SETUP.md](docs/SETUP.md) for detailed manual installation instructions.

---

## 📚 Documentation

- **[Planning Document](docs/planning.md)** - Strategic approach and technical decisions
- **[Progress Tracking](docs/progress-tracking.md)** - Development progress and metrics
- **[Architecture](docs/ARCHITECTURE.md)** - System design and component descriptions *(Coming Soon)*
- **[Evaluation Report](docs/EVALUATION-REPORT.md)** - RAGAS metrics and improvements *(Coming Soon)*
- **[Future Improvements](docs/FUTURE-IMPROVEMENTS.md)** - Production scaling plans *(Coming Soon)*

---

## 🏗️ Project Structure

```
ai-engineer-coding-exercise/
├── docs/                           # Documentation
│   ├── assignment.md              # Original assignment
│   ├── planning.md                # Strategic planning
│   └── progress-tracking.md       # Progress checklist
├── backend/                        # FastAPI application
├── frontend/                       # React application
├── docker-compose.yml             # Docker setup
└── README.md                      # This file
```

---

## 🎯 Key Differentiators

### **Production Mindset**
- Error handling and logging from Day 1
- Configuration management with environment variables
- Proper project structure and type hints
- Unit tests for critical paths

### **Constrained Generation**
- Strict source attribution in all responses
- "Unknown/TBD" handling for out-of-scope queries
- Confidence scoring based on retrieval quality
- Hallucination detection with faithfulness checks

### **Evaluation Excellence**
- RAGAS framework with 5 metrics
- Custom metrics (response time, token cost, source coverage)
- Demonstrated improvement iteration (baseline → optimized)
- 50 realistic test queries from FastAPI documentation

### **Agent-Style Workflow**
- Multi-step pipeline: Query → Retrieval → Validation → Generation → Post-processing
- Conditional logic based on confidence scores
- State management between steps

---

## 📊 Evaluation Results

### **RAGAS Metrics** *(Target: Available after Hour 8)*

| Metric | Baseline | Improved | Change |
|--------|----------|----------|--------|
| Context Precision | TBD | TBD | TBD |
| Faithfulness | TBD | TBD | TBD |
| Answer Relevancy | TBD | TBD | TBD |
| Context Recall | TBD | TBD | TBD |
| Answer Correctness | TBD | TBD | TBD |

*See [EVALUATION-REPORT.md](docs/EVALUATION-REPORT.md) for detailed analysis.*

---

## 🛠️ Technology Stack

**Backend:**
- FastAPI (REST API framework)
- ChromaDB (vector database)
- Ollama (local LLM - llama3:8b)
- sentence-transformers (embeddings)
- RAGAS (evaluation framework)

**Frontend:**
- React 18 (Vite)
- Axios (API client)

**Infrastructure:**
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

---

## 🧪 Testing

```bash
# Run unit tests
cd backend
pytest tests/

# Run RAGAS evaluation
python -m app.rag.evaluation
```

---

## 📝 Development Log

- **March 4, 2026** - Project initialization, planning document created
- *(Progress updates will be tracked in [progress-tracking.md](docs/progress-tracking.md))*

---

## 🚧 Current Status

**Progress:** 0% (Pre-development)  
**Stage:** Stage 0 - Requirements & Setup  
**Next Steps:** Download FastAPI docs, setup project structure

See [progress-tracking.md](docs/progress-tracking.md) for detailed checklist.

---

## 👤 Author

**Kefei Mo**  
Full-Stack AI Engineer Candidate  
[GitHub](https://github.com/kefeimo) | [LinkedIn](https://linkedin.com/in/kefei-mo)

---

## 📄 License

This project is created for the Visa AI Engineer coding exercise.

---

*Last Updated: March 4, 2026*
