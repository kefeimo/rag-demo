"""
Repository Documentation Extractor (Pillar 1)
Clones git repositories and extracts documentation files (.md, .rst, .txt)
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RepoDocsExtractor:
    """Extract documentation files from git repositories"""
    
    # File extensions to extract
    DOC_EXTENSIONS = {'.md', '.rst', '.txt', '.markdown'}
    
    # Directories to exclude (performance optimization)
    EXCLUDE_DIRS = {
        'node_modules', 'venv', 'env', '.venv', '__pycache__', 
        '.git', '.github', 'dist', 'build', 'target', '.next',
        'coverage', '.pytest_cache', '.tox', 'htmlcov'
    }
    
    def __init__(self, repo_url: str, branch: str = "main", temp_dir: Optional[str] = None):
        """
        Initialize repository documentation extractor
        
        Args:
            repo_url: GitHub repository URL (e.g., https://github.com/visa/visa-chart-components)
            branch: Branch to clone (default: main)
            temp_dir: Optional temporary directory for cloning (auto-created if None)
        """
        self.repo_url = repo_url
        self.branch = branch
        self.temp_dir = temp_dir
        self.repo_name = self._extract_repo_name(repo_url)
        self.clone_path: Optional[Path] = None
        
    def _extract_repo_name(self, url: str) -> str:
        """Extract repository name from URL"""
        # Example: https://github.com/visa/visa-chart-components -> visa/visa-chart-components
        parts = url.rstrip('/').split('/')
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1].replace('.git', '')}"
        return parts[-1].replace('.git', '')
    
    def clone_repository(self) -> Path:
        """
        Clone repository using shallow clone for performance
        
        Returns:
            Path to cloned repository
        """
        if self.temp_dir:
            clone_dir = Path(self.temp_dir)
            clone_dir.mkdir(parents=True, exist_ok=True)
        else:
            clone_dir = Path(tempfile.mkdtemp(prefix='repo_extract_'))
        
        self.clone_path = clone_dir / self.repo_name.split('/')[-1]
        
        logger.info(f"Cloning {self.repo_url} (branch: {self.branch}) to {self.clone_path}")
        
        try:
            # Shallow clone for performance (only latest commit)
            cmd = [
                'git', 'clone',
                '--depth=1',
                '--branch', self.branch,
                '--single-branch',
                self.repo_url,
                str(self.clone_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Git clone failed: {result.stderr}")
            
            logger.info(f"Successfully cloned repository to {self.clone_path}")
            return self.clone_path
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Git clone timed out after 5 minutes")
        except Exception as e:
            logger.error(f"Failed to clone repository: {str(e)}")
            raise
    
    def find_documentation_files(self, repo_path: Path) -> List[Path]:
        """
        Recursively find all documentation files in repository
        
        Args:
            repo_path: Path to cloned repository
            
        Returns:
            List of paths to documentation files
        """
        doc_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in self.DOC_EXTENSIONS:
                    doc_files.append(file_path)
        
        logger.info(f"Found {len(doc_files)} documentation files")
        return doc_files
    
    def _get_git_commit_hash(self, repo_path: Path) -> str:
        """Get current commit hash"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()[:8]  # Short hash
        except Exception:
            return "unknown"
    
    def _generate_doc_id(self, content: str) -> str:
        """Generate unique document ID using content hash"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def extract_document(self, file_path: Path, repo_path: Path) -> Dict[str, Any]:
        """
        Extract content and metadata from a documentation file
        
        Args:
            file_path: Path to documentation file
            repo_path: Root path of repository (for relative path calculation)
            
        Returns:
            Dictionary with content and metadata
        """
        try:
            # Read file with encoding detection
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Fallback to latin-1 if UTF-8 fails
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            
            # Calculate relative path from repo root
            relative_path = file_path.relative_to(repo_path)
            
            # Extract metadata
            metadata = {
                "source": "repo_docs",
                "repo_name": self.repo_name,
                "file_path": str(relative_path),
                "file_name": file_path.name,
                "file_extension": file_path.suffix,
                "file_size_bytes": file_path.stat().st_size,
                "commit_hash": self._get_git_commit_hash(repo_path),
                "branch": self.branch,
                "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                "extracted_at": datetime.now().isoformat(),
                "doc_id": self._generate_doc_id(content),
                "doc_type": "readme" if "readme" in file_path.name.lower() else "documentation",
                "audience": "external",  # Default to external, can be refined later
            }
            
            # Detect if it's a package-specific README
            if "packages" in str(relative_path) and "README" in file_path.name:
                parts = str(relative_path).split(os.sep)
                if len(parts) >= 2 and parts[0] == "packages":
                    metadata["package"] = parts[1]
                    metadata["component_type"] = "chart"  # Visa Chart Components specific
            
            return {
                "content": content,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to extract {file_path}: {str(e)}")
            return None
    
    def extract_all(self, cleanup: bool = True) -> List[Dict[str, Any]]:
        """
        Extract all documentation from repository
        
        Args:
            cleanup: Whether to delete cloned repository after extraction
            
        Returns:
            List of extracted documents with content and metadata
        """
        documents = []
        
        try:
            # Clone repository
            repo_path = self.clone_repository()
            
            # Find all documentation files
            doc_files = self.find_documentation_files(repo_path)
            
            # Extract each file
            for file_path in doc_files:
                doc = self.extract_document(file_path, repo_path)
                if doc:
                    documents.append(doc)
            
            logger.info(f"Successfully extracted {len(documents)} documents from {self.repo_name}")
            
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            raise
        
        finally:
            # Cleanup cloned repository if requested
            if cleanup and self.clone_path and self.clone_path.exists():
                import shutil
                shutil.rmtree(self.clone_path, ignore_errors=True)
                logger.info(f"Cleaned up cloned repository at {self.clone_path}")
        
        return documents


def main():
    """Example usage"""
    import json
    
    # Extract from Visa Chart Components
    extractor = RepoDocsExtractor(
        repo_url="https://github.com/visa/visa-chart-components",
        branch="main"
    )
    
    # Extract all documentation
    documents = extractor.extract_all(cleanup=False)  # Keep repo for debugging
    
    # Print summary
    print(f"\n✅ Extracted {len(documents)} documents")
    print(f"Repository: {extractor.repo_name}")
    print(f"Clone path: {extractor.clone_path}")
    
    # Show first 3 documents
    for i, doc in enumerate(documents[:3], 1):
        print(f"\n--- Document {i} ---")
        print(f"File: {doc['metadata']['file_path']}")
        print(f"Type: {doc['metadata']['doc_type']}")
        print(f"Size: {doc['metadata']['file_size_bytes']} bytes")
        if 'package' in doc['metadata']:
            print(f"Package: {doc['metadata']['package']}")
        print(f"Content preview: {doc['content'][:200]}...")
    
    # Save to JSON for inspection
    output_path = Path(__file__).parent.parent / "data" / "raw" / "repo_docs.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved to {output_path}")


if __name__ == "__main__":
    main()
