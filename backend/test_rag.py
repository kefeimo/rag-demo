"""
Simple test script for RAG system
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_query(query: str, top_k: int = 3):
    """Test query endpoint"""
    print(f"\n=== Testing Query: '{query}' ===")
    start_time = time.time()
    
    response = requests.post(
        f"{BASE_URL}/api/v1/query",
        json={"query": query, "top_k": top_k},
        timeout=120  # 2 minute timeout for LLM generation
    )
    
    elapsed = time.time() - start_time
    print(f"Status: {response.status_code}")
    print(f"Time: {elapsed:.2f}s")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nQuery: {data['query']}")
        print(f"Confidence: {data['confidence']:.3f}")
        print(f"Model: {data['model']}")
        print(f"\nAnswer:\n{data['answer']}")
        print(f"\nSources ({len(data['sources'])}):")
        for i, source in enumerate(data['sources'], 1):
            print(f"  {i}. {source['metadata'].get('source', 'unknown')} "
                  f"(confidence: {source['confidence']:.3f})")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200

def main():
    """Run tests"""
    print("=" * 60)
    print("RAG System Test Suite")
    print("=" * 60)
    
    # Test health
    if not test_health():
        print("\n❌ Health check failed!")
        return
    
    print("\n✅ Health check passed!")
    
    # Test queries
    test_queries = [
        "What is FastAPI?",
        "How do I create a path parameter in FastAPI?",
        "What are FastAPI's main features?",
    ]
    
    for query in test_queries:
        try:
            test_query(query)
            time.sleep(1)  # Brief pause between queries
        except Exception as e:
            print(f"❌ Query failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
