"""
Test VCC-specific queries against the RAG system.
"""

from app.rag.retrieval import Retriever
from app.rag.generation import generate_answer

# Initialize retriever
retriever = Retriever()

# Test queries
test_queries = [
    "How do I contribute to Visa Chart Components?",
    "What props are available for the data table component?",
    "How do I create a bar chart with VCC?",
    "What is IDataTableProps interface?",
    "How to install Visa Chart Components?"
]

print("=" * 80)
print("VCC-SPECIFIC QUERY TESTING")
print("=" * 80)
print(f"\nTesting with {len(test_queries)} queries against ChromaDB")
print(f"Note: Currently only 10 sample documents ingested\n")

for i, query in enumerate(test_queries, 1):
    print(f"\n{'='*80}")
    print(f"QUERY {i}: {query}")
    print('='*80)
    
    # Retrieve context
    results = retriever.retrieve(query, top_k=3)
    
    print(f"\n📊 Retrieval Stats:")
    print(f"   Documents found: {results['retrieval_count']}")
    print(f"   Confidence: {results['confidence']:.4f}")
    
    print(f"\n📄 Retrieved Documents:")
    for j, doc in enumerate(results['documents'][:2], 1):  # Show top 2
        content = doc.get('content', str(doc))
        preview = content[:200] if len(content) > 200 else content
        print(f"\n   {j}. {preview}...")
        if 'metadata' in doc:
            print(f"      Source: {doc['metadata'].get('source', 'N/A')}")
            print(f"      File: {doc['metadata'].get('file_path', doc['metadata'].get('filename', 'N/A'))}")
    
    # Generate response
    print(f"\n🤖 Generated Response:")
    try:
        response = generate_answer(query, results['documents'][:3])
        answer_text = response.get('answer', str(response))
        print(f"   {answer_text[:300]}...")
    except Exception as e:
        print(f"   ⚠️ Response generation failed: {e}")
    
    print()

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
