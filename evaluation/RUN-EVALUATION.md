# 🚀 Running RAGAS Baseline Evaluation with OpenAI

## Prerequisites

✅ Backend server running on port 8000  
✅ Test data ready: `data/baseline_20.json`  
✅ Evaluation environment set up: `venv-eval/`  
✅ Script updated with all 5 metrics  

## Quick Start

### 1. Set OpenAI API Key

```bash
export OPENAI_API_KEY="sk-proj-your-api-key-here"
```

**Important**: Replace with your actual OpenAI API key!

### 2. Activate Evaluation Environment

```bash
cd evaluation

# Create virtual environment (first time only)
python3 -m venv venv-eval

# Activate and install dependencies
source venv-eval/bin/activate
pip install -r requirements.txt
```

### 3. Run Baseline Evaluation

```bash
python run_ragas_baseline.py
```

**Expected Output:**
```
✓ Loaded 20 test queries
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1: Running RAG Queries
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Query 1/20: What is FastAPI?
  ✓ Success (3 sources, 81.6% confidence) [2.35s]
...
✓ Saved raw results to: data/results/baseline_20_raw.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 2: Running RAGAS Evaluation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Running RAGAS evaluation...
[Evaluation progress...]
✓ Saved RAGAS results to: data/results/baseline_20_ragas.json
```

## Expected Timing

- **Phase 1 (RAG Queries)**: ~40-80 seconds (20 queries × 2-4s each)
- **Phase 2 (RAGAS Evaluation)**: ~5-10 minutes with OpenAI API
- **Total**: ~6-11 minutes

## RAGAS Metrics Evaluated

1. **context_precision**: How relevant are the retrieved contexts?
   - Higher = better context relevance
   - Range: 0.0 to 1.0

2. **faithfulness**: Is the answer grounded in the context?
   - Higher = less hallucination
   - Range: 0.0 to 1.0

3. **answer_relevancy**: Does the answer address the question?
   - Higher = more relevant answers
   - Range: 0.0 to 1.0

4. **context_recall**: How much of ground truth is captured? ⚠️
   - Requires ground_truth field (may skip if not available)
   - Range: 0.0 to 1.0

5. **context_entity_recall**: How many entities are recalled? ⚠️
   - Requires ground_truth field (may skip if not available)
   - Range: 0.0 to 1.0

⚠️ **Note**: Metrics 4 & 5 require reference answers. The script will evaluate what's possible with available data.

## Output Files

### 1. Raw RAG Results
**Path**: `data/results/baseline_20_raw.json`

Contains:
- Original queries
- RAG system responses
- Retrieved contexts
- Confidence scores
- Response times

### 2. RAGAS Evaluation Results
**Path**: `data/results/baseline_20_ragas.json`

Contains:
- Aggregated metric scores
- Per-query breakdown
- Timestamp
- Dataset size

## Troubleshooting

### API Key Not Set
```
Error: OpenAI API key not found
```
**Solution**: Set the environment variable:
```bash
export OPENAI_API_KEY="sk-proj-your-key"
```

### Backend Not Running
```
Error: Connection refused to localhost:8000
```
**Solution**: Start the backend server:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Module Import Errors
```
ModuleNotFoundError: No module named 'ragas'
```
**Solution**: Activate the correct environment and install dependencies:
```bash
cd evaluation
source venv-eval/bin/activate
pip install -r requirements.txt
```

## Cost Estimation

**OpenAI API Usage:**
- Model: gpt-3.5-turbo (default for RAGAS)
- Estimated cost: ~$0.50 - $1.00 for 20 queries
- Based on: ~5 metrics × 20 queries × small evaluations

**Alternative (GPT4All):**
- Cost: $0 (free)
- Time: ~3 hours instead of 10 minutes
- See: `RAGAS-GPT4ALL-INVESTIGATION.md` for setup

## Next Steps After Evaluation

1. **Analyze Results**: Review `baseline_20_ragas.json`
2. **Document Findings**: Create `EVALUATION-REPORT.md`
3. **Calculate Statistics**:
   - Mean scores per metric
   - Query difficulty analysis (easy/medium/hard)
   - Identify weakest areas
4. **Complete Stage 1C**: Update todo list and commit
5. **Plan Improvements**: Based on metric scores

## Quick Reference Commands

```bash
# Full workflow
cd evaluation
export OPENAI_API_KEY="sk-proj-your-key"
source venv-eval/bin/activate
python run_ragas_baseline.py

# Check results
cat data/results/baseline_20_ragas.json | jq '.metrics'

# View raw queries
cat data/results/baseline_20_raw.json | jq '.[0]'
```

## Environment Info

**venv-eval/** environment contains:
- ragas==0.4.3
- openai==2.24.0
- langchain==1.2.10
- datasets==3.2.0
- All necessary dependencies

Created: 2026-03-04  
Last Updated: 2026-03-05
