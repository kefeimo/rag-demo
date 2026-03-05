# Collection Naming Fix - Implementation Plan

**Issue:** ChromaDB collection named `fastapi_docs` contains VCC documentation  
**Priority:** CRITICAL  
**Risk:** High (future re-ingestion could overwrite VCC with FastAPI docs)  
**Date:** March 5, 2026  
**Status:** Ready to implement

---

## 🚨 Problem Statement

### Current State
- Collection name: `fastapi_docs`
- Actual content: 2696 chunks from `visa/visa-chart-components`
- Configuration: `backend/.env` has `CHROMA_COLLECTION_NAME=fastapi_docs`

### Impact
1. **Confusing naming** prevents proper documentation organization
2. **Risk of data loss** if FastAPI docs are re-ingested
3. **Cannot isolate** FastAPI vs VCC evaluations properly
4. **Misleading for future developers**

---

## ✅ Solution Options

### Option A: Quick Rename (RECOMMENDED for immediate fix)
**Time:** 5 minutes  
**Risk:** Low  
**Rollback:** Easy

**Steps:**
1. Update `backend/.env`: `CHROMA_COLLECTION_NAME=vcc_docs`
2. No code changes needed (app will create new collection on next start)
3. Delete old `fastapi_docs` collection (or keep as backup)

**Pros:**
- Immediate fix
- No code changes
- Preserves existing data

**Cons:**
- Requires re-ingestion or manual collection rename
- Doesn't solve multi-collection support

### Option B: Separate Collections Architecture (RECOMMENDED for production)
**Time:** 1-2 hours  
**Risk:** Medium  
**Rollback:** Requires code revert

**Implementation:**
1. Create separate collections: `fastapi_docs`, `vcc_docs`
2. Add `collection_name` parameter to `/query` endpoint
3. Update frontend to support collection selection
4. Implement collection management API

**Pros:**
- True isolation between doc sets
- Scalable for future doc sources
- Better organization

**Cons:**
- Requires API changes
- Frontend updates needed
- More complex architecture

---

## 🔧 Implementation: Option A (Quick Fix)

### Step 1: Rename Collection in ChromaDB

```python
# backend/rename_collection.py
"""
Quick script to rename fastapi_docs → vcc_docs in ChromaDB
"""
import chromadb

client = chromadb.PersistentClient(path='./data/chroma_db')

# Option 1: Get all data and re-insert (safe but slow)
old_coll = client.get_collection('fastapi_docs')
data = old_coll.get(include=['documents', 'metadatas', 'embeddings'])

# Create new collection
new_coll = client.get_or_create_collection(
    name='vcc_docs',
    metadata={"description": "Visa Chart Components documentation"}
)

# Insert all data
if data['ids']:
    new_coll.add(
        ids=data['ids'],
        documents=data['documents'],
        metadatas=data['metadatas'],
        embeddings=data['embeddings']
    )
    print(f"✓ Migrated {len(data['ids'])} documents to vcc_docs")

# Optional: Delete old collection
# client.delete_collection('fastapi_docs')
# print("✓ Deleted old fastapi_docs collection")
```

### Step 2: Update Environment Configuration

```bash
# backend/.env
# BEFORE:
CHROMA_COLLECTION_NAME=fastapi_docs

# AFTER:
CHROMA_COLLECTION_NAME=vcc_docs
```

### Step 3: Verify Changes

```bash
# Test that backend can access new collection
cd backend
source venv/bin/activate
python -c "
from app.config import settings
import chromadb

client = chromadb.PersistentClient(path='./data/chroma_db')
coll = client.get_collection(settings.chroma_collection_name)
print(f'Collection: {coll.name}')
print(f'Document count: {coll.count()}')
assert coll.count() == 2696, 'Count mismatch!'
print('✓ Collection rename successful!')
"
```

### Step 4: Update Documentation

```markdown
# Update all references:
- README.md: Change fastapi_docs → vcc_docs
- progress-tracking.md: Note collection rename
- VCC-EVALUATION-STRATEGY.md: Update collection name
```

---

## 🔧 Implementation: Option B (Production Architecture)

### Phase 1: Backend API Changes

#### 1.1 Update Retrieval Service

```python
# backend/app/rag/retrieval.py
class Retriever:
    def __init__(self, collection_name: str = None):
        """
        Initialize retriever with optional collection name.
        If None, uses settings.chroma_collection_name
        """
        self.collection_name = collection_name or settings.chroma_collection_name
        # ... rest of init
```

#### 1.2 Update Query Endpoint

```python
# backend/app/api/routes.py
from typing import Optional

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    collection_name: Optional[str] = None  # NEW

@router.post("/query")
async def query_documents(request: QueryRequest):
    """Query RAG system with optional collection selection"""
    
    # Use specified collection or default
    collection = request.collection_name or settings.chroma_collection_name
    
    # Create retriever for specific collection
    retriever = Retriever(collection_name=collection)
    
    # ... rest of logic
```

#### 1.3 Add Collection Management Endpoint

```python
# backend/app/api/routes.py
@router.get("/collections")
async def list_collections():
    """List all available document collections"""
    client = chromadb.PersistentClient(path=settings.chroma_persist_directory)
    collections = client.list_collections()
    
    return {
        "collections": [
            {
                "name": coll.name,
                "count": coll.count(),
                "metadata": coll.metadata
            }
            for coll in collections
        ],
        "default": settings.chroma_collection_name
    }
```

### Phase 2: Frontend Changes

#### 2.1 Add Collection Selector

```typescript
// frontend/src/components/DocumentSelector.tsx
export function DocumentSelector() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selected, setSelected] = useState<string>('vcc_docs');

  useEffect(() => {
    // Fetch available collections
    fetch('/api/v1/collections')
      .then(res => res.json())
      .then(data => {
        setCollections(data.collections);
        setSelected(data.default);
      });
  }, []);

  return (
    <select 
      value={selected} 
      onChange={(e) => setSelected(e.target.value)}
      className="...">
      {collections.map(coll => (
        <option key={coll.name} value={coll.name}>
          {coll.name} ({coll.count} docs)
        </option>
      ))}
    </select>
  );
}
```

#### 2.2 Update Query Logic

```typescript
// frontend/src/App.tsx
const handleQuery = async (query: string) => {
  const response = await fetch('/api/v1/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      top_k: 5,
      collection_name: selectedCollection  // NEW
    })
  });
  // ... handle response
};
```

### Phase 3: Data Migration

```bash
# Create separate collections
cd backend
source venv/bin/activate

# Rename current VCC collection
python rename_collection.py

# Re-ingest FastAPI docs into fastapi_docs collection
python ingest_fastapi_docs.py  # Original ingestion script

# Verify both collections exist
python -c "
import chromadb
client = chromadb.PersistentClient(path='./data/chroma_db')
for coll in client.list_collections():
    print(f'{coll.name}: {coll.count()} documents')
"
```

---

## 📋 Testing Checklist

### Quick Fix (Option A)
- [ ] Run rename script successfully
- [ ] Update .env file
- [ ] Verify collection accessible via API
- [ ] Test frontend query still works
- [ ] Verify document count (2696)
- [ ] Update documentation references

### Production Architecture (Option B)
- [ ] Collection management endpoint working
- [ ] Frontend selector displays collections
- [ ] Query with collection_name parameter works
- [ ] Default collection used when not specified
- [ ] Both fastapi_docs and vcc_docs accessible
- [ ] Frontend persists collection selection
- [ ] API documentation updated
- [ ] Integration tests pass

---

## 🚀 Rollout Plan

### Immediate (Today)
1. **Quick fix** (Option A): Rename collection to `vcc_docs`
2. Update environment configuration
3. Verify system functionality
4. Update documentation

### Near-term (This Week)
1. Plan Option B architecture details
2. Review API design with team
3. Create frontend mockups
4. Estimate effort for full implementation

### Future (Next Sprint)
1. Implement Option B (separate collections)
2. Add collection management UI
3. Re-ingest FastAPI docs
4. Deploy to staging
5. User acceptance testing
6. Production deployment

---

## 📊 Success Metrics

### Quick Fix
- ✅ Collection correctly named `vcc_docs`
- ✅ No data loss (2696 documents intact)
- ✅ API queries working normally
- ✅ Documentation updated

### Production Architecture
- ✅ Both collections accessible
- ✅ Frontend allows collection switching
- ✅ Query performance unchanged
- ✅ User can select doc source
- ✅ Isolation between doc sets verified

---

## 🔄 Rollback Procedure

### If Quick Fix Fails
```bash
# Restore old collection name in .env
CHROMA_COLLECTION_NAME=fastapi_docs

# Restart backend
# Data is still in fastapi_docs collection, no loss
```

### If Production Architecture Fails
```bash
# Revert code changes
git revert <commit-hash>

# Set default collection to vcc_docs
CHROMA_COLLECTION_NAME=vcc_docs

# Restart services
```

---

**Recommendation:** Start with Option A (quick fix) today, plan Option B for next sprint

**Estimated Time:**
- Option A: 30 minutes (including testing)
- Option B: 2-3 hours (full implementation)

**Next Steps:**
1. Get approval for Option A implementation
2. Run rename script
3. Test and verify
4. Plan Option B for future enhancement
