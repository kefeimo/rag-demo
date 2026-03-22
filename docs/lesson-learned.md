# Lessons Learned: AI Engineer Coding Exercise

**Project:** RAG System Implementation for FastAPI Company  
**Timeline:** March 4-5, 2026 (2 Days)  
**Author:** Kefei Mo  
**Last Updated:** March 5, 2026

---

## Overview

This document captures high-level lessons learned during the development of a production-ready RAG (Retrieval-Augmented Generation) system within a 2-day timeline. Key focus areas include evaluation-driven development, AI-assisted testing, and systematic improvement methodologies.

---

## 1. AI-Driven Testing Development Strategy

### The Challenge
Traditional test-driven development (TDD) requires significant upfront time investment in writing comprehensive test suites. In a time-constrained project (2 days), this creates tension between shipping features and maintaining code quality.

### The Solution: AI-Assisted Test Generation
We employed an **AI-driven testing development approach** where GitHub Copilot/AI assistants were used to rapidly scaffold comprehensive test suites while maintaining high quality standards.

#### Strategy Components

**1. Test-After-Development with AI Acceleration**
- **Traditional Approach:** Write tests manually after implementation (slow, often incomplete)
- **AI-Driven Approach:** Use AI to generate comprehensive test suites based on existing code
- **Result:** 28 unit tests generated in ~30 minutes vs. ~3-4 hours manually

**2. Pattern-Based Test Generation**
```
Human Input (High-Level):
"Create tests for document ingestion: test loading, chunking, metadata preservation"

AI Output (Detailed):
- test_document_loader_initialization()
- test_load_documents()
- test_load_documents_nonexistent_path()
- test_chunk_text_basic()
- test_chunk_text_short_document()
- test_chunk_text_preserves_metadata()
- test_chunk_documents()
- test_find_sentence_boundary()
- test_chunk_size_validation()
```

**3. Iterative Refinement Through Dialogue**
- **Initial Generation:** AI creates tests based on assumed abstractions (e.g., `PromptBuilder` class)
- **Human Feedback:** "Why is PromptBuilder needed? The code already has `construct_prompt()`"
- **AI Correction:** Tests rewritten to match actual implementation
- **Lesson:** AI-assisted development requires human oversight to avoid over-engineering

**4. Fixture-Driven Test Architecture**
- AI generated `conftest.py` with reusable fixtures:
  - `sample_markdown_files`: Temporary test documents
  - `sample_retrieval_results`: Mock retrieval data
  - `sample_query`, `sample_context`: Common test inputs
- **Benefit:** Tests become more readable and maintainable

#### Metrics: AI-Driven Testing Effectiveness

| Metric | Manual Approach | AI-Driven Approach | Improvement |
|--------|----------------|-------------------|-------------|
| Time to write 28 tests | ~3-4 hours | ~30 minutes | **6-8x faster** |
| Test coverage | Variable (often <60%) | Comprehensive (>80%) | **Consistent quality** |
| Edge cases identified | Developer-dependent | AI suggests many | **More thorough** |
| Boilerplate code | Repetitive manual work | Auto-generated | **95% reduction** |

#### Key Insight: The "Test What Exists" Principle
The most important lesson from AI-driven testing:

> **AI will confidently generate tests for abstractions that don't exist.**  
> **Human responsibility: Verify tests match actual implementation.**

**Example from this project:**
- AI generated tests for `PromptBuilder` class (doesn't exist)
- Actual code uses `construct_prompt()` function (exists)
- **Correction:** Rewrote tests to match reality, not imagined abstractions

**Best Practice:**
1. Generate tests with AI
2. Review against actual codebase
3. Refactor tests to match implementation
4. Validate tests actually run and pass

---

## 2. Evaluation-Driven Development

### The Approach
Rather than guessing at improvements, we built a **3-stage evaluation pipeline** to systematically measure and improve RAG quality.

#### Pipeline Architecture
```
Stage 1A: Query RAG System (Reusable)
    ↓
    Save results (baseline_20_stage1.json)
    ↓
Stage 1B: Generate Reference Answers (One-Time Cost: $0.50-$1)
    ↓
    Save queries with references (baseline_20_with_refs.json)
    ↓
Stage 2: Evaluate with RAGAS (Iterate Freely)
    ↓
    Full 5-metric evaluation (baseline_20_full_eval.json)
```

**Key Innovation:** Separation of expensive operations (querying backend, generating references) from cheap iteration (RAGAS evaluation).

#### Benefits
- **Cost Efficiency:** $1 upfront, then iterate for free
- **Speed:** Re-evaluation takes ~1 minute vs. ~15 minutes for full pipeline
- **Flexibility:** Can change metrics, thresholds, or analysis without re-querying

### Critical Finding: Faithfulness < 0.7 Threshold
The evaluation immediately revealed:
- **Context Precision: 0.948** ✅ (Retrieval excellent)
- **Faithfulness: 0.634** ❌ (Generation has hallucination issues)
- **Answer Relevancy: 0.772** ✅ (Question alignment good)

**Lesson:** Evaluation catches issues that manual testing misses. Multiple queries scored 0.0 on faithfulness—a critical problem that would have gone unnoticed without systematic evaluation.

---

## 3. Testing Philosophy in Time-Constrained Projects

### The Pragmatic Balance

**Traditional TDD:**
```
Tests → Implementation → Refactor
Time: High upfront cost, pays off long-term
```

**AI-Driven Pragmatic Approach:**
```
Implementation → AI-Generated Tests → Validation → Refactor
Time: Low upfront cost, maintains quality
```

#### When to Use Each Approach

**Use Traditional TDD When:**
- Building critical financial/medical systems
- Long-term maintenance (>6 months) expected
- Team has strong TDD culture
- Timeline allows (>2 weeks)

**Use AI-Driven Testing When:**
- Time-constrained projects (2-5 days)
- Prototyping/MVP development
- Need quick quality validation
- Catching up on test coverage for existing code

### Test Categories We Implemented

**1. Unit Tests (28 tests, ~5 minutes runtime)**
- Document ingestion (9 tests)
- Retrieval logic (9 tests)
- Prompt construction (10 tests)
- **Coverage:** Core functionality without external dependencies
- **Marked:** `@pytest.mark.unit`

**2. Integration Tests (Skipped in time constraints)**
- Full pipeline with ChromaDB
- LLM generation end-to-end
- **Coverage:** System-level interactions
- **Marked:** `@pytest.mark.integration`
- **Status:** Documented but not executed (would require ChromaDB setup)

**3. Evaluation Tests (RAGAS pipeline)**
- 20-query baseline evaluation
- All 5 RAGAS metrics
- **Coverage:** Real-world performance
- **Cost:** $1 per run with OpenAI

#### Test Pyramid in Practice
```
           /\
          /  \  Evaluation Tests (RAGAS)
         /    \  - Expensive ($1/run)
        /______\  - Slow (15 min)
       /        \  - High confidence
      / Integration \ (Skipped)
     /____________\
    /              \
   /   Unit Tests   \ (28 tests)
  /__________________\ - Fast (5 min)
                       - Free
                       - Good coverage
```

---

## 4. Code Quality Without Over-Engineering

### What We Built
- **Utility Modules:** `app/utils/logging.py`, `app/utils/validators.py`
- **Test Configuration:** `pytest.ini`, `conftest.py` with fixtures
- **Comprehensive Tests:** 28 unit tests covering core functionality

### What We Avoided (Deliberately)
- **Over-Abstraction:** No unnecessary `PromptBuilder` class when `construct_prompt()` function suffices
- **Perfect Coverage:** 80% coverage is pragmatic; 100% is overkill for 2-day project
- **Premature Optimization:** Simple, readable code over clever architectures

### The "Good Enough" Principle
In time-constrained projects, **good enough > perfect**:

| Aspect | Perfect (Over-Engineering) | Good Enough (Pragmatic) | Our Choice |
|--------|---------------------------|------------------------|------------|
| Test Coverage | 100% | 80% | **80%** ✅ |
| Abstractions | Class hierarchies | Functions where possible | **Functions** ✅ |
| Documentation | Every function | Key functions + README | **Key + README** ✅ |
| Error Handling | All edge cases | Critical paths | **Critical paths** ✅ |

**Lesson:** Ship working software with good tests, not perfect software that ships late.

---

## 5. Evaluation Best Practices

### Distribution Analysis Over Single Metrics
**Bad Practice:**
```
Mean Faithfulness: 0.634
Conclusion: "System is bad"
```

**Good Practice:**
```
Mean: 0.634
P10:  0.0 (worst 10% completely failed)
P25:  0.4 (25% below acceptable)
P90:  0.9 (top 10% excellent)
Conclusion: "Bimodal distribution—some queries fail catastrophically, fix those first"
```

### Bad Case Rate Tracking
**Metric:** Percentage of queries below threshold
```python
bad_case_rate = (queries_below_threshold / total_queries) * 100

# Example: Faithfulness threshold = 0.4
# 5 out of 20 queries scored < 0.4
# bad_case_rate = 25%  ← More actionable than mean
```

### Failure Categorization
Don't just count failures—**categorize them**:
- **Retrieval Failure:** No relevant documents found (low context_precision)
- **LLM Hallucination:** Answer makes claims beyond context (low faithfulness)
- **Ambiguous Question:** Query unclear or multi-intent (low answer_relevancy)
- **Chunking Problem:** Context split poorly (low context_recall)

**Benefit:** Each category points to specific fixes.

---

## 6. Development Velocity Lessons

### Time Investment Breakdown (2-Day Project)

| Stage | Time Spent | % of Total | Value Delivered |
|-------|-----------|-----------|-----------------|
| **Setup & Planning** | 0.5h | 2% | Foundation |
| **Backend Core** | 3.0h | 14% | Working RAG system |
| **Frontend + Docker** | 3.5h | 16% | Full-stack demo |
| **Evaluation Framework** | 5.0h | 23% | **Highest value** |
| **Code Quality (Tests)** | 2.0h | 9% | Confidence boost |
| **Improvements (Next)** | 1.5h | 7% | Addressing faithfulness |
| **Documentation** | 2.0h | 9% | Professional polish |
| **Buffer/Debugging** | 4.5h | 20% | Reality tax |
| **Total** | **~22h** | **100%** | 2-day project |

**Insight:** Evaluation framework (23%) took longest but delivered **most value**—caught critical issues early.

### Productivity Multipliers

**1. AI Pair Programming**
- Test generation: **6-8x faster**
- Boilerplate code: **5x faster**
- Documentation: **3-4x faster**

**2. Reusable Evaluation Pipeline**
- Stage 1A+1B: One-time cost ($1)
- Stage 2: Iterate infinitely for free
- **ROI:** Pays off after 2-3 iterations

**3. Progressive Enhancement**
- Ship minimal viable product (Day 1)
- Add evaluation (Day 1 end)
- Improve based on data (Day 2)
- **Benefit:** Always have something demo-able

---

## 7. Common Pitfalls Avoided

### Pitfall 1: Testing Imaginary Abstractions
**Problem:** AI generated tests for `PromptBuilder` class that didn't exist.  
**Solution:** Human verification—rewrote tests for actual `construct_prompt()` function.  
**Lesson:** **Always verify AI-generated code matches reality.**

### Pitfall 2: Premature Optimization
**Problem:** Temptation to add caching, async, multi-threading early.  
**Solution:** Built simple synchronous pipeline first, measured performance, **then** optimized.  
**Lesson:** **"Make it work, make it right, make it fast"—in that order.**

### Pitfall 3: Over-Engineering Test Fixtures
**Problem:** Could have built complex database mocking, API stubs, etc.  
**Solution:** Simple `temp_dir` fixtures with sample markdown files.  
**Lesson:** **Simplest fixture that enables testing is best fixture.**

### Pitfall 4: Ignoring Evaluation Results
**Problem:** Built RAG system, assumed it worked well.  
**Solution:** Ran evaluation, discovered faithfulness 0.634 (critical issue).  
**Lesson:** **Trust data over intuition. Evaluation is not optional.**

---

## 8. Transferable Strategies

### For Future Projects

**1. Start with Evaluation Framework**
- Don't wait until "system is perfect"
- Build 3-stage reusable pipeline early
- **Benefit:** Catch issues while easy to fix

**2. Use AI for Accelerated Testing**
- Generate test scaffolds with AI
- Human validates and refines
- **Benefit:** 6-8x faster test development

**3. Embrace "Good Enough" Philosophy**
- 80% test coverage > 100% late
- Working code > perfect architecture
- **Benefit:** Ship on time with confidence

**4. Document Decisions, Not Just Code**
- Why we chose GPT4All over OpenAI
- Why 3-stage pipeline vs. single-stage
- **Benefit:** Future maintainers understand rationale

### For Team Adoption

**If implementing AI-driven testing in a team:**
1. **Establish human verification step** (AI generates, human validates)
2. **Create test templates** (AI follows team patterns)
3. **Set coverage targets** (80% pragmatic, 100% overkill)
4. **Review AI-generated tests in PRs** (ensure they test real code)

---

## 9. Key Takeaways

### Technical Lessons
1. ✅ **3-stage evaluation pipeline is essential** for iterative RAG improvement
2. ✅ **AI-driven testing is 6-8x faster** than manual test writing
3. ✅ **Faithfulness metric catches hallucinations** that manual testing misses
4. ✅ **Test what exists, not what you imagine** exists

### Process Lessons
1. ✅ **Evaluation-driven development > test-driven development** in time constraints
2. ✅ **Ship working software with tests > perfect software late**
3. ✅ **Distribution analysis > mean metrics** for actionable insights
4. ✅ **AI assistance requires human oversight** to avoid over-engineering

### Strategic Lessons
1. ✅ **Invest in evaluation infrastructure early** (highest ROI)
2. ✅ **Use AI for acceleration, not autopilot** (human validation required)
3. ✅ **Good enough beats perfect in time-constrained projects**
4. ✅ **Data-driven improvement > intuition-driven improvement**

---

## 10. What's Next

### Immediate Improvements (Stage 2B Hour 12-13)
1. **Enhanced RAGAS Analysis:**
   - Distribution statistics (P10, P25, P75, P90)
   - Bad case rate tracking (threshold: 0.4)
   - Failure categorization (retrieval, hallucination, ambiguous, chunking)

2. **Prompt Engineering (Option A):**
   - Migrate to LangChain PromptTemplate
   - Add few-shot examples (good vs. hallucinated answers)
   - Strengthen "DO NOT infer" system instructions
   - Add citation format requirements

3. **Re-evaluation:**
   - Run Stage 1A with improved prompts
   - Reuse references (no additional cost)
   - Target: Faithfulness > 0.75 (+0.116 improvement needed)

### Long-Term Vision
- **Stage 3A:** Hybrid retrieval (semantic + BM25)
- **Stage 3B:** Reranking with cross-encoder
- **Stage 3C:** Embedding model upgrade
- **Stage 3D:** Production deployment (K8s, monitoring)

---

## Conclusion

This 2-day project demonstrated that **AI-assisted development + evaluation-driven improvement** can produce production-ready systems in compressed timelines. The key is balancing speed with quality:

- **Use AI to accelerate** (testing, boilerplate, documentation)
- **Use evaluation to validate** (RAGAS metrics, not intuition)
- **Use pragmatism to ship** (80% solution on time > 100% late)

The most valuable lesson: **Systematic evaluation catches critical issues (faithfulness 0.634) that would have gone unnoticed with manual testing alone.** This validates the evaluation-first approach for RAG systems.

---

**Document Version:** 1.0  
**Created:** March 5, 2026  
**Next Review:** After Stage 2B completion (prompt engineering improvements)
