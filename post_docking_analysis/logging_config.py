"""
Logging configuration for post-docking analysis pipeline.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(log_file: Optional[str] = None, log_level: str = "INFO"):
    """
    Set up logging for the pipeline.
    
    Parameters
    ----------
    log_file : str, optional
        Path to log file
    log_level : str
        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create logger
    logger = logging.getLogger("post_docking_analysis")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger

def get_logger():
    """
    Get the configured logger.
    
    Returns
    -------
    logging.Logger
        Configured logger
    """
    return logging.getLogger("post_docking_analysis")

# Exception classes
class PostDockingAnalysisError(Exception):
    """Base exception for post-docking analysis errors."""
    pass

class ConfigurationError(PostDockingAnalysisError):
    """Exception raised for configuration errors."""
    pass

class FileProcessingError(PostDockingAnalysisError):
    """Exception raised for file processing errors."""
    pass

class AnalysisError(PostDockingAnalysisError):
    """Exception raised for analysis errors."""
    pass

class VisualizationError(PostDockingAnalysisError):
    """Exception raised for visualization errors."""
    pass

class PluginError(PostDockingAnalysisError):
    """Exception raised for plugin errors."""
    pass