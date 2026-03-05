# VCC RAG Evaluation - Quick Start Guide

**Purpose:** Run RAGAS evaluation on Visa Chart Components documentation

---

## Prerequisites

✅ Backend running: `http://localhost:8000`  
✅ VCC docs ingested: 276 documents, 2696 chunks  
✅ Evaluation environment: `venv-eval` with RAGAS + OpenAI API key  

---

## 3-Stage Pipeline

### Stage 1A: Query RAG System (~3 min)

```bash
cd backend/evaluation

# Activate evaluation environment
source ../../venv-eval/bin/activate

# Run VCC queries with source validation
python run_ragas_stage1_query.py \
  --input ../../data/test_queries/vcc_baseline_10.json \
  --output ../../data/results/vcc_baseline_10_stage1.json \
  --dataset-name vcc \
  --validate-sources
```

**Output:** `data/results/vcc_baseline_10_stage1.json`  
**Contains:** 10 queries, answers, contexts, confidence scores, source files

---

### Stage 1B: Generate References (~2 min, ~$0.50)

```bash
python run_ragas_stage1b_generate_references.py \
  --input ../../data/results/vcc_baseline_10_stage1.json \
  --output ../../data/results/vcc_baseline_10_with_refs.json
```

**Output:** `data/results/vcc_baseline_10_with_refs.json`  
**Contains:** Same as Stage 1A + ground truth references (OpenAI generated)

---

### Stage 2: RAGAS Evaluation (~1 min)

```bash
python run_ragas_stage2_eval.py \
  --input ../../data/results/vcc_baseline_10_with_refs.json \
  --output ../../data/results/vcc_baseline_10_full_eval.json
```

**Output:** `data/results/vcc_baseline_10_full_eval.json`  
**Contains:** All 5 RAGAS metrics for 10 queries (50 evaluations)

---

## Verify Results

```bash
# Check aggregated metrics
python -c "
import json
with open('../../data/results/vcc_baseline_10_full_eval.json') as f:
    data = json.load(f)
    metrics = data['aggregated_metrics']
    print('\nVCC Baseline Metrics:')
    for metric, score in metrics.items():
        print(f'  {metric}: {score:.3f}')
"
```

---

## Expected Metrics

| Metric | Target | Notes |
|--------|--------|-------|
| Context Precision | ≥0.75 | Retrieval quality |
| Faithfulness | ≥0.70 | Hallucination control |
| Answer Relevancy | ≥0.75 | Question alignment |
| Context Recall | ≥0.70 | Ground truth coverage |
| Context Entity Recall | ≥0.50 | Entity matching |

---

## Troubleshooting

### No contexts retrieved
- Check backend is running: `curl http://localhost:8000/health`
- Verify VCC docs ingested: `curl -X POST http://localhost:8000/api/v1/ingest/visa-docs?force_reingest=false`

### Source contamination warning
- Review `source_files` in Stage 1A output
- Check if FastAPI docs are being returned instead of VCC docs
- May indicate need for backend collection filtering

### OpenAI API errors
- Verify API key: `echo $OPENAI_API_KEY`
- Check rate limits (use `--batch-size 5` if hitting limits)

---

## Next Steps

1. **Run pipeline** (follow 3 stages above)
2. **Create summary**: `docs/VCC-BASELINE-SUMMARY.md`
3. **Analyze results**: Compare metrics with targets
4. **Document findings**: Add to `progress-tracking.md`

---

## File Locations

| File | Purpose |
|------|---------|
| `data/test_queries/vcc_baseline_10.json` | Input: VCC test queries |
| `data/results/vcc_baseline_10_stage1.json` | Stage 1A: RAG query results |
| `data/results/vcc_baseline_10_with_refs.json` | Stage 1B: + ground truth refs |
| `data/results/vcc_baseline_10_full_eval.json` | Stage 2: + RAGAS metrics |
| `docs/VCC-BASELINE-SUMMARY.md` | Final: Analysis & summary |

---

**Total time:** ~6 minutes  
**Total cost:** ~$0.50 (OpenAI API for references)  
**Ready:** Run Stage 1A now! 🚀
