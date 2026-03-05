"""
Quick test of repo_docs_extractor with pre-cloned repository
"""

from pathlib import Path
from repo_docs_extractor import RepoDocsExtractor
import json

def test_with_existing_repo():
    """Test extractor with already-cloned repo"""
    
    # Path to the repo we just cloned
    repo_path = Path("/tmp/visa-chart-components")
    
    if not repo_path.exists():
        print("❌ Repository not found at /tmp/visa-chart-components")
        print("Please clone it first:")
        print("  cd /tmp && git clone --depth=1 https://github.com/visa/visa-chart-components.git")
        return
    
    print(f"📂 Using existing repo at: {repo_path}")
    
    # Create extractor (won't clone, we'll use existing)
    extractor = RepoDocsExtractor(
        repo_url="https://github.com/visa/visa-chart-components",
        branch="main"
    )
    
    # Manually set clone_path to existing repo
    extractor.clone_path = repo_path
    
    # Find documentation files
    print("\n🔍 Finding documentation files...")
    doc_files = extractor.find_documentation_files(repo_path)
    print(f"✅ Found {len(doc_files)} documentation files")
    
    # Extract first 10 documents
    print("\n📄 Extracting documents...")
    documents = []
    for file_path in doc_files[:10]:  # Just first 10 for testing
        doc = extractor.extract_document(file_path, repo_path)
        if doc:
            documents.append(doc)
    
    print(f"✅ Extracted {len(documents)} documents\n")
    
    # Show summary
    print("=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    
    for i, doc in enumerate(documents, 1):
        meta = doc['metadata']
        print(f"\n{i}. {meta['file_name']}")
        print(f"   Path: {meta['file_path']}")
        print(f"   Type: {meta['doc_type']}")
        print(f"   Size: {meta['file_size_bytes']} bytes")
        if 'package' in meta:
            print(f"   Package: {meta['package']}")
        print(f"   Content: {doc['content'][:100].strip()}...")
    
    # Save to JSON
    output_dir = Path(__file__).parent.parent / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "visa_repo_docs_sample.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n💾 Saved {len(documents)} documents to:")
    print(f"   {output_path}")
    
    # Statistics
    total_files = len(doc_files)
    print(f"\n📊 Statistics:")
    print(f"   Total .md files found: {total_files}")
    print(f"   Extracted (sample): {len(documents)}")
    print(f"   Package READMEs: {sum(1 for d in documents if 'package' in d['metadata'])}")
    print(f"   Root docs: {sum(1 for d in documents if 'packages' not in d['metadata']['file_path'])}")

if __name__ == "__main__":
    test_with_existing_repo()
