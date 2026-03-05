# Data Pipeline Scalability & Update Strategy

**Date:** March 5, 2026  
**Context:** VCC documentation in JSON format - scalability analysis

---

## Current Architecture

### Data Flow
```
GitHub Repo (visa-chart-components)
    ↓
Data Pipeline (3 extractors)
    ↓
JSON Files (3 files: repo_docs, code_docs, issue_qa)
    ↓
ingest_visa_docs.py
    ↓
ChromaDB (2696 chunks)
    ↓
RAG System (FastAPI endpoints)
```

### Current State
- ✅ **276 documents** extracted (53 repo + 210 code + 13 issues)
- ✅ **3 JSON files** stored in `data-pipeline/data/raw/`
- ✅ **2696 chunks** in ChromaDB
- ✅ **Full ingestion** takes ~8s (initial) or ~0.01s (if already loaded)

---

## Scalability Analysis

### ✅ Pros: Current JSON Approach

#### 1. **Fast Development & Testing**
- Extract once, ingest many times
- No GitHub API rate limits during testing
- Can modify ingestion logic without re-extraction
- Perfect for prototyping and evaluation

#### 2. **Reproducibility**
- Fixed snapshot of documentation (version control friendly)
- Consistent evaluation results
- Easy to share datasets (commit JSON files)

#### 3. **Offline Capability**
- No internet required for ingestion
- Works in air-gapped environments
- Useful for demos and presentations

#### 4. **Debugging & Inspection**
- Human-readable JSON format
- Easy to inspect with `jq` or text editor
- Can manually curate/fix problematic docs

### ⚠️ Cons: Current JSON Approach

#### 1. **Manual Update Process**
```bash
# When new documentation is released:
cd data-pipeline/extractors/
python run_extraction.py              # Re-extract (5-10 min)
cd ../../backend/
python ingest_visa_docs.py --reingest # Re-ingest (8s)
```
- Requires manual trigger
- No automatic detection of upstream changes
- Re-extracts EVERYTHING (no incremental updates)

#### 2. **Storage Inefficiency**
- JSON files: 1.3MB (not huge, but redundant)
- Git commits: Large diffs for small changes
- ChromaDB: Stores embeddings separately (another copy)

#### 3. **Stale Data Risk**
- Documentation can become outdated
- No visibility into "last updated" timestamps
- Users don't know if data is fresh

#### 4. **No Version Tracking**
- Can't track which git commit/tag was extracted
- Hard to correlate docs with specific releases
- No automatic rollback on bad updates

---

## Production Scalability Solutions

### Option A: **Incremental Updates** (RECOMMENDED for MVP+)

**Add incremental update capability to existing pipeline**

#### Implementation (2-3 hours)
```python
# 1. Add document fingerprinting
def calculate_doc_fingerprint(content: str, metadata: dict) -> str:
    """Generate hash of content + metadata for change detection"""
    data = f"{content}{json.dumps(metadata, sort_keys=True)}"
    return hashlib.sha256(data.encode()).hexdigest()

# 2. Store fingerprints in ChromaDB metadata
chunk_metadata = {
    "source": "visa_repo_docs.json",
    "file_path": "packages/bar-chart/README.md",
    "doc_fingerprint": "abc123...",  # NEW
    "extracted_at": "2026-03-05T12:00:00Z"
}

# 3. Update ingest_visa_docs.py
def ingest_visa_docs_incremental():
    """Only ingest changed documents"""
    
    # Load new JSON files
    new_docs = load_json_documents(...)
    
    # Query existing documents from ChromaDB
    existing_docs = get_existing_documents()
    existing_fingerprints = {doc['file_path']: doc['fingerprint']}
    
    # Detect changes
    changed_docs = []
    new_docs_list = []
    deleted_paths = set(existing_fingerprints.keys())
    
    for doc in new_docs:
        path = doc['metadata']['file_path']
        new_fp = calculate_doc_fingerprint(doc['content'], doc['metadata'])
        
        if path in existing_fingerprints:
            deleted_paths.remove(path)
            if existing_fingerprints[path] != new_fp:
                changed_docs.append(doc)  # Modified
        else:
            new_docs_list.append(doc)  # New
    
    # Update ChromaDB
    # - Delete removed docs
    # - Update changed docs (delete old chunks, add new)
    # - Add new docs
    
    return {
        "new": len(new_docs_list),
        "modified": len(changed_docs),
        "deleted": len(deleted_paths),
        "unchanged": len(new_docs) - len(new_docs_list) - len(changed_docs)
    }
```

#### Benefits
- ✅ Only re-process changed documents
- ✅ Faster updates (seconds instead of minutes)
- ✅ Preserves working data (no full wipe)
- ✅ Backward compatible (can still do full reingest)

#### Tradeoffs
- Requires ChromaDB query support for existing docs
- More complex logic (change detection, partial updates)
- Need to handle edge cases (deleted files, renamed files)

---

### Option B: **Scheduled Automation** (RECOMMENDED for Production)

**Add automated pipeline triggering**

#### Implementation (1-2 hours)
```yaml
# .github/workflows/update-docs.yml
name: Update VCC Documentation

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:  # Manual trigger

jobs:
  update-docs:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Run extraction pipeline
        run: |
          cd data-pipeline/extractors
          python run_extraction.py
      
      - name: Check for changes
        id: changes
        run: |
          git diff --exit-code data-pipeline/data/raw/ || echo "changed=true" >> $GITHUB_OUTPUT
      
      - name: Commit and push if changed
        if: steps.changes.outputs.changed == 'true'
        run: |
          git config user.name "docs-bot"
          git config user.email "bot@example.com"
          git add data-pipeline/data/raw/
          git commit -m "docs: Update VCC documentation [automated]"
          git push
      
      - name: Trigger backend reingest
        if: steps.changes.outputs.changed == 'true'
        run: |
          curl -X POST "https://api.example.com/api/v1/ingest/visa-docs?force_reingest=true" \
            -H "Authorization: Bearer ${{ secrets.API_TOKEN }}"
```

#### Benefits
- ✅ Automatic updates (daily, weekly, on-demand)
- ✅ Git tracks all changes (full audit trail)
- ✅ Zero manual intervention
- ✅ Can notify team on updates (Slack, email)

#### Tradeoffs
- Requires CI/CD setup (GitHub Actions, GitLab CI)
- Need API authentication for reingest trigger
- Still full re-extraction (unless combined with Option A)

---

### Option C: **Live Extraction** (NOT RECOMMENDED for MVP)

**Skip JSON, extract directly from GitHub on ingestion**

#### Implementation
```python
# backend/app/rag/ingestion.py
class GitHubDocumentLoader:
    def load_from_github(self, repo: str, branch: str = "main"):
        """
        Directly clone and extract from GitHub during ingestion
        """
        # Clone repo
        # Run extractors in-memory
        # Return documents without saving JSON
        pass

# backend/app/main.py
@app.post("/api/v1/ingest/visa-docs-live")
async def ingest_visa_docs_live(branch: str = "main"):
    loader = GitHubDocumentLoader()
    docs = loader.load_from_github("visa/visa-chart-components", branch)
    # ... ingest into ChromaDB
```

#### Benefits
- ✅ Always up-to-date (fetches latest on demand)
- ✅ No intermediate JSON storage
- ✅ Can specify git branch/tag/commit

#### Tradeoffs
- ❌ Slow ingestion (5-10 min every time)
- ❌ GitHub API rate limits (5000/hour authenticated)
- ❌ Requires internet during ingestion
- ❌ Non-reproducible (different results each run)
- ❌ Hard to debug (no intermediate artifacts)

**Verdict:** Only suitable for advanced production with caching layer

---

### Option D: **Hybrid Approach** (BEST for Production Scale)

**Combine incremental updates + scheduled automation + JSON caching**

#### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                   GitHub Repository                          │
│              (visa/visa-chart-components)                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ GitHub Actions (daily)
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              Data Pipeline (extractors/)                     │
│  - Detects changes via git diff                              │
│  - Only re-extracts modified files                           │
│  - Updates JSON cache with timestamps                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Commit + Push
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              JSON Cache (data/raw/)                          │
│  - visa_repo_docs.json (with version metadata)              │
│  - visa_code_docs.json                                       │
│  - visa_issue_qa.json                                        │
│  - extraction_manifest.json (NEW: timestamps, versions)     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ API call (webhook or manual)
                        ↓
┌─────────────────────────────────────────────────────────────┐
│         Backend Ingestion (ingest_visa_docs.py)             │
│  - Check manifest for changes                                │
│  - Incremental update (Option A logic)                       │
│  - Update ChromaDB with only changed docs                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
                   ChromaDB
                (always current)
```

#### extraction_manifest.json (NEW)
```json
{
  "last_extraction": "2026-03-05T16:00:00Z",
  "source_commit": "abc123...",
  "source_branch": "main",
  "extraction_version": "1.2.0",
  "documents": {
    "visa_repo_docs.json": {
      "count": 53,
      "size_bytes": 973000,
      "fingerprint": "def456...",
      "changed_files": ["packages/bar-chart/README.md"]
    },
    "visa_code_docs.json": {
      "count": 210,
      "size_bytes": 307000,
      "fingerprint": "ghi789...",
      "changed_files": []
    }
  }
}
```

#### Benefits
- ✅ **Best of all worlds**
- ✅ Automatic updates (GitHub Actions)
- ✅ Fast incremental ingestion (seconds)
- ✅ Reproducible (JSON cache + git versioning)
- ✅ Offline capable (JSON fallback)
- ✅ Full audit trail (manifest tracking)

#### Implementation Time
- Option A (incremental): 2-3 hours
- Option B (automation): 1-2 hours
- Manifest tracking: 1 hour
- **Total: 4-6 hours** (worth it for production)

---

## Recommendation for Current MVP

### Short-term (VCC Evaluation - Current Sprint)
**Status Quo: Keep JSON approach**
- ✅ Works perfectly for evaluation
- ✅ No scalability issues with 276 docs
- ✅ Focus on RAGAS evaluation first

**When new docs arrive:**
```bash
# Manual update (5-10 minutes)
cd data-pipeline/extractors/
python run_extraction.py              # Re-extract
cd ../../backend/
python ingest_visa_docs.py --reingest # Re-ingest
```

### Medium-term (Post-Evaluation - Week 2)
**Add Option A: Incremental updates**
- Implement fingerprint-based change detection
- Add `ingest_visa_docs_incremental()` function
- Keep JSON files (still useful for reproducibility)
- Reduces update time from 10 min → 30 seconds

### Long-term (Production - Month 1)
**Implement Option D: Hybrid approach**
- Add scheduled GitHub Actions
- Add extraction manifest tracking
- Combine with incremental ingestion
- Full automation + fast updates + reproducibility

---

## Decision Matrix

| Approach | Speed | Auto | Reproducible | Offline | Complexity | Cost |
|----------|-------|------|--------------|---------|------------|------|
| **Current (JSON)** | ⭐⭐⭐ | ❌ | ✅ | ✅ | ⭐ | $0 |
| **Option A (Incremental)** | ⭐⭐⭐⭐⭐ | ❌ | ✅ | ✅ | ⭐⭐⭐ | $0 |
| **Option B (Scheduled)** | ⭐⭐⭐ | ✅ | ✅ | ❌ | ⭐⭐ | $0 |
| **Option C (Live)** | ⭐ | ✅ | ❌ | ❌ | ⭐⭐⭐⭐ | API limits |
| **Option D (Hybrid)** | ⭐⭐⭐⭐⭐ | ✅ | ✅ | ✅ | ⭐⭐⭐⭐ | $0 |

---

## Answers to Your Question

### "Is the current JSON format scalable?"
**Yes, for current scale (276 docs)**
- 1.3MB JSON is negligible
- 2696 chunks manageable
- No performance issues

**But not ideal for:**
- Frequent updates (manual process)
- Large-scale (10,000+ docs)
- Real-time requirements (GitHub → RAG in <1 min)

### "Do we run the data pipeline again?"
**Current answer: YES (manual re-extraction)**
```bash
python run_extraction.py  # 5-10 min
```

**Future answer: DEPENDS (with Option A/D)**
```bash
# Only if documents changed (30 sec incremental)
python ingest_visa_docs.py --incremental

# OR: Fully automated (GitHub Actions)
# Just push code, pipeline auto-updates
```

---

## Implementation Priority

### For VCC Evaluation (This Week)
1. ✅ **Keep current approach** (no changes needed)
2. ✅ **Document scalability strategy** (this doc)
3. ⬜ **Add extraction timestamp** to JSON metadata (5 min)

### For Portfolio Demo (Next Week)
4. ⬜ **Implement Option A** (incremental updates - 2-3h)
5. ⬜ **Add manifest tracking** (1h)
6. ⬜ **Document in README** (30 min)

### For Production (Future)
7. ⬜ **Add GitHub Actions** (Option B - 1-2h)
8. ⬜ **Add API webhook** for auto-reingest (1h)
9. ⬜ **Monitoring & alerts** (30 min)

---

## Code Examples

### Quick Win: Add Timestamp to JSON (5 minutes)
```python
# data-pipeline/extractors/run_extraction.py
summary = {
    "timestamp": datetime.now().isoformat(),
    "source_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], 
        cwd=REPO_DIR
    ).decode().strip(),
    "documents": {
        "repo_docs": len(repo_docs),
        "code_docs": len(code_docs),
        "issue_qa": len(issue_qa_docs)
    }
}
```

### Medium Effort: Incremental Ingestion (2-3 hours)
See Option A implementation above.

---

**Current Status:** ✅ Scalable for MVP, documented for future  
**Next Action:** Focus on VCC RAGAS evaluation first  
**Future Enhancement:** Implement Option A (incremental) post-evaluation
