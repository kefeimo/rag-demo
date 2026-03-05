# AI Engineer Coding Exercise - Progress Tracking

**Project:** RAG System Implementation for Visa  
**Timeline:** March 4-5, 2026 (2 Days)  
**Status:** 🟡 In Progress  
**Last Updated:** March 4, 2026

---

## 📊 Overall Progress

| Phase | Status | Progress | Time Spent | Notes |
|-------|--------|----------|------------|-------|
| **Stage 0: Setup** | ⬜ Not Started | 0% | 0h | Requirements & environment |
| **Stage 1A: Backend Core** | ⬜ Not Started | 0% | 0h | FastAPI + ChromaDB + Ollama |
| **Stage 1B: Frontend + Docker** | ⬜ Not Started | 0% | 0h | React UI + Docker Compose |
| **Stage 1C: Basic Evaluation** | ⬜ Not Started | 0% | 0h | RAGAS baseline |
| **Stage 2A: Code Quality** | ⬜ Not Started | 0% | 0h | Refactoring + Testing |
| **Stage 2B: Evaluation Enhancement** | ⬜ Not Started | 0% | 0h | 50 queries + 5 metrics |
| **Stage 2C: Production Features** | ⬜ Not Started | 0% | 0h | Unknown handling + Hallucination detection |
| **Stage 2D: Documentation** | ⬜ Not Started | 0% | 0h | README + Report + Architecture |

**Legend:** ⬜ Not Started | 🟡 In Progress | ✅ Complete | ⚠️ Blocked

**Total Progress:** 0/8 stages complete (0%)

---

## 📅 DAY 1 CHECKLIST (8-10 hours)

### **Stage 0: Requirements & Setup (Hour 0-1)** ⬜

- [ ] Re-read assignment requirements
- [ ] Document deliverables checklist
- [ ] Download FastAPI documentation
  - [ ] Tutorial section
  - [ ] User Guide
  - [ ] Advanced User Guide
- [ ] Setup project structure
- [ ] Initialize git repository
- [ ] Create initial README skeleton

**Status:** ⬜ Not Started  
**Time Spent:** 0h  
**Blockers:** None

---

### **Stage 1A: Backend Core (Hours 1-5)** ⬜

#### **Document Ingestion Pipeline (Hour 1-2)**
- [ ] Install backend dependencies
  - [ ] fastapi, uvicorn, chromadb
  - [ ] sentence-transformers
  - [ ] python-dotenv, pydantic
  - [ ] langchain, ollama
- [ ] Implement document loader
  - [ ] Parse FastAPI markdown docs
  - [ ] Text chunking (500 chars, 50 overlap)
  - [ ] Metadata extraction
- [ ] Implement ChromaDB ingestion
  - [ ] Collection creation
  - [ ] Embedding generation
  - [ ] Batch insertion
- [ ] Test ingestion with 10 docs

#### **RAG Query Pipeline (Hour 2-3)**
- [ ] Implement `/query` endpoint
  - [ ] Input validation (Pydantic models)
  - [ ] Retrieval logic (top-k=5)
  - [ ] Context formatting
  - [ ] Error handling
- [ ] Implement retrieval confidence scoring
  - [ ] Based on similarity scores
  - [ ] Threshold: <0.65 = "unknown"

#### **LLM Integration (Hour 3-4)**
- [ ] Setup Ollama client
  - [ ] Pull llama3:8b model
  - [ ] Test connection
- [ ] Implement prompt construction
  - [ ] System prompt: "Use ONLY provided context"
  - [ ] User prompt template with sources
  - [ ] "Unknown" instruction
- [ ] Implement generation endpoint
  - [ ] Call Ollama
  - [ ] Parse response
  - [ ] Extract source citations
- [ ] Add OpenAI-ready config
  - [ ] Environment variable toggle
  - [ ] Abstracted LLM client interface

#### **Production Patterns (Hour 4-5)**
- [ ] Add logging
  - [ ] Request/response logging
  - [ ] Error logging
  - [ ] Performance metrics (latency)
- [ ] Add error handling
  - [ ] Try-except blocks
  - [ ] Graceful degradation
  - [ ] User-friendly error messages
- [ ] Config management
  - [ ] .env file structure
  - [ ] Config validation
  - [ ] Defaults for all settings

**Status:** ⬜ Not Started  
**Time Spent:** 0h  
**Blockers:** None

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
  - [ ] Basic CSS (clean, readable)

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

- [ ] Can ingest FastAPI docs
- [ ] Can query and get responses
- [ ] Frontend displays results with sources
- [ ] Docker Compose works
- [ ] Baseline RAGAS scores documented
- [ ] Could submit this if needed

**Day 1 Status:** ⬜ Not Complete  
**Day 1 Time Spent:** 0h / 8-10h

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
- ⚠️ **Risk:** Ollama model download may be slow
  - **Mitigation:** Download in Hour 0, before starting Hour 1
- ⚠️ **Risk:** ChromaDB setup issues
  - **Mitigation:** Use in-memory mode as fallback
- ⚠️ **Risk:** Running behind schedule
  - **Mitigation:** Follow fallback plans in planning.md

---

## 💡 Notes & Decisions

### **Technical Decisions**
*Document key decisions made during implementation*

**Example:**
- ✅ **Decision:** Use chunk size 500 chars
  - **Reason:** FastAPI docs have clear section boundaries
  - **Alternative Considered:** 800 chars (rejected: too large for focused retrieval)
  - **Time:** Hour 2

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
- [ ] LLM integration (Ollama)
- [ ] Evaluation framework (RAGAS)
- [ ] React frontend (optional but included)
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

**Current Priority:** Stage 0 - Requirements & Setup

**Next Steps:**
1. Download FastAPI documentation
2. Setup project structure
3. Initialize git repository
4. Begin Stage 1A - Backend Core

**Blockers:** None

---

## 📊 Time Summary

| Day | Planned | Actual | Variance | Status |
|-----|---------|--------|----------|--------|
| Day 1 | 8-10h | 0h | - | ⬜ Not Started |
| Day 2 | 8-10h | 0h | - | ⬜ Not Started |
| **Total** | **16-20h** | **0h** | **-** | **0% Complete** |

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

### March 4, 2026 - 00:00
- 🆕 Created progress tracking document
- 📋 Initialized all checklists
- 🎯 Set baseline targets
- ✅ Ready to begin execution
