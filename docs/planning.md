# AI Engineer Coding Exercise - Strategic Planning Document

**Project:** RAG System Implementation for FastAPI Company  
**Timeline:** 2 Days (16-20 hours)  
**Date:** March 4-5, 2026  
**Objective:** Demonstrate production-ready GenAI engineering skills with focus on planning, evaluation, and SDLC best practices

---

## ✅ **Stack Alignment with Day 1-4 Projects**

**This coding exercise uses 100% of the technology stack from your existing projects:**

| Component | This Exercise | Your Day 1-4 Projects | Status |
|-----------|---------------|----------------------|--------|
| **Backend** | FastAPI | Day 2 FastAPI-K8s | ✅ Aligned |
| **Vector DB** | ChromaDB | Day 1-2 ChromaDB | ✅ Aligned |
| **Local LLM** | GPT4All | Day 1-2 GPT4All | ✅ Aligned |
| **Cloud LLM** | OpenAI (optional) | Day 1-2 OpenAI | ✅ Aligned |
| **RAG Framework** | LangChain | Day 1-2 LangChain | ✅ Aligned |
| **Embeddings** | sentence-transformers | Day 1-2-4 sentence-transformers | ✅ Aligned |
| **Evaluation** | RAGAS | Day 4 RAGAS | ✅ Aligned |
| **Frontend** | React 19 + Vite | Day 3 React + Vite | ✅ Aligned |
| **Styling** | Tailwind CSS | Day 3 Tailwind CSS | ✅ Aligned |
| **API Client** | Axios | Day 3 Axios | ✅ Aligned |
| **Container** | Docker Compose | Day 2 Docker Compose | ✅ Aligned |
| **Testing** | pytest | Day 2 pytest | ✅ Aligned |

**🎯 Key Advantage:** You can leverage all your Day 1-4 learning and code patterns directly!

---

## 🎯 Strategic Positioning

### **What This Project Showcases**

Based on qualification evaluation, this project emphasizes:

1. **Production Mindset Throughout** - Not just working code, but production-ready patterns
2. **Constrained Generation Strength** - Strict source attribution, hallucination detection
3. **Agent-Style Workflow** - Multi-step pipeline with validation and state management
4. **Evaluation as First-Class Citizen** - RAGAS framework with iterative improvements
5. **Planning & SDLC Excellence** - Clear requirements, testing strategy, documentation

### **Key Distinguishing Strengths**

- ✅ **Production-ready from Day 1:** Error handling, logging, config management
- ✅ **Realistic testing with quality dataset:** 20-50 queries from FastAPI documentation
- ✅ **Evaluation-driven development:** Show baseline → improvements with metrics
- ✅ **Enterprise mindset:** Unknown handling, source attribution, confidence thresholding
- ✅ **Interview adaptability:** Code designed for easy modification

---

## 📋 Core Decisions & Rationale

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Dataset** | FastAPI Documentation | Relevant to assignment, abundant quality docs, realistic queries, saves 2 hours vs FastAPI Company repos exploration |
| **LLM** | GPT4All (mistral-7b) primary, OpenAI-ready config | Free, aligned with Day 1-2 experience, shows infrastructure skills, easy to switch for better quality if needed |
| **Vector DB** | ChromaDB | Lightweight, Python-native, sufficient for assignment scale, easy local setup |
| **Evaluation** | Start 3 metrics/20 queries → Expand 5 metrics/50 queries | Core functionality first, expand if ahead of schedule |
| **Frontend** | Minimal React (functional, not fancy) | Backend/evaluation are differentiators, not UI/UX |
| **Testing** | 5 key unit tests + RAGAS evaluation | Shows testing culture without time sink |
| **Documentation** | README + 2-3 page report + FUTURE-IMPROVEMENTS.md | Demonstrates communication and strategic thinking |
| **Deployment** | Local only (Docker Compose) | Live deployment sacrificed for code quality in 2-day timeline |

---

## 🏗️ System Architecture Overview

### **High-Level Pipeline**

```
User Query
    ↓
[1. Query Validation]
    ↓
[2. Retrieval (ChromaDB)]
    ↓
[3. Confidence Check] ─→ Low confidence? → Return "Unknown/Need clarification"
    ↓ High confidence
[4. Context Validation]
    ↓
[5. Prompt Construction] (with strict source attribution instructions)
    ↓
[6. LLM Generation (GPT4All/OpenAI)]
    ↓
[7. Post-Processing] (hallucination check, source extraction)
    ↓
Response + Sources + Confidence Score
```

### **Technology Stack**

**Backend:**
- FastAPI (REST API) ✅ **Aligned with Day 2**
- ChromaDB (vector database) ✅ **Aligned with Day 1-2**
- ~~Ollama (local LLM)~~ → **Use GPT4All** ✅ **Aligned with Day 1-2** (you used gpt4all, not Ollama)
- OpenAI (optional upgrade via config toggle) ✅ **Aligned with Day 1-2**
- LangChain (RAG orchestration) ✅ **ADD - Used in Day 1-2**
- sentence-transformers (embeddings) ✅ **Aligned with Day 1-2-4**
- RAGAS (evaluation framework) ✅ **Aligned with Day 4**

**Frontend:**
- React 19 (Vite) ✅ **Aligned with Day 3**
- Axios (API calls) ✅ **Aligned with Day 3**
- ~~Basic CSS~~ → **Tailwind CSS** ✅ **Aligned with Day 3** (you used Tailwind in day3-react-fundamentals)

**Infrastructure:**
- Docker Compose (local development) ✅ **Aligned with Day 2**
- Python 3.11+
- Node 18+

**Testing:**
- pytest (unit tests) ✅ **Aligned with Day 2**
- RAGAS (RAG quality evaluation) ✅ **Aligned with Day 4**

**📝 Stack Alignment Notes:**
- **100% aligned** with your existing Day 1-4 projects
- **Key correction:** Using **GPT4All** instead of Ollama (matches your Day 1-2 choice)
- **Enhancement:** Adding **LangChain** for RAG orchestration (you used it in all projects)
- **UI correction:** Using **Tailwind CSS** instead of basic CSS (matches Day 3)
- All other choices perfectly match your existing projects

---

## 📅 Detailed Timeline Breakdown

### **DAY 1: Working End-to-End System (8-10 hours)**

#### **Hour 0-1: Stage 0 - Requirements & Setup**
**Goal:** Deep understanding + environment ready

- [ ] Re-read assignment requirements (15 min)
- [ ] Document deliverables checklist (10 min)
- [ ] Download FastAPI documentation (10 min)
  - Source: https://fastapi.tiangolo.com/
  - Extract: Tutorial, User Guide, Advanced User Guide
  - Format: Markdown files (~500KB total)
- [ ] Setup project structure (15 min)
- [ ] Initialize git repository (5 min)
- [ ] Create initial README skeleton (5 min)

**Deliverable:** Project skeleton + dataset ready

---

#### **Hours 1-5: Stage 1A - Backend Core**
**Goal:** FastAPI + ChromaDB + GPT4All working

**Hour 1-2: Document Ingestion Pipeline**
- [ ] Install dependencies (15 min)
  ```bash
  fastapi, uvicorn, chromadb, sentence-transformers, 
  python-dotenv, pydantic, langchain, langchain-community, gpt4all
  ```
- [ ] Implement document loader (30 min)
  - Parse FastAPI markdown docs
  - Text chunking (500 chars, 50 overlap)
  - Metadata extraction (doc title, section, URL)
- [ ] Implement ChromaDB ingestion (30 min)
  - Collection creation
  - Embedding generation
  - Batch insertion
- [ ] Test ingestion with 10 docs (15 min)

**Hour 2-3: RAG Query Pipeline**
- [ ] Implement `/query` endpoint (45 min)
  - Input validation (Pydantic models)
  - Retrieval logic (top-k=5)
  - Context formatting
  - Error handling
- [ ] Implement retrieval confidence scoring (15 min)
  - Based on similarity scores
  - Threshold: <0.65 = "unknown"

**Hour 3-4: LLM Integration**
- [ ] Setup GPT4All client (15 min)
  - Download mistral-7b-instruct model
  - Test connection
- [ ] Implement prompt construction (30 min)
  - System prompt: "Use ONLY provided context"
  - User prompt template with sources
  - "Unknown" instruction
- [ ] Implement generation endpoint (30 min)
  - Call GPT4All
  - Parse response
  - Extract source citations
- [ ] Add OpenAI-ready config (15 min)
  - Environment variable toggle
  - Abstracted LLM client interface

**Hour 4-5: Production Patterns**
- [ ] Add logging (30 min)
  - Request/response logging
  - Error logging
  - Performance metrics (latency)
- [ ] Add error handling (15 min)
  - Try-except blocks
  - Graceful degradation
  - User-friendly error messages
- [ ] Config management (15 min)
  - .env file structure
  - Config validation
  - Defaults for all settings

**Deliverable:** Working FastAPI backend with RAG

---

#### **Hours 5-8: Stage 1B - Frontend + Docker**
**Goal:** React UI + Docker Compose

**Hour 5-6: React Frontend (Minimal)**
- [ ] Vite React setup (10 min)
- [ ] Single page component (50 min)
  - Query input textarea
  - Submit button
  - Loading state
  - Response display
  - Sources list with confidence scores
  - Error display
  - **Tailwind CSS** for clean, professional styling (aligned with Day 3)

**Hour 6-7: Integration + Docker**
- [ ] Connect frontend to backend (20 min)
  - Axios setup
  - CORS configuration
  - API calls
- [ ] Docker Compose setup (40 min)
  - Backend Dockerfile
  - Frontend Dockerfile
  - docker-compose.yml
  - Volume mounts for development

**Hour 7-8: Stage 1C - Basic Evaluation**
- [ ] Create 20 test queries (30 min)
  - 6 easy (factual): "What is FastAPI?" "How to install?"
  - 10 medium (procedural): "How to add authentication?" "How to handle file uploads?"
  - 4 hard (complex): "Compare FastAPI vs Flask performance" "Best practices for async endpoints"
- [ ] Setup RAGAS (15 min)
  - Install ragas package
  - Configure metrics
- [ ] Run baseline evaluation (15 min)
  - 3 metrics: context_precision, faithfulness, answer_relevancy
  - Document scores in EVALUATION-REPORT.md

**Deliverable:** Full working system with baseline scores

**🎯 Day 1 Success Criteria:**
- ✅ Can ingest FastAPI docs
- ✅ Can query and get responses
- ✅ Frontend displays results with sources
- ✅ Docker Compose works
- ✅ Baseline RAGAS scores documented
- ✅ Could submit this if needed

---

### **DAY 2: Quality + Differentiation (8-10 hours)**

#### **Hours 8-10: Stage 2A - Code Quality**
**Goal:** Production-ready code

**Hour 8-9: Code Refactoring**
- [ ] Add type hints throughout (30 min)
- [ ] Add docstrings (Google style) (30 min)
- [ ] Refactor into clean modules (30 min)
  ```
  backend/
  ├── app/
  │   ├── main.py
  │   ├── config.py
  │   ├── models.py (Pydantic)
  │   ├── rag/
  │   │   ├── ingestion.py
  │   │   ├── retrieval.py
  │   │   ├── generation.py
  │   │   └── evaluation.py
  │   └── utils/
  │       ├── logging.py
  │       └── validators.py
  ```

**Hour 9-10: Testing**
- [ ] Write 5 key unit tests (60 min)
  1. `test_document_ingestion()` - Verify chunking works
  2. `test_retrieval_returns_results()` - Query returns top-k
  3. `test_prompt_construction()` - Template includes sources
  4. `test_unknown_handling()` - Low confidence → "unknown" response
  5. `test_source_attribution()` - Response includes source references
- [ ] Setup pytest configuration (10 min)
- [ ] Run tests, ensure all pass (10 min)

**Deliverable:** Clean, tested codebase

---

#### **Hours 10-13: Stage 2B - Evaluation Enhancement**
**Goal:** Showcase RAGAS expertise

**Hour 10-11: Run Full Baseline Evaluation**
- [x] ✅ 20-query baseline prepared with difficulty levels (easy/medium/hard)
- [x] ✅ 3-stage RAGAS pipeline implemented and tested
- [x] ✅ All 5 metrics validated with 3-query test
- [ ] Run full 20-query baseline (15 min)
  - Stage 1A: Query RAG system
  - Stage 1B: Generate references (OpenAI)
  - Stage 2: Evaluate with all 5 metrics
  - Expected: ~10-15 minutes, ~$1 OpenAI cost
- [ ] Document baseline results (15 min)
  - Calculate aggregate statistics (mean, min, max)
  - Identify lowest-scoring queries
  - Note: Enhanced analytics (percentiles, bad_case_rate) deferred to Hour 12
- [ ] Commit baseline results (5 min)
- [ ] Quick review: Any critical issues blocking Stage 2A? (5 min)

**Hour 11-12: Stage 2A - Code Quality** (if time permits, can defer to end)
- [ ] Core refactoring (30 min)
  - Add type hints and docstrings
  - Split into clean modules (config, models, rag/*)
- [ ] Write 3-5 key unit tests (30 min)

**Hour 12-13: Improvement Iteration**
- [ ] Enhanced RAGAS analysis framework (20 min)
  - Create `run_ragas_analysis.py` with distribution stats
  - Add percentile calculations (P10, P25, P75, P90)
  - Add bad_case_rate tracking (threshold: 0.4)
  - Add failure categorization (retrieval, hallucination, ambiguous, etc.)
  - Generate debugging dashboard output
- [ ] Analyze baseline with enhanced framework (10 min)
  - Identify worst 5-10 cases per metric
  - Categorize failure patterns
  - Prioritize improvement areas
- [ ] Implement targeted improvement (30 min)
  - **Option A: Prompt Engineering** (if faithfulness <0.7)
    - Migrate to LangChain PromptTemplate
    - Add few-shot examples (good vs bad answers)
    - Strengthen "DO NOT infer" rules
  - **Option B: Retrieval Optimization** (if context_precision <0.8)
    - Tune chunk size or top_k
    - Add query expansion
    - Test MMR for diversity
  - **Option C-E:** Other options from planning (embedding upgrade, hybrid, reranking)
- [ ] Re-evaluate with same queries (10 min)
- [ ] Document improvement with comparison table (10 min)
- [ ] Analyze baseline results to identify improvement opportunities (5 min)
  - Low faithfulness → Prompt engineering needed
  - Low context precision → Retrieval tuning needed
  - Low answer relevancy → Better query understanding needed
- [ ] Implement improvement based on evaluation (30 min)
  
  **Option A: Prompt Engineering (if faithfulness <0.7)**
  - Migrate to LangChain PromptTemplate for better management
    - Benefits: Variable validation, template versioning, reusability
    - Enable A/B testing of different prompt versions
  - Add few-shot examples showing:
    - Good: Answer citing specific sources
    - Bad: Answer making inferences beyond context
  - Strengthen system instructions:
    - More explicit "DO NOT infer" rules
    - Require citation format: "According to [Source X]..."
  - Add output formatting instructions
  
  **Option B: Retrieval Optimization (if context_precision <0.8)**
  - Tune chunk size (current: 500 chars)
    - Test 800 chars (more context per chunk)
    - Test 300 chars (more precise matching)
  - Adjust top_k parameter (current: 5)
    - Try k=3 for higher precision
    - Try k=10 for better recall
  - Add query expansion:
    - Extract key terms from query
    - Include synonyms in retrieval
  - Implement MMR (Maximal Marginal Relevance):
    - Balance relevance vs diversity
    - Reduce redundant context
  
  **Option C: Embedding Model Upgrade (if time permits)**
  - Switch from all-MiniLM-L6-v2 to larger model
  - Options: all-mpnet-base-v2 (better quality, slower)
  - Re-index documents with new embeddings
  
  **Option D: Hybrid Retrieval (advanced)**
  - Combine semantic + keyword (BM25) search
  - Weight: 0.7 semantic + 0.3 BM25
  - Better for technical queries with specific terms
  
  **Option E: Reranking (if context_recall <0.7)**
  - Add cross-encoder reranker after retrieval
  - Re-score top 10 candidates, return top 5
  - Models: ms-marco-MiniLM-L-12-v2

- [ ] Re-evaluate with same 20/50 queries (15 min)
- [ ] Document improvement methodology and results (10 min)
- [ ] Create comparison table (5 min)
  ```
  Metric          | Baseline | After Improvement | Change
  ----------------|----------|-------------------|-------
  Context Prec.   | 0.72     | 0.84             | +16%
  Faithfulness    | 0.68     | 0.88             | +29%
  Answer Relevancy| 0.81     | 0.86             | +6%
  Context Recall  | 0.75     | 0.82             | +9%
  ```

**Deliverable:** Comprehensive evaluation with demonstrated improvement and clear methodology

---

#### **Hours 13-16: Stage 2C - Production Differentiation**
**Goal:** Showcase unique strengths

**Hour 13-14: Constrained Generation Features**
- [ ] Enhance "Unknown/TBD" handling (30 min)
  - Detect out-of-scope queries
  - Return helpful message: "This is outside FastAPI documentation. Try asking about..."
  - Log unknown queries for analysis
- [ ] Add hallucination detection (30 min)
  - Post-generation faithfulness check
  - If faithfulness <0.7, flag response
  - Option to suppress low-confidence answers

**Hour 14-15: Agent-Style Enhancements**
- [ ] Add retrieval validation step (30 min)
  - Check if retrieved docs are relevant to query
  - Multi-step: Query → Retrieval → Validation → Generation
- [ ] Add conditional logic (30 min)
  - If confidence >0.8: Direct answer
  - If confidence 0.65-0.8: Answer with caveat
  - If confidence <0.65: Ask for clarification
  - Log decision path

**Hour 15-16: Final Touches**
- [ ] Add API versioning (/api/v1/) (10 min)
- [ ] Add health check endpoint (10 min)
- [ ] Add metrics endpoint (20 min)
  - Return aggregated stats (avg response time, total queries, etc.)
- [ ] Frontend polish (20 min)
  - Show confidence score
  - Highlight "unknown" responses
  - Display source links

**Deliverable:** Production-differentiated features

---

#### **Hours 16-20: Stage 2D - Documentation**
**Goal:** Professional communication

**Hour 16-17: README.md**
- [ ] Project overview (15 min)
- [ ] Features list (10 min)
- [ ] Prerequisites (5 min)
- [ ] Installation instructions (15 min)
- [ ] Usage examples (15 min)

**Hour 17-18: ARCHITECTURE.md**
- [ ] System architecture diagram (20 min)
- [ ] Component descriptions (20 min)
- [ ] Key technical decisions (20 min)
  - Why ChromaDB?
  - Why chunk size 500?
  - Why confidence threshold 0.65?

**Hour 18-19: EVALUATION-REPORT.md (2-3 pages)**
- [ ] **Section 1: Approach** (20 min)
  - Dataset choice rationale
  - Architecture decisions
  - Evaluation strategy
- [ ] **Section 2: Implementation** (20 min)
  - Technical highlights
  - Production patterns used
  - Challenges & solutions
- [ ] **Section 3: Evaluation Results** (20 min)
  - Baseline metrics
  - Improvement iteration
  - Analysis by query category
  - Key findings

**Hour 19-20: FUTURE-IMPROVEMENTS.md**
- [ ] Stage 3 documentation (60 min)
  - **Scaling:** Caching strategy, load balancing, vector DB optimization
    - **ChromaDB Scale-up Path:**
      - Current: SQLite persistence (suitable for < 1M vectors, single-server deployment)
      - Medium scale: ChromaDB server mode (1M-10M vectors, multiple clients, HTTP API)
      - Large scale: Distributed ChromaDB with PostgreSQL (10M+ vectors, multi-region, HA)
      - Enterprise: ChromaDB Cloud or migrate to Pinecone/Weaviate for full managed solution
  - **CI/CD:** GitHub Actions pipeline, automated testing, deployment
  - **Kubernetes:** Deployment manifests, horizontal pod autoscaling
  - **Security:** Authentication, rate limiting, input sanitization
  - **UX:** Streaming responses, auto-complete, feedback loop
  - **Advanced Evaluation:** A/B testing framework, metric monitoring dashboard
  - **Cost Optimization:** Embedding caching, LLM request batching

**Deliverable:** Complete documentation package

**🎯 Day 2 Success Criteria:**
- ✅ Code quality: Type hints, docstrings, tests
- ✅ Evaluation: 50 queries, 5 metrics, demonstrated improvement
- ✅ Differentiation: Unknown handling, confidence thresholding, hallucination detection
- ✅ Documentation: README + Report + Architecture + Future plans
- ✅ Ready for submission

---

## 📂 Project Structure

```
ai-engineer-coding-exercise/
├── README.md
├── ARCHITECTURE.md
├── EVALUATION-REPORT.md
├── FUTURE-IMPROVEMENTS.md
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── .env
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Configuration management
│   │   ├── models.py               # Pydantic models
│   │   │
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── ingestion.py        # Document loading + chunking
│   │   │   ├── retrieval.py        # ChromaDB queries
│   │   │   ├── generation.py       # LLM integration
│   │   │   └── evaluation.py       # RAGAS framework
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── logging.py          # Logging configuration
│   │       └── validators.py       # Input validation
│   │
│   ├── data/
│   │   ├── documents/              # FastAPI documentation
│   │   └── test_queries/
│   │       └── queries.json        # 50 test queries
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_ingestion.py
│   │   ├── test_retrieval.py
│   │   ├── test_generation.py
│   │   ├── test_unknown_handling.py
│   │   └── test_source_attribution.py
│   │
│   └── chromadb/                   # Vector DB persistent storage
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   │
│   ├── src/
│   │   ├── App.jsx                 # Main component
│   │   ├── main.jsx
│   │   ├── App.css
│   │   └── components/
│   │       ├── QueryInput.jsx
│   │       ├── ResponseDisplay.jsx
│   │       └── SourcesList.jsx
│   │
│   └── public/
│
└── docs/
    ├── planning.md                 # This document
    ├── assignment.md               # Original assignment
    └── evaluation-results/
        ├── baseline-scores.json
        └── improved-scores.json
```

---

## 🎯 Success Criteria Checklist

### **Minimum Requirements (Must Have)**
- [ ] FastAPI backend running
- [ ] Vector database (ChromaDB) operational
- [ ] RAG pipeline working (retrieve → generate)
- [ ] React frontend functional
- [ ] Docker Compose setup
- [ ] Basic evaluation framework
- [ ] README with setup instructions
- [ ] 2-3 page report

### **Differentiation (Should Have)**
- [ ] Production patterns (error handling, logging, config)
- [ ] Source attribution in responses
- [ ] "Unknown" handling for out-of-scope queries
- [ ] Confidence thresholding
- [ ] Hallucination detection
- [ ] 50 realistic test queries
- [ ] 5 RAGAS metrics + custom metrics
- [ ] Demonstrated improvement iteration
- [ ] 5 unit tests
- [ ] FUTURE-IMPROVEMENTS.md

### **Excellence (Nice to Have)**
- [ ] OpenAI integration ready (config toggle)
- [ ] Agent-style multi-step pipeline
- [ ] Conditional logic based on confidence
- [ ] API versioning
- [ ] Metrics endpoint
- [ ] Architecture diagram
- [ ] Detailed evaluation analysis

---

## 🚨 Risk Mitigation & Fallback Plans

### **If Running Behind Schedule:**

**End of Day 1 (Hour 8):**
- ✅ Must have: Working backend + frontend + Docker
- ⚠️ Can skip: Baseline evaluation (do on Day 2)

**Hour 12 (Mid Day 2):**
- ✅ Must have: Code quality pass + testing done
- ⚠️ Can skip: Expansion to 50 queries (stick with 20)
- ⚠️ Can skip: Custom metrics (stick with 3 RAGAS metrics)

**Hour 16 (Late Day 2):**
- ✅ Must have: Basic documentation (README + short report)
- ⚠️ Can skip: ARCHITECTURE.md (combine into README)
- ⚠️ Can skip: Detailed improvement iteration (just show baseline)

**Hour 18 (Final Hours):**
- ✅ Must have: Submit what you have
- 🎯 Priority: Working demo > Perfect docs

### **Common Issues & Solutions:**

| Issue | Solution |
|-------|----------|
| GPT4All slow/crashes | Switch to OpenAI API (already configured) |
| ChromaDB issues | Use in-memory mode, simpler but functional |
| React build problems | Use pure HTML/JS (still counts as frontend) |
| RAGAS setup issues | Manual evaluation script (simple metrics) |
| Docker compose fails | Document local setup, demo without Docker |

---

## 💡 Key Technical Decisions

### **1. Chunk Size: 500 characters, 50 overlap**
**Rationale:**
- FastAPI docs have clear section boundaries
- 500 chars ≈ 1-2 paragraphs = semantic unit
- Small enough for focused retrieval
- 50 overlap prevents context loss at boundaries

### **2. Confidence Threshold: 0.65**
**Rationale:**
- Cosine similarity >0.65 = strong semantic match
- Below 0.65 = likely off-topic or ambiguous
- Balanced: Not too conservative (0.8) nor too lenient (0.5)
- Will be validated in evaluation phase

### **3. Top-k Retrieval: 5 documents**
**Rationale:**
- 5 docs × 500 chars = 2500 chars context
- Fits comfortably in LLM context window
- Enough diversity without noise
- Standard RAG practice

### **4. LLM: GPT4All mistral-7b-instruct**
**Rationale:**
- Free and fast for local development
- 7B parameter = good quality/speed tradeoff
- Aligned with Day 1-2 experience (you used gpt4all)
- Designed to easily switch to OpenAI gpt-3.5/gpt-4
- Shows infrastructure skills

### **5. Embeddings: sentence-transformers/all-MiniLM-L6-v2**
**Rationale:**
- Fast (384 dimensions)
- Good semantic understanding
- Widely used in production
- Low resource requirements

---

## 🎤 Interview Preparation

### **Anticipated Questions & Prepared Answers**

**Q: "Why FastAPI documentation instead of FastAPI Company repos?"**
> "I chose FastAPI docs for three reasons: First, it's directly relevant to the backend framework in the assignment, showing domain alignment. Second, the documentation is high-quality and comprehensive, allowing me to focus on RAG quality rather than data cleaning. Third, it saved 2-3 hours compared to exploring unfamiliar repos, letting me invest that time in evaluation quality and production patterns. In a real scenario with more time, I'd absolutely use FastAPI Company-specific documentation."

**Q: "Walk me through your evaluation strategy."**
> "I used a three-phase approach: First, baseline evaluation with 20 queries and 3 core RAGAS metrics to establish initial quality. Second, I expanded to 50 queries covering diverse scenarios including adversarial cases. Third, I implemented an improvement (specific change made) and demonstrated measurable improvement from X to Y. The evaluation isn't just about scores—it drove specific technical decisions like chunk size and confidence thresholding."

**Q: "How would you handle this at production scale?"**
> "I've documented this in FUTURE-IMPROVEMENTS.md. Key areas: One, implement caching for embeddings and frequent queries to reduce latency and cost. Two, add horizontal scaling with load balancing for the API layer. Three, scale the vector database—currently using ChromaDB with SQLite which is appropriate for < 1M vectors, but production would move to ChromaDB server mode (1M-10M vectors) or distributed setup with PostgreSQL for enterprise scale. Four, implement comprehensive monitoring and alerting on RAGAS metrics. Five, add A/B testing framework to validate changes before rollout. The architecture I built is designed to scale—it's not overengineered for the assignment, but the patterns extend naturally."

**Q: "Show me how you'd add [new feature]."**
> [This is the adaptability test they mentioned]
> Strategy: Point to the modular structure, show where feature would fit, explain minimal changes needed. Key areas ready for modification:
> - LLM switching (already abstracted)
> - New metrics (evaluation.py modular)
> - Frontend changes (component-based)
> - API endpoints (FastAPI routing clear)

**Q: "What's the most important production pattern you implemented?"**
> "The confidence thresholding and 'Unknown' handling. In production GenAI, controlled degradation is critical. Rather than always generating an answer (which risks hallucination), the system explicitly says 'I don't have information on this' when confidence is low. This is paired with source attribution—every response includes references. These two patterns together prevent the #1 production risk: user trust erosion from hallucinated content."

---

## 📊 Expected Outcomes

### **Baseline Metrics (Estimated)**
- Context Precision: 0.70-0.75
- Faithfulness: 0.65-0.70
- Answer Relevancy: 0.75-0.80

### **Improved Metrics (Target)**
- Context Precision: 0.80-0.85 (+12-15%)
- Faithfulness: 0.85-0.90 (+25-30%)
- Answer Relevancy: 0.82-0.87 (+8-10%)

### **Improvement Strategies**
1. **Prompt Engineering:** Add explicit "stick to context" instructions
2. **Chunk Tuning:** Adjust from 500 → 800 chars if context loss detected
3. **Confidence Gating:** Suppress low-confidence responses (faithfulness boost)

---

## 🔄 **PLAN PIVOT: RAG Data Pipeline Framework** (March 5, 2026)

### **Strategic Addition: Stage 2C - Data Acquisition Framework**

**Rationale:** Differentiate by showcasing **data engineering skills** for RAG systems, not just model/prompt tuning.

**New Stage 2C: RAG Data Pipeline (3 hours)**

#### **Goals:**
1. Build reusable framework for generating RAG datasets from real codebases
2. Demo with actual FastAPI Company repositories (show initiative + research)
3. Showcase end-to-end thinking: data acquisition → processing → ingestion → RAG

#### **Three-Pillar Data Sources:**

**Pillar 1: Repository Documentation Extraction**
- Clone FastAPI Company open-source repos (e.g., sample-code)
- Extract existing docs: README, API guides, CHANGELOG, wiki
- File types: `.md`, `.rst`, `.txt`, `.pdf` (if present)
- **Output:** Raw documentation corpus

**Pillar 2: Auto-Generated Code Documentation**
- Parse source code (Java, Python, JavaScript depending on repo)
- Generate API reference using tools:
  - Python: `pydoc`, `sphinx`
  - Java: JavaDoc extraction
  - JavaScript: JSDoc/TSDoc
- Extract: Class descriptions, method signatures, parameters, return types
- **Output:** Structured API documentation

**Pillar 3: Issue/Ticket-Driven Q&A Dataset**
- Scrape GitHub Issues & PRs from FastAPI Company repos
- Filter: Closed issues with accepted answers
- Convert to (question, answer, context) triples
- Extract common pain points and solutions
- **Output:** Developer Q&A pairs

#### **Architecture:**

```
data-pipeline/
├── extractors/
│   ├── repo_docs_extractor.py        # Clone & extract .md files
│   ├── code_doc_generator.py         # Generate API docs from code
│   └── issue_qa_converter.py         # GitHub Issues → Q&A pairs
├── processors/
│   ├── markdown_cleaner.py           # Remove HTML, normalize formatting
│   ├── code_snippet_extractor.py    # Extract code examples
│   └── metadata_enricher.py         # Add source, type, timestamp
├── pipeline_orchestrator.py          # Main pipeline runner
└── config.yaml                        # Repo URLs, patterns, filters
```

#### **Implementation Plan:**

**Hour 14: Framework Development**
- [ ] Create `data-pipeline/` directory structure
- [ ] Implement Pillar 1: `repo_docs_extractor.py` (git clone, find .md files)
- [ ] Implement Pillar 2: `code_doc_generator.py` (basic docstring extraction)
- [ ] Implement Pillar 3: `issue_qa_converter.py` (GitHub API → Q&A format)
- [ ] Create `config.yaml` with FastAPI Company repo configurations

**Hour 15: Demo with FastAPI Company Repositories**
- [ ] Select 1-2 FastAPI Company repos (e.g., sample-code, openapi-spec)
- [ ] Run pipeline to generate dataset
- [ ] Metrics: Before (15 FastAPI docs) vs. After (150+ docs including FastAPI Company content)
- [ ] Ingest new dataset into existing RAG system
- [ ] Test queries: "How do I authenticate with FastAPI Company API?"

**Hour 16: Documentation & Polish**
- [ ] Create `docs/DATA-PIPELINE.md` (architecture, usage, extensibility)
- [ ] Add section to `lesson-learned.md`: "Building RAG Datasets from Scratch"
- [ ] Update README with data pipeline showcase
- [ ] Create example config for other repos (GitHub, GitLab, Bitbucket)

#### **Value Propositions for Interview:**

1. **"I don't just build RAG systems, I build data pipelines to feed them"**
2. **"Used YOUR actual repos (company/...) as the demo dataset"**
3. **"Converted 50 GitHub issues into 50 training Q&A pairs"**
4. **"Auto-generated 200+ API docs from your Java sample code"**
5. **"Framework is reusable for any organization's codebase"**
6. **"Showed how to keep docs fresh: git hooks → auto-regenerate"**

#### **Candidate FastAPI Company Repositories:**

Research targets (to be confirmed):
- `sdk-javascript` - Frontend SDK
- `sample-code` - Backend code samples
- `developer-guides` - API integration guides
- `openapi-spec` - API specifications (OpenAPI/Swagger)

#### **Success Metrics:**

- **Before:** 13 FastAPI docs → 252 chunks
- **After:** 150+ documents (FastAPI + FastAPI Company repos) → 1000+ chunks
- **Quality:** Demonstrate queries spanning both datasets
- **Reusability:** Framework can be configured for any GitHub org in 5 minutes

---

## 🎯 Final Notes

### **What Makes This Submission Stand Out**

1. **Production Mindset:** Not a prototype—built with production patterns from start
2. **Evaluation Excellence:** Not just "it works"—demonstrated measurement and improvement
3. **Enterprise Thinking:** Unknown handling, source attribution, confidence scoring
4. **Data Engineering Skills:** Built reusable pipeline for RAG dataset generation ⭐ NEW
5. **FastAPI Company-Specific Research:** Used actual FastAPI Company repositories in the demo ⭐ NEW
6. **Clear Communication:** Documentation shows strategic thinking, not just code
7. **Interview Ready:** Code designed for easy modification, improvements documented

### **Backup Plan**

If absolutely necessary, can submit end-of-Day-1 deliverable (Hour 8):
- Working system ✅
- Docker Compose ✅
- Basic evaluation ✅
- README ✅

But Day 2 work is where differentiation happens.

### **Time Tracking Strategy**

Track hours loosely—if ahead, invest in quality; if behind, use fallback plans. The hour breakdown is a guide, not a prison.

**Success = Demonstrating production-ready GenAI engineering skills, not perfection.**

---

*Planning Document Version: 1.0*  
*Created: March 4, 2026*  
*Status: Ready for Execution*
