# Data Pipeline - RAG Documentation Extraction

This directory contains the data extraction pipeline for generating RAG-ready documentation datasets from the Visa Chart Components repository.

## Directory Structure

```
data-pipeline/
├── extractors/                          # Python extraction scripts
│   ├── repo_docs_extractor.py          # Pillar 1: Extract .md files from repo
│   ├── code_doc_generator.py           # Pillar 2: Generate API docs from TypeScript
│   ├── issue_qa_converter.py           # Pillar 3: Convert GitHub Issues to Q&A
│   ├── run_extraction.py               # Main orchestrator script
│   └── test_*.py                       # Test scripts
│
└── data/
    └── raw/                            # Extracted documentation (JSON format)
        ├── visa_repo_docs.json         # 53 repository markdown files (973KB)
        ├── visa_code_docs.json         # 210 API documentation entries (307KB)
        └── extraction_summary.json     # Extraction metadata
```

## Extracted Data

### Pillar 1: Repository Documentation (53 docs)
- **Source**: `.md` files from visa-chart-components repo
- **Output**: `data/raw/visa_repo_docs.json`
- **Contents**: README.md, CONTRIBUTING.md, package docs, CHANGELOGs
- **Format**: `{content: "markdown string", metadata: {...}}`

### Pillar 2: Code Documentation (210 docs)
- **Source**: TypeScript source files (interfaces, props, functions)
- **Output**: `data/raw/visa_code_docs.json`
- **Contents**: Auto-generated API documentation
- **Format**: `{content: "formatted markdown", metadata: {...}}`
- **Metadata includes**: `auto_generated: true`, `generation_method: code_doc_generator`

### Pillar 3: Issue Q&A (13 docs)
- **Source**: GitHub Issues from visa-chart-components
- **Output**: `data/raw/visa_issue_qa.json`
- **Contents**: Issue-to-Q&A pairs with audience classification
- **Extracted**: 13 Q&A pairs from 18 closed issues
  - Types: 4 bugs, 4 other, 2 docs, 1 question, 1 release, 1 feature
  - Audience: 9 external, 4 internal
  - Contexts: 9 development, 2 ci_cd, 2 documentation

#### ⚠️ Data Quality Observations
- **Low issue volume**: Only 21 total issues (18 closed + 3 open) in the repository
  - This is unusually low for a mature open-source project (182 stars)
  - Possible reasons: Issues managed elsewhere, GitHub Discussions used, or minimal public issue tracking
  - **Recommendation**: Further investigate if issues are maintained in JIRA, internal systems, or GitHub Discussions

#### 💡 Future Enhancement: Pull Request Extraction
- **Feasibility**: The pipeline can be extended to extract knowledge from Pull Requests
- **Use cases**: 
  - PRs with rich descriptions and code review discussions
  - Design decisions documented in PR conversations
  - Implementation patterns and best practices
- **Note**: visa-chart-components has limited PR knowledge richness
  - Most PRs are automated (Dependabot, CI updates)
  - Code-heavy, minimal documentation discussions
  - **Better suited for**: Projects with detailed PR descriptions and review discussions

## Data Format

Each JSON file contains an array of document objects:

```json
[
  {
    "content": "# Full markdown content as string...",
    "metadata": {
      "source": "repo_docs" | "code_docs" | "issue_qa",
      "repo_name": "visa/visa-chart-components",
      "file_path": "packages/bar-chart/README.md",
      "package": "bar-chart",
      "doc_type": "readme" | "api" | "documentation",
      "audience": "external" | "internal",
      "auto_generated": true,
      "generation_method": "code_doc_generator",
      "extracted_at": "2026-03-05T16:55:20.673734"
    }
  }
]
```

## Usage

### Extract All Documentation
```bash
cd extractors/
python run_extraction.py
```

This will:
1. Clone visa-chart-components (if needed)
2. Extract repository documentation (Pillar 1)
3. Generate API documentation (Pillar 2)
4. Save results to `data/raw/`

### Individual Extractors
```bash
# Test repo docs extractor
python test_extractor.py

# Test code doc generator
python test_code_doc.py

# Extract Issue Q&A (requires GitHub token)
export GITHUB_TOKEN=your_token
python issue_qa_converter.py
```

## Golden Test Cases

See [GOLDEN-TEST-CASES.md](./GOLDEN-TEST-CASES.md) for high-quality test queries:
- **Issue #84**: Improve group focus indicator (open enhancement)
- **Issue #51**: Alluvial Chart Frequency Values (closed question)

These represent real user questions with resolutions, ideal for evaluating RAG performance.

## Next Steps

1. **Process & Ingest**: Load JSON files into RAG system (ChromaDB)
2. **Chunking**: Split large documents into smaller chunks
3. **Embedding**: Generate vector embeddings
4. **Test with Golden Cases**: Use queries from GOLDEN-TEST-CASES.md to measure quality

## Statistics

- **Total Documents**: 276 (53 repo + 210 code + 13 issues)
- **Total Size**: ~1.3 MB
- **Packages Covered**: 24
- **Repository**: visa/visa-chart-components (182 ⭐)
- **Issue Coverage**: 13 Q&A pairs from 18 closed issues (72% conversion rate)
