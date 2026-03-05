# RAG Data Pipeline - Architecture Design

**Project:** RAG System Implementation for Visa  
**Component:** Data Acquisition Framework  
**Status:** 📝 Design Phase  
**Date:** March 5, 2026

---

## 🎯 Strategic Goal

**Build a reusable framework for generating RAG datasets from real codebases**

This demonstrates:
- Data engineering skills (not just prompt tuning)
- Visa-specific research (using their actual repos)
- End-to-end thinking (data → RAG → queries)
- Production mindset (reusable framework, not one-off script)

---

## 🏗️ System Architecture

### **High-Level Pipeline**

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SOURCES (3 Pillars)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Pillar 1: Repository Docs    Pillar 2: Code Docs    Pillar 3: Issues/Q&A │
│  ├── README.md                ├── API Reference      ├── GitHub Issues   │
│  ├── docs/*.md                ├── Docstrings         ├── Pull Requests   │
│  ├── CHANGELOG                ├── Comments           ├── Stack Overflow  │
│  └── Wiki pages               └── Type hints         └── Discussions     │
│                                                                  │
└────────────┬──────────────────┬──────────────────┬──────────────┘
             │                  │                  │
             ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                         EXTRACTORS                               │
├─────────────────────────────────────────────────────────────────┤
│  repo_docs_extractor.py  │  code_doc_generator.py  │  issue_qa_converter.py │
│  • git clone            │  • Parse Python          │  • GitHub API          │
│  • Find .md/.rst/.txt   │  • Parse Java            │  • Filter closed       │
│  • Extract content      │  • Parse JavaScript      │  • Extract Q&A pairs   │
│  • Add metadata         │  • Generate API ref      │  • Format triples      │
└────────────┬──────────────────┬──────────────────┬──────────────┘
             │                  │                  │
             ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                         PROCESSORS                               │
├─────────────────────────────────────────────────────────────────┤
│  markdown_cleaner.py      │  code_snippet_extractor.py  │  metadata_enricher.py │
│  • Remove HTML           │  • Extract code examples    │  • Add source info    │
│  • Normalize formatting  │  • Syntax highlighting      │  • Add timestamps     │
│  • Fix broken links      │  • Language detection       │  • Add doc type       │
│  • Convert tables        │  • Comment extraction       │  • Add confidence     │
└────────────┬──────────────────┬──────────────────┬──────────────┘
             │                  │                  │
             └──────────────────┴──────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE ORCHESTRATOR                         │
├─────────────────────────────────────────────────────────────────┤
│  • Read config.yaml                                              │
│  • Run extractors in parallel                                    │
│  • Apply processors sequentially                                 │
│  • Merge datasets with deduplication                             │
│  • Generate statistics report                                    │
│  • Output: processed/dataset.json                                │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT DATASETS                             │
├─────────────────────────────────────────────────────────────────┤
│  data/raw/                     │  data/processed/                │
│  ├── repo_docs/                │  └── visa_docs_dataset.json     │
│  │   ├── visa-java-sample/    │      ├── documents: []           │
│  │   └── visa-openapi/         │      ├── metadata: {}            │
│  ├── code_docs/                │      ├── statistics: {}          │
│  │   └── api_reference.json   │      └── source_map: {}          │
│  └── issues_qa/                │                                  │
│      └── qa_pairs.json         │                                  │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXISTING RAG SYSTEM                           │
├─────────────────────────────────────────────────────────────────┤
│  • Ingest new dataset (ingest.py)                                │
│  • Update ChromaDB collection                                    │
│  • Test Visa-specific queries                                    │
│  • Measure improvements (doc count, chunk count, query quality)  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Component Specifications

### **1. Extractors**

#### **A) repo_docs_extractor.py**
```python
"""Extract documentation files from git repositories"""

class RepoDocsExtractor:
    def __init__(self, repo_url: str, branch: str = "main"):
        self.repo_url = repo_url
        self.branch = branch
        
    def extract(self) -> List[Document]:
        # 1. Clone repo to temp directory
        # 2. Find all .md, .rst, .txt files
        # 3. Read content with encoding detection
        # 4. Extract metadata (path, size, last_modified, commit_hash)
        # 5. Return Document objects
        pass
        
    def _find_docs(self, repo_path: Path) -> List[Path]:
        # Recursively find documentation files
        # Exclude: node_modules/, venv/, .git/, build/
        pass
```

**Input:** Repository URL (e.g., `https://github.com/visa/java-sample-code`)  
**Output:** List of Document objects with raw content + metadata  
**Metadata:** `{"source": "repo_docs", "repo_name": "visa/java-sample-code", "file_path": "README.md", "commit_hash": "abc123", "last_modified": "2026-03-01"}`

---

#### **B) code_doc_generator.py**
```python
"""Generate API documentation from source code"""

class CodeDocGenerator:
    def __init__(self, language: str):
        self.language = language  # "python", "java", "javascript"
        
    def extract_from_file(self, file_path: Path) -> List[Document]:
        if self.language == "python":
            return self._extract_python_docstrings(file_path)
        elif self.language == "java":
            return self._extract_javadoc(file_path)
        elif self.language == "javascript":
            return self._extract_jsdoc(file_path)
            
    def _extract_python_docstrings(self, file_path: Path) -> List[Document]:
        # Use ast module to parse Python
        # Extract: class docstrings, method docstrings, module docstrings
        # Format: "Class: ClassName\nDescription: ...\nMethods: ..."
        pass
        
    def _extract_javadoc(self, file_path: Path) -> List[Document]:
        # Parse JavaDoc comments (/** ... */)
        # Extract: @param, @return, @throws tags
        pass
```

**Input:** Source code file (e.g., `PaymentAPI.java`)  
**Output:** List of API documentation entries  
**Metadata:** `{"source": "code_docs", "language": "java", "class_name": "PaymentAPI", "method": "processPayment", "generated": true}`

---

#### **C) issue_qa_converter.py**
```python
"""Convert GitHub Issues to Q&A pairs"""

class IssueQAConverter:
    def __init__(self, repo_owner: str, repo_name: str, github_token: str = None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token
        
    def fetch_issues(self, state: str = "closed", labels: List[str] = None) -> List[Issue]:
        # Use GitHub API: GET /repos/{owner}/{repo}/issues
        # Filter: state=closed, has comments, accepted answer label
        pass
        
    def convert_to_qa(self, issue: Issue) -> Document:
        # Question: issue.title + issue.body
        # Answer: top comment (by votes or "accepted answer" label)
        # Context: All comments + issue description
        # Return: Document with structured Q&A format
        pass
```

**Input:** GitHub repository (e.g., `visa/java-sample-code`)  
**Output:** List of Q&A pair documents  
**Metadata:** `{"source": "issue_qa", "issue_number": 123, "created_at": "2025-12-01", "labels": ["bug", "authentication"], "votes": 15}`

---

### **2. Processors**

#### **A) markdown_cleaner.py**
- Remove HTML tags (keep content)
- Normalize whitespace (consistent newlines)
- Fix broken links (replace with placeholder or remove)
- Convert tables to readable format
- Strip excessive formatting

#### **B) code_snippet_extractor.py**
- Detect code blocks (```language ... ```)
- Extract inline code (`code`)
- Add syntax highlighting metadata
- Detect language from fence or content
- Preserve code structure (indentation)

#### **C) metadata_enricher.py**
- Add `source_type`: "repo_docs", "code_docs", "issue_qa"
- Add `timestamp`: ISO 8601 format
- Add `doc_id`: unique hash (SHA256 of content)
- Add `confidence`: 1.0 for docs, 0.8 for code, 0.6 for issues
- Add `language`: detected from file extension or content

---

### **3. Pipeline Orchestrator**

```python
"""Main pipeline runner"""

class PipelineOrchestrator:
    def __init__(self, config_path: Path):
        self.config = self._load_config(config_path)
        
    def run(self):
        # Phase 1: Extraction (parallel)
        docs_from_repo = self._extract_repo_docs()
        docs_from_code = self._extract_code_docs()
        docs_from_issues = self._extract_issues()
        
        # Phase 2: Processing (sequential)
        all_docs = docs_from_repo + docs_from_code + docs_from_issues
        cleaned_docs = self._clean_markdown(all_docs)
        enriched_docs = self._enrich_metadata(cleaned_docs)
        
        # Phase 3: Merging (deduplication)
        final_docs = self._deduplicate(enriched_docs)
        
        # Phase 4: Output
        self._save_dataset(final_docs)
        self._generate_stats(final_docs)
```

---

## 📊 Configuration Format

### **config.yaml**

```yaml
# RAG Data Pipeline Configuration

pipeline:
  name: "visa-rag-dataset"
  version: "1.0"
  output_dir: "data/processed"

sources:
  # Pillar 1: Repository Documentation
  repositories:
    - url: "https://github.com/visa/java-sample-code"
      branch: "main"
      include_patterns:
        - "*.md"
        - "*.rst"
        - "docs/**"
      exclude_patterns:
        - "node_modules/**"
        - ".git/**"
      
    - url: "https://github.com/visa/openapi"
      branch: "master"
      include_patterns:
        - "*.yaml"
        - "*.md"
  
  # Pillar 2: Code Documentation
  code_extraction:
    - repo: "visa/java-sample-code"
      languages: ["java"]
      include_patterns:
        - "src/**/*.java"
      extract_types:
        - "class_docs"
        - "method_docs"
        - "javadoc"
    
    - repo: "visa/openapi"
      languages: ["python"]
      include_patterns:
        - "**/*.py"
      extract_types:
        - "docstrings"
  
  # Pillar 3: Issues & Q&A
  issues:
    - repo_owner: "visa"
      repo_name: "java-sample-code"
      state: "closed"
      labels: ["question", "documentation", "bug"]
      min_comments: 2
      date_range:
        start: "2024-01-01"
        end: "2026-03-01"

github:
  # Optional: Add token for higher rate limits
  token_env_var: "GITHUB_TOKEN"
  rate_limit_strategy: "wait"  # or "skip"

processing:
  markdown:
    remove_html: true
    normalize_whitespace: true
    fix_broken_links: true
  
  deduplication:
    enabled: true
    similarity_threshold: 0.95
    hash_algorithm: "sha256"
  
  metadata:
    add_timestamps: true
    add_doc_ids: true
    add_confidence_scores: true

output:
  format: "json"  # or "jsonl", "parquet"
  compression: "gzip"
  split_by_source: false
  max_file_size_mb: 100
```

---

## 🎯 Target Visa Repositories (Research Needed)

### **Priority 1: High-Value Targets**

1. **visa/java-sample-code**
   - Expected: Code samples, README, API usage examples
   - Value: Backend integration patterns
   - Languages: Java
   - Estimated docs: 20-30 files

2. **visa/openapi**
   - Expected: OpenAPI specs, API documentation
   - Value: API reference, endpoints, schemas
   - Languages: YAML, Markdown
   - Estimated docs: 50-100 files

3. **visa/developer-recipes**
   - Expected: Integration guides, tutorials
   - Value: Step-by-step recipes
   - Languages: Markdown
   - Estimated docs: 30-50 files

### **Priority 2: Supplementary Targets**

4. **visa/visa-sdk-javascript**
   - Expected: SDK docs, examples
   - Value: Frontend integration
   - Languages: JavaScript, Markdown
   - Estimated docs: 40-60 files

5. **visa GitHub Issues** (across all repos)
   - Expected: Developer Q&A, bug reports, feature requests
   - Value: Real developer pain points
   - Estimated issues: 100-200 closed issues

---

## 📈 Success Metrics

### **Quantitative Metrics**

| Metric | Baseline (FastAPI) | Target (FastAPI + Visa) | Improvement |
|--------|-------------------|------------------------|-------------|
| **Document Count** | 13 | 150+ | 11.5x |
| **Chunk Count** | 252 | 1000+ | 4x |
| **Source Diversity** | 1 (FastAPI) | 2+ (FastAPI + Visa) | 2x |
| **Query Coverage** | FastAPI only | FastAPI + Visa APIs | +50% |
| **Code Examples** | 20 | 100+ | 5x |

### **Qualitative Metrics**

- ✅ Can answer Visa-specific queries: "How do I authenticate with Visa API?"
- ✅ Code examples in response include Visa SDK usage
- ✅ Source attribution shows mix of FastAPI + Visa docs
- ✅ Confidence scores remain >0.75 for Visa queries

---

## 🚀 Implementation Timeline

### **Hour 14: Core Framework (60 min)**
- [ ] 15 min: Create directory structure + config.yaml template
- [ ] 20 min: Implement `repo_docs_extractor.py` (basic version)
- [ ] 15 min: Implement `code_doc_generator.py` (Python only first)
- [ ] 10 min: Implement `issue_qa_converter.py` (GitHub API basic)

### **Hour 15: Demo Execution (60 min)**
- [ ] 10 min: Research + select 2 Visa repos (java-sample-code + openapi)
- [ ] 20 min: Run pipeline, debug issues
- [ ] 15 min: Ingest into RAG system
- [ ] 15 min: Test Visa queries, collect metrics

### **Hour 16: Documentation (60 min)**
- [ ] 20 min: Write DATA-PIPELINE.md (this document + usage guide)
- [ ] 15 min: Update lesson-learned.md
- [ ] 15 min: Update README.md
- [ ] 10 min: Git commit + push

---

## 🔧 Technical Decisions

### **Technology Stack**

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Git operations** | GitPython | Pure Python, no shell dependencies |
| **GitHub API** | PyGithub or requests | Simple REST API, no complex SDK needed |
| **Code parsing** | ast (Python), javalang (Java) | Lightweight, standard library when possible |
| **Markdown processing** | markdown-it-py | Fast, extensible |
| **Config management** | PyYAML | Standard, human-readable |
| **Parallel execution** | concurrent.futures | Built-in, simple |

### **Design Principles**

1. **Modularity:** Each extractor/processor is independent
2. **Extensibility:** Easy to add new sources (GitLab, Bitbucket, Stack Overflow)
3. **Configurability:** Everything driven by config.yaml
4. **Idempotency:** Can re-run pipeline without side effects
5. **Observability:** Log everything, generate statistics

### **Error Handling**

- **Network errors:** Retry with exponential backoff (3 attempts)
- **Parsing errors:** Log error, skip file, continue pipeline
- **Rate limits:** Wait or skip based on config
- **Missing data:** Use defaults, mark with metadata

---

## 🎓 Lessons Learned (Anticipated)

### **Challenges**

1. **GitHub rate limits:** 60 req/hour unauthenticated, 5000/hour authenticated
   - Solution: Use token, implement caching

2. **Large repositories:** Cloning 1GB+ repos takes time
   - Solution: Shallow clone (`--depth=1`), sparse checkout

3. **Parsing edge cases:** Malformed markdown, unusual docstring formats
   - Solution: Graceful degradation, skip problematic files

4. **Deduplication:** Same content in README vs. docs/index.md
   - Solution: Hash-based dedup with 0.95 similarity threshold

### **Best Practices**

1. **Metadata is crucial:** Track source, timestamp, confidence
2. **Start simple:** Get 1 repo working before scaling to 10
3. **Validate early:** Test with small repos before Visa repos
4. **Cache aggressively:** Don't re-clone/re-parse on every run

---

## 📚 References

- **GitHub API:** https://docs.github.com/en/rest
- **GitPython:** https://gitpython.readthedocs.io/
- **PyGithub:** https://pygithub.readthedocs.io/
- **AST (Python):** https://docs.python.org/3/library/ast.html
- **JavaDoc:** https://www.oracle.com/technical-resources/articles/java/javadoc-tool.html

---

*Architecture Document Version: 1.0*  
*Created: March 5, 2026*  
*Status: Design Phase - Ready for Implementation*
