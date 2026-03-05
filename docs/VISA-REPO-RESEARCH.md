# Visa Repository Research - Findings

**Research Date:** March 5, 2026  
**Purpose:** Identify suitable Visa repositories for RAG data pipeline demo  
**Method:** GitHub API exploration + manual assessment

---

## 🎯 Selected Repository: visa-chart-components

### **Repository Details**

| Attribute | Value |
|-----------|-------|
| **Name** | visa-chart-components |
| **URL** | https://github.com/visa/visa-chart-components |
| **Stars** | 182 ⭐ |
| **Forks** | 41 |
| **License** | MIT |
| **Language** | TypeScript |
| **Size** | 35.8 MB |
| **Open Issues** | 3 |
| **Has Wiki** | Yes |
| **Has Pages** | Yes (likely documentation site) |

### **Description**

> "Visa Chart Components (VCC) is an accessibility focused, framework agnostic set of data experience design systems components for the web. VCC attempts to provide a toolset to enable developers to build equal data experiences for everyone, everywhere."

### **Why This Repository?**

✅ **Rich Documentation Potential**
- README.md (main documentation)
- CONTRIBUTING.md (contributor guidelines)
- docs/ directory (contains assets)
- GitHub Pages (likely extensive docs)

✅ **Modular Structure**
- `packages/` with 20+ chart component libraries:
  - alluvial-diagram
  - bar-chart, clustered-bar-chart, stacked-bar-chart
  - line-chart
  - pie-chart
  - scatter-plot
  - heat-map
  - circle-packing
  - dumbbell-plot
  - parallel-plot
  - data-table
  - keyboard-instructions
- Multi-framework support: React, Angular, Vue, Python, R, Figma

✅ **Code Documentation Opportunities**
- TypeScript/JavaScript source code
- Component API interfaces
- Props, methods, events documentation
- Example code in each package

✅ **Real-World Visa Product**
- Production library used by Visa
- Demonstrates accessibility focus
- Shows modern frontend architecture

---

## 📊 Repository Structure Analysis

### **Top-Level Files (Documentation)**

```
/
├── README.md                  ✅ Main documentation
├── CONTRIBUTING.md            ✅ Contributor guide
├── LICENSE                    ✅ Legal info
├── docs/                      ✅ Documentation assets
├── .storybook/                ✅ Component examples (Storybook)
├── packages/                  ✅ 20+ component packages
└── lerna.json                 ℹ️ Monorepo configuration
```

### **Packages Directory (20+ Components)**

Each package likely contains:
- `README.md` - Component usage guide
- `src/` - TypeScript source code
- Examples/demos
- API documentation

### **Expected Documentation Count**

| Source | Estimated Files | Notes |
|--------|----------------|-------|
| **Root docs** | 2-5 | README, CONTRIBUTING, LICENSE |
| **Package READMEs** | 20+ | One per component |
| **Storybook examples** | 50+ | Component stories/examples |
| **GitHub Pages** | 30-50 | If extensive docs site exists |
| **Total** | **100-125 files** | Conservative estimate |

---

## 🔍 Issues Analysis

### **Issue Quality Assessment**

**Observation:** Most closed issues are internal (merge PRs, releases)

```
Sample closed issues:
- #125: "chore: clean up yarn audit log content" (0 comments)
- #124: "Web5" (0 comments)  
- #113: "merge main with fix release back to development" (0 comments)
- #111: "Feat/release 8.0.1" (0 comments)
```

**Conclusion:** ❌ **Low Q&A value from Issues**
- Mostly internal development issues
- Few comments (0-1 per issue)
- Not user-facing questions
- **Recommendation:** Skip Pillar 3 (Issue Q&A) for this repo, focus on Pillars 1 & 2

---

## 🎯 Data Pipeline Strategy

### **Pillar 1: Repository Documentation** ✅ HIGH VALUE
**Extract:**
- Root: README.md, CONTRIBUTING.md
- Each package: README.md (20+ files)
- docs/ directory (if HTML/MD files present)

**Expected Output:** 25-30 documentation files

### **Pillar 2: Code Documentation** ✅ MEDIUM VALUE
**Extract:**
- TypeScript interface definitions
- Component props (React/Angular/Vue)
- JSDoc comments
- Method signatures

**Expected Output:** 50-100 API reference entries

### **Pillar 3: Issue Q&A** ❌ LOW VALUE (Skip for this repo)
**Reason:** Most issues are internal PRs, not user questions

**Alternative:** Focus on GitHub Pages documentation (if accessible)

---

## 🚀 Revised Implementation Plan

### **Hour 14: Core Extraction (Pillars 1 & 2)**

#### **Phase 1: Repository Clone & Doc Extraction (20 min)**
```bash
# Clone visa-chart-components
git clone --depth=1 https://github.com/visa/visa-chart-components.git

# Find all markdown files
find visa-chart-components -name "*.md" -type f > doc_files.txt

# Expected: ~25-30 .md files
```

#### **Phase 2: Package Documentation (20 min)**
```python
# Extract README from each package
for package in packages/*/:
    if README.md exists:
        extract(package/README.md)
        metadata = {
            "source": "visa-chart-components",
            "package": package_name,
            "component_type": "chart",
            "language": "typescript"
        }
```

#### **Phase 3: Code Documentation (20 min)**
```python
# Find TypeScript files with exported interfaces
find packages/ -name "*.tsx" -o -name "*.ts"

# Extract:
# - Component props interfaces
# - Exported classes/functions
# - JSDoc comments
```

### **Hour 15: Processing & Ingestion (60 min)**

#### **Markdown Cleaning (15 min)**
- Remove HTML tags
- Fix relative links (→ absolute GitHub URLs)
- Normalize code blocks

#### **Metadata Enrichment (15 min)**
- Add source: "visa-chart-components"
- Add component_name, package_name
- Add file_path, commit_hash
- Add doc_type: "readme" | "api" | "guide"

#### **RAG Ingestion (15 min)**
- Run existing `ingest.py` with new dataset
- Verify ChromaDB collection
- Check chunk count increase

#### **Testing (15 min)**
- Query: "How do I create a bar chart with Visa Chart Components?"
- Query: "What accessibility features does VCC provide?"
- Query: "How do I use VCC with React?"
- Expected: Confidence >0.75, proper source attribution

### **Hour 16: Documentation (60 min)**
- Document extraction process
- Create example queries
- Show before/after metrics
- Update README

---

## 📈 Expected Metrics

### **Before (FastAPI Only)**
- Documents: 13
- Chunks: 252
- Sources: 1 (FastAPI)
- Query coverage: FastAPI framework only

### **After (FastAPI + VCC)**
- Documents: 100-125 (13 FastAPI + 87-112 VCC)
- Chunks: 1000-1500 (252 FastAPI + 748-1248 VCC)
- Sources: 2 (FastAPI + Visa)
- Query coverage: FastAPI + Data visualization + Accessibility

### **Success Criteria**
✅ Ingest 80+ new documents from VCC  
✅ Answer VCC-specific queries with confidence >0.75  
✅ Show source attribution mixing FastAPI and VCC docs  
✅ Demonstrate reusable pipeline (config-driven)

---

## 🔄 Alternative/Backup Repositories

### **Option 2: visa/superset** (Fork of Apache Superset)
- **Language:** TypeScript/Python
- **Description:** Data Visualization and Data Exploration Platform
- **Stars:** Not shown (likely fork)
- **Value:** Rich documentation, but it's a fork (not original Visa content)
- **Status:** Backup option if VCC insufficient

### **Option 3: visa/moloch** (Network Traffic Analysis)
- **Language:** JavaScript
- **Description:** Open source, large scale, full packet capturing, indexing
- **Stars:** Unknown
- **Value:** Different domain (security/networking)
- **Status:** Tertiary option

---

## ✅ Final Decision

**Primary Target:** `visa/visa-chart-components`

**Rationale:**
1. ✅ **Original Visa product** (not a fork)
2. ✅ **Rich documentation** (25-30 .md files + Storybook)
3. ✅ **Clear structure** (monorepo with 20+ packages)
4. ✅ **Relevant to data engineering** (charts, data viz)
5. ✅ **MIT license** (permissive)
6. ✅ **Active maintenance** (3 open issues, recent activity)

**Implementation Focus:**
- **Pillar 1:** ✅ Full implementation (repo docs)
- **Pillar 2:** ✅ Full implementation (code docs from TypeScript)
- **Pillar 3:** ❌ Skip (low-value issues, focus elsewhere)

---

*Research Document Version: 1.0*  
*Created: March 5, 2026*  
*Status: Ready for Implementation*
