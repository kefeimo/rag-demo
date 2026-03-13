"""
Minimal LangGraph orchestration for the existing RAG pipeline.

This module keeps current retrieval/generation behavior but expresses it as a
stateful graph so we can evolve toward agent-based orchestration incrementally.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from app.config import settings
from app.rag.generation import extract_sources, generate_answer, get_llm_client
from app.rag.retrieval import Retriever

logger = logging.getLogger(__name__)


# Keep parity with current main.py hybrid gate behavior
HYBRID_GATE_THRESHOLD = 0.65


class RAGAgentState(TypedDict, total=False):
    """State shared across LangGraph nodes for one query."""

    query: str
    top_k: int
    collection: str
    query_type: str
    planned_strategy: str
    decision_path: List[str]

    retrieval_result: Dict[str, Any]
    documents: List[Dict[str, Any]]
    relevance_score: float
    retrieval_method: str
    is_relevant: bool

    answer: str
    sources: List[Dict[str, Any]]
    error: str


class LangGraphRAGPipeline:
    """Minimal graph-based orchestrator for the RAG request lifecycle."""

    def __init__(self, hybrid_retrievers: Optional[Dict[str, Any]] = None):
        self.hybrid_retrievers = hybrid_retrievers if hybrid_retrievers is not None else {}
        self._compiled_graph = self._build_graph().compile()

    def run(self, query: str, top_k: int, collection: str) -> RAGAgentState:
        """Run one query through the graph."""
        initial_state: RAGAgentState = {
            "query": query,
            "top_k": top_k,
            "collection": collection,
            "decision_path": [],
        }
        return self._compiled_graph.invoke(initial_state)

    def get_mermaid(self) -> str:
        """Return Mermaid diagram source for graph visualization/demo."""
        return self._compiled_graph.get_graph().draw_mermaid()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(RAGAgentState)

        graph.add_node("planner", self._planner_node)
        graph.add_node("semantic_retrieve", self._semantic_retrieve_node)
        graph.add_node("hybrid_retrieve", self._hybrid_retrieve_node)
        graph.add_node("evaluate", self._evaluate_node)
        graph.add_node("generate", self._generate_node)

        graph.add_edge(START, "planner")

        graph.add_conditional_edges(
            "planner",
            self._route_after_planner,
            {
                "semantic_retrieve": "semantic_retrieve",
                "hybrid_retrieve": "hybrid_retrieve",
            },
        )

        graph.add_conditional_edges(
            "semantic_retrieve",
            self._route_after_semantic,
            {
                "hybrid_retrieve": "hybrid_retrieve",
                "evaluate": "evaluate",
                "finish": END,
            },
        )

        graph.add_edge("hybrid_retrieve", "evaluate")

        graph.add_conditional_edges(
            "evaluate",
            self._route_after_evaluate,
            {
                "generate": "generate",
                "finish": END,
            },
        )

        graph.add_edge("generate", END)
        return graph

    def _planner_node(self, state: RAGAgentState) -> RAGAgentState:
        query = state["query"]
        collection = state["collection"]
        has_hybrid = self.hybrid_retrievers.get(collection) is not None

        # Rule-based query-shape detection for minimal planner demo:
        # API-ish tokens (camelCase, PascalCase, interface-like, prop-like) prefer hybrid-first.
        api_like_patterns = [
            r"\bI[A-Z][A-Za-z0-9_]+\b",      # interface-like: IDataTableProps
            r"\b[a-z]+[A-Z][A-Za-z0-9_]*\b", # camelCase
            r"\b[A-Z][A-Za-z0-9_]+Props\b",  # *Props
            r"\b[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+\b",  # dotted API terms
        ]
        is_api_like = any(re.search(pattern, query) for pattern in api_like_patterns)

        if is_api_like and has_hybrid:
            planned_strategy = "hybrid_first"
            query_type = "api_like"
        else:
            planned_strategy = "semantic_first"
            query_type = "general"

        decision_path = list(state.get("decision_path", []))
        decision_path.append(
            f"planner(query_type={query_type}, strategy={planned_strategy}, has_hybrid={has_hybrid})"
        )

        logger.info(
            "Planner decision: query_type=%s, strategy=%s, has_hybrid=%s",
            query_type,
            planned_strategy,
            has_hybrid,
        )

        return {
            "query_type": query_type,
            "planned_strategy": planned_strategy,
            "decision_path": decision_path,
        }

    def _semantic_retrieve_node(self, state: RAGAgentState) -> RAGAgentState:
        decision_path = list(state.get("decision_path", []))
        decision_path.append("semantic_retrieve")

        retriever = Retriever(collection_name=state["collection"])
        result = retriever.retrieve(state["query"], top_k=state["top_k"])

        if "error" in result:
            logger.error("Semantic retrieval error: %s", result["error"])
            return {
                "retrieval_result": result,
                "documents": [],
                "relevance_score": 0.0,
                "retrieval_method": "semantic",
                "error": result["error"],
                "is_relevant": False,
                "decision_path": decision_path,
            }

        return {
            "retrieval_result": result,
            "documents": result.get("documents", []),
            "relevance_score": result.get("relevance_score", 0.0),
            "retrieval_method": "semantic",
            "decision_path": decision_path,
        }

    def _hybrid_retrieve_node(self, state: RAGAgentState) -> RAGAgentState:
        decision_path = list(state.get("decision_path", []))
        decision_path.append("hybrid_retrieve")

        collection = state["collection"]
        hybrid_retriever = self.hybrid_retrievers.get(collection)
        current_result = state.get("retrieval_result", {})

        if hybrid_retriever is None:
            logger.info("Hybrid retriever not available for collection=%s", collection)
            return {"decision_path": decision_path}

        hybrid_result = hybrid_retriever.search(state["query"], top_k=state["top_k"])
        if "error" in hybrid_result:
            logger.warning("Hybrid retrieval error; keeping semantic result: %s", hybrid_result["error"])
            return {"decision_path": decision_path}

        hybrid_score = hybrid_result.get("relevance_score", 0.0)
        semantic_score = current_result.get("relevance_score", 0.0)

        # If planner chose hybrid-first (no semantic result yet), accept hybrid directly.
        if not current_result:
            logger.info("Using hybrid-first result (relevance=%.3f)", hybrid_score)
            return {
                "retrieval_result": hybrid_result,
                "documents": hybrid_result.get("documents", []),
                "relevance_score": hybrid_score,
                "retrieval_method": "hybrid",
                "decision_path": decision_path,
            }

        if hybrid_score > semantic_score:
            logger.info(
                "Using hybrid result (relevance=%.3f > semantic=%.3f)",
                hybrid_score,
                semantic_score,
            )
            return {
                "retrieval_result": hybrid_result,
                "documents": hybrid_result.get("documents", []),
                "relevance_score": hybrid_score,
                "retrieval_method": "hybrid",
                "decision_path": decision_path,
            }

        logger.info(
            "Keeping semantic result (relevance=%.3f >= hybrid=%.3f)",
            semantic_score,
            hybrid_score,
        )
        return {"decision_path": decision_path}

    def _evaluate_node(self, state: RAGAgentState) -> RAGAgentState:
        decision_path = list(state.get("decision_path", []))
        decision_path.append("evaluate")

        retrieval_result = state.get("retrieval_result", {})
        documents = retrieval_result.get("documents", [])
        relevance_score = retrieval_result.get("relevance_score", 0.0)

        is_relevant = bool(documents) and relevance_score >= settings.relevance_threshold
        logger.info(
            "Relevance evaluation: docs=%s, score=%.3f, threshold=%.3f, is_relevant=%s",
            len(documents),
            relevance_score,
            settings.relevance_threshold,
            is_relevant,
        )

        return {
            "documents": documents,
            "relevance_score": relevance_score,
            "is_relevant": is_relevant,
            "decision_path": decision_path,
        }

    def _generate_node(self, state: RAGAgentState) -> RAGAgentState:
        decision_path = list(state.get("decision_path", []))
        decision_path.append("generate")

        try:
            llm_client = get_llm_client()
            documents = state.get("documents", [])

            answer = generate_answer(
                query=state["query"],
                retrieved_documents=documents,
                llm_client=llm_client,
            )
            sources = extract_sources(documents)

            return {
                "answer": answer,
                "sources": sources,
                "decision_path": decision_path,
            }
        except Exception as exc:
            logger.error("Generation failed: %s", str(exc), exc_info=True)
            return {
                "error": str(exc),
                "decision_path": decision_path,
            }

    def _route_after_planner(self, state: RAGAgentState) -> str:
        strategy = state.get("planned_strategy", "semantic_first")
        has_hybrid = self.hybrid_retrievers.get(state["collection"]) is not None
        if strategy == "hybrid_first" and has_hybrid:
            return "hybrid_retrieve"
        return "semantic_retrieve"

    def _route_after_semantic(self, state: RAGAgentState) -> str:
        if state.get("error"):
            return "finish"

        relevance_score = state.get("relevance_score", 0.0)
        has_hybrid = self.hybrid_retrievers.get(state["collection"]) is not None

        if relevance_score < HYBRID_GATE_THRESHOLD and has_hybrid:
            logger.info(
                "Semantic relevance %.3f < %.2f, routing to hybrid retrieval",
                relevance_score,
                HYBRID_GATE_THRESHOLD,
            )
            return "hybrid_retrieve"

        return "evaluate"

    def _route_after_evaluate(self, state: RAGAgentState) -> str:
        return "generate" if state.get("is_relevant", False) else "finish"
