"""
Document Ingestion Pipeline
Loads markdown documents, chunks text, and stores in ChromaDB
"""

import os
import logging
from typing import List, Dict, Any, Tuple
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
import time

from app.config import settings
from app.rag.embeddings import EmbeddingProvider
from app.rag.utils import get_chroma_client

logger = logging.getLogger(__name__)


class DocumentLoader:
    """
    Load and process documents for ingestion.

    Supports two source formats:
    - Markdown files via load_documents()      — used for FastAPI docs corpus
    - JSON files via load_json_documents()     — used for VCC docs corpus
    """
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize document loader
        
        Args:
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        logger.info(f"DocumentLoader initialized (chunk_size={self.chunk_size}, overlap={self.chunk_overlap})")
    
    def load_documents(self, document_path: str) -> List[Dict[str, Any]]:
        """
        Load all markdown files from directory
        
        Args:
            document_path: Path to documents directory
            
        Returns:
            List of document dictionaries with content and metadata
        """
        documents = []
        doc_path = Path(document_path)
        
        if not doc_path.exists():
            raise FileNotFoundError(f"Document path not found: {document_path}")
        
        # Find all markdown files recursively
        md_files = list(doc_path.rglob("*.md"))
        logger.info(f"Found {len(md_files)} markdown files in {document_path}")
        
        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract metadata
                relative_path = md_file.relative_to(doc_path)
                metadata = {
                    "source": str(relative_path),
                    "filename": md_file.name,
                    "file_path": str(md_file),
                    "file_size": len(content)
                }
                
                documents.append({
                    "content": content,
                    "metadata": metadata
                })
                
                logger.debug(f"Loaded: {relative_path} ({len(content)} chars)")
                
            except Exception as e:
                logger.error(f"Error loading {md_file}: {str(e)}")
                continue
        
        logger.info(f"Successfully loaded {len(documents)} documents")
        return documents

    def load_json_documents(self, *json_paths: str) -> List[Dict[str, Any]]:
        """
        Load pre-structured documents from one or more JSON files.

        Each JSON file must be a list of objects with 'content' and 'metadata' keys,
        which is the format produced by the data-pipeline extractors:
            visa_repo_docs.json, visa_code_docs.json, visa_issue_qa.json

        Args:
            *json_paths: One or more paths to JSON files. Non-existent paths are
                         skipped with a warning so partial loads still succeed.

        Returns:
            Combined list of document dicts from all supplied files.
        """
        import json

        all_documents: List[Dict[str, Any]] = []

        for json_path in json_paths:
            path = Path(json_path)
            if not path.exists():
                logger.warning(f"JSON file not found, skipping: {json_path}")
                continue

            try:
                with open(path, "r", encoding="utf-8") as f:
                    docs = json.load(f)

                if not isinstance(docs, list):
                    raise ValueError(f"Expected a JSON array, got {type(docs).__name__}")

                # Validate first few entries
                for i, doc in enumerate(docs[:3]):
                    if "content" not in doc or "metadata" not in doc:
                        raise ValueError(
                            f"{path.name}[{i}] is missing 'content' or 'metadata' keys"
                        )

                logger.info(f"Loaded {len(docs)} documents from {path.name}")
                all_documents.extend(docs)

            except Exception as e:
                logger.error(f"Error loading {json_path}: {e}")
                raise

        logger.info(f"Successfully loaded {len(all_documents)} documents from {len(json_paths)} JSON file(s)")
        return all_documents

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            metadata: Document metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        chunks = []
        text_length = len(text)
        
        # Handle empty or very short documents
        if text_length <= self.chunk_size:
            return [{
                "content": text,
                "metadata": {**metadata, "chunk_id": 0, "chunk_count": 1}
            }]
        
        # Create overlapping chunks
        start = 0
        chunk_id = 0
        
        while start < text_length:
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            # Try to break at sentence or word boundary (unless it's the last chunk)
            if end < text_length:
                # Look for sentence end (., !, ?) within last 100 chars
                for punct in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                    last_punct = chunk_text.rfind(punct)
                    if last_punct > self.chunk_size - 100:
                        chunk_text = chunk_text[:last_punct + 1]
                        break
                else:
                    # No sentence end found, try word boundary
                    last_space = chunk_text.rfind(' ')
                    if last_space > self.chunk_size - 50:
                        chunk_text = chunk_text[:last_space]
            
            chunk_metadata = {
                **metadata,
                "chunk_id": chunk_id,
                "start_char": start,
                "end_char": start + len(chunk_text)
            }
            
            chunks.append({
                "content": chunk_text.strip(),
                "metadata": chunk_metadata
            })
            
            # Move to next chunk with overlap
            start += self.chunk_size - self.chunk_overlap
            chunk_id += 1
        
        # Add total chunk count to all chunks
        for chunk in chunks:
            chunk["metadata"]["chunk_count"] = len(chunks)
        
        return chunks
    
    def process_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process documents into chunks
        
        Args:
            documents: List of documents to process
            
        Returns:
            List of all chunks from all documents
        """
        all_chunks = []
        
        for doc in documents:
            chunks = self.chunk_text(doc["content"], doc["metadata"])
            all_chunks.extend(chunks)
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(documents)} documents")
        return all_chunks


class ChromaDBIngestion:
    """Handle ChromaDB ingestion and vector storage"""
    
    def __init__(self, collection_name: str = None):
        """Initialize ChromaDB client and collection
        
        Args:
            collection_name: Override the target collection. Defaults to
                             CHROMA_COLLECTION_NAME env var if not specified.
        """
        self.persist_directory = settings.chroma_persist_directory
        self.collection_name = collection_name or settings.chroma_collection_name
        self.embedding_model_name = settings.embedding_model
        
        # Create persist directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Use singleton ChromaDB client to avoid conflicts
        self.client = get_chroma_client()
        
        # Load embedding model
        self.embedding_model = EmbeddingProvider()
        logger.info(f"ChromaDB initialized (persist_dir={self.persist_directory})")
    
    def get_or_create_collection(self, reset: bool = False):
        """
        Get or create ChromaDB collection
        
        Args:
            reset: If True, delete existing collection and create new one
            
        Returns:
            ChromaDB collection
        """
        if reset:
            try:
                self.client.delete_collection(name=self.collection_name)
                logger.info(f"Deleted existing collection: {self.collection_name}")
            except Exception as e:
                logger.debug(f"No existing collection to delete: {str(e)}")
        
        collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        
        logger.info(f"Collection ready: {self.collection_name} (count: {collection.count()})")
        return collection
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for text chunks
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        logger.info(f"Generating embeddings for {len(texts)} texts...")
        return self.embedding_model.encode(texts)
    
    def ingest_chunks(self, chunks: List[Dict[str, Any]], force_reingest: bool = False) -> Tuple[int, float]:
        """
        Ingest chunks into ChromaDB
        
        Args:
            chunks: List of chunk dictionaries
            force_reingest: If True, reset collection before ingestion
            
        Returns:
            Tuple of (chunks_added, time_elapsed)
        """
        start_time = time.time()
        
        # Get or create collection
        collection = self.get_or_create_collection(reset=force_reingest)
        
        # Check if collection already has documents
        if collection.count() > 0 and not force_reingest:
            logger.info(f"Collection already contains {collection.count()} documents. Skipping ingestion.")
            logger.info("Use force_reingest=True to re-ingest.")
            return 0, time.time() - start_time
        
        # Prepare data for ChromaDB
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        documents = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.generate_embeddings(documents)
        
        # Batch insert into ChromaDB
        logger.info(f"Inserting {len(chunks)} chunks into ChromaDB...")
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch_end = min(i + batch_size, len(chunks))
            collection.add(
                ids=ids[i:batch_end],
                documents=documents[i:batch_end],
                metadatas=metadatas[i:batch_end],
                embeddings=embeddings[i:batch_end]
            )
            logger.debug(f"Inserted batch {i//batch_size + 1} ({batch_end}/{len(chunks)})")
        
        elapsed_time = time.time() - start_time
        logger.info(f"Ingestion complete: {len(chunks)} chunks in {elapsed_time:.2f}s")
        
        return len(chunks), elapsed_time


def ingest_documents(document_path: str, force_reingest: bool = False) -> Dict[str, Any]:
    """
    Main ingestion function: Load, chunk, and store documents into FastAPI docs collection.

    Always targets the 'fastapi_docs' collection regardless of CHROMA_COLLECTION_NAME env var.
    (CHROMA_COLLECTION_NAME is only used as a query fallback default, not for ingestion routing.)
    
    Args:
        document_path: Path to documents directory
        force_reingest: If True, re-ingest even if documents exist
        
    Returns:
        Dictionary with ingestion statistics
    """
    try:
        # Initialize loader and ingestion — FastAPI docs always go into 'fastapi_docs'
        loader = DocumentLoader()
        ingestion = ChromaDBIngestion(collection_name="fastapi_docs")
        
        # Load documents
        documents = loader.load_documents(document_path)
        
        # Process into chunks
        chunks = loader.process_documents(documents)
        
        # Ingest into ChromaDB
        chunks_added, elapsed_time = ingestion.ingest_chunks(chunks, force_reingest)
        
        return {
            "status": "success",
            "documents_processed": len(documents),
            "chunks_created": len(chunks),
            "chunks_added": chunks_added,
            "time_elapsed": f"{elapsed_time:.2f}s"
        }
        
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "documents_processed": 0,
            "chunks_created": 0,
            "chunks_added": 0,
            "time_elapsed": "0s"
        }


def ingest_vcc_documents(
    repo_docs_path: str = None,
    code_docs_path: str = None,
    issue_qa_path: str = None,
    force_reingest: bool = True,
) -> Dict[str, Any]:
    """
    Load, chunk, and store VCC documentation into the 'vcc_docs' collection.

    Reads up to three JSON files produced by the data-pipeline extractors:
      - visa_repo_docs.json  — README, CONTRIBUTING, CHANGELOGs (53 docs)
      - visa_code_docs.json  — auto-generated API docs from source (210 docs)
      - visa_issue_qa.json   — GitHub issue Q&A pairs (13 docs)

    Missing files are skipped with a warning; at least one must exist.
    Always targets the 'vcc_docs' collection regardless of CHROMA_COLLECTION_NAME.

    Args:
        repo_docs_path: Path to visa_repo_docs.json (default: Docker path)
        code_docs_path: Path to visa_code_docs.json (default: Docker path)
        issue_qa_path:  Path to visa_issue_qa.json  (default: Docker path)
        force_reingest: If True, reset collection before ingestion

    Returns:
        Dictionary with ingestion statistics
    """
    # Default to paths baked into the Docker image
    repo_docs_path = repo_docs_path or "/app/data-pipeline/data/raw/visa_repo_docs.json"
    code_docs_path = code_docs_path or "/app/data-pipeline/data/raw/visa_code_docs.json"
    issue_qa_path  = issue_qa_path  or "/app/data-pipeline/data/raw/visa_issue_qa.json"

    try:
        loader    = DocumentLoader()
        ingestion = ChromaDBIngestion(collection_name="vcc_docs")

        # Load all JSON sources; non-existent paths are skipped with a warning
        documents = loader.load_json_documents(
            repo_docs_path,
            code_docs_path,
            issue_qa_path,
        )

        if not documents:
            raise FileNotFoundError(
                "No VCC documents found. Check that at least one JSON path exists."
            )

        chunks = loader.process_documents(documents)
        chunks_added, elapsed_time = ingestion.ingest_chunks(chunks, force_reingest)

        collection = ingestion.get_or_create_collection()
        return {
            "status": "success",
            "documents_processed": len(documents),
            "chunks_created": len(chunks),
            "chunks_added": chunks_added,
            "collection_count": collection.count(),
            "time_elapsed": f"{elapsed_time:.2f}s",
        }

    except Exception as e:
        logger.error(f"VCC ingestion failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "documents_processed": 0,
            "chunks_created": 0,
            "chunks_added": 0,
            "time_elapsed": "0s",
        }
