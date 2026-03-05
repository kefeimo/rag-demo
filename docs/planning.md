# AI Engineer Coding Exercise - Strategic Planning Document

**Project:** RAG System Implementation for Visa  
**Timeline:** 2 Days (16-20 hours)  
**Date:** March 4-5, 2026  
**Objective:** Demonstrate production-ready GenAI engineering skills with focus on planning, evaluation, and SDLC best practices

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
| **Dataset** | FastAPI Documentation | Relevant to assignment, abundant quality docs, realistic queries, saves 2 hours vs Visa repos exploration |
| **LLM** | Ollama (llama3:8b) primary, OpenAI-ready config | Free, shows infrastructure skills, easy to switch for better quality if needed |
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
[6. LLM Generation (Ollama/OpenAI)]
    ↓
[7. Post-Processing] (hallucination check, source extraction)
    ↓
Response + Sources + Confidence Score
```

### **Technology Stack**

**Backend:**
- FastAPI (REST API)
- ChromaDB (vector database)
- Ollama (local LLM) / OpenAI (optional upgrade)
- sentence-transformers (embeddings)
- RAGAS (evaluation framework)

**Frontend:**
- React (Vite)
- Axios (API calls)
- Basic CSS (no Tailwind, keep it simple)

**Infrastructure:**
- Docker Compose (local development)
- Python 3.11+
- Node 18+

**Testing:**
- pytest (unit tests)
- RAGAS (RAG quality evaluation)

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
**Goal:** FastAPI + ChromaDB + Ollama working

**Hour 1-2: Document Ingestion Pipeline**
- [ ] Install dependencies (15 min)
  ```bash
  fastapi, uvicorn, chromadb, sentence-transformers, 
  python-dotenv, pydantic, langchain, ollama
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
- [ ] Setup Ollama client (15 min)
  - Pull llama3:8b model
  - Test connection
- [ ] Implement prompt construction (30 min)
  - System prompt: "Use ONLY provided context"
  - User prompt template with sources
  - "Unknown" instruction
- [ ] Implement generation endpoint (30 min)
  - Call Ollama
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
  - Basic CSS (clean, readable)

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

**Hour 10-11: Expand Test Dataset**
- [ ] Create 30 additional queries (45 min)
  - Cover more FastAPI topics (WebSockets, background tasks, dependencies)
  - Add adversarial queries:
    - "How to use Django with FastAPI?" (out of scope)
    - "What's the admin password?" (security)
  - Total: 50 queries
- [ ] Categorize queries (15 min)
  - By topic: basics, auth, async, testing, deployment
  - By difficulty: easy/medium/hard
  - By expected answer length: short/medium/long

**Hour 11-12: Full RAGAS Evaluation**
- [ ] Add 2 more metrics (30 min)
  - context_recall
  - answer_correctness
- [ ] Add custom metrics (30 min)
  - response_time (ms)
  - token_cost (estimated)
  - source_coverage (how many sources cited)

**Hour 12-13: Improvement Iteration**
- [ ] Run full evaluation, document baseline (15 min)
- [ ] Implement improvement (30 min)
  - Option 1: Tune chunk size (500→800 chars)
  - Option 2: Improve prompt (more explicit instructions)
  - Option 3: Add reranking (if time)
- [ ] Re-evaluate, document improvement (15 min)
- [ ] Create comparison table (15 min)
  ```
  Metric          | Baseline | After Improvement | Change
  ----------------|----------|-------------------|-------
  Context Prec.   | 0.72     | 0.84             | +16%
  Faithfulness    | 0.68     | 0.88             | +29%
  Answer Relevancy| 0.81     | 0.86             | +6%
  ```

**Deliverable:** Comprehensive evaluation with demonstrated improvement

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
| Ollama slow/crashes | Switch to OpenAI API (already configured) |
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

### **4. LLM: Ollama llama3:8b**
**Rationale:**
- Free and fast for local development
- 8B parameter = good quality/speed tradeoff
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

**Q: "Why FastAPI documentation instead of Visa repos?"**
> "I chose FastAPI docs for three reasons: First, it's directly relevant to the backend framework in the assignment, showing domain alignment. Second, the documentation is high-quality and comprehensive, allowing me to focus on RAG quality rather than data cleaning. Third, it saved 2-3 hours compared to exploring unfamiliar repos, letting me invest that time in evaluation quality and production patterns. In a real scenario with more time, I'd absolutely use Visa-specific documentation."

**Q: "Walk me through your evaluation strategy."**
> "I used a three-phase approach: First, baseline evaluation with 20 queries and 3 core RAGAS metrics to establish initial quality. Second, I expanded to 50 queries covering diverse scenarios including adversarial cases. Third, I implemented an improvement (specific change made) and demonstrated measurable improvement from X to Y. The evaluation isn't just about scores—it drove specific technical decisions like chunk size and confidence thresholding."

**Q: "How would you handle this at production scale?"**
> "I've documented this in FUTURE-IMPROVEMENTS.md. Key areas: One, implement caching for embeddings and frequent queries to reduce latency and cost. Two, add horizontal scaling with load balancing for the API layer. Three, move to a production vector database like Pinecone or Weaviate with replication. Four, implement comprehensive monitoring and alerting on RAGAS metrics. Five, add A/B testing framework to validate changes before rollout. The architecture I built is designed to scale—it's not overengineered for the assignment, but the patterns extend naturally."

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

## 🎯 Final Notes

### **What Makes This Submission Stand Out**

1. **Production Mindset:** Not a prototype—built with production patterns from start
2. **Evaluation Excellence:** Not just "it works"—demonstrated measurement and improvement
3. **Enterprise Thinking:** Unknown handling, source attribution, confidence scoring
4. **Clear Communication:** Documentation shows strategic thinking, not just code
5. **Interview Ready:** Code designed for easy modification, improvements documented

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
