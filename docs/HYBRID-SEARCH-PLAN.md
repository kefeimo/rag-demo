# Hybrid Search Implementation Plan

**Goal:** Improve retrieval relevance for exact term matching (e.g., API names, interface names)  
**Priority:** HIGH  
**Impact:** Expected +10-15% Answer Relevancy, +20% Entity Recall  
**Date:** March 5, 2026  
**Status:** Design complete, ready for implementation

---

## 🎯 Problem Statement

### Current Issue
- **Semantic-only search** prioritizes meaning similarity over exact matches
- Query "What is IDataTableProps?" retrieves:
  - ❌ `IDataLabelType` (distance: 0.60)
  - ❌ `IAccessibilityType` (distance: 0.63)
  - ✅ `IDataTableProps` NOT in top 5 (should be #1)

### Root Cause
- Embedding model (`all-MiniLM-L6-v2`) treats all "I*Type" interfaces as similar
- No boost for exact term matches
- API names, function names, interface names need keyword matching

### Impact on Metrics
- Answer Relevancy: 0.656 (below 0.75 target)
- Context Entity Recall: 0.333 (below 0.50 target)
- Query 9 (IDataTableProps): Complete failure (0.0 relevancy)

---

## ✅ Solution: Hybrid Search (Semantic + Keyword)

### Architecture Overview

```
User Query: "What is IDataTableProps?"
      |
      ├─────────────┬─────────────┐
      |             |             |
  Semantic      BM25         Metadata
  Search      Keyword        Filtering
  (ChromaDB)   Search      (doc_type=api)
      |             |             |
  Results (5)   Results (5)   Boost Factor
      |             |             |
      └─────────────┴─────────────┘
                    |
            Weighted Fusion
         (0.6 semantic + 0.4 BM25)
                    |
              Reranked Results
                    |
            Top-K to LLM (5)
```

### Key Components

1. **Semantic Search** (existing): Best for conceptual queries
2. **BM25 Keyword Search** (new): Best for exact term matching
3. **Score Fusion** (new): Combine scores intelligently
4. **Metadata Boosting** (new): Prioritize relevant doc_types

---

## 🔧 Implementation Options

### Option 1: BM25 with rank_bm25 Library (RECOMMENDED)

**Pros:**
- Pure Python, easy to integrate
- Fast for <10K documents
- Well-tested library
- No external dependencies

**Cons:**
- Requires separate BM25 index (not in ChromaDB)
- Extra memory overhead
- Need to keep BM25 index in sync with ChromaDB

**Implementation:**

```python
# backend/app/rag/hybrid_retrieval.py
from rank_bm25 import BM25Okapi
from typing import List, Dict, Any
import numpy as np

class HybridRetriever:
    def __init__(self, collection_name: str = "vcc_docs"):
        # Semantic search (existing)
        self.semantic_retriever = Retriever(collection_name)
        
        # BM25 keyword search (new)
        self.bm25_index = None
        self.documents = []
        self.document_ids = []
        self._build_bm25_index()
    
    def _build_bm25_index(self):
        """Build BM25 index from ChromaDB documents"""
        # Get all documents from ChromaDB
        all_docs = self.semantic_retriever.collection.get(
            include=['documents', 'metadatas']
        )
        
        # Tokenize documents for BM25
        self.documents = all_docs['documents']
        self.document_ids = all_docs['ids']
        
        # Create BM25 index
        tokenized_docs = [doc.lower().split() for doc in self.documents]
        self.bm25_index = BM25Okapi(tokenized_docs)
        
        print(f"✓ BM25 index built: {len(self.documents)} documents")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        semantic_weight: float = 0.6,
        bm25_weight: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic and keyword matching
        
        Args:
            query: Search query
            top_k: Number of results to return
            semantic_weight: Weight for semantic search scores (0-1)
            bm25_weight: Weight for BM25 scores (0-1)
        
        Returns:
            List of results with combined scores
        """
        # 1. Semantic search
        semantic_results = self.semantic_retriever.retrieve(
            query=query,
            top_k=top_k * 2  # Get more for fusion
        )
        
        # 2. BM25 keyword search
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25_index.get_scores(tokenized_query)
        
        # Get top BM25 results
        bm25_top_indices = np.argsort(bm25_scores)[::-1][:top_k * 2]
        
        # 3. Score fusion
        combined_scores = {}
        
        # Add semantic scores (normalized by max distance)
        max_semantic_dist = max([r['distance'] for r in semantic_results], default=1.0)
        for result in semantic_results:
            doc_id = result['id']
            # Convert distance to similarity score (lower distance = higher score)
            similarity = 1.0 - (result['distance'] / max_semantic_dist)
            combined_scores[doc_id] = semantic_weight * similarity
        
        # Add BM25 scores (normalized)
        max_bm25_score = max(bm25_scores) if len(bm25_scores) > 0 else 1.0
        for idx in bm25_top_indices:
            doc_id = self.document_ids[idx]
            bm25_normalized = bm25_scores[idx] / max_bm25_score
            
            if doc_id in combined_scores:
                combined_scores[doc_id] += bm25_weight * bm25_normalized
            else:
                combined_scores[doc_id] = bm25_weight * bm25_normalized
        
        # 4. Sort by combined score and return top-k
        sorted_results = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        # 5. Fetch full documents from ChromaDB
        final_results = []
        for doc_id, score in sorted_results:
            doc_data = self.semantic_retriever.collection.get(
                ids=[doc_id],
                include=['documents', 'metadatas']
            )
            
            if doc_data['documents']:
                final_results.append({
                    'id': doc_id,
                    'document': doc_data['documents'][0],
                    'metadata': doc_data['metadatas'][0],
                    'score': score
                })
        
        return final_results
```

### Option 2: Elasticsearch Integration

**Pros:**
- Industry-standard search engine
- Built-in BM25 + semantic search
- Scalable to millions of documents
- Advanced features (fuzzy matching, phrase search)

**Cons:**
- External dependency (Docker container)
- More complex setup
- Overkill for <10K documents
- Higher resource usage

### Option 3: ChromaDB Native (if supported)

**Pros:**
- No additional dependencies
- Integrated with existing system
- Simple to use

**Cons:**
- ChromaDB v0.4+ may not have BM25 built-in
- Need to verify feature availability

---

## 📝 Implementation Steps (Option 1)

### Phase 1: Add BM25 Support (1 hour)

#### Step 1: Install Dependencies
```bash
cd backend
source venv/bin/activate
pip install rank-bm25
pip freeze > requirements.txt
```

#### Step 2: Create Hybrid Retriever
```bash
# Create new file
touch app/rag/hybrid_retrieval.py
```

#### Step 3: Implement Hybrid Retriever
(See Option 1 implementation above)

#### Step 4: Update Query Endpoint
```python
# backend/app/api/routes.py
from app.rag.hybrid_retrieval import HybridRetriever

# Global instance (cache BM25 index)
hybrid_retriever = HybridRetriever()

@router.post("/query")
async def query_documents(request: QueryRequest):
    """Query RAG system with hybrid search"""
    
    # Use hybrid search instead of pure semantic
    results = hybrid_retriever.search(
        query=request.query,
        top_k=request.top_k,
        semantic_weight=0.6,  # 60% semantic
        bm25_weight=0.4       # 40% keyword
    )
    
    # ... rest of logic (LLM generation, etc.)
```

### Phase 2: Add Metadata Boosting (30 min)

```python
# backend/app/rag/hybrid_retrieval.py

def _apply_metadata_boost(
    self,
    query: str,
    results: List[Dict],
    boost_config: Dict[str, float] = None
) -> List[Dict]:
    """
    Boost scores based on metadata matching
    
    Example boost_config:
    {
        'doc_type': {
            'api': 1.5,      # Boost API docs by 50%
            'readme': 1.0,   # No boost for READMEs
            'issue_qa': 1.2  # Slight boost for issues
        }
    }
    """
    if boost_config is None:
        # Default: Boost API docs for queries containing interface/function/class keywords
        api_keywords = ['interface', 'function', 'class', 'props', 'api', 'type']
        has_api_keyword = any(kw in query.lower() for kw in api_keywords)
        
        if has_api_keyword:
            boost_config = {'doc_type': {'api': 1.5}}
        else:
            boost_config = {}
    
    for result in results:
        metadata = result.get('metadata', {})
        
        # Apply boosts
        for meta_key, boost_values in boost_config.items():
            meta_value = metadata.get(meta_key)
            if meta_value in boost_values:
                result['score'] *= boost_values[meta_value]
    
    # Re-sort after boosting
    results.sort(key=lambda x: x['score'], reverse=True)
    return results
```

### Phase 3: Add Query Classification (30 min)

```python
# backend/app/rag/query_classifier.py

from typing import Literal

QueryType = Literal['api', 'how_to', 'troubleshooting', 'general']

def classify_query(query: str) -> QueryType:
    """
    Classify query type for optimized retrieval
    
    - API: Looking for interface/function/class definitions
    - How-to: Looking for usage examples, guides
    - Troubleshooting: Looking for issue solutions
    - General: General questions about concepts
    """
    query_lower = query.lower()
    
    # API keywords
    api_keywords = [
        'interface', 'function', 'class', 'props', 'api', 'type',
        'what is', 'definition', 'idatatable', 'iaccessibility'
    ]
    
    # How-to keywords
    howto_keywords = [
        'how', 'create', 'use', 'implement', 'setup', 'configure',
        'example', 'tutorial', 'guide'
    ]
    
    # Troubleshooting keywords
    trouble_keywords = [
        'error', 'issue', 'problem', 'fix', 'not working', 'broken',
        'bug', 'fail', 'crash'
    ]
    
    # Count matches
    api_score = sum(1 for kw in api_keywords if kw in query_lower)
    howto_score = sum(1 for kw in howto_keywords if kw in query_lower)
    trouble_score = sum(1 for kw in trouble_keywords if kw in query_lower)
    
    if api_score > max(howto_score, trouble_score):
        return 'api'
    elif howto_score > trouble_score:
        return 'how_to'
    elif trouble_score > 0:
        return 'troubleshooting'
    else:
        return 'general'


# Update HybridRetriever.search()
def search(self, query: str, top_k: int = 5):
    # Classify query
    query_type = classify_query(query)
    
    # Adjust weights based on query type
    if query_type == 'api':
        semantic_weight = 0.4   # Less semantic
        bm25_weight = 0.6       # More keyword (exact matches)
        boost_config = {'doc_type': {'api': 1.5}}
    elif query_type == 'how_to':
        semantic_weight = 0.7   # More semantic
        bm25_weight = 0.3       # Less keyword
        boost_config = {'doc_type': {'readme': 1.3, 'documentation': 1.2}}
    elif query_type == 'troubleshooting':
        semantic_weight = 0.5
        bm25_weight = 0.5
        boost_config = {'doc_type': {'issue_qa': 1.5}}
    else:  # general
        semantic_weight = 0.6
        bm25_weight = 0.4
        boost_config = {}
    
    # ... rest of search logic
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
# backend/tests/test_hybrid_retrieval.py

def test_hybrid_search_api_query():
    """Test that API queries return correct interfaces"""
    retriever = HybridRetriever('vcc_docs')
    
    # Query that failed in evaluation
    results = retriever.search(
        query="What is IDataTableProps and how do I use it?",
        top_k=5
    )
    
    # Assert IDataTableProps is in top 3
    api_names = [r['metadata'].get('api_name') for r in results[:3]]
    assert 'IDataTableProps' in api_names, f"IDataTableProps not in top 3: {api_names}"
    
    # Assert it's #1 result
    assert results[0]['metadata'].get('api_name') == 'IDataTableProps'


def test_semantic_weight_adjustment():
    """Test that semantic weight affects ranking"""
    retriever = HybridRetriever('vcc_docs')
    
    # Pure semantic (should fail)
    semantic_only = retriever.search(
        query="IDataTableProps",
        semantic_weight=1.0,
        bm25_weight=0.0
    )
    
    # Pure BM25 (should succeed)
    bm25_only = retriever.search(
        query="IDataTableProps",
        semantic_weight=0.0,
        bm25_weight=1.0
    )
    
    # Hybrid (should succeed)
    hybrid = retriever.search(
        query="IDataTableProps",
        semantic_weight=0.4,
        bm25_weight=0.6
    )
    
    # BM25 and hybrid should both have IDataTableProps at #1
    assert bm25_only[0]['metadata'].get('api_name') == 'IDataTableProps'
    assert hybrid[0]['metadata'].get('api_name') == 'IDataTableProps'
```

### Integration Tests

```python
def test_vcc_evaluation_with_hybrid_search():
    """Re-run Query 9 with hybrid search"""
    from backend.evaluation.run_ragas_stage1_query import run_rag_query
    
    # Enable hybrid search in backend
    # ... (configure endpoint to use HybridRetriever)
    
    # Run Query 9
    result = run_rag_query("What is IDataTableProps and how do I use it?")
    
    # Should now retrieve correct context
    contexts = result['contexts']
    assert any('IDataTableProps' in ctx for ctx in contexts)
    
    # Answer relevancy should improve
    # (requires full RAGAS evaluation)
```

### Performance Benchmarks

```python
def benchmark_hybrid_vs_semantic():
    """Compare performance: hybrid vs semantic-only"""
    test_queries = [
        "What is IDataTableProps?",
        "How do I create a bar chart?",
        "What accessibility features are available?",
        # ... more queries
    ]
    
    semantic_retriever = Retriever('vcc_docs')
    hybrid_retriever = HybridRetriever('vcc_docs')
    
    import time
    
    # Semantic-only timing
    start = time.time()
    for query in test_queries:
        semantic_retriever.retrieve(query)
    semantic_time = time.time() - start
    
    # Hybrid timing
    start = time.time()
    for query in test_queries:
        hybrid_retriever.search(query)
    hybrid_time = time.time() - start
    
    print(f"Semantic-only: {semantic_time:.2f}s")
    print(f"Hybrid: {hybrid_time:.2f}s")
    print(f"Overhead: {(hybrid_time - semantic_time) / semantic_time * 100:.1f}%")
```

---

## 📊 Expected Improvements

### Before (Semantic-only)
| Metric | Score | Status |
|--------|-------|--------|
| Answer Relevancy | 0.656 | ⚠️ Below target (0.75) |
| Context Entity Recall | 0.333 | ❌ Below target (0.50) |
| Query 9 (IDataTableProps) | 0.0 | ❌ Complete failure |

### After (Hybrid Search)
| Metric | Expected Score | Expected Status |
|--------|----------------|-----------------|
| Answer Relevancy | **0.75-0.80** | ✅ Above target |
| Context Entity Recall | **0.45-0.55** | ✅ At/above target |
| Query 9 (IDataTableProps) | **0.85+** | ✅ Excellent |

### Confidence Intervals
- **Conservative**: +10% Answer Relevancy, +15% Entity Recall
- **Expected**: +15% Answer Relevancy, +20% Entity Recall
- **Optimistic**: +20% Answer Relevancy, +30% Entity Recall

---

## 🚀 Rollout Plan

### Phase 1: Development (Day 1-2)
- [ ] Install rank_bm25 library
- [ ] Implement HybridRetriever class
- [ ] Add metadata boosting logic
- [ ] Add query classification
- [ ] Write unit tests

### Phase 2: Testing (Day 2-3)
- [ ] Test with Query 9 (IDataTableProps)
- [ ] Test with all 10 VCC baseline queries
- [ ] Performance benchmarking
- [ ] Compare results with semantic-only

### Phase 3: Evaluation (Day 3-4)
- [ ] Re-run full RAGAS evaluation with hybrid search
- [ ] Compare metrics: hybrid vs semantic-only
- [ ] Document improvements
- [ ] Create comparison report

### Phase 4: Production (Day 4-5)
- [ ] Code review
- [ ] Update API documentation
- [ ] Deploy to staging
- [ ] User acceptance testing
- [ ] Production deployment
- [ ] Monitor performance

---

## 🎯 Success Criteria

### Must Have
- ✅ Query "IDataTableProps" returns IDataTableProps in top 3
- ✅ Answer Relevancy ≥ 0.75
- ✅ No regression in Context Precision (maintain 0.98+)
- ✅ Query latency increase < 20%

### Should Have
- ✅ Context Entity Recall ≥ 0.50
- ✅ All API queries improved
- ✅ Query classification working
- ✅ Metadata boosting effective

### Nice to Have
- ✅ Configurable weights via API
- ✅ A/B testing framework
- ✅ Query analytics dashboard
- ✅ Auto-tuning of weights

---

**Next Steps:**
1. Get approval for implementation
2. Start with Phase 1 (development)
3. Test thoroughly with VCC evaluation queries
4. Deploy and measure improvements

**Estimated Time:** 2-3 hours (Phases 1-2)  
**Expected Impact:** High (fixes critical retrieval issue)
