"""
Run all extractors and save to proper data directories.

This script runs:
1. Pillar 1: Repository Documentation Extractor
2. Pillar 2: Code Documentation Generator

And saves results to:
- data/raw/visa_repo_docs.json (Pillar 1)
- data/raw/visa_code_docs.json (Pillar 2)
"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from repo_docs_extractor import RepoDocsExtractor
from code_doc_generator import CodeDocGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_data_directories():
    """Create data directories if they don't exist."""
    data_dir = Path(__file__).parent.parent / 'data'
    raw_dir = data_dir / 'raw'
    processed_dir = data_dir / 'processed'
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Data directories ready: {raw_dir}")
    return raw_dir, processed_dir


def run_pillar1_repo_docs(raw_dir: Path, repo_path: str = '/tmp/visa-chart-components'):
    """Extract repository documentation (Pillar 1)."""
    logger.info("=" * 60)
    logger.info("PILLAR 1: Repository Documentation Extraction")
    logger.info("=" * 60)
    
    if not Path(repo_path).exists():
        logger.error(f"Repository not found at {repo_path}")
        logger.info("Please clone it first:")
        logger.info(f"  cd /tmp && git clone --depth=1 https://github.com/visa/visa-chart-components.git")
        return None
    
    extractor = RepoDocsExtractor(
        repo_url='https://github.com/visa/visa-chart-components',
        branch='main'
    )
    
    # Use existing cloned repo
    extractor.clone_path = Path(repo_path)
    
    # Find all documentation files
    logger.info(f"Searching for documentation in {repo_path}...")
    doc_files = extractor.find_documentation_files(extractor.clone_path)
    
    # Extract all documents
    logger.info(f"Extracting {len(doc_files)} documentation files...")
    documents = []
    for i, file_path in enumerate(doc_files, 1):
        if i % 10 == 0:
            logger.info(f"  Progress: {i}/{len(doc_files)}")
        
        try:
            doc = extractor.extract_document(file_path, extractor.clone_path)
            documents.append(doc)
        except Exception as e:
            logger.warning(f"Failed to extract {file_path}: {e}")
    
    # Save to file
    output_file = raw_dir / 'visa_repo_docs.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Saved {len(documents)} repository documents to {output_file}")
    
    # Print statistics
    packages = set()
    doc_types = {}
    for doc in documents:
        meta = doc['metadata']
        if meta.get('package'):
            packages.add(meta['package'])
        doc_type = meta.get('doc_type', 'unknown')
        doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
    
    logger.info(f"   Packages found: {len(packages)}")
    logger.info(f"   Doc types: {dict(doc_types)}")
    
    return documents


def run_pillar2_code_docs(raw_dir: Path, repo_path: str = '/tmp/visa-chart-components'):
    """Extract code documentation (Pillar 2)."""
    logger.info("\n" + "=" * 60)
    logger.info("PILLAR 2: Code Documentation Generation")
    logger.info("=" * 60)
    
    if not Path(repo_path).exists():
        logger.error(f"Repository not found at {repo_path}")
        return None
    
    generator = CodeDocGenerator(
        repo_path=repo_path,
        repo_name='visa/visa-chart-components'
    )
    
    # Extract API docs from all source files
    logger.info(f"Extracting API documentation from TypeScript files...")
    documents = generator.extract_all(max_files=None)  # Process all files
    
    # Save to file
    output_file = raw_dir / 'visa_code_docs.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Saved {len(documents)} API documentation entries to {output_file}")
    
    # Print statistics
    if documents:
        api_types = {}
        packages = set()
        for doc in documents:
            meta = doc['metadata']
            api_type = meta.get('api_type', 'unknown')
            api_types[api_type] = api_types.get(api_type, 0) + 1
            if meta.get('package'):
                packages.add(meta['package'])
        
        logger.info(f"   API types: {dict(api_types)}")
        logger.info(f"   Packages found: {len(packages)}")
    
    return documents


def generate_summary(raw_dir: Path, repo_docs: list, code_docs: list):
    """Generate extraction summary."""
    logger.info("\n" + "=" * 60)
    logger.info("EXTRACTION SUMMARY")
    logger.info("=" * 60)
    
    summary = {
        'extraction_time': datetime.utcnow().isoformat(),
        'repository': 'visa/visa-chart-components',
        'pillars': {
            'pillar1_repo_docs': {
                'count': len(repo_docs) if repo_docs else 0,
                'output_file': 'data/raw/visa_repo_docs.json',
                'description': 'Repository documentation (.md files)'
            },
            'pillar2_code_docs': {
                'count': len(code_docs) if code_docs else 0,
                'output_file': 'data/raw/visa_code_docs.json',
                'description': 'API documentation (TypeScript interfaces)'
            }
        },
        'total_documents': (len(repo_docs) if repo_docs else 0) + (len(code_docs) if code_docs else 0)
    }
    
    # Save summary
    summary_file = raw_dir / 'extraction_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"\n📊 Total documents extracted: {summary['total_documents']}")
    logger.info(f"   - Repository docs: {summary['pillars']['pillar1_repo_docs']['count']}")
    logger.info(f"   - Code docs: {summary['pillars']['pillar2_code_docs']['count']}")
    logger.info(f"\n📁 Files saved in: {raw_dir}/")
    logger.info(f"   - visa_repo_docs.json")
    logger.info(f"   - visa_code_docs.json")
    logger.info(f"   - extraction_summary.json")


def main():
    """Main extraction pipeline."""
    print("\n" + "=" * 60)
    print("VISA CHART COMPONENTS - DATA EXTRACTION PIPELINE")
    print("=" * 60)
    print()
    
    # Setup directories
    raw_dir, processed_dir = setup_data_directories()
    
    # Run Pillar 1: Repository Documentation
    repo_docs = run_pillar1_repo_docs(raw_dir)
    
    # Run Pillar 2: Code Documentation
    code_docs = run_pillar2_code_docs(raw_dir)
    
    # Generate summary
    if repo_docs or code_docs:
        generate_summary(raw_dir, repo_docs or [], code_docs or [])
        print("\n✅ Extraction complete!")
    else:
        print("\n❌ Extraction failed - no documents extracted")


if __name__ == '__main__':
    main()
