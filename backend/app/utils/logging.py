"""
Logging Utilities
Centralized logging configuration and utilities for structured logging
"""

import logging
import sys
import time
from typing import Optional, Dict, Any
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log string with ANSI color codes
        """
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        # Format the message
        formatted = super().format(record)
        
        # Reset levelname for other handlers
        record.levelname = levelname
        
        return formatted


class RequestResponseLogger:
    """Utility for logging API requests and responses"""
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize request/response logger
        
        Args:
            logger: Logger instance to use
        """
        self.logger = logger
    
    def log_request(
        self,
        method: str,
        path: str,
        query_params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Log incoming API request
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            query_params: Query parameters dictionary
            body: Request body dictionary
            
        Returns:
            Timestamp for calculating latency
        """
        start_time = time.time()
        
        log_parts = [f"{method} {path}"]
        
        if query_params:
            log_parts.append(f"params={query_params}")
        
        if body:
            # Truncate body for logging
            body_preview = str(body)[:200]
            if len(str(body)) > 200:
                body_preview += "..."
            log_parts.append(f"body={body_preview}")
        
        self.logger.info(" | ".join(log_parts))
        
        return start_time
    
    def log_response(
        self,
        start_time: float,
        status_code: int,
        response_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Log API response with latency
        
        Args:
            start_time: Request start timestamp
            status_code: HTTP status code
            response_data: Response data dictionary
            error: Error message if request failed
        """
        latency_ms = (time.time() - start_time) * 1000
        
        log_parts = [f"Status: {status_code}", f"Latency: {latency_ms:.2f}ms"]
        
        if error:
            log_parts.append(f"Error: {error}")
        elif response_data:
            # Log response summary
            if isinstance(response_data, dict):
                keys = list(response_data.keys())
                log_parts.append(f"Response keys: {keys}")
        
        if status_code >= 500:
            self.logger.error(" | ".join(log_parts))
        elif status_code >= 400:
            self.logger.warning(" | ".join(log_parts))
        else:
            self.logger.info(" | ".join(log_parts))


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    use_colors: bool = True
) -> logging.Logger:
    """
    Setup centralized logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        use_colors: Whether to use colored output for console
        
    Returns:
        Configured root logger instance
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    if use_colors:
        console_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        console_handler.setFormatter(ColoredFormatter(console_format))
    else:
        console_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        console_handler.setFormatter(logging.Formatter(console_format))
    
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
        file_handler.setFormatter(logging.Formatter(file_format))
        logger.addHandler(file_handler)
        
        logger.info(f"Logging to file: {log_file}")
    
    logger.info(f"Logging configured (level={log_level})")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
