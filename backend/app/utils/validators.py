"""
Input Validation Utilities
Validators for API inputs, files, and data structures
"""

import re
from typing import Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class QueryValidator:
    """Validate user queries and inputs"""
    
    # Query length constraints
    MIN_QUERY_LENGTH = 3
    MAX_QUERY_LENGTH = 1000
    
    # Patterns for detection
    SPECIAL_CHAR_PATTERN = re.compile(r'[<>{}\\]')
    REPEATED_CHAR_PATTERN = re.compile(r'(.)\1{10,}')  # 10+ repeated chars
    
    @classmethod
    def validate_query(cls, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate user query
        
        Args:
            query: User query text
            
        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, error_message) if invalid
        """
        # Check if query is empty or None
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        query = query.strip()
        
        # Check length
        if len(query) < cls.MIN_QUERY_LENGTH:
            return False, f"Query too short (min {cls.MIN_QUERY_LENGTH} characters)"
        
        if len(query) > cls.MAX_QUERY_LENGTH:
            return False, f"Query too long (max {cls.MAX_QUERY_LENGTH} characters)"
        
        # Check for suspicious patterns
        if cls.SPECIAL_CHAR_PATTERN.search(query):
            logger.warning(f"Query contains suspicious characters: {query[:50]}")
            # Don't reject, just log
        
        # Check for spam (repeated characters)
        if cls.REPEATED_CHAR_PATTERN.search(query):
            return False, "Query contains repeated characters (possible spam)"
        
        return True, None
    
    @classmethod
    def sanitize_query(cls, query: str) -> str:
        """
        Sanitize user query
        
        Args:
            query: Raw user query
            
        Returns:
            Sanitized query string
        """
        # Strip whitespace
        query = query.strip()
        
        # Remove null bytes
        query = query.replace('\x00', '')
        
        # Normalize whitespace
        query = ' '.join(query.split())
        
        return query


class FileValidator:
    """Validate file paths and file operations"""
    
    ALLOWED_EXTENSIONS = {'.md', '.txt', '.json'}
    MAX_FILE_SIZE_MB = 10
    
    @classmethod
    def validate_document_path(cls, path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate document directory path
        
        Args:
            path: Path to documents directory
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            doc_path = Path(path)
            
            # Check if path exists
            if not doc_path.exists():
                return False, f"Path does not exist: {path}"
            
            # Check if it's a directory
            if not doc_path.is_dir():
                return False, f"Path is not a directory: {path}"
            
            # Check for markdown files
            md_files = list(doc_path.rglob("*.md"))
            if not md_files:
                return False, f"No markdown files found in: {path}"
            
            logger.info(f"Valid document path: {path} ({len(md_files)} .md files)")
            return True, None
            
        except Exception as e:
            return False, f"Invalid path: {str(e)}"
    
    @classmethod
    def validate_file_extension(cls, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file extension
        
        Args:
            file_path: Path to file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        extension = Path(file_path).suffix.lower()
        
        if extension not in cls.ALLOWED_EXTENSIONS:
            return False, f"Invalid file extension: {extension} (allowed: {cls.ALLOWED_EXTENSIONS})"
        
        return True, None
    
    @classmethod
    def validate_file_size(cls, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file size
        
        Args:
            file_path: Path to file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            file_size_bytes = Path(file_path).stat().st_size
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            if file_size_mb > cls.MAX_FILE_SIZE_MB:
                return False, f"File too large: {file_size_mb:.2f}MB (max {cls.MAX_FILE_SIZE_MB}MB)"
            
            return True, None
            
        except Exception as e:
            return False, f"Cannot check file size: {str(e)}"


class ConfigValidator:
    """Validate configuration values"""
    
    @classmethod
    def validate_chunk_size(cls, chunk_size: int, chunk_overlap: int) -> Tuple[bool, Optional[str]]:
        """
        Validate chunking configuration
        
        Args:
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if chunk_size <= 0:
            return False, "Chunk size must be positive"
        
        if chunk_overlap < 0:
            return False, "Chunk overlap cannot be negative"
        
        if chunk_overlap >= chunk_size:
            return False, "Chunk overlap must be less than chunk size"
        
        if chunk_size > 10000:
            logger.warning(f"Very large chunk size: {chunk_size}")
        
        return True, None
    
    @classmethod
    def validate_top_k(cls, top_k: int) -> Tuple[bool, Optional[str]]:
        """
        Validate top-k retrieval parameter
        
        Args:
            top_k: Number of results to retrieve
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if top_k <= 0:
            return False, "top_k must be positive"
        
        if top_k > 20:
            return False, "top_k too large (max 20)"
        
        return True, None
    
    @classmethod
    def validate_relevance_threshold(cls, threshold: float) -> Tuple[bool, Optional[str]]:
        """
        Validate retrieval relevance threshold
        
        Args:
            threshold: Relevance threshold value
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not 0.0 <= threshold <= 1.0:
            return False, "Relevance threshold must be between 0.0 and 1.0"
        
        return True, None


def validate_and_sanitize_query(query: str) -> Tuple[str, Optional[str]]:
    """
    Validate and sanitize a user query (convenience function)
    
    Args:
        query: Raw user query
        
    Returns:
        Tuple of (sanitized_query, error_message)
        - (sanitized_query, None) if valid
        - (original_query, error_message) if invalid
    """
    # Sanitize first
    sanitized = QueryValidator.sanitize_query(query)
    
    # Then validate
    is_valid, error = QueryValidator.validate_query(sanitized)
    
    if not is_valid:
        return query, error
    
    return sanitized, None
