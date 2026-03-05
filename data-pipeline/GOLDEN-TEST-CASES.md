# Golden Test Cases for RAG Evaluation

This document lists high-quality test cases for evaluating the RAG system's performance with Visa Chart Components documentation.

## Purpose

These test cases represent **real user questions** with:
- Clear question format
- Actual discussions and resolutions
- External audience (user-facing)
- Varying complexity levels

Use these to measure:
- Retrieval confidence scores
- Answer quality and accuracy
- Source attribution correctness
- Context relevance

---

## Test Case 1: Feature Enhancement Question (OPEN)

**GitHub Issue:** [#84 - Improve group focus indicator](https://github.com/visa/visa-chart-components/issues/84)

**Labels:**
- `enhancement` - New feature or request
- `help wanted` - Extra attention is needed
- `needs investigation` - Additional content needed
- `question` - Further information is requested

**Status:** Open (as of March 2026)

**Test Query:**
```
"How can I improve the group focus indicator in Visa Chart Components?"
```

**Expected Behavior:**
- Should retrieve issue #84
- Should mention it's an open enhancement request
- Should indicate it needs investigation
- Context: `development`
- Audience: `external`
- Issue type: `feature`

**Evaluation Criteria:**
- Confidence score: Should be > 0.75 (if included in ingestion)
- Source attribution: Must cite issue #84
- Answer accuracy: Should mention it's under investigation
- Relevance: Should discuss focus indicators and accessibility

---

## Test Case 2: Technical Question with Resolution (CLOSED)

**GitHub Issue:** [#51 - Alluvial Chart Frequency Values](https://github.com/visa/visa-chart-components/issues/51)

**Labels:**
- `fixed-in-next-release` - Addressed, awaiting release
- `question` - Further information is requested

**Status:** Closed (fixed)

**Test Query:**
```
"How do I work with frequency values in Alluvial Chart?"
```

**Expected Behavior:**
- Should retrieve issue #51
- Should mention it was fixed in a release
- Should provide solution/workaround from comments
- Context: `development`
- Audience: `external`
- Issue type: `question`

**Evaluation Criteria:**
- Confidence score: Should be > 0.80 (specific technical question)
- Source attribution: Must cite issue #51
- Answer accuracy: Should explain the resolution
- Completeness: Should reference the fix/release notes

---

## Additional Test Queries (Derived)

Based on the golden test cases, these queries should also work well:

### From Issue #84 (Focus Indicators)
```
"What accessibility features does Visa Chart Components provide?"
"How do keyboard navigation and focus work in VCC?"
"Can I customize focus indicators in the charts?"
```

### From Issue #51 (Alluvial Chart)
```
"How do I use the Alluvial Chart component?"
"What data format does Alluvial Chart expect?"
"Are there any known issues with Alluvial Chart?"
```

---

## Evaluation Workflow

### 1. Baseline (Before Full Ingestion)
Run these queries with only 10 documents ingested (current state):
- Record confidence scores
- Check if any relevant docs are retrieved
- Note: Issues likely NOT included in 10-doc sample

### 2. After Full Ingestion (276 docs)
Re-run the same queries:
- Compare confidence scores (should improve)
- Verify issue #51 and #84 are retrieved
- Measure answer quality improvements

### 3. Comparison Metrics
```
| Query | Before (10 docs) | After (276 docs) | Improvement |
|-------|------------------|------------------|-------------|
| #84 Focus indicator | <0.65? | >0.75? | +X% |
| #51 Alluvial freq | <0.65? | >0.80? | +X% |
```

### 4. Manual Validation
For each golden test case:
- [ ] Read retrieved sources (top 3)
- [ ] Verify issue #51 or #84 appears
- [ ] Check answer accuracy against actual issue content
- [ ] Confirm source attribution is correct

---

## Why These Are Golden Test Cases

**Issue #84 (Open Enhancement):**
- ✅ Real user question format
- ✅ Active discussion (help wanted)
- ✅ Requires investigation (complex)
- ✅ Accessibility focus (important use case)
- ✅ Multiple labels (rich metadata)
- ⚠️ No resolution yet (tests "open issue" handling)

**Issue #51 (Closed Question):**
- ✅ Specific technical question
- ✅ Has resolution (fixed in release)
- ✅ Clear answer path (from discussion to fix)
- ✅ Component-specific (Alluvial Chart)
- ✅ Fixed status (tests closed issue handling)
- ✅ Reference to release notes (tests cross-doc linking)

---

## Notes

- **Issue Volume:** Only 21 total issues (18 closed, 3 open) in the repository
- **Quality Concern:** Low issue count may indicate:
  - Well-maintained project with few bugs
  - Small user base / limited adoption
  - Issues tracked elsewhere (internal Jira?)
  - Community uses other channels (Discord, Slack?)
- **Recommendation:** Supplement with documentation and code examples for comprehensive coverage

---

**Created:** March 5, 2026  
**Author:** Data Pipeline Framework (Stage 2C)  
**Purpose:** RAG system evaluation and quality benchmarking
