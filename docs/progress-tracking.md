# AI Engineer Coding Exercise - Progress Tracking

**Project:** RAG System Implementation for Visa  
**Timeline:** March 4-5, 2026 (2 Days)  
**Status:** 🟡 In Progress  
**Last Updated:** March 4, 2026

---

## 📊 Overall Progress

| Phase | Status | Progress | Time Spent | Notes |
|-------|--------|----------|------------|-------|
| **Stage 0: Setup** | ✅ Complete | 100% | 0.5h | Requirements & environment |
| **Stage 1A: Backend Core** | ✅ Complete | 100% | 3.0h | FastAPI + ChromaDB + GPT4All - All endpoints working |
| **Stage 1B: Frontend + Docker** | ⬜ Not Started | 0% | 0h | React UI + Tailwind + Docker Compose |
| **Stage 1C: Basic Evaluation** | ⬜ Not Started | 0% | 0h | RAGAS baseline |
| **Stage 2A: Code Quality** | ⬜ Not Started | 0% | 0h | Refactoring + Testing |
| **Stage 2B: Evaluation Enhancement** | ⬜ Not Started | 0% | 0h | 50 queries + 5 metrics |
| **Stage 2C: Production Features** | ⬜ Not Started | 0% | 0h | Unknown handling + Hallucination detection |
| **Stage 2D: Documentation** | ⬜ Not Started | 0% | 0h | README + Report + Architecture |

**Legend:** ⬜ Not Started | 🟡 In Progress | ✅ Complete | ⚠️ Blocked

**Total Progress:** 2/8 stages complete (25.0%)

---

## 📅 DAY 1 CHECKLIST (8-10 hours)

### **Stage 0: Requirements & Setup (Hour 0-1)** ✅

- [x] Re-read assignment requirements
- [x] Document deliverables checklist
- [x] Download FastAPI documentation
  - [x] Tutorial section (7 files)
  - [x] User Guide (features.md, index.md)
  - [x] Advanced User Guide (advanced/index.md, deployment/index.md)
- [x] Setup project structure
- [x] Initialize git repository
- [x] Create initial README skeleton
- [x] Create requirements.txt
- [x] Create .env.example and .env

**Status:** ✅ Complete  
**Time Spent:** 0.5h  
**Blockers:** None  
**Notes:** Successfully downloaded 12 FastAPI documentation files. Project structure ready for Stage 1A implementation.

---

### **Stage 1A: Backend Core (Hours 1-5)** ✅

#### **Document Ingestion Pipeline (Hour 1-2)** ✅
- [x] Install backend dependencies
  - [x] fastapi, uvicorn, chromadb
  - [x] sentence-transformers
  - [x] python-dotenv, pydantic
  - [x] langchain, langchain-community, gpt4all
- [x] Implement document loader
  - [x] Parse FastAPI markdown docs
  - [x] Text chunking (500 chars, 50 overlap)
  - [x] Metadata extraction
- [x] Implement ChromaDB ingestion
  - [x] Collection creation
  - [x] Embedding generation (sentence-transformers/all-MiniLM-L6-v2)
  - [x] Batch insertion (100 per batch)
- [x] Test ingestion with 13 docs → 252 chunks in 0.94s

#### **RAG Query Pipeline (Hour 2-3)** ✅
- [x] Implement `/query` endpoint
  - [x] Input validation (Pydantic models)
  - [x] Retrieval logic (top-k=5)
  - [x] Context formatting
  - [x] Error handling
- [x] Implement retrieval confidence scoring
  - [x] Based on similarity scores (cosine distance)
  - [x] Threshold: <0.65 = "unknown"

#### **LLM Integration (Hour 3-4)** ✅
- [x] Setup GPT4All client
  - [x] Download mistral-7b-instruct model (~4GB to ~/.cache/gpt4all/)
  - [x] Test connection
- [x] Implement prompt construction
  - [x] System prompt: "Use ONLY provided context"
  - [x] User prompt template with sources
  - [x] "Unknown" instruction
- [x] Implement generation endpoint
  - [x] Call GPT4All
  - [x] Parse response
  - [x] Extract source citations
- [x] Add OpenAI-ready config
  - [x] Environment variable toggle
  - [x] Abstracted LLM client interface

#### **Production Patterns (Hour 4-5)** ✅
- [x] Add logging
  - [x] Request/response logging
  - [x] Error logging
  - [x] Performance metrics (latency)
- [x] Add error handling
  - [x] Try-except blocks
  - [x] Graceful degradation
  - [x] User-friendly error messages
- [x] Config management
  - [x] .env file structure
  - [x] Config validation
  - [x] Defaults for all settings
- [x] ChromaDB singleton pattern (avoid client conflicts)

**Status:** ✅ Complete  
**Time Spent:** 3.0h  
**Blockers:** None  
**Test Results:**
- ✅ Health endpoint: Working (200 OK)
- ✅ Ingestion: 13 docs → 252 chunks in 0.94s
- ✅ Query 1 "What is FastAPI?": 98.81s, confidence 0.810, accurate answer
- ✅ Query 2 "How do I create a path parameter?": 85.68s, confidence 0.847, accurate answer  
- ✅ Query 3 "What are FastAPI's main features?": 80.78s, confidence 0.804, accurate answer
- ✅ All 3 test queries passed with proper source attribution

**Notes:** 
- All RAG pipeline components working end-to-end
- GPT4All running on CPU (CUDA 11.0 not available, falls back gracefully)
- Response times 80-99s acceptable for local LLM on CPU
- Confidence scores all above 0.80 (well above 0.65 threshold)
- Source attribution working correctly with chunk metadata

---

### **Stage 1B: Frontend + Docker (Hours 5-8)** ⬜

#### **React Frontend (Hour 5-6)**
- [ ] Vite React setup
- [ ] Single page component
  - [ ] Query input textarea
  - [ ] Submit button
  - [ ] Loading state
  - [ ] Response display
  - [ ] Sources list with confidence scores
  - [ ] Error display
  - [ ] Tailwind CSS styling (aligned with Day 3)

#### **Integration + Docker (Hour 6-7)**
- [ ] Connect frontend to backend
  - [ ] Axios setup
  - [ ] CORS configuration
  - [ ] API calls
- [ ] Docker Compose setup
  - [ ] Backend Dockerfile
  - [ ] Frontend Dockerfile
  - [ ] docker-compose.yml
  - [ ] Volume mounts for development

#### **Stage 1C: Basic Evaluation (Hour 7-8)**
- [ ] Create 20 test queries
  - [ ] 6 easy (factual)
  - [ ] 10 medium (procedural)
  - [ ] 4 hard (complex)
- [ ] Setup RAGAS
  - [ ] Install ragas package
  - [ ] Configure metrics
- [ ] Run baseline evaluation
  - [ ] 3 metrics: context_precision, faithfulness, answer_relevancy
  - [ ] Document scores in EVALUATION-REPORT.md

**Status:** ⬜ Not Started  
**Time Spent:** 0h  
**Blockers:** None

---

### **🎯 Day 1 Success Criteria**

- [x] Can ingest FastAPI docs ✅
- [x] Can query and get responses ✅
- [ ] Frontend displays results with sources
- [ ] Docker Compose works
- [ ] Baseline RAGAS scores documented
- [ ] Could submit this if needed

**Day 1 Status:** 🟡 In Progress (Backend Complete)  
**Day 1 Time Spent:** 3.5h / 8-10h

---

## 📅 DAY 2 CHECKLIST (8-10 hours)

### **Stage 2A: Code Quality (Hours 8-10)** ⬜

#### **Code Refactoring (Hour 8-9)**
- [ ] Add type hints throughout
- [ ] Add docstrings (Google style)
- [ ] Refactor into clean modules
  - [ ] main.py, config.py, models.py
  - [ ] rag/ingestion.py
  - [ ] rag/retrieval.py
  - [ ] rag/generation.py
  - [ ] rag/evaluation.py
  - [ ] utils/logging.py, utils/validators.py

#### **Testing (Hour 9-10)**
- [ ] Write 5 key unit tests
  - [ ] test_document_ingestion()
  - [ ] test_retrieval_returns_results()
  - [ ] test_prompt_construction()
  - [ ] test_unknown_handling()
  - [ ] test_source_attribution()
- [ ] Setup pytest configuration
- [ ] Run tests, ensure all pass

**Status:** ⬜ Not Started  
**Time Spent:** 0h  
**Blockers:** None

---

### **Stage 2B: Evaluation Enhancement (Hours 10-13)** ⬜

#### **Expand Test Dataset (Hour 10-11)**
- [ ] Create 30 additional queries
  - [ ] Cover more FastAPI topics
  - [ ] Add adversarial queries
  - [ ] Total: 50 queries
- [ ] Categorize queries
  - [ ] By topic
  - [ ] By difficulty
  - [ ] By expected answer length

#### **Full RAGAS Evaluation (Hour 11-12)**
- [ ] Add 2 more metrics
  - [ ] context_recall
  - [ ] answer_correctness
- [ ] Add custom metrics
  - [ ] response_time (ms)
  - [ ] token_cost (estimated)
  - [ ] source_coverage

#### **Improvement Iteration (Hour 12-13)**
- [ ] Run full evaluation, document baseline
- [ ] Implement improvement
  - [ ] Option: Tune chunk size
  - [ ] Option: Improve prompt
  - [ ] Option: Add reranking
- [ ] Re-evaluate, document improvement
- [ ] Create comparison table

**Status:** ⬜ Not Started  
**Time Spent:** 0h  
**Blockers:** None

---

### **Stage 2C: Production Differentiation (Hours 13-16)** ⬜

#### **Constrained Generation Features (Hour 13-14)**
- [ ] Enhance "Unknown/TBD" handling
  - [ ] Detect out-of-scope queries
  - [ ] Return helpful message
  - [ ] Log unknown queries for analysis
- [ ] Add hallucination detection
  - [ ] Post-generation faithfulness check
  - [ ] Flag low-confidence responses
  - [ ] Option to suppress low-confidence answers

#### **Agent-Style Enhancements (Hour 14-15)**
- [ ] Add retrieval validation step
  - [ ] Check if retrieved docs are relevant
  - [ ] Multi-step: Query → Retrieval → Validation → Generation
- [ ] Add conditional logic
  - [ ] If confidence >0.8: Direct answer
  - [ ] If confidence 0.65-0.8: Answer with caveat
  - [ ] If confidence <0.65: Ask for clarification
  - [ ] Log decision path

#### **Final Touches (Hour 15-16)**
- [ ] Add API versioning (/api/v1/)
- [ ] Add health check endpoint
- [ ] Add metrics endpoint
- [ ] Frontend polish
  - [ ] Show confidence score
  - [ ] Highlight "unknown" responses
  - [ ] Display source links

**Status:** ⬜ Not Started  
**Time Spent:** 0h  
**Blockers:** None

---

### **Stage 2D: Documentation (Hours 16-20)** ⬜

#### **README.md (Hour 16-17)**
- [ ] Project overview
- [ ] Features list
- [ ] Prerequisites
- [ ] Installation instructions
- [ ] Usage examples

#### **ARCHITECTURE.md (Hour 17-18)**
- [ ] System architecture diagram
- [ ] Component descriptions
- [ ] Key technical decisions

#### **EVALUATION-REPORT.md (Hour 18-19)**
- [ ] Section 1: Approach
  - [ ] Dataset choice rationale
  - [ ] Architecture decisions
  - [ ] Evaluation strategy
- [ ] Section 2: Implementation
  - [ ] Technical highlights
  - [ ] Production patterns used
  - [ ] Challenges & solutions
- [ ] Section 3: Evaluation Results
  - [ ] Baseline metrics
  - [ ] Improvement iteration
  - [ ] Analysis by query category
  - [ ] Key findings

#### **FUTURE-IMPROVEMENTS.md (Hour 19-20)**
- [ ] Scaling strategy
- [ ] CI/CD pipeline design
- [ ] Kubernetes deployment
- [ ] Security hardening
- [ ] UX improvements
- [ ] Advanced evaluation
- [ ] Cost optimization

**Status:** ⬜ Not Started  
**Time Spent:** 0h  
**Blockers:** None

---

### **🎯 Day 2 Success Criteria**

- [ ] Code quality: Type hints, docstrings, tests
- [ ] Evaluation: 50 queries, 5 metrics, demonstrated improvement
- [ ] Differentiation: Unknown handling, confidence thresholding, hallucination detection
- [ ] Documentation: README + Report + Architecture + Future plans
- [ ] Ready for submission

**Day 2 Status:** ⬜ Not Complete  
**Day 2 Time Spent:** 0h / 8-10h

---

## 📈 Metrics Tracking

### **RAGAS Baseline Scores** (Target: Hour 8)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Context Precision | 0.70-0.75 | - | ⬜ |
| Faithfulness | 0.65-0.70 | - | ⬜ |
| Answer Relevancy | 0.75-0.80 | - | ⬜ |

### **RAGAS Improved Scores** (Target: Hour 13)

| Metric | Target | Actual | Change | Status |
|--------|--------|--------|--------|--------|
| Context Precision | 0.80-0.85 | - | - | ⬜ |
| Faithfulness | 0.85-0.90 | - | - | ⬜ |
| Answer Relevancy | 0.82-0.87 | - | - | ⬜ |
| Context Recall | 0.75+ | - | - | ⬜ |
| Answer Correctness | 0.75+ | - | - | ⬜ |

### **Custom Metrics**

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Avg Response Time | <2000ms | - | ⬜ |
| Test Dataset Size | 50 queries | 0 | ⬜ |
| Unit Test Coverage | 5 tests | 0 | ⬜ |

---

## 🚨 Issues & Blockers

### **Active Issues**
*None yet*

### **Resolved Issues**
*None yet*

### **Risks**
- ⚠️ **Risk:** GPT4All model download may be slow
  - **Mitigation:** Download in Hour 0, before starting Hour 1
- ⚠️ **Risk:** ChromaDB setup issues
  - **Mitigation:** Use in-memory mode as fallback
- ⚠️ **Risk:** Running behind schedule
  - **Mitigation:** Follow fallback plans in planning.md

---

## 💡 Notes & Decisions

### **Technical Decisions**
*Document key decisions made during implementation*

**March 4, 2026 - Stage 1A Implementation:**

- ✅ **Decision:** ChromaDB singleton pattern (app/rag/utils.py)
  - **Reason:** Avoid "instance already exists" errors when initializing multiple clients
  - **Implementation:** Global _chroma_client with get_chroma_client() factory
  - **Time:** Hour 2.5

- ✅ **Decision:** Chunk size 500 chars with 50 overlap
  - **Reason:** FastAPI docs have clear section boundaries, 500 chars ≈ 1-2 paragraphs
  - **Alternative Considered:** 800 chars (rejected: too large for focused retrieval)
  - **Result:** 13 docs → 252 chunks, avg confidence 0.81
  - **Time:** Hour 1

- ✅ **Decision:** Smart boundary detection in chunking
  - **Reason:** Avoid breaking mid-sentence or mid-word
  - **Implementation:** Try sentence endings (., !, ?) within last 100 chars, fallback to word boundaries
  - **Impact:** Improved context quality for LLM
  - **Time:** Hour 1.5

- ✅ **Decision:** Confidence threshold 0.65
  - **Reason:** Balance between "too permissive" (hallucinations) and "too strict" (too many unknowns)
  - **Alternative Considered:** 0.70 (rejected: too strict for baseline)
  - **Actual Performance:** All test queries 0.80-0.85 (well above threshold)
  - **Time:** Hour 2

- ✅ **Decision:** GPT4All mistral-7b-instruct over llama
  - **Reason:** Better instruction following, aligned with Day 1 project
  - **Tradeoff:** 80-99s generation time on CPU (acceptable for demo)
  - **Alternative:** OpenAI API (implemented as config option)
  - **Time:** Hour 3

- ✅ **Decision:** Batch insertion 100 chunks at a time
  - **Reason:** ChromaDB performance optimization
  - **Impact:** 252 chunks ingested in 0.94s
  - **Time:** Hour 2

- ✅ **Decision:** Separate LLM client classes (GPT4AllClient, OpenAIClient)
  - **Reason:** Clean abstraction, easy to switch providers
  - **Pattern:** Factory function get_llm_client() based on config
  - **Time:** Hour 3.5

### **Lessons Learned**
*Document insights for future reference*

### **Shortcuts Taken**
*Document intentional compromises for 2-day timeline*

---

## 🎯 Submission Checklist

### **Required Deliverables**
- [ ] GitHub repository with source code
- [ ] README with setup instructions
- [ ] 2-3 page report or YouTube video
- [ ] Working demo (local or deployed)

### **Code Quality Checklist**
- [ ] Type hints throughout
- [ ] Docstrings for all functions
- [ ] Error handling implemented
- [ ] Logging configured
- [ ] Config management (.env)
- [ ] 5 unit tests passing
- [ ] Docker Compose working

### **Feature Checklist**
- [ ] Data preparation (FastAPI docs)
- [ ] FastAPI backend service
- [ ] RAG system (retrieve + generate)
- [ ] Vector database (ChromaDB)
- [ ] LLM integration (GPT4All + OpenAI config)
- [ ] Evaluation framework (RAGAS)
- [ ] React frontend with Tailwind CSS
- [ ] Source attribution
- [ ] Unknown handling
- [ ] Confidence scoring

### **Documentation Checklist**
- [ ] README.md (setup + usage)
- [ ] ARCHITECTURE.md (design decisions)
- [ ] EVALUATION-REPORT.md (2-3 pages)
- [ ] FUTURE-IMPROVEMENTS.md (Stage 3 plans)
- [ ] Code comments
- [ ] API documentation

---

## 🚀 Next Actions

**Current Priority:** Stage 1A - Backend Core (Document Ingestion Pipeline)

**Next Steps:**
1. Install backend dependencies (pip install -r requirements.txt)
2. Download GPT4All model (mistral-7b-instruct, ~4GB)
3. Implement document loader and ingestion pipeline
4. Implement ChromaDB integration
5. Test ingestion with FastAPI docs

**Blockers:** None

---

## 📊 Time Summary

| Day | Planned | Actual | Variance | Status |
|-----|---------|--------|----------|--------|
| Day 1 | 8-10h | 3.5h | -4.5h to -6.5h | 🟡 In Progress |
| Day 2 | 8-10h | 0h | - | ⬜ Not Started |
| **Total** | **16-20h** | **3.5h** | **-** | **25.0% Complete** |

---

## 🎯 Success Indicators

### **Minimum Success (Must Submit)**
- [ ] Working RAG system
- [ ] Basic documentation
- [ ] Can demo live

### **Target Success (Competitive)**
- [ ] All above +
- [ ] Production patterns
- [ ] Evaluation with improvements
- [ ] Comprehensive documentation

### **Exceptional Success (Stand Out)**
- [ ] All above +
- [ ] 50 test queries from FastAPI docs
- [ ] 5 RAGAS metrics + custom metrics
- [ ] Agent-style multi-step pipeline
- [ ] Clear improvement iteration
- [ ] Interview-ready code structure

**Current Status:** Minimum ⬜ | Target ⬜ | Exceptional ⬜

---

*Progress Tracking Version: 1.0*  
*Created: March 4, 2026*  
*Update Frequency: After each stage completion*

---

## 📝 Update Log

### March 4, 2026 - 20:30
- ✅ **Stage 1A Complete** - Backend Core RAG System Fully Functional
- **Components Implemented:**
  - Document ingestion pipeline (app/rag/ingestion.py)
    - DocumentLoader: Recursive .md file loading, smart chunking (500/50)
    - ChromaDBIngestion: Embedding generation, batch insertion
  - Vector retrieval (app/rag/retrieval.py)
    - Semantic search with sentence-transformers
    - Confidence scoring (cosine similarity)
    - Singleton ChromaDB client pattern
  - LLM generation (app/rag/generation.py)
    - GPT4All client (mistral-7b-instruct)
    - OpenAI client (optional)
    - Prompt construction with source attribution
  - Shared utilities (app/rag/utils.py)
    - ChromaDB singleton to avoid client conflicts
  - FastAPI endpoints (app/main.py)
    - GET /health - Working
    - POST /api/v1/ingest - Working (13 docs → 252 chunks in 0.94s)
    - POST /api/v1/query - Working (3/3 test queries passed)
  - Configuration (app/config.py, .env)
    - Pydantic Settings with validation
    - All 15+ parameters documented
- **Test Results (test_rag.py):**
  - ✅ Health check: PASSED (200 OK)
  - ✅ Query 1 "What is FastAPI?": 98.81s, confidence 0.810, accurate answer with 3 sources
  - ✅ Query 2 "How do I create a path parameter?": 85.68s, confidence 0.847, accurate answer with 3 sources
  - ✅ Query 3 "What are FastAPI's main features?": 80.78s, confidence 0.804, accurate answer with 3 sources
- **Performance:**
  - Ingestion: 0.94s for 13 documents
  - Query latency: 80-99s (GPT4All on CPU)
  - Confidence: All queries >0.80 (above 0.65 threshold)
- **Documentation:**
  - Updated backend/README.md with real examples
  - Streamlined from ~500 lines to concise format
  - Added actual test results and response samples
- 🎯 **Backend RAG pipeline production-ready**
- 🎯 **Ready to begin Stage 1B: Frontend + Docker**

### March 4, 2026 - 00:30
- ✅ **Stage 0 Complete**
- Downloaded 12 FastAPI documentation files (index, tutorial, advanced, deployment, features)
- Created project structure (backend/app/rag, backend/tests, frontend/src, data/documents)
- Created requirements.txt with all dependencies (FastAPI, LangChain, ChromaDB, GPT4All, RAGAS, etc.)
- Created .env.example and .env with comprehensive configuration
- Created DELIVERABLES.md checklist
- Updated README.md with current status and detailed setup instructions
- Stack 100% aligned with Day 1-4 projects (GPT4All, LangChain, Tailwind CSS)
- Environment: Linux (Day 2-4 experience applies directly)
- 🎯 **Ready to begin Stage 1A: Backend Core**

### March 4, 2026 - 00:00
- 🆕 Created progress tracking document
- 📋 Initialized all checklists
- 🎯 Set baseline targets
- ✅ Ready to begin execution
