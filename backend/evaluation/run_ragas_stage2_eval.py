#!/usr/bin/env python3
"""
Stage 2: RAGAS Evaluation

This script reads query results from Stage 1 (optionally with Stage 1B references)
and runs RAGAS evaluation using OpenAI API. This allows you to re-run evaluation
without querying the RAG system again.

Metrics Evaluated:
- Always: Faithfulness, AnswerRelevancy (don't need reference)
- If references available: ContextPrecision, ContextRecall, ContextEntityRecall, AnswerCorrectness

Usage:
    # Without references (2 metrics):
    python run_ragas_stage2_eval.py \\
        --input ../../data/results/baseline_20_stage1.json \\
        --output ../../data/results/baseline_20_evaluated.json
    
    # With references (6 metrics):
    python run_ragas_stage2_eval.py \\
        --input ../../data/results/baseline_20_stage1_with_references.json \\
        --output ../../data/results/baseline_20_evaluated.json
"""

import json
import time
from pathlib import Path
import sys
from typing import List, Dict, Any

from ragas import evaluate
from ragas.metrics import (
    Faithfulness, 
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    ContextEntityRecall,
    AnswerCorrectness  # ✅ Added for answer quality evaluation
)
from datasets import Dataset
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import os


def load_query_results(file_path: str) -> Dict[str, Any]:
    """Load query results from Stage 1 JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    results = data.get('results', [])
    print(f"✓ Loaded {len(results)} query results from Stage 1")
    print(f"  Timestamp: {data.get('timestamp', 'unknown')}")
    print(f"  Success rate: {data.get('successful_queries', 0)}/{data.get('total_queries', 0)}")
    
    return data

def prepare_ragas_dataset(results: List[Dict[str, Any]]) -> tuple[Dataset, bool]:
    """
    Convert query results to RAGAS Dataset format.
    
    RAGAS 0.4.x expects:
    - user_input: The question
    - response: The generated answer
    - retrieved_contexts: List of retrieved context strings
    - reference: (optional) Ground truth answer for metrics that need it
    
    Returns:
        Tuple of (Dataset, has_references)
    """
    data = {
        "user_input": [],
        "response": [],
        "retrieved_contexts": [],
        "reference": []
    }
    
    has_references = False
    
    for result in results:
        data["user_input"].append(result['query'])
        data["response"].append(result['answer'])
        data["retrieved_contexts"].append(result['contexts'])
        
        # Add reference if available
        if 'reference' in result and result['reference']:
            data["reference"].append(result['reference'])
            has_references = True
        else:
            data["reference"].append("")  # Placeholder for queries without references
    
    # Check if we have at least some references (not requiring ALL)
    reference_count = sum(1 for ref in data["reference"] if ref)
    has_sufficient_references = reference_count >= len(results) * 0.8  # 80% threshold
    
    return Dataset.from_dict(data), has_sufficient_references

def run_ragas_evaluation(dataset: Dataset, has_references: bool) -> Any:
    """
    Run RAGAS evaluation on the dataset.
    
    Metrics evaluated:
    - Always: Faithfulness, AnswerRelevancy (don't need reference)
    - If has_references: ContextPrecision, ContextRecall, ContextEntityRecall
    """
    print(f"\n{'='*60}")
    print("Stage 2: Running RAGAS Evaluation")
    print(f"{'='*60}\n")
    
    # Check for OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError(
            "OPENAI_API_KEY environment variable not set!\n"
            "Please set it with: export OPENAI_API_KEY='sk-proj-your-key-here'"
        )
    
    # Configure LLM and embeddings explicitly
    print("Configuring OpenAI models...")
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    embeddings = OpenAIEmbeddings()
    print("✓ LLM and embeddings configured\n")
    
    # Determine which metrics to use
    metrics = [
        Faithfulness(llm=llm),
        AnswerRelevancy(llm=llm, embeddings=embeddings)
    ]
    
    metric_names = ["Faithfulness", "AnswerRelevancy"]
    
    if has_references:
        metrics.extend([
            ContextPrecision(llm=llm),
            ContextRecall(llm=llm),
            ContextEntityRecall(llm=llm),
            AnswerCorrectness(llm=llm)  # ✅ Added: Measures answer quality vs ground truth
        ])
        metric_names.extend(["ContextPrecision", "ContextRecall", "ContextEntityRecall", "AnswerCorrectness"])
        print("✓ References found! Evaluating all 6 metrics")
    else:
        print("⚠ No references found. Evaluating 2 metrics only")
        print("  (Run Stage 1B to generate references for full evaluation)")
    
    # Run evaluation
    print(f"\nEvaluating {len(dataset)} queries with {len(metrics)} metrics...")
    for name in metric_names:
        print(f"  • {name}")
    print()
    
    result = evaluate(
        dataset,
        metrics=metrics
    )
    
    return result

def save_evaluation_results(
    ragas_result: Any,
    original_data: Dict[str, Any],
    output_path: str
) -> None:
    """Save RAGAS evaluation results with original query data."""
    
    # Extract scores from RAGAS EvaluationResult
    scores_list = ragas_result.scores if hasattr(ragas_result, 'scores') else []
    
    if not scores_list:
        print("⚠️  No scores available from RAGAS evaluation")
        return
    
    # Calculate average scores
    metric_names = scores_list[0].keys()
    aggregated_metrics = {}
    
    for metric_name in metric_names:
        values = [score[metric_name] for score in scores_list if metric_name in score and score[metric_name] is not None]
        if values:
            aggregated_metrics[metric_name] = {
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "count": len(values)
            }
    
    # Combine with original query results
    results_with_scores = []
    for idx, (original_result, ragas_score) in enumerate(zip(original_data['results'], scores_list)):
        combined = {
            **original_result,
            "ragas_scores": ragas_score
        }
        results_with_scores.append(combined)
    
    # Create output data
    output_data = {
        "evaluation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "query_timestamp": original_data.get('timestamp', 'unknown'),
        "dataset_info": {
            "total_queries": original_data.get('total_queries', 0),
            "successful_queries": original_data.get('successful_queries', 0),
            "failed_queries": original_data.get('failed_queries', 0),
            "evaluated_queries": len(scores_list)
        },
        "aggregated_metrics": aggregated_metrics,
        "results": results_with_scores
    }
    
    # Save to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"✓ Evaluation results saved to {output_file}")

def print_summary(ragas_result: Any) -> None:
    """Print summary of evaluation results."""
    
    scores_list = ragas_result.scores if hasattr(ragas_result, 'scores') else []
    
    if not scores_list:
        print("No scores available")
        return
    
    print(f"\n{'='*60}")
    print("RAGAS EVALUATION RESULTS")
    print(f"{'='*60}\n")
    
    metric_names = scores_list[0].keys()
    metric_labels = {
        "faithfulness": "Faithfulness",
        "answer_relevancy": "Answer Relevancy",
        "context_precision": "Context Precision",
        "context_recall": "Context Recall",
        "context_entity_recall": "Context Entity Recall"
    }
    
    for metric_name in metric_names:
        values = [score[metric_name] for score in scores_list if metric_name in score and score[metric_name] is not None]
        if values:
            avg_score = sum(values) / len(values)
            min_score = min(values)
            max_score = max(values)
            label = metric_labels.get(metric_name, metric_name.replace('_', ' ').title())
            
            print(f"{label:20s}: {avg_score:.4f} (min: {min_score:.4f}, max: {max_score:.4f})")
    
    print(f"\n{'='*60}\n")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Stage 2: Run RAGAS evaluation on query results')
    parser.add_argument('--input', type=str, required=True, help='Path to Stage 1 query results JSON file')
    parser.add_argument('--output', type=str, required=True, help='Path to save evaluation results JSON file')
    args = parser.parse_args()
    
    try:
        # Load Stage 1 results
        original_data = load_query_results(args.input)
        
        if not original_data.get('results'):
            print("✗ No query results found in input file")
            sys.exit(1)
        
        # Prepare RAGAS dataset
        dataset, has_references = prepare_ragas_dataset(original_data['results'])
        print(f"✓ Prepared dataset with {len(dataset)} queries")
        if has_references:
            print(f"✓ All queries have reference answers\n")
        else:
            print(f"⚠ No reference answers found\n")
        
        # Run RAGAS evaluation
        ragas_result = run_ragas_evaluation(dataset, has_references)
        
        # Print summary
        print_summary(ragas_result)
        
        # Save results
        save_evaluation_results(ragas_result, original_data, args.output)
        
        print("✓ Stage 2 evaluation complete!")
        
    except Exception as e:
        print(f"✗ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
