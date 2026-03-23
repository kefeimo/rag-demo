"""Tests to keep enhanced Mermaid labels aligned with routing logic."""

import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.agent_graph import HYBRID_GATE_THRESHOLD, LangGraphRAGPipeline


@pytest.mark.unit
def test_enhanced_mermaid_uses_threshold_constant():
    """Enhanced Mermaid should reflect the current hybrid fallback threshold constant."""
    pipeline = LangGraphRAGPipeline(hybrid_retrievers={})
    mermaid = pipeline.get_mermaid_enhanced()

    expected_label = f'relevance < {HYBRID_GATE_THRESHOLD:.2f} AND has_hybrid'
    assert expected_label in mermaid


@pytest.mark.unit
def test_planner_route_and_label_are_aligned():
    """Planner route criteria should match the enhanced Mermaid label semantics."""
    pipeline = LangGraphRAGPipeline(hybrid_retrievers={"vcc_docs": object()})

    state_hybrid = {"planned_strategy": "hybrid_first", "collection": "vcc_docs"}
    state_semantic = {"planned_strategy": "semantic_first", "collection": "vcc_docs"}

    assert pipeline._route_after_planner(state_hybrid) == "hybrid_retrieve"
    assert pipeline._route_after_planner(state_semantic) == "semantic_retrieve"

    mermaid = pipeline.get_mermaid_enhanced()
    assert 'strategy == hybrid_first AND has_hybrid' in mermaid


@pytest.mark.unit
def test_semantic_route_and_label_are_aligned():
    """Semantic fallback route criteria should match the enhanced Mermaid label semantics."""
    pipeline = LangGraphRAGPipeline(hybrid_retrievers={"vcc_docs": object()})

    low_score_state = {
        "collection": "vcc_docs",
        "relevance_score": HYBRID_GATE_THRESHOLD - 0.01,
    }
    error_state = {
        "collection": "vcc_docs",
        "error": "retrieval failed",
    }
    high_score_state = {
        "collection": "vcc_docs",
        "relevance_score": HYBRID_GATE_THRESHOLD,
    }

    assert pipeline._route_after_semantic(low_score_state) == "hybrid_retrieve"
    assert pipeline._route_after_semantic(error_state) == "finish"
    assert pipeline._route_after_semantic(high_score_state) == "evaluate"

    mermaid = pipeline.get_mermaid_enhanced()
    assert 'error exists' in mermaid
    assert f'relevance < {HYBRID_GATE_THRESHOLD:.2f} AND has_hybrid' in mermaid


@pytest.mark.unit
def test_evaluate_route_and_label_are_aligned():
    """Evaluate route criteria should match enhanced Mermaid label semantics."""
    pipeline = LangGraphRAGPipeline(hybrid_retrievers={})

    assert pipeline._route_after_evaluate({"is_relevant": True}) == "generate"
    assert pipeline._route_after_evaluate({"is_relevant": False}) == "finish"

    mermaid = pipeline.get_mermaid_enhanced()
    assert 'is_relevant == true' in mermaid
    assert 'is_relevant == false' in mermaid
