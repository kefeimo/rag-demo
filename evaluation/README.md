# 🎯 RAGAS Evaluation Framework

Three-stage evaluation system for RAG (Retrieval-Augmented Generation) quality assessment using RAGAS metrics.

## 📋 Overview

**Three-Stage Pipeline:**
1. **Stage 1**: Query RAG system → Save responses
2. **Stage 1B**: (Optional) Generate reference answers → Enable all 5 metrics  
3. **Stage 2**: Run RAGAS evaluation → Get quality scores

**Benefits:**
- ✅ Reusable: Run evaluation multiple times without re-querying RAG
- ✅ Cost-effective: Separate data collection from evaluation
- ✅ Flexible: Generate references only when needed
- ✅ Fast iteration: Experiment with evaluation parameters

## 🎯 RAGAS Metrics

### Without References (2 metrics)
- **Faithfulness**: Answer grounded in retrieved context?
- **AnswerRelevancy**: Answer addresses the question?

### With References (5 metrics total)
- **ContextPrecision**: Relevant contexts retrieved?
- **ContextRecall**: Ground truth coverage?
- **ContextEntityRecall**: Entity match with reference?

## 🚀 Quick Start

### Minimal (2 metrics, ~2 minutes)

```bash
cd evaluation
source venv-eval/bin/activate

# Stage 1: Query RAG
python run_ragas_stage1_query.py \
  --input ../data/test_queries/baseline_3.json \
  --output ../data/results/baseline_3_stage1.json

# Stage 2: Evaluate
python run_ragas_stage2_eval.py \
  --input ../data/results/baseline_3_stage1.json \
  --output ../data/results/baseline_3_evaluated.json
```

### Full (5 metrics, ~5 minutes)

```bash
# Stage 1: Query RAG
python run_ragas_stage1_query.py \
  --input ../data/test_queries/baseline_20.json \
  --output ../data/results/baseline_20_stage1.json

# Stage 1B: Generate references
python run_ragas_stage1b_generate_references.py \
  --input ../data/results/baseline_20_stage1.json \
  --output ../data/results/baseline_20_with_refs.json

# Stage 2: Evaluate with all metrics
python run_ragas_stage2_eval.py \
  --input ../data/results/baseline_20_with_refs.json \
  --output ../data/results/baseline_20_evaluated.json
```

## 🔧 Setup

### Prerequisites
- ✅ Backend running on `localhost:8000`
- ✅ OpenAI API key set: `export OPENAI_API_KEY="sk-proj-..."`

### Install

```bash
cd evaluation

# Create virtual environment
python3 -m venv venv-eval
source venv-eval/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test setup
python test_openai_key.py
```

## 📊 Stages Explained

### Stage 1: Query RAG System

**What**: Execute queries through RAG, save responses

**Input**: Test queries JSON
```json
[{
  "id": 1,
  "query": "What is FastAPI?",
  "difficulty": "easy"
}]
```

**Output**: RAG responses JSON
```json
{
  "results": [{
    "query": "What is FastAPI?",
    "answer": "FastAPI is...",
    "contexts": ["context1", "context2"],
    "confidence": 0.85
  }]
}
```

**Command**:
```bash
python run_ragas_stage1_query.py \
  --input <queries.json> \
  --output <results.json>
```

### Stage 1B: Generate References (Optional)

**What**: Create ground truth answers using LLM

**Why**: Enables 3 additional RAGAS metrics

**Input**: Stage 1 results

**Output**: Stage 1 results + `reference` field per query

**Command**:
```bash
python run_ragas_stage1b_generate_references.py \
  --input <stage1.json> \
  --output <with_refs.json> \
  [--model gpt-3.5-turbo] \
  [--regenerate]
```

**Cost**: ~$0.30 for 20 queries

### Stage 2: RAGAS Evaluation

**What**: Evaluate responses using RAGAS metrics

**Input**: Stage 1 or Stage 1B results

**Output**: Evaluation scores + aggregated metrics

**Metrics**:
- Without references: 2 metrics
- With references: 5 metrics

**Command**:
```bash
python run_ragas_stage2_eval.py \
  --input <stage1_or_1b.json> \
  --output <evaluated.json>
```

**Cost**: ~$0.30 (2 metrics) or ~$0.80 (5 metrics)

## 💰 Cost Breakdown (20 queries)

| Stage | Model | Cost | Time |
|-------|-------|------|------|
| 1: Query RAG | Local GPT4All | $0 | 1-2 min |
| 1B: References | gpt-3.5-turbo | ~$0.30 | 2-3 min |
| 2: Eval (2 metrics) | gpt-3.5-turbo | ~$0.30 | 3-5 min |
| 2: Eval (5 metrics) | gpt-3.5-turbo | ~$0.80 | 5-10 min |
| **Total (Full)** | | **~$1.10** | **~10-15 min** |

**Free Alternative**: GPT4All (~3 hours, $0) - See `RAGAS-GPT4ALL-INVESTIGATION.md`

## 📁 File Structure

```
evaluation/
├── run_ragas_stage1_query.py          # Stage 1: Query RAG
├── run_ragas_stage1b_generate_references.py  # Stage 1B: Gen references
├── run_ragas_stage2_eval.py           # Stage 2: Evaluate
├── test_openai_key.py                 # Test API key
├── requirements.txt                   # Dependencies
├── README.md                          # This file
├── RAGAS-GPT4ALL-INVESTIGATION.md    # GPT4All breakthrough
├── venv-eval/                         # Virtual environment
└── archive/                           # Old test scripts
```

## 🔍 Output Analysis

Final evaluation output:
```json
{
  "aggregated_metrics": {
    "faithfulness": 0.92,
    "answer_relevancy": 0.88,
    "context_precision": 0.85,
    "context_recall": 0.80,
    "context_entity_recall": 0.78
  },
  "results": [...]
}
```

**Score Interpretation**:
- 0.9-1.0: Excellent ✅
- 0.7-0.9: Good 👍
- 0.5-0.7: Fair ⚠️
- <0.5: Poor ❌

## 🎯 Best Practices

1. **Start small**: Test with `baseline_3.json` first
2. **Stage 1 once**: Query RAG once, evaluate multiple times
3. **References optional**: Only generate for full metrics
4. **Version control**: Save all intermediate outputs
5. **Cost management**: Stage 1B is optional

## 🐛 Troubleshooting

### Backend not running
```
Error: HTTPConnectionPool...Max retries exceeded
```
**Fix**: Start backend
```bash
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### API quota exceeded
```
Error: You exceeded your current quota
```
**Fix**: Add credits at https://platform.openai.com/settings/organization/billing

### No references warning
```
⚠ No reference answers found
```
**Info**: Run Stage 1B to generate references (optional for full metrics)

## 📚 Resources

- [RAGAS Docs](https://docs.ragas.io/)
- [OpenAI API](https://platform.openai.com/docs)
- [Our GPT4All Breakthrough](RAGAS-GPT4ALL-INVESTIGATION.md)

---

**Next**: Test with `baseline_3.json` to verify setup! 🚀
