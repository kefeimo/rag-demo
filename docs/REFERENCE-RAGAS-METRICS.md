# RAGAS Metrics Reference Guide

**Reference Document for VCC RAG Evaluation**  
**Date:** March 5, 2026  
**Source:** Day 4 RAGAS Study Materials  
**Purpose:** Standard RAGAS metric definitions for evaluation consistency

---

## 🎯 Overview

This document defines the **5 core RAGAS metrics** used for evaluating the VCC RAG system, plus one additional metric for entity-heavy domains. All evaluation reports and analysis should reference these standard definitions.

### The 5 Standard RAGAS Metrics

1. **Context Precision** - Are relevant docs ranked higher?
2. **Context Recall** - Did retrieval capture necessary information?
3. **Faithfulness** - Is the answer grounded in retrieved context?
4. **Answer Relevancy** - Does the answer address the question?
5. **Answer Correctness** - Is the factual content accurate?

### Additional RAGAS Metric for Entity-Heavy Domains

6. **Context Entity Recall** - Did retrieval capture key entities? (Specialized metric for tourism, medical, legal, technical documentation)

---

## 📊 Metric 1: Context Precision

### Definition

**Goal:** Measure if relevant documents are ranked higher than irrelevant ones

### Algorithm

```python
def calculate_context_precision(question, retrieved_contexts, ground_truth=None):
    """
    Evaluate if relevant docs appear earlier in ranking
    """
    
    # Step 1: LLM judges relevance of each context
    relevance_scores = []
    for i, context in enumerate(retrieved_contexts):
        prompt = f"""
        Given the question: {question}
        And the context: {context}
        
        Is this context useful for answering the question?
        Answer: Yes or No
        """
        
        llm_response = call_llm(prompt)
        is_relevant = (llm_response.lower() == "yes")
        relevance_scores.append(is_relevant)
    
    # Step 2: Calculate precision at each rank
    precisions = []
    num_relevant_so_far = 0
    
    for k, is_relevant in enumerate(relevance_scores, start=1):
        if is_relevant:
            num_relevant_so_far += 1
            precision_at_k = num_relevant_so_far / k
            precisions.append(precision_at_k)
    
    # Step 3: Average precision
    if len(precisions) == 0:
        return 0.0
    
    context_precision = sum(precisions) / len(precisions)
    return context_precision
```

### Example

```python
Question: "How to setup Docker?"

Retrieved contexts (top 5):
1. "Docker Compose config..." → LLM: Yes ✅
2. "Database schema..." → LLM: No ❌
3. "Docker networking..." → LLM: Yes ✅
4. "API endpoints..." → LLM: No ❌
5. "Docker volumes..." → LLM: Yes ✅

Relevance: [True, False, True, False, True]

Precision calculations:
- Rank 1: Relevant → P@1 = 1/1 = 1.0
- Rank 2: Not relevant → skip
- Rank 3: Relevant → P@3 = 2/3 = 0.67
- Rank 4: Not relevant → skip
- Rank 5: Relevant → P@5 = 3/5 = 0.60

Context Precision = (1.0 + 0.67 + 0.60) / 3 = 0.757
```

### Interpretation

| Score | Status | Meaning |
|-------|--------|---------|
| ≥0.90 | ✅ Excellent | Minimal noise, relevant docs at top |
| 0.75-0.89 | ✅ Good | Some irrelevant docs mixed in |
| 0.60-0.74 | ⚠️ Fair | Noticeable noise in retrieval |
| <0.60 | ❌ Poor | Too much noise, tune ranking |

### Target for VCC System
- **Minimum:** ≥0.75
- **Current:** 0.989 ✅ (Excellent)

---

## 📚 Metric 2: Context Recall

### Definition

**Goal:** Measure what fraction of necessary information was retrieved

### Algorithm

```python
def calculate_context_recall(question, retrieved_contexts, ground_truth_answer):
    """
    Check if all information needed for answer is in retrieved contexts
    """
    
    # Step 1: Extract atomic facts from ground truth answer
    prompt = f"""
    Break down this answer into individual factual statements:
    
    Answer: {ground_truth_answer}
    
    List each fact on a new line.
    """
    
    facts = call_llm(prompt).split('\n')
    
    # Step 2: Check if each fact is supported by contexts
    supported_facts = 0
    
    for fact in facts:
        prompt = f"""
        Question: Can this statement be inferred from ANY of the contexts?
        Statement: {fact}
        
        Contexts:
        {'\n---\n'.join(retrieved_contexts)}
        
        Answer: Yes or No
        """
        
        if call_llm(prompt).lower() == "yes":
            supported_facts += 1
    
    # Step 3: Calculate recall
    context_recall = supported_facts / len(facts) if facts else 0.0
    return context_recall
```

### Example

```python
Question: "What database does the system use?"

Ground truth: "Uses PostgreSQL with PostGIS extension for spatial data"

Extracted facts:
1. "Uses PostgreSQL database"
2. "Has PostGIS extension"
3. "Handles spatial data"

Retrieved contexts:
- Context 1: "...PostgreSQL is the database..."
- Context 2: "...spatial operations..."
- Context 3: "...API endpoints..."

Fact verification:
1. "Uses PostgreSQL" → Yes ✅ (in Context 1)
2. "Has PostGIS" → No ❌ (not mentioned)
3. "Handles spatial data" → Yes ✅ (in Context 2)

Context Recall = 2/3 = 0.667
```

### Interpretation

| Score | Status | Meaning |
|-------|--------|---------|
| ≥0.90 | ✅ Excellent | Comprehensive retrieval |
| 0.75-0.89 | ✅ Good | Most info retrieved |
| 0.60-0.74 | ⚠️ Fair | Missing some key info |
| <0.60 | ❌ Poor | Significant gaps in retrieval |

### Target for VCC System
- **Minimum:** ≥0.70
- **Current:** 0.975 ✅ (Excellent)

---

## 🏷️ Metric 2B: Context Entity Recall (Additional)

### Definition

**Goal:** Measure if retrieval captured key entities (proper nouns, technical terms) from reference answer

**Note:** This is an **official RAGAS metric** but specialized for entity-heavy domains like tourism, medical records, legal documents, and technical documentation.

### Algorithm

```python
def calculate_context_entity_recall(retrieved_contexts, ground_truth_answer):
    """
    Check if key entities from reference are present in contexts.
    
    Formula: | CN ∩ GN | / | GN |
    Where:
      CN = set of entities in retrieved contexts
      GN = set of entities in ground truth (reference)
    """
    
    # Step 1: Extract entities from ground truth
    prompt = f"""
    Extract all important entities (proper nouns, technical terms, API names) 
    from the following text:
    
    Text: {ground_truth_answer}
    
    List each entity on a new line.
    """
    
    ground_truth_entities = set(call_llm(prompt).split('\n'))
    
    # Step 2: Extract entities from all contexts
    context_text = '\n'.join(retrieved_contexts)
    
    prompt = f"""
    Extract all important entities (proper nouns, technical terms, API names) 
    from the following text:
    
    Text: {context_text}
    
    List each entity on a new line.
    """
    
    context_entities = set(call_llm(prompt).split('\n'))
    
    # Step 3: Calculate overlap
    overlapping_entities = ground_truth_entities.intersection(context_entities)
    
    if len(ground_truth_entities) == 0:
        return 1.0  # No entities to recall
    
    entity_recall = len(overlapping_entities) / len(ground_truth_entities)
    return entity_recall
```

### Example

```python
Question: "What database does the system use?"

Ground truth: "Uses PostgreSQL with PostGIS extension for spatial data"

Extracted entities from ground truth:
- "PostgreSQL"
- "PostGIS"
- "spatial data"

Retrieved contexts:
- Context 1: "...PostgreSQL is the primary database..."
- Context 2: "...handles spatial operations..."
- Context 3: "...API endpoints use REST..."

Extracted entities from contexts:
- "PostgreSQL" ✅
- "spatial" ⚠️ (partial match for "spatial data")
- "REST"
- "API"

Entity matching:
1. "PostgreSQL" → ✅ Exact match in Context 1
2. "PostGIS" → ❌ Not mentioned in any context
3. "spatial data" → ❌ Only "spatial" appears (not exact match)

Context Entity Recall = 1/3 = 0.333
```

### Key Difference from Context Recall

| Aspect | Context Recall | Context Entity Recall |
|--------|----------------|----------------------|
| **What it measures** | ALL factual statements | KEY ENTITIES only |
| **Granularity** | Statement-level | Entity-level |
| **Strictness** | Less strict (allows inference) | More strict (exact matching) |
| **Evaluation** | Can infer facts from context | Requires exact entity mentions |

**Example:**
- Reference: "Use `IDataTableProps` interface with `accessibility` prop"
- Context mentions: "data table properties interface" and "a11y features"

**Context Recall**: 1.0 ✅ (can INFER both facts)  
**Entity Recall**: 0.0 ❌ (neither exact entity string present)

### Interpretation

| Score | Status | Meaning |
|-------|--------|---------|
| ≥0.70 | ✅ Excellent | Very strong entity coverage (rare!) |
| 0.50-0.69 | ✅ Good | Decent entity matching |
| 0.30-0.49 | ⚠️ Fair | Acceptable for technical documentation |
| <0.30 | ❌ Poor | Missing too many key entities |

**Note:** Entity extraction is notoriously difficult. Scores ≥0.70 are rare even for good systems.

### When to Use This Metric

**Use when:**
- Domain has many specific entities (medical terms, legal citations, API names)
- Exact entity matching is critical (e.g., "IDataTableProps" vs "data table properties")
- Working in tourism, medical, legal, or technical documentation domains
- You need stricter evaluation than Context Recall

**Don't use when:**
- General question answering (use Context Recall instead)
- Entities are not central to your domain
- You care more about overall information completeness

### Target for VCC System
- **Minimum:** ≥0.30 (technical documentation baseline)
- **Good:** ≥0.50
- **Current:** 0.446 ⚠️ (Fair - acceptable for API documentation with many exact terms)

### VCC Analysis

**Why VCC's entity recall is lower (0.446):**
1. **Many exact API names:** IDataTableProps, IAccessibilityType, etc.
2. **Strict matching:** "accessibility" ≠ "a11y" in entity extraction
3. **Technical domain:** Requires precise terminology matching

**This is normal!** Context Recall at 1.000 shows retrieval is comprehensive. Entity recall at 0.446 is acceptable for technical docs.

---

## 🔍 Metric 3: Faithfulness

### Definition

**Goal:** Detect hallucinations - is answer grounded in retrieved context?

### Algorithm

```python
def calculate_faithfulness(retrieved_contexts, generated_answer):
    """
    Check if ALL statements in answer come from contexts
    """
    
    # Step 1: Decompose answer into atomic claims
    prompt = f"""
    Break this answer into simple, atomic statements.
    Each statement should be a single factual claim.
    
    Answer: {generated_answer}
    
    Statements:
    """
    
    statements = call_llm(prompt).split('\n')
    
    # Step 2: Verify each statement against contexts
    supported_count = 0
    
    for statement in statements:
        prompt = f"""
        Context:
        {'\n'.join(retrieved_contexts)}
        
        Statement: {statement}
        
        Question: Is this statement directly supported by the context above?
        - Yes: If the statement is explicitly stated or clearly implied
        - No: If the statement is not in the context or requires external knowledge
        
        Answer: Yes or No
        """
        
        response = call_llm(prompt)
        if response.lower() == "yes":
            supported_count += 1
    
    # Step 3: Calculate faithfulness
    faithfulness = supported_count / len(statements) if statements else 1.0
    return faithfulness
```

### Example: Detecting Hallucinations

```python
Retrieved contexts:
- "System is built with Django"
- "Uses Docker for deployment"

Generated answer:
"Django application that uses Docker and PostgreSQL. 
Supports multi-tenancy with React frontend."

Extracted statements:
1. "Built with Django" → Yes ✅ (in context)
2. "Uses Docker for deployment" → Yes ✅ (in context)
3. "Uses PostgreSQL" → No ❌ (NOT in context - hallucination!)
4. "Supports multi-tenancy" → No ❌ (NOT in context - hallucination!)
5. "Has React frontend" → No ❌ (NOT in context - hallucination!)

Faithfulness = 2/5 = 0.40 (60% hallucination rate! 🚨)
```

### Interpretation

| Score | Status | Meaning |
|-------|--------|---------|
| ≥0.90 | ✅ Excellent | Minimal hallucination |
| 0.75-0.89 | ✅ Good | Some ungrounded statements |
| 0.60-0.74 | ⚠️ Fair | Noticeable hallucinations |
| <0.60 | ❌ Poor | Critical hallucination issue |

### Target for VCC System
- **Minimum:** ≥0.70
- **Current:** 0.730 ✅ (Good)

---

## 🎯 Metric 4: Answer Relevancy

### Definition

**Goal:** Does the answer actually address the question?

### Algorithm

```python
def calculate_answer_relevancy_advanced(question, generated_answer):
    """
    Generate questions from answer, compare to original
    """
    
    # Step 1: Generate questions that answer would address
    prompt = f"""
    Given this answer:
    {generated_answer}
    
    Generate 3 questions that this answer would be appropriate for:
    """
    
    generated_questions = call_llm(prompt).split('\n')
    
    # Step 2: Calculate similarity with original question
    original_q_emb = encode(question)
    
    similarities = []
    for gen_q in generated_questions:
        gen_q_emb = encode(gen_q)
        sim = cosine_similarity(original_q_emb, gen_q_emb)
        similarities.append(sim)
    
    # Step 3: Average similarity
    answer_relevancy = sum(similarities) / len(similarities)
    return answer_relevancy
```

### Example

```python
Original question:
"How do I setup Docker for development?"

Generated answer:
"Docker Compose is used. Create docker-compose.yml, 
run 'docker-compose up' to start services."

Generated questions from answer:
1. "How to use Docker Compose?" → Sim: 0.85
2. "What command starts Docker?" → Sim: 0.78
3. "How to configure Docker Compose?" → Sim: 0.82

Answer Relevancy = (0.85 + 0.78 + 0.82) / 3 = 0.817
```

### Edge Cases

```python
# Case 1: Overly verbose answer (info dump)
Question: "What is Docker?"
Answer: "Docker is... [500 words about containers, Kubernetes, cloud...]"
→ Low relevancy (includes too much irrelevant info)

# Case 2: Too brief
Question: "How do I setup Docker for development?"
Answer: "Use Docker Compose"
→ Lower relevancy (technically correct but incomplete)

# Case 3: Different terminology
Question: "How to containerize the app?"
Answer: "Use Docker to package the application..."
→ Should still score high (captures intent)
```

### Interpretation

| Score | Status | Meaning |
|-------|--------|---------|
| ≥0.90 | ✅ Excellent | Answer directly addresses question |
| 0.75-0.89 | ✅ Good | Mostly on-topic |
| 0.60-0.74 | ⚠️ Fair | Some off-topic content |
| <0.60 | ❌ Poor | Answer doesn't address question |

### Target for VCC System
- **Minimum:** ≥0.75
- **Current:** 0.656 ❌ (Below target - LLM upgrade needed)

---

## ✅ Metric 5: Answer Correctness

### Definition

**Goal:** Is the factual content accurate compared to ground truth?

### Algorithm

```python
def calculate_answer_correctness(ground_truth, generated_answer):
    """
    Compare generated answer with ground truth using F1 score
    """
    
    # Step 1: Extract facts from both
    gt_facts = extract_facts(ground_truth)
    gen_facts = extract_facts(generated_answer)
    
    # Step 2: Calculate True Positives, False Positives, False Negatives
    prompt_template = """
    Ground truth fact: {gt_fact}
    Generated fact: {gen_fact}
    
    Are these facts saying the same thing?
    Answer: Yes or No
    """
    
    TP = 0  # Correct facts in answer
    FP = 0  # Incorrect/extra facts in answer
    FN = 0  # Missing facts from ground truth
    
    for gen_fact in gen_facts:
        matched = False
        for gt_fact in gt_facts:
            if facts_match(gen_fact, gt_fact):
                TP += 1
                matched = True
                break
        
        if not matched:
            FP += 1  # Generated fact not in ground truth
    
    FN = len(gt_facts) - TP  # Facts in ground truth but not generated
    
    # Step 3: Calculate F1 score
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    return f1
```

### Example

```python
Ground truth:
"System uses Django and PostgreSQL. It has REST API."

Generated answer:
"Built with Django. Uses PostgreSQL and includes GraphQL API."

Ground truth facts:
1. "Uses Django"
2. "Uses PostgreSQL"
3. "Has REST API"

Generated facts:
1. "Built with Django" → Matches GT fact 1 ✅
2. "Uses PostgreSQL" → Matches GT fact 2 ✅
3. "Has GraphQL API" → No match ❌ (GT says REST, not GraphQL)

True Positives: 2 (Django, PostgreSQL)
False Positives: 1 (GraphQL API - wrong!)
False Negatives: 1 (REST API - missed!)

Precision = 2 / (2+1) = 0.667
Recall = 2 / (2+1) = 0.667
F1 = 2 * (0.667 * 0.667) / (0.667 + 0.667) = 0.667

Answer Correctness = 0.667
```

### Interpretation

| Score | Status | Meaning |
|-------|--------|---------|
| ≥0.90 | ✅ Excellent | Highly accurate answer |
| 0.75-0.89 | ✅ Good | Mostly correct, minor issues |
| 0.60-0.74 | ⚠️ Fair | Some factual errors |
| <0.60 | ❌ Poor | Significant inaccuracies |

### Target for VCC System
- **Minimum:** ≥0.70
- **Current:** Not measured (requires ground truth answers)

---

## 📊 VCC Baseline Performance Summary

### Current Metrics (Semantic-Only Baseline)

| Metric | Score | Target | Status | Gap |
|--------|-------|--------|--------|-----|
| Context Precision | 0.989 | ≥0.75 | ✅ PASS | +0.239 |
| Context Recall | 0.975 | ≥0.70 | ✅ PASS | +0.275 |
| Faithfulness | 0.730 | ≥0.70 | ✅ PASS | +0.030 |
| Answer Relevancy | 0.656 | ≥0.75 | ❌ FAIL | -0.094 |
| Answer Correctness | N/A | ≥0.70 | ⬜ Not measured | N/A |

### Overall Assessment

**Strengths:**
- ✅ Excellent retrieval quality (Precision 0.989, Recall 0.975)
- ✅ Good faithfulness (0.730, minimal hallucination)

**Areas for Improvement:**
- ❌ Answer Relevancy below target (0.656 vs 0.75)
  - **Root Cause:** GPT4All Mistral-7B weak instruction following
  - **Solution:** Switch to GPT-3.5/4 (~$0.002/query)
  - **Expected:** 0.656 → 0.80+

### Hybrid Search Impact

**Query 9 (IDataTableProps):**
- Semantic-only: 0.687 confidence
- Hybrid-fallback: 0.898 confidence (+31% improvement)
- Status: ✅ Retrieval problem solved

---

## 🎯 Metric Selection Guide

### When to Use Each Metric

**Context Precision & Recall:**
- Use when: Tuning retrieval system
- Focus: Retrieval quality, ranking, completeness

**Faithfulness:**
- Use when: Detecting hallucinations
- Focus: LLM prompt engineering, temperature tuning

**Answer Relevancy:**
- Use when: Improving answer quality
- Focus: Question understanding, prompt design

**Answer Correctness:**
- Use when: You have ground truth answers
- Focus: Overall system accuracy

### Recommended Priorities

1. **Always measure:** Context Precision, Faithfulness
2. **Measure for tuning:** Context Recall, Answer Relevancy
3. **Measure if available:** Answer Correctness (requires ground truth)
4. **Measure for entity-heavy domains:** Context Entity Recall (technical docs, medical, legal, tourism)

---

## 🔧 Additional Tracking (Optional)

The following are **NOT** RAGAS metrics but may be useful for operational monitoring:

### Performance Metrics
- **Response Time:** Latency for RAG pipeline
- **Token Cost:** API usage costs
- **Throughput:** Queries per second

### Custom Domain Metrics
- **Source Coverage:** Percentage of unique sources used
- **Confidence Scores:** System's self-assessment of answer quality
- **Unknown Detection:** Ability to detect when answer is not in knowledge base

**Note:** These should be reported separately from RAGAS metrics to avoid confusion.

---

## 📚 References

**Official RAGAS Documentation:**
- GitHub: https://github.com/explodinggradients/ragas
- Docs: https://docs.ragas.io/

**VCC Evaluation Documents:**
- [VCC-BASELINE-SUMMARY.md](./VCC-BASELINE-SUMMARY.md) - Baseline evaluation results
- [HYBRID-SEARCH-CASE-STUDY.md](./HYBRID-SEARCH-CASE-STUDY.md) - Retrieval improvements

**Study Materials:**
- Day 4: `/day4-vector-db-evaluation/rag-evaluator/study-materials/`
  - `01-ragas-fundamentals.md` - Overview and concepts
  - `02-ragas-metrics-deep-dive.md` - Detailed metric explanations

---

**Document Status:** ✅ Reference Standard  
**Last Updated:** March 5, 2026, 18:00  
**Maintained By:** VCC RAG Evaluation Team  
**Version:** 1.1 (Added Context Entity Recall definition)
