# UI Query Cache Implementation

## Overview

The frontend implements an in-memory query cache to prevent redundant API calls when users re-query the same questions, particularly when clicking on query history items.

**Problem Solved:** Clicking historical queries was triggering new API calls (1-2 seconds latency + LLM cost) even though the answer was already known.

**Solution:** Client-side cache that returns instant results for repeated queries.

---

## Architecture

### Cache Structure

```javascript
// State in App.jsx
const [queryCache, setQueryCache] = useState({});

// Cache format:
{
  "what is fastapi": {                    // Normalized query (lowercase, trimmed)
    query: "What is FastAPI?",            // Original query
    answer: "FastAPI is...",              // LLM-generated answer
    confidence: 0.85,                 // Retrieval confidence
    sources: [...],                   // Source documents
    response_time: 1.23,              // Original response time
    provider: "openai",               // LLM provider used
    // ... full API response
  },
  "how to create a bar chart": { ... }
}
```

### Cache Key Normalization

```javascript
const cacheKey = `${query.trim().toLowerCase()}`;
```

**Normalization Strategy:**
- Convert to lowercase (case-insensitive matching)
- Trim whitespace (ignore leading/trailing spaces)
- No stemming or lemmatization (exact match after normalization)

**Examples:**
```
"What is FastAPI?"         → "what is fastapi?"
"  What is FastAPI?  "     → "what is fastapi?" (same key)
"what is FastAPI"          → "what is fastapi"  (same key)
"What is FastAPI Company Chart?"  → "what is FastAPI chart?" (different key)
```

---

## Implementation

### Cache Check Flow

```
User clicks query
      ↓
handleQuery(query)
      ↓
Normalize query → cacheKey
      ↓
   Cache Hit? ────YES──→ Return cached result (instant)
      │                  Show "Cached" badge
      NO                 Log: "✅ Cache HIT"
      ↓
Make API call
      ↓
Store in cache
      ↓
Return result
Log: "❌ Cache MISS"
```

### Code Implementation

**Location:** `frontend/src/App.jsx`

```javascript
const handleQuery = async (query) => {
  setIsLoading(true);
  setError(null);
  setResponse(null);

  try {
    // Check cache first
    const cacheKey = `${query.trim().toLowerCase()}`;
    if (queryCache[cacheKey]) {
      console.log('✅ Cache HIT:', query);
      setResponse(queryCache[cacheKey]);
      setBackendStatus('connected');
      setIsLoading(false);
      return; // Return cached result immediately
    }

    console.log('❌ Cache MISS:', query);
    
    // Make API call
    const data = await queryRAG(query);
    setResponse(data);
    setBackendStatus('connected');
    
    // Cache the result
    setQueryCache(prev => ({
      ...prev,
      [cacheKey]: data
    }));
    
    // Add to history...
  } catch (err) {
    // Error handling...
  } finally {
    setIsLoading(false);
  }
};
```

---

## Visual Indicators

### Cached Badge in Query History

When a query is cached, it displays a purple badge:

```jsx
{isCached && (
  <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 flex items-center gap-1" 
        title="Cached - instant response">
    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
      {/* Database icon */}
    </svg>
    Cached
  </span>
)}
```

**Visual Design:**
- **Color:** Purple (`bg-purple-100`, `text-purple-700`)
- **Icon:** Database/storage icon
- **Tooltip:** "Cached - instant response"
- **Position:** Next to RAG system badge (FastAPI/API)

### Console Logging

```javascript
// Cache hit (green checkmark)
console.log('✅ Cache HIT:', query);

// Cache miss (red X)
console.log('❌ Cache MISS:', query);
```

**Use Cases:**
- Development debugging
- Performance monitoring
- Cache behavior verification

---

## Performance Impact

### Before Cache (Every Query)
```
User clicks history item
      ↓
Network request (50-200ms)
      ↓
Backend processing:
  - Query embedding (100-1000ms)
  - Vector retrieval (50-200ms)
  - LLM generation (1000-2000ms)
      ↓
Total: 1.5-3 seconds
Cost: $0.002 (OpenAI API)
```

### After Cache (Repeated Query)
```
User clicks history item
      ↓
Memory lookup (<1ms)
      ↓
Display result
      ↓
Total: <10ms (instant)
Cost: $0 (no API call)
```

### Performance Metrics

| Metric | First Query | Cached Query | Improvement |
|--------|-------------|--------------|-------------|
| Response Time | 1.5-3s | <10ms | **150-300x faster** |
| API Cost | $0.002 | $0 | **100% savings** |
| Backend Load | Full pipeline | None | **100% reduction** |
| GPU Usage | Embeddings | None | **100% reduction** |
| Network Traffic | ~5KB request/response | None | **100% reduction** |

---

## Cache Characteristics

### Storage Type: In-Memory (React State)

**Advantages:**
- ✅ Instant access (no disk I/O)
- ✅ No external dependencies
- ✅ Simple implementation
- ✅ Automatic React re-renders

**Limitations:**
- ❌ Lost on page refresh
- ❌ Not shared across tabs/windows
- ❌ Limited by browser memory
- ❌ No persistence

### Cache Scope

| Scope | Behavior |
|-------|----------|
| **Per Session** | Cache persists during single browsing session |
| **Per Tab** | Each browser tab has separate cache |
| **User-Specific** | Not shared across users (client-side only) |
| **Query-Specific** | Normalized query text is the key |

### Cache Size

**Current Implementation:** Unlimited

**Considerations:**
- Each cached query: ~2-5KB (JSON response)
- 100 cached queries: ~200-500KB
- Browser memory limit: Typically 100MB+ per tab

**Future:** Could implement LRU (Least Recently Used) eviction:
```javascript
const MAX_CACHE_SIZE = 100; // Keep last 100 queries

if (Object.keys(queryCache).length > MAX_CACHE_SIZE) {
  // Remove oldest entries
}
```

### Cache Invalidation

**Current Strategy:** None

**Cache Lifetime:**
- Persists until page refresh
- Cleared when user closes tab
- Not affected by document ingestion

**Future Considerations:**
1. **Time-based expiration:** Cache for 1 hour
2. **Manual invalidation:** Clear cache button
3. **Selective invalidation:** Clear cache on document update
4. **Version tracking:** Invalidate on backend version change

---

## Use Cases

### 1. Query History Navigation ⭐ Primary Use Case

**Scenario:** User clicks a query from history
```
User asks: "What is FastAPI?"
  → First time: 2s (API call)
  → Adds to history

User clicks history item: "What is FastAPI?"
  → Instant (<10ms, cached)
```

**Benefit:** Immediate response, no waiting

### 2. Exploring Similar Queries

**Scenario:** User refines query
```
"What is FastAPI?" → cached
"what is fastapi"  → cached (same normalized key)
"What is FastAPI?" → cached (exact match)
```

**Benefit:** Variations of same query return instantly

### 3. Comparing Responses

**Scenario:** User switches between RAG systems
```
FastAPI mode: "What is authentication?"
FastAPI mode: "What is FastAPI?"
FastAPI mode: "What is authentication?" ← cached
```

**Note:** Cache is system-agnostic (no ragSystem in key)

### 4. Accidental Re-queries

**Scenario:** User accidentally re-submits
```
User types: "How to create bar chart"
  → Submits (2s response)
User types: "How to create bar chart" again
  → Submits (instant, cached)
```

**Benefit:** Prevents wasteful redundant API calls

---

## Browser Console Usage

### Viewing Cache Hits/Misses

Open browser DevTools console and query:

```javascript
// First query
❌ Cache MISS: What is FastAPI?

// Click history item
✅ Cache HIT: What is FastAPI?
```

### Inspecting Cache State

```javascript
// In browser console (React DevTools)
// Select App component
$r.props.queryCache

// Output:
{
  "what is fastapi": { query: "What is FastAPI?", answer: "...", ... },
  "how to create bar chart": { query: "...", answer: "...", ... }
}
```

### Manual Cache Clearing

```javascript
// Not currently exposed in UI
// Future: Add "Clear Cache" button
```

---

## Future Enhancements

### 1. Persistent Cache (LocalStorage)

**Implementation:**
```javascript
// Save to localStorage
useEffect(() => {
  localStorage.setItem('queryCache', JSON.stringify(queryCache));
}, [queryCache]);

// Load on mount
useEffect(() => {
  const cached = localStorage.getItem('queryCache');
  if (cached) setQueryCache(JSON.parse(cached));
}, []);
```

**Benefits:**
- Survives page refresh
- Faster subsequent visits

**Considerations:**
- 5-10MB storage limit
- Security (don't cache sensitive queries)
- Versioning (invalidate on app update)

### 2. Cache Expiration

**Implementation:**
```javascript
const cacheEntry = {
  data: responseData,
  timestamp: Date.now(),
  ttl: 3600000 // 1 hour in ms
};

// Check expiration
const isExpired = Date.now() - cacheEntry.timestamp > cacheEntry.ttl;
if (isExpired) {
  // Re-fetch
}
```

**Benefits:**
- Ensures fresh data
- Automatic cleanup

### 3. Cache Statistics

**Display:**
```
Cache Statistics:
- Total Entries: 47
- Cache Hits: 123
- Cache Misses: 47
- Hit Rate: 72%
- Estimated Savings: $0.25 (125 API calls)
```

**Implementation:**
```javascript
const [cacheStats, setCacheStats] = useState({
  hits: 0,
  misses: 0,
  totalSavings: 0
});
```

### 4. Fuzzy Matching

**Implementation:**
```javascript
import Fuse from 'fuse.js';

// Find similar cached queries
const fuse = new Fuse(Object.keys(queryCache), { threshold: 0.3 });
const similar = fuse.search(query);
```

**Benefits:**
- Match typos: "What is VC?" → "What is FastAPI?"
- Catch variations: "FastAPI definition" → "What is FastAPI?"

**Considerations:**
- Increased complexity
- May return incorrect matches

### 5. Cache Preloading

**Strategy:** Pre-cache common queries on app load

```javascript
const COMMON_QUERIES = [
  "What is FastAPI?",
  "How to create a bar chart?",
  "What are the props for IDataTableProps?"
];

// Preload on app start
useEffect(() => {
  COMMON_QUERIES.forEach(q => handleQuery(q));
}, []);
```

**Benefits:**
- Instant answers for common questions
- Better first-time experience

---

## Testing

### Manual Testing Procedure

1. **First Query (Cache Miss)**
   ```
   Steps:
   1. Open app: http://localhost:5173
   2. Submit query: "What is FastAPI?"
   3. Wait 1-2 seconds for response
   4. Check console: ❌ Cache MISS
   5. Verify no "Cached" badge in history
   ```

2. **Repeated Query (Cache Hit)**
   ```
   Steps:
   1. Click query from history: "What is FastAPI?"
   2. Response appears instantly (<10ms)
   3. Check console: ✅ Cache HIT
   4. Verify purple "Cached" badge appears
   ```

3. **Case Insensitivity**
   ```
   Steps:
   1. Submit: "What is FastAPI?"
   2. Submit: "what is fastapi"
   3. Submit: "WHAT IS FastAPI?"
   4. All three should be cache hits (same key)
   ```

4. **Cache Persistence in Session**
   ```
   Steps:
   1. Submit 5 different queries
   2. Reload page (Ctrl+R)
   3. Cache is cleared (all queries are misses)
   4. Expected: Cache does not persist across page refresh
   ```

### Automated Testing

```javascript
// frontend/src/__tests__/cache.test.js
describe('Query Cache', () => {
  test('Cache hit returns instant result', async () => {
    const { getByText, getByPlaceholderText } = render(<App />);
    
    // First query
    const input = getByPlaceholderText('Ask a question...');
    fireEvent.change(input, { target: { value: 'What is FastAPI?' } });
    fireEvent.submit(input);
    
    await waitFor(() => {
      expect(getByText(/FastAPI is/)).toBeInTheDocument();
    });
    
    // Second query (cached)
    const startTime = performance.now();
    fireEvent.click(getByText('What is FastAPI?')); // Click history
    const endTime = performance.now();
    
    expect(endTime - startTime).toBeLessThan(100); // <100ms
    expect(getByText('Cached')).toBeInTheDocument();
  });
  
  test('Different queries generate different cache keys', () => {
    const key1 = normalizeQuery('What is FastAPI?');
    const key2 = normalizeQuery('How to use FastAPI?');
    
    expect(key1).not.toEqual(key2);
  });
});
```

---

## Troubleshooting

### Issue: Cache Not Working

**Symptoms:**
- Repeated queries still take 1-2 seconds
- No "✅ Cache HIT" in console
- No "Cached" badge appears

**Diagnosis:**
```javascript
// Check if queryCache state exists
console.log('Cache state:', queryCache);

// Check if cacheKey is being generated correctly
const cacheKey = `${query.trim().toLowerCase()}`;
console.log('Cache key:', cacheKey);
console.log('Key exists?', queryCache[cacheKey] !== undefined);
```

**Solutions:**
1. Check browser console for errors
2. Verify React DevTools shows queryCache state
3. Ensure handleQuery is not being bypassed
4. Check if page was refreshed (clears cache)

### Issue: "Cached" Badge Not Showing

**Symptoms:**
- Cache works (instant response)
- Console shows "✅ Cache HIT"
- But no purple badge in history

**Diagnosis:**
```javascript
// Check if isCached calculation is correct
const cacheKey = `${item.query.trim().toLowerCase()}`;
const isCached = queryCache[cacheKey] !== undefined;
console.log('Is cached?', isCached);
```

**Solutions:**
1. Verify queryCache state is updated
2. Check if query normalization matches
3. Ensure component re-renders when cache updates

### Issue: Memory Leak (Too Many Cached Queries)

**Symptoms:**
- Browser becomes slow after many queries
- Memory usage increases over time

**Diagnosis:**
```javascript
// Check cache size
console.log('Cache size:', Object.keys(queryCache).length);
console.log('Memory estimate:', JSON.stringify(queryCache).length / 1024, 'KB');
```

**Solutions:**
1. Implement cache size limit (LRU eviction)
2. Add manual "Clear Cache" button
3. Implement automatic cleanup on app unmount

---

## Security Considerations

### Current Implementation: Safe

**Why:**
- Client-side only (no server storage)
- No sensitive data cached
- Cache cleared on session end

### Potential Risks (Future)

1. **Sensitive Queries**
   - Risk: Caching queries with sensitive info
   - Mitigation: Implement query sanitization

2. **XSS via Cached Content**
   - Risk: Malicious content in cached responses
   - Mitigation: Sanitize HTML before rendering (already done)

3. **Cache Poisoning**
   - Risk: Attacker manipulates cache
   - Mitigation: Validate cached data structure

4. **LocalStorage Security (If Implemented)**
   - Risk: Sensitive data persisted on disk
   - Mitigation: Encrypt cached data, set expiration

---

## Related Documentation

- [Frontend README](../frontend/README.md) - React app architecture
- [API Documentation](../README.md#api-endpoints) - Backend API specs
- [Performance Optimization](../docs/ARCHITECTURE.md#performance-characteristics) - System performance

---

**Version:** 1.0  
**Last Updated:** 2026-03-06  
**Status:** Implemented and tested ✅  
**Performance Impact:** 150-300x faster for repeated queries
