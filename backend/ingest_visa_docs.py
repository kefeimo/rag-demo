"""
Test script to ingest extracted Visa Chart Components documentation into ChromaDB.
This validates that the data pipeline output can be consumed by the RAG system.
"""

import json
import sys
import os
from pathlib import Path
import logging

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.rag.ingestion import ChromaDBIngestion, DocumentLoader
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_json_documents(json_file_path: str) -> list:
    """
    Load documents from JSON file.
    
    Args:
        json_file_path: Path to JSON file with extracted docs
        
    Returns:
        List of document dictionaries with content and metadata
    """
    logger.info(f"Loading documents from: {json_file_path}")
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        docs = json.load(f)
    
    logger.info(f"Loaded {len(docs)} documents from JSON")
    
    # Validate format
    for i, doc in enumerate(docs[:3]):  # Check first 3
        if 'content' not in doc or 'metadata' not in doc:
            raise ValueError(f"Document {i} missing 'content' or 'metadata' keys")
    
    return docs


def ingest_visa_docs(
    repo_docs_path: str = None,
    code_docs_path: str = None,
    issue_qa_path: str = None,
    force_reingest: bool = True,
    max_docs: int = None
) -> dict:
    """
    Ingest Visa Chart Components documentation into ChromaDB.
    
    Args:
        repo_docs_path: Path to visa_repo_docs.json
        code_docs_path: Path to visa_code_docs.json
        issue_qa_path: Path to visa_issue_qa.json (optional)
        force_reingest: If True, reset collection before ingestion
        max_docs: Optional limit on number of docs to ingest (for testing)
        
    Returns:
        Dictionary with ingestion statistics
    """
    # Default paths
    if repo_docs_path is None:
        repo_docs_path = "../data-pipeline/data/raw/visa_repo_docs.json"
    if code_docs_path is None:
        code_docs_path = "../data-pipeline/data/raw/visa_code_docs.json"
    if issue_qa_path is None:
        issue_qa_path = "../data-pipeline/data/raw/visa_issue_qa.json"
    
    # Make paths absolute
    backend_dir = Path(__file__).parent
    repo_docs_path = (backend_dir / repo_docs_path).resolve()
    code_docs_path = (backend_dir / code_docs_path).resolve()
    issue_qa_path = (backend_dir / issue_qa_path).resolve()
    
    logger.info("=" * 70)
    logger.info("VISA CHART COMPONENTS - DOCUMENTATION INGESTION TEST")
    logger.info("=" * 70)
    logger.info(f"Repository docs: {repo_docs_path}")
    logger.info(f"Code docs: {code_docs_path}")
    logger.info(f"Issue Q&A: {issue_qa_path}")
    logger.info(f"Force reingest: {force_reingest}")
    logger.info(f"Max docs limit: {max_docs or 'None (all)'}")
    logger.info("")
    
    # Load documents from JSON files
    all_documents = []
    
    if repo_docs_path.exists():
        repo_docs = load_json_documents(str(repo_docs_path))
        all_documents.extend(repo_docs)
        logger.info(f"✅ Loaded {len(repo_docs)} repository documents")
    else:
        logger.warning(f"⚠️  Repository docs not found: {repo_docs_path}")
    
    if code_docs_path.exists():
        code_docs = load_json_documents(str(code_docs_path))
        all_documents.extend(code_docs)
        logger.info(f"✅ Loaded {len(code_docs)} code documentation entries")
    else:
        logger.warning(f"⚠️  Code docs not found: {code_docs_path}")
    
    if issue_qa_path.exists():
        issue_qa = load_json_documents(str(issue_qa_path))
        all_documents.extend(issue_qa)
        logger.info(f"✅ Loaded {len(issue_qa)} issue Q&A pairs")
    else:
        logger.warning(f"⚠️  Issue Q&A not found: {issue_qa_path}")
    
    if not all_documents:
        raise FileNotFoundError("No documents found to ingest")
    
    # Apply max_docs limit if specified
    if max_docs:
        all_documents = all_documents[:max_docs]
        logger.info(f"📊 Limited to first {len(all_documents)} documents for testing")
    
    logger.info(f"\n📚 Total documents to ingest: {len(all_documents)}")
    
    # Show sample metadata
    sample_doc = all_documents[0]
    logger.info(f"\n📄 Sample document metadata:")
    for key, value in sample_doc['metadata'].items():
        logger.info(f"   {key}: {value}")
    
    # Initialize components
    logger.info("\n🔧 Initializing ingestion pipeline...")
    loader = DocumentLoader()
    ingestion = ChromaDBIngestion()
    
    # Process documents into chunks
    logger.info(f"\n✂️  Chunking documents (size={loader.chunk_size}, overlap={loader.chunk_overlap})...")
    chunks = loader.process_documents(all_documents)
    logger.info(f"✅ Created {len(chunks)} chunks")
    
    # Show chunk statistics
    chunk_sizes = [len(chunk['content']) for chunk in chunks]
    logger.info(f"\n📊 Chunk statistics:")
    logger.info(f"   Total chunks: {len(chunks)}")
    logger.info(f"   Avg chunk size: {sum(chunk_sizes) / len(chunk_sizes):.0f} chars")
    logger.info(f"   Min chunk size: {min(chunk_sizes)} chars")
    logger.info(f"   Max chunk size: {max(chunk_sizes)} chars")
    
    # Ingest into ChromaDB
    logger.info(f"\n💾 Ingesting into ChromaDB...")
    logger.info(f"   Collection: {ingestion.collection_name}")
    logger.info(f"   Persist dir: {ingestion.persist_directory}")
    
    chunks_added, elapsed_time = ingestion.ingest_chunks(chunks, force_reingest)
    
    # Get final collection stats
    collection = ingestion.get_or_create_collection()
    
    logger.info("\n" + "=" * 70)
    logger.info("INGESTION COMPLETE!")
    logger.info("=" * 70)
    logger.info(f"✅ Documents processed: {len(all_documents)}")
    logger.info(f"✅ Chunks created: {len(chunks)}")
    logger.info(f"✅ Chunks added: {chunks_added}")
    logger.info(f"✅ Collection total: {collection.count()}")
    logger.info(f"⏱️  Time elapsed: {elapsed_time:.2f}s")
    logger.info("")
    
    return {
        "status": "success",
        "documents_processed": len(all_documents),
        "chunks_created": len(chunks),
        "chunks_added": chunks_added,
        "collection_count": collection.count(),
        "time_elapsed": f"{elapsed_time:.2f}s"
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest Visa docs into ChromaDB")
    parser.add_argument("--repo-docs", help="Path to visa_repo_docs.json")
    parser.add_argument("--code-docs", help="Path to visa_code_docs.json")
    parser.add_argument("--issue-qa", help="Path to visa_issue_qa.json")
    parser.add_argument("--no-reingest", action="store_true", help="Skip if already ingested")
    parser.add_argument("--max-docs", type=int, help="Limit number of docs (for testing)")
    
    args = parser.parse_args()
    
    try:
        result = ingest_visa_docs(
            repo_docs_path=args.repo_docs,
            code_docs_path=args.code_docs,
            issue_qa_path=args.issue_qa,
            force_reingest=not args.no_reingest,
            max_docs=args.max_docs
        )
        
        print("\n✅ Ingestion successful!")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {str(e)}", exc_info=True)
        sys.exit(1)
