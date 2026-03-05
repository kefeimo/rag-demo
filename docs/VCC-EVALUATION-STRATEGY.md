# VCC RAG Evaluation Strategy

**Date:** March 5, 2026  
**Status:** 🟡 In Progress  
**Goal:** Evaluate RAG system with Visa Chart Components documentation (isolated from FastAPI)

---

## 1. Background

### Previous Work (FastAPI Baseline)
- ✅ 20-query FastAPI evaluation complete
- ✅ Results: Context Precision 0.948 ✓, Faithfulness 0.634 ✗, Answer Relevancy 0.772 ✓
- ✅ Archived in `docs/results-archive/`

### Pivot Decision
- **Focus:** VCC docs RAG system evaluation (new data pipeline)
- **Reason:** Showcase data engineering + RAG with real Visa repositories
- **Archive:** FastAPI evaluation complete, no further iterations

---

## 2. Isolation Strategy

### Why Isolation is Critical
1. **Different data sources:** VCC (276 docs, 2696 chunks) vs FastAPI (13 docs, 252 chunks)
2. **Prevent contamination:** VCC queries should NOT retrieve FastAPI docs
3. **Separate evaluation:** Independent baselines, metrics, improvements

### Isolation Approach

#### ✅ Level 1: File-Based Separation (IMPLEMENTED)
- **Test queries:** 
  - VCC: `data/test_queries/vcc_baseline_10.json`
  - FastAPI: `data/test_queries/baseline_20.json` (archived)
- **Result files:**
  - VCC: `vcc_baseline_10_stage1.json`, `vcc_baseline_10_with_refs.json`, `vcc_baseline_10_full_eval.json`
  - FastAPI: `baseline_20_*.json` (archived)
- **Benefit:** Clear separation, no file naming conflicts

#### ✅ Level 2: Source Validation (IMPLEMENTED)
- **Script enhancement:** `run_ragas_stage1_query.py` now supports:
  - `--dataset-name vcc` parameter (tracks dataset in output)
  - `--validate-sources` flag (checks source files match expected)
  - `expected_source` field in test queries (e.g., "visa_code_docs.json")
- **Validation logic:**
  - Check if ≥50% of retrieved sources match expected dataset
  - Warn if contamination detected (e.g., FastAPI docs in VCC results)
  - Log source files: `["visa_code_docs.json", "visa_repo_docs.json", ...]`
- **Benefit:** Detect cross-contamination, validate RAG isolation

#### 🔄 Level 3: Backend Collection Filtering (FUTURE)
- **Not implemented yet** (beyond current scope)
- **Option A:** Separate ChromaDB collections (`fastapi_docs`, `vcc_docs`)
- **Option B:** Single collection with metadata filtering (`source="vcc"`)
- **Option C:** Hybrid with cross-search capability
- **Benefit:** Guaranteed isolation at retrieval level

---

## 3. VCC Test Dataset

### Source: Golden Test Cases
File: `data-pipeline/GOLDEN-TEST-CASES.md`

### 10 Test Queries

#### From Issues (2 queries)
1. **Issue #84** (feature enhancement): "How can I improve the group focus indicator in Visa Chart Components?"
   - Expected source: `visa_issue_qa.json`
   - Difficulty: Medium
   - Category: Feature enhancement

2. **Issue #51** (technical question): "How do I work with frequency values in Alluvial Chart?"
   - Expected source: `visa_issue_qa.json`
   - Difficulty: Medium
   - Category: Technical question

#### Derived from Issue #84 (3 queries)
3. "What accessibility features does Visa Chart Components provide?"
4. "How do keyboard navigation and focus work in VCC charts?"
5. "Can I customize focus indicators in the charts?"
   - Expected source: `visa_repo_docs.json`
   - Difficulty: Medium
   - Category: Feature inquiry

#### Derived from Issue #51 (2 queries)
6. "How do I use the Alluvial Chart component?"
7. "What data format does Alluvial Chart expect?"
   - Expected source: `visa_code_docs.json`
   - Difficulty: Easy-Medium
   - Category: API usage

#### General VCC (3 queries)
8. "How do I create a bar chart with Visa Chart Components?"
9. "What is IDataTableProps and how do I use it?"
10. "How do I integrate Visa Chart Components with React?"
    - Expected sources: `visa_code_docs.json`, `visa_repo_docs.json`
    - Difficulty: Easy-Medium
    - Category: Usage, API interface, Integration

---

## 4. Evaluation Pipeline (3 Stages)

### Stage 1A: Query RAG System (~3 min)
```bash
cd backend/evaluation
python run_ragas_stage1_query.py \
  --input ../../data/test_queries/vcc_baseline_10.json \
  --output ../../data/results/vcc_baseline_10_stage1.json \
  --dataset-name vcc \
  --validate-sources
```

**Expected output:**
- 10/10 queries successful
- All contexts from VCC sources (validated)
- Saved: `vcc_baseline_10_stage1.json`

### Stage 1B: Generate References (~2 min)
```bash
python run_ragas_stage1b_generate_references.py \
  --input ../../data/results/vcc_baseline_10_stage1.json \
  --output ../../data/results/vcc_baseline_10_with_refs.json
```

**Expected output:**
- 10/10 references generated (OpenAI gpt-3.5-turbo)
- Cost: ~$0.50
- Saved: `vcc_baseline_10_with_refs.json`

### Stage 2: RAGAS Evaluation (~1 min)
```bash
python run_ragas_stage2_eval.py \
  --input ../../data/results/vcc_baseline_10_with_refs.json \
  --output ../../data/results/vcc_baseline_10_full_eval.json
```

**Expected output:**
- All 5 metrics: context_precision, faithfulness, answer_relevancy, context_recall, context_entity_recall
- 50 evaluations (10 queries × 5 metrics)
- Saved: `vcc_baseline_10_full_eval.json`

---

## 5. Success Criteria

### Isolation Validation
- ✅ **Source purity:** ≥95% of retrieved sources are VCC docs
- ✅ **No FastAPI contamination:** <5% sources from FastAPI docs
- ✅ **Expected source match:** ≥50% per query category

### RAGAS Metrics (Targets)
| Metric | Target | Notes |
|--------|--------|-------|
| Context Precision | ≥0.75 | Retrieval quality |
| Faithfulness | ≥0.70 | Hallucination control |
| Answer Relevancy | ≥0.75 | Question alignment |
| Context Recall | ≥0.70 | Ground truth coverage |
| Context Entity Recall | ≥0.50 | Entity matching |

### Golden Test Cases
- ✅ **Issue #84** (focus indicator): Confidence ≥0.75, correct source
- ✅ **Issue #51** (Alluvial Chart): Confidence ≥0.75, correct source

---

## 6. Analysis & Documentation

### VCC-BASELINE-SUMMARY.md (to be created)
- Aggregated metrics (mean, min, max, median)
- Per-query results with confidence scores
- Source purity analysis
- Golden test case results
- Comparison with FastAPI baseline (if applicable)
- VCC-specific challenges and insights

### Key Questions to Answer
1. **Retrieval quality:** How well does RAG retrieve VCC docs?
2. **Data type distribution:** Repo docs vs Code docs vs Issue Q&A
3. **Chart-specific queries:** Bar chart vs Alluvial vs general APIs
4. **Issue Q&A effectiveness:** Do Issue #84/#51 retrieve correctly?
5. **Source contamination:** Any FastAPI docs leaking in?

---

## 7. Timeline

| Hour | Task | Status |
|------|------|--------|
| Hour 11 | Setup VCC evaluation infrastructure | 🟡 In Progress |
| Hour 12 | Run 3-stage VCC baseline | ⬜ Pending |
| Hour 13 | Analysis & documentation | ⬜ Pending |

**Total time:** 3 hours  
**Cost:** ~$0.50 (OpenAI API)

---

## 8. Next Steps (After Baseline)

### Improvement Options (if needed)
1. **Prompt Engineering:** Enhance system prompt for VCC context
2. **Retrieval Tuning:** Adjust chunk size, top_k for chart docs
3. **Reranking:** Cross-encoder for VCC-specific ranking
4. **Metadata Filtering:** Backend support for collection isolation

### Future Enhancements
- Expand to 20-30 VCC queries
- Add code example retrieval tests
- Test multi-turn conversations
- Evaluate cross-chart queries (e.g., "Compare bar chart vs alluvial")

---

## 9. Files Created/Modified

### New Files
- ✅ `data/test_queries/vcc_baseline_10.json` (VCC test queries)
- ✅ `docs/VCC-EVALUATION-STRATEGY.md` (this document)
- ⬜ `data/results/vcc_baseline_10_stage1.json` (pending Stage 1A)
- ⬜ `data/results/vcc_baseline_10_with_refs.json` (pending Stage 1B)
- ⬜ `data/results/vcc_baseline_10_full_eval.json` (pending Stage 2)
- ⬜ `docs/VCC-BASELINE-SUMMARY.md` (pending analysis)

### Modified Files
- ✅ `backend/evaluation/run_ragas_stage1_query.py` (added `--dataset-name`, `--validate-sources`)
- ✅ `docs/progress-tracking.md` (updated Stage 2B plan)

---

**Status:** 🟡 Ready to run VCC baseline evaluation  
**Blockers:** None  
**Next Action:** Run Stage 1A (Query RAG system with VCC queries)
