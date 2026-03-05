# AI Engineer Coding Exercise - RAG System

**Status:** 🔨 Stage 0 Complete - Beginning Implementation  
**Timeline:** March 4-5, 2026 (2 Days)  
**Submission For:** Visa Full-Stack AI Engineer Position

---

## 🎯 Project Overview

A production-ready Retrieval-Augmented Generation (RAG) system built with FastAPI, ChromaDB, and GPT4All, demonstrating enterprise-grade GenAI engineering with comprehensive evaluation framework.

**Dataset:** FastAPI documentation (12 markdown files covering tutorials, advanced topics, and deployment)

### **Key Features**

- 🔨 **FastAPI Backend** with production patterns (error handling, logging, config management)
- 🔨 **Vector Database** (ChromaDB) for semantic search with sentence-transformers embeddings
- 🔨 **Local LLM** (GPT4All mistral-7b-instruct) with OpenAI-ready configuration
- 🔨 **React Frontend** (Vite + Tailwind CSS) for user interaction
- 🔨 **LangChain** orchestration for RAG pipeline
- 🔨 **RAGAS Evaluation** framework with 5 metrics
- 🔨 **Production Differentiation:**
  - Source attribution in all responses
  - "Unknown" handling for out-of-scope queries (confidence threshold <0.65)
  - Confidence thresholding and hallucination detection
  - Agent-style multi-step pipeline

**Legend:** ✅ Complete | 🔨 In Development | ⏳ Planned

---

## 📋 Assignment Requirements

This project fulfills the following deliverables:

1. ✅ **Data Preparation** - FastAPI documentation dataset (12 files downloaded, 50 test queries planned)
2. 🔨 **Backend Development** - FastAPI + ChromaDB + GPT4All RAG system
3. 🔨 **Evaluation Framework** - RAGAS metrics (5 total) + custom metrics (response time, token cost, source coverage)
4. 🔨 **Frontend Development** - React + Vite + Tailwind CSS UI with query input and response display
5. ⏳ **Documentation** - README (in progress) + 2-3 page report + architecture docs

**Progress:** Stage 0 complete (setup & requirements). Beginning Stage 1A (Backend Core).

---

## 🚀 Quick Start

### **Prerequisites**

- Python 3.12+
- Node.js 20+ (use nvm for easy version management)
- Docker & Docker Compose (optional, for containerized deployment)
- 8GB RAM minimum (for GPT4All model)

### **Installation**

#### **Option 1: Local Development**

```bash
# Clone repository
git clone https://github.com/kefeimo/resume.git
cd resume/project/visa-full-stack-ai-engineer/ai-engineer-coding-exercise

# Setup Node.js with nvm (recommended)
nvm install  # Reads .nvmrc file (Node 20)
nvm use

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env if needed (defaults work for local development)

# Start backend (GPT4All will auto-download ~4GB model on first run)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend setup (in new terminal)
cd ../frontend
nvm use  # Ensure Node 20 is active
npm install
npm run dev

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

#### **Option 2: Docker Compose** ✅

**Production Build:**
```bash
# Build and start (optimized production build)
docker-compose up --build

# Or run in background
docker-compose up -d
```

**Development Mode (Hot Reload):**
```bash
# Start with hot reloading (changes reflect instantly)
docker-compose -f docker-compose-dev.yml up --build

# Code changes auto-reload without rebuild!
```

**Common Commands:**
```bash
# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Docker Benefits:**
- ✅ No Python/Node.js installation needed
- ✅ Consistent environment across machines
- ✅ Easy deployment to cloud
- ✅ Volume mounts for data persistence
- ✅ Health checks and auto-restart
- ✅ Development mode with hot reloading

See **[DOCKER.md](DOCKER.md)** for detailed Docker documentation and **[DOCKER-COMPOSE.md](DOCKER-COMPOSE.md)** for production vs development comparison.

---

## 📚 Documentation

- **[Planning Document](docs/planning.md)** - 20-hour strategic plan with technology decisions
- **[Progress Tracking](docs/progress-tracking.md)** - Real-time development progress and metrics
- **[Deliverables Checklist](docs/DELIVERABLES.md)** - All submission requirements tracked
- **[Assignment](docs/assignment.md)** - Original requirements
- **[Docker Guide](DOCKER.md)** - Docker deployment and troubleshooting ✅
- **[Backend README](backend/README.md)** - Backend API documentation
- **[Frontend Setup](frontend/SETUP.md)** - Frontend development guide
- **[Architecture](docs/ARCHITECTURE.md)** - System design and component descriptions *(Day 2)*
- **[Evaluation Report](docs/EVALUATION-REPORT.md)** - RAGAS metrics and improvements *(Day 2)*
- **[Future Improvements](docs/FUTURE-IMPROVEMENTS.md)** - Production scaling plans *(Day 2)*

---

## 🏗️ Project Structure

```
ai-engineer-coding-exercise/
├── docs/                              # Documentation
│   ├── assignment.md                 # Original assignment requirements
│   ├── planning.md                   # 20-hour strategic plan
│   ├── progress-tracking.md          # Development progress tracking
│   └── DELIVERABLES.md               # Submission checklist
├── data/                              # Dataset
│   └── documents/                    # FastAPI markdown docs (12 files)
├── backend/                           # FastAPI application
│   ├── app/                          # Application code
│   │   ├── rag/                      # RAG pipeline (ingestion, retrieval, generation)
│   │   └── utils/                    # Utilities (logging, validators)
│   ├── tests/                        # Unit tests (pytest)
│   ├── data/                         # Runtime data
│   │   ├── results/                  # Evaluation results
│   │   └── test_queries/             # Test query dataset
│   ├── requirements.txt              # Python dependencies
│   ├── .env.example                  # Configuration template
│   └── .env                          # Local configuration
├── frontend/                          # React application
│   └── src/                          # React components (Vite + Tailwind)
├── download_docs.sh                   # Script to download FastAPI docs
├── docker-compose.yml                 # Docker setup (coming in Stage 1B)
└── README.md                         # This file
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
