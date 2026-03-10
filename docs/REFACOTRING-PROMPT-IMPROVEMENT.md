# Prompt Engineering Improvement Notes

**Date:** March 5-6, 2026  
**Status:** ✅ Implemented & Tested (March 6, 2026)

---

## 🎯 Overview

This document tracks prompt engineering improvements based on real-world testing and evaluation results. These improvements enhance the RAG system's robustness to user input variations and improve answer quality.

---

## ✅ COMPLETED IMPROVEMENTS (March 6, 2026)

### Improvement 1: Relaxed Prompt Instructions for Code Examples

**Date Implemented:** March 6, 2026  
**Priority:** HIGH - Critical for functionality  
**Category:** Prompt Engineering

#### Problem Description

The LLM was returning "I don't have enough information" responses even when relevant code examples and documentation were retrieved and included in the prompt.

**Symptoms:**
- Retrieved documents: 3 sources with 65-69% relevance
- Document content: 470-481 chars of actual VCC documentation including code examples
- Prompt length: 2700-3000 chars (properly formatted with CONTEXT section)
- **LLM Response:** 236 chars generic "I don't have enough information" message

**Example Failed Query:**
```
Query: "how to create pie chart"
Retrieved: @visa/pie-chart README with <pie-chart> component example
Context included:
  - Component usage: <pie-chart accessibility={...} data={...} valueAccessor="value" ordinalAccessor="label" />
  - Props documentation: valueAccessor, ordinalAccessor, sortOrder, colorPalette
  - Relevance: 69.5%
Response: "I don't have enough information..." ❌
```

#### Root Cause Analysis

The original prompt was **too strict** with these rules:
1. "Answer based ONLY on provided context" (emphasis on ONLY)
2. "If context doesn't contain enough information, say you don't have enough information"
3. "Do not infer or assume information beyond what's explicitly stated"

**Why it failed:**
- OpenAI saw code placeholders like `{data}` and `{...}` and thought the examples were incomplete
- The strict "ONLY" rule made OpenAI overly cautious about using the examples
- Even though examples showed clear usage patterns, OpenAI refused to explain them

#### Solution Implemented

**Changed prompt from restrictive to encouraging:**

**BEFORE (Restrictive):**
```
You are a helpful AI assistant specialized in {domain}. Answer the user's question based ONLY on the provided context.

IMPORTANT RULES:
1. Only use information from the provided context
2. If the context doesn't contain enough information, say "I don't have enough information..."
3. Cite sources when possible
4. Be concise and accurate
5. Do not infer or assume information beyond what's explicitly stated
```

**AFTER (Encouraging):**
```
You are a helpful AI assistant specialized in {domain}. Answer the user's question based on the provided context.

IMPORTANT RULES:
1. Use the information from the provided context to answer the question
2. If you see code examples, usage patterns, or component descriptions in the context, use them to explain how to accomplish the user's goal
3. Code snippets may contain placeholders like {...} or {data} - these are intentional and show where users should insert their own values
4. Cite sources when possible (e.g., "According to the documentation...")
5. Be helpful and provide actionable information when the context contains relevant examples or descriptions
6. Only say you don't have enough information if the context is truly unrelated to the question
```

**Key Changes:**
- ❌ Removed "ONLY" emphasis
- ✅ Added explicit instruction about code placeholders being intentional
- ✅ Changed from "don't have enough information" to "be helpful when context has examples"
- ✅ Reframed rule #6: only refuse if context is "truly unrelated"

#### Implementation Details

**File:** `backend/app/rag/generation.py`  
**Function:** `PromptBuilder._create_prompt_template()`  
**Lines Modified:** 347-368

**Added debug logging:**
```python
logger.info(f"Prompt preview (first 2000 chars):\n{prompt[:2000]}")
logger.info(f"Prompt preview (last 500 chars):\n...{prompt[-500:]}")
```

#### Results & Verification

**Test Query:** "how to create pie chart"

**Before Fix:**
- Response length: 236 chars
- Content: "I don't have enough information..." ❌

**After Fix:**
- Response length: **1115 chars** ✅
- Content: Detailed explanation with code example
- Used retrieved documentation effectively

**Improvement:**  
**4.7x longer responses** with actual helpful information!

#### Benefits

✅ **Improved Answer Quality:**
- LLM now uses code examples from retrieved documents
- Provides actionable information instead of refusing to answer
- Better utilizes the RAG-retrieved context

✅ **Better User Experience:**
- Users get helpful answers to "how to" questions
- Code examples are explained properly
- Reduced false negatives (refusing when information exists)

✅ **Production Readiness:**
- System is more useful for real users
- Confidence threshold (65%) now works correctly
- Retrieved documentation is actually used

#### Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Response Length | 236 chars | 1115 chars | **372% increase** |
| False Negatives | High (refused with 69% relevance) | Low | **Much better** |
| Usability | Poor (always says "not enough info") | Good | **Significantly improved** |

---

## 🔍 ORIGINAL IDENTIFIED ISSUES (Still Relevant)

### Issue 1: Typo Handling in User Queries

**Date Identified:** March 5, 2026  
**Priority:** Medium  
**Category:** Query Robustness

#### Problem Description

The system performs well with correctly spelled queries but fails to retrieve relevant information when user queries contain typos:

**Examples:**

✅ **Works (Correct Spelling):**
- Query: "what is visa chart components?"
- Answer: "Visa Chart Components (VCC) is an accessibility-focused, framework-agnostic set of data experience design systems components for the web. VCC provides a toolset to enable developers to build equal data experiences for everyone. (Source 2: repo_docs)"

❌ **Fails (Typo):**
- Query: "what is visa chart componont?" (typo: "componont" instead of "components")
- Answer: "I don't have enough information to answer that question based on the provided documentation."

#### Root Cause

The vector embedding model creates embeddings based on exact tokens. Typos in user queries:
1. Create different embeddings than the correct terms in the documentation
2. Reduce semantic similarity scores
3. Lead to poor or no retrieval results
4. Cause the LLM to respond with "insufficient information"

#### Impact

- **User Experience:** Frustrating for users who make typos
- **Accessibility:** Affects users with dyslexia or typing difficulties
- **Production Readiness:** Real users make typos regularly

---

### Issue 2: Acronym Expansion Handling

**Date Identified:** March 5, 2026  
**Priority:** Medium  
**Category:** Query Understanding

#### Problem Description

The system handles spelled-out terms well but may struggle when users mix acronyms and full forms:

**Examples to Test:**
- "what is VCC?" vs "what is Visa Chart Components?"
- "VCC accessibility features" vs "Visa Chart Components accessibility"

#### Root Cause

- Embeddings treat "VCC" and "Visa Chart Components" as different semantic concepts
- Documents may use one form more than the other
- Query-document mismatch reduces retrieval effectiveness

#### Impact

- Users need to know which form (acronym or full name) is used in docs
- Reduces system usability for new users unfamiliar with terminology

---

## 💡 Proposed Solutions

### Solution 1: Prompt-Based Query Expansion

**Approach:** Enhance the system prompt to handle query variations

**Implementation:**

```python
system_prompt = """You are a helpful AI assistant. Answer the user's question based ONLY on the provided context.

IMPORTANT RULES:
1. Only use information from the provided context
2. If the context doesn't contain enough information, say "I don't have enough information to answer that"
3. Cite sources when possible (e.g., "According to [source]...")
4. Be concise and accurate
5. Do not infer or assume information beyond what's explicitly stated

QUERY UNDERSTANDING:
- If the query contains typos or spelling variations, try to understand the intent from context
- Consider common acronyms (e.g., "VCC" = "Visa Chart Components")
- Look for semantically similar terms in the context even if exact spelling differs
"""
```

**Pros:**
- Simple to implement (prompt change only)
- No additional infrastructure
- Leverages LLM's language understanding

**Cons:**
- Relies on LLM's ability to correct typos
- Doesn't help with initial retrieval (typo still affects vector search)
- Limited effectiveness if context doesn't contain the right documents

**Estimated Effort:** 15 minutes (prompt update + testing)

---

### Solution 2: Query Pre-processing with Spell Check

**Approach:** Add a query pre-processing step before retrieval

**Implementation:**

```python
from spellchecker import SpellChecker

def preprocess_query(query: str) -> str:
    """
    Pre-process query to correct common typos
    """
    spell = SpellChecker()
    words = query.split()
    corrected_words = []
    
    for word in words:
        # Get the most likely correction
        correction = spell.correction(word)
        corrected_words.append(correction if correction else word)
    
    return ' '.join(corrected_words)

# In retrieval pipeline:
corrected_query = preprocess_query(user_query)
results = retriever.retrieve(corrected_query, k=5)
```

**Pros:**
- Fixes typos before retrieval (improves vector search)
- User-transparent (happens automatically)
- Improves overall system robustness

**Cons:**
- Adds latency (~50-100ms per query)
- May incorrectly "fix" technical terms or proper nouns
- Requires additional dependency (`pyspellchecker`)
- Domain-specific terms need custom dictionaries

**Estimated Effort:** 1-2 hours (implementation + testing + optimization)

---

### Solution 3: Fuzzy Matching in Retrieval

**Approach:** Implement hybrid search with BM25 + fuzzy matching

**Implementation:**

See: [`docs/archive/HYBRID-SEARCH-PLAN.md`](./archive/HYBRID-SEARCH-PLAN.md)

Add fuzzy matching to the BM25 component:

```python
from fuzzywuzzy import fuzz

def fuzzy_bm25_search(query: str, documents: List[str], threshold: int = 80):
    """
    BM25 search with fuzzy matching support
    """
    # Standard BM25
    bm25_scores = bm25.get_scores(query.split())
    
    # Add fuzzy matching for low-scoring queries
    if max(bm25_scores) < 0.5:
        # Try fuzzy matching
        for doc in documents:
            fuzzy_score = fuzz.token_set_ratio(query, doc)
            if fuzzy_score >= threshold:
                # Boost this document's score
                ...
```

**Pros:**
- Handles typos at retrieval level
- Works well with BM25 (already planned)
- Can handle multiple types of variations (typos, word order, etc.)

**Cons:**
- Higher computational cost
- Complex to tune (fuzzy threshold, score weighting)
- May return false positives

**Estimated Effort:** 2-3 hours (on top of hybrid search implementation)

---

### Solution 4: Query Rewriting with LLM

**Approach:** Use a lightweight LLM to rewrite the query before retrieval

**Implementation:**

```python
def rewrite_query(original_query: str) -> str:
    """
    Use LLM to rewrite query, fixing typos and expanding acronyms
    """
    rewrite_prompt = f"""Fix any typos and expand acronyms in this query. 
Output only the corrected query, nothing else.

Known acronyms:
- VCC = Visa Chart Components

Query: {original_query}
Corrected query:"""
    
    # Use fast, cheap LLM (e.g., GPT-3.5-turbo or local model)
    corrected_query = llm.generate(rewrite_prompt)
    return corrected_query.strip()

# In pipeline:
rewritten_query = rewrite_query(user_query)
results = retriever.retrieve(rewritten_query, k=5)
```

**Pros:**
- Handles typos AND acronyms
- Can handle complex query reformulations
- Leverages LLM's language understanding

**Cons:**
- Adds significant latency (LLM call)
- Requires API costs (if using OpenAI) or local model overhead
- May change user intent incorrectly
- Needs validation step

**Estimated Effort:** 3-4 hours (implementation + testing + validation)

---

## 📊 Recommendation

### Immediate Action (Hours 0-1): Solution 1 - Prompt Enhancement
- **Why:** No code changes, instant deployment, low risk
- **Implementation:** Update system prompt with typo-awareness instructions
- **Expected Impact:** 10-20% improvement in typo tolerance (LLM-dependent)

### Future Enhancement (Post-MVP): Solution 2 + Solution 3
- **Why:** Best balance of accuracy and performance
- **Implementation:** 
  1. Add spell check pre-processing (1-2 hours)
  2. Integrate with hybrid search when implemented (already planned)
- **Expected Impact:** 60-80% improvement in typo tolerance

### Not Recommended: Solution 4
- **Why:** High cost, high latency, diminishing returns
- **When to Reconsider:** If users frequently use complex queries with multiple issues

---

## 🧪 Testing Strategy

### Test Queries for Validation

Create a test set with intentional typos and acronyms:

```python
test_queries = [
    # Typo variations
    ("what is visa chart componont?", "components"),
    ("tell me about accesibility features", "accessibility"),
    ("how to instal VCC", "install"),
    
    # Acronym variations  
    ("what is VCC?", "Visa Chart Components"),
    ("VCC setup guide", "Visa Chart Components setup"),
    
    # Combined issues
    ("VCC accesibility fetures", "accessibility features"),
]
```

### Success Metrics

For each solution, measure:
1. **Retrieval Success Rate:** % of queries that retrieve relevant documents
2. **Answer Quality:** RAGAS faithfulness and answer relevancy scores
3. **Latency Impact:** Additional ms per query
4. **False Positive Rate:** % of incorrect "corrections"

### Acceptance Criteria

- Typo tolerance: ≥70% of single-typo queries should retrieve correct documents
- Latency: <100ms additional overhead
- False positives: <5% incorrect corrections

---

## 📝 Implementation Plan

### Phase 1: Quick Win (15 minutes)
- [ ] Update system prompt (Solution 1)
- [ ] Test with typo examples
- [ ] Document results

### Phase 2: Robust Solution (2-3 hours) - Post-MVP
- [ ] Implement spell check pre-processing (Solution 2)
- [ ] Create custom dictionary for technical terms
- [ ] Add acronym expansion mapping
- [ ] Integrate with hybrid search (Solution 3)
- [ ] Create comprehensive test suite
- [ ] Measure RAGAS metrics improvement

### Phase 3: Monitoring (Ongoing)
- [ ] Log typo corrections for analysis
- [ ] Track user query patterns
- [ ] Update custom dictionary based on user queries
- [ ] A/B test different approaches

---

## 📚 Related Documents

- **Hybrid Search Plan:** [`docs/archive/HYBRID-SEARCH-PLAN.md`](./archive/HYBRID-SEARCH-PLAN.md) - Fuzzy matching mentioned
- **Current System Prompt:** [`backend/app/rag/generation.py`](../backend/app/rag/generation.py) - Lines 318-335
- **Future Improvements:** [`docs/DELIVERABLES.md`](./DELIVERABLES.md) - Lines 189-195 (planned document)
- **Prompt Engineering History:** [`docs/progress-tracking.md`](./progress-tracking.md) - Lines 1008, 1063, 1088

---

## 🎓 Key Takeaways

### What We Learned

1. **Vector embeddings are spelling-sensitive** - Exact token matching means typos significantly impact retrieval
2. **Real users make typos** - Production systems need robustness to input variations
3. **Multiple solutions exist** - From simple prompt changes to complex query rewriting
4. **Trade-offs matter** - Balance accuracy, latency, and implementation complexity

### Production Considerations

1. **User Feedback:** Consider showing "Did you mean...?" suggestions
2. **Monitoring:** Track typo patterns to improve dictionary
3. **Graceful Degradation:** Always show best-effort results even with typos
4. **Documentation:** Educate users on query best practices

---

## 🔄 Status

**Current State:**
- ✅ Issue identified and documented
- ✅ Multiple solutions proposed with trade-offs
- ✅ Testing strategy defined
- ⏳ Implementation pending (prioritized for post-MVP)

**Next Steps:**
1. Implement Solution 1 (prompt update) - 15 minutes
2. Test with typo examples
3. Schedule Solution 2+3 for post-MVP enhancement

**Last Updated:** March 5, 2026
