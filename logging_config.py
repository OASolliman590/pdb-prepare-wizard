#!/usr/bin/env python3
"""
Logging Configuration Module
=============================

Provides standardized logging configuration for the entire pipeline.
Replaces ad-hoc print statements with proper logging infrastructure.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import json


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to console output.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    # Unicode symbols for visual hierarchy
    SYMBOLS = {
        'DEBUG': '🔍',
        'INFO': '✓',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🔥',
    }

    def format(self, record):
        """Format log record with colors and symbols."""
        # Add color
        if record.levelname in self.COLORS:
            record.levelname_colored = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname}{self.RESET}"
            )
            record.symbol = self.SYMBOLS.get(record.levelname, '')
        else:
            record.levelname_colored = record.levelname
            record.symbol = ''

        return super().format(record)


class ProgressFormatter(logging.Formatter):
    """
    Formatter for progress messages with step tracking.
    """

    def __init__(self, *args, show_progress=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_progress = show_progress
        self.step_count = 0

    def format(self, record):
        """Format with step numbers for progress tracking."""
        if self.show_progress and record.levelname == 'INFO':
            self.step_count += 1
            record.step = f"[{self.step_count}]"
        else:
            record.step = ""

        return super().format(record)


class PipelineLogger:
    """
    Centralized logger configuration for the pipeline.
    """

    def __init__(
        self,
        name: str = "pdb_prepare_wizard",
        log_file: Optional[Path] = None,
        level: str = "INFO",
        console_output: bool = True,
        file_output: bool = True,
        use_colors: bool = True,
        show_progress: bool = True
    ):
        """
        Initialize pipeline logger.

        Args:
            name: Logger name
            log_file: Path to log file (auto-generated if None)
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console_output: Enable console logging
            file_output: Enable file logging
            use_colors: Use colored output for console
            show_progress: Show step numbers for progress tracking
        """
        self.name = name
        self.level = getattr(logging, level.upper())
        self.console_output = console_output
        self.file_output = file_output
        self.use_colors = use_colors and sys.stdout.isatty()
        self.show_progress = show_progress

        # Generate log file path if not provided
        if log_file is None and file_output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            self.log_file = log_dir / f"{name}_{timestamp}.log"
        else:
            self.log_file = Path(log_file) if log_file else None

        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        self.logger.handlers.clear()  # Remove existing handlers

        # Setup handlers
        self._setup_handlers()

        # Log initial message
        self.logger.info(f"Logger initialized: {name}")
        if self.log_file:
            self.logger.info(f"Log file: {self.log_file}")

    def _setup_handlers(self):
        """Setup console and file handlers with appropriate formatters."""

        # Console handler
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.level)

            if self.use_colors:
                console_format = (
                    "%(symbol)s %(levelname_colored)s%(step)s: %(message)s"
                )
                console_formatter = ColoredFormatter(console_format)
                if self.show_progress:
                    console_formatter = type('ProgressColoredFormatter',
                                            (ProgressFormatter, ColoredFormatter), {})(
                        console_format, show_progress=True
                    )
            else:
                console_format = "%(levelname)s%(step)s: %(message)s"
                console_formatter = ProgressFormatter(
                    console_format, show_progress=self.show_progress
                )

            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        # File handler
        if self.file_output and self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file

            file_format = (
                "%(asctime)s | %(name)s | %(levelname)-8s | "
                "%(filename)s:%(lineno)d | %(message)s"
            )
            file_formatter = logging.Formatter(
                file_format,
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger

    def set_level(self, level: str):
        """Change logging level dynamically."""
        new_level = getattr(logging, level.upper())
        self.logger.setLevel(new_level)
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(new_level)
        self.logger.info(f"Log level changed to {level}")

    def add_metadata(self, **kwargs):
        """
        Add metadata to log file (config, environment, etc.).
        """
        if self.log_file:
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'logger_name': self.name,
                'log_level': logging.getLevelName(self.level),
                **kwargs
            }

            with open(self.log_file.parent / f"{self.log_file.stem}_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)


# Global logger instance
_global_logger: Optional[logging.Logger] = None


def setup_logger(
    name: str = "pdb_prepare_wizard",
    level: str = "INFO",
    log_file: Optional[Path] = None,
    verbose: bool = False,
    quiet: bool = False,
    **kwargs
) -> logging.Logger:
    """
    Setup and return a configured logger.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        verbose: Enable verbose output (DEBUG level)
        quiet: Suppress console output except errors
        **kwargs: Additional arguments for PipelineLogger

    Returns:
        Configured logger instance
    """
    global _global_logger

    # Adjust level based on flags
    if verbose:
        level = "DEBUG"
    elif quiet:
        level = "ERROR"

    pipeline_logger = PipelineLogger(
        name=name,
        level=level,
        log_file=log_file,
        console_output=not quiet,
        **kwargs
    )

    _global_logger = pipeline_logger.get_logger()
    return _global_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get logger instance. Creates default logger if not initialized.

    Args:
        name: Logger name (uses global logger if None)

    Returns:
        Logger instance
    """
    global _global_logger

    if name:
        return logging.getLogger(name)

    if _global_logger is None:
        _global_logger = setup_logger()

    return _global_logger


def log_section(title: str, logger: Optional[logging.Logger] = None):
    """
    Log a section header for better organization.

    Args:
        title: Section title
        logger: Logger instance (uses global if None)
    """
    if logger is None:
        logger = get_logger()

    separator = "=" * 60
    logger.info(separator)
    logger.info(f"  {title}")
    logger.info(separator)


def log_step(step_num: int, description: str, logger: Optional[logging.Logger] = None):
    """
    Log a numbered step in a process.

    Args:
        step_num: Step number
        description: Step description
        logger: Logger instance (uses global if None)
    """
    if logger is None:
        logger = get_logger()

    logger.info(f"Step {step_num}: {description}")


def log_result(key: str, value, logger: Optional[logging.Logger] = None):
    """
    Log a key-value result.

    Args:
        key: Result key
        value: Result value
        logger: Logger instance (uses global if None)
    """
    if logger is None:
        logger = get_logger()

    logger.info(f"  {key}: {value}")


def log_file_operation(operation: str, file_path: str,
                       success: bool = True,
                       logger: Optional[logging.Logger] = None):
    """
    Log a file operation.

    Args:
        operation: Operation type (read, write, delete, etc.)
        file_path: Path to file
        success: Whether operation succeeded
        logger: Logger instance (uses global if None)
    """
    if logger is None:
        logger = get_logger()

    status = "✓" if success else "✗"
    level = logging.INFO if success else logging.ERROR
    logger.log(level, f"{status} {operation}: {file_path}")


# Context manager for timed operations
class LogTimer:
    """
    Context manager for timing operations.
    """

    def __init__(self, operation: str, logger: Optional[logging.Logger] = None):
        """
        Initialize timer.

        Args:
            operation: Operation description
            logger: Logger instance
        """
        self.operation = operation
        self.logger = logger or get_logger()
        self.start_time = None

    def __enter__(self):
        """Start timing."""
        self.logger.info(f"🔄 Starting: {self.operation}")
        self.start_time = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log duration."""
        duration = (datetime.now() - self.start_time).total_seconds()

        if exc_type is None:
            self.logger.info(f"✓ Completed: {self.operation} ({duration:.2f}s)")
        else:
            self.logger.error(f"✗ Failed: {self.operation} ({duration:.2f}s)")
            self.logger.exception(f"Exception: {exc_val}")

        return False  # Don't suppress exceptions


if __name__ == "__main__":
    # Example usage
    print("=== Logging System Demo ===\n")

    # Setup logger
    logger = setup_logger(name="demo", level="DEBUG", verbose=True)

    # Section logging
    log_section("Pipeline Initialization", logger)
    logger.debug("Debug message - detailed information")
    logger.info("Info message - normal operation")
    logger.warning("Warning message - something to note")
    logger.error("Error message - something failed")

    # Step logging
    log_section("Processing Steps", logger)
    log_step(1, "Download PDB file", logger)
    log_step(2, "Validate structure", logger)
    log_step(3, "Extract ligands", logger)

    # Result logging
    log_section("Results", logger)
    log_result("PDB ID", "7CMD", logger)
    log_result("Ligands found", 3, logger)
    log_result("Binding affinity", -9.5, logger)

    # File operations
    log_section("File Operations", logger)
    log_file_operation("write", "/tmp/output.pdb", True, logger)
    log_file_operation("read", "/tmp/missing.pdb", False, logger)

    # Timed operation
    log_section("Timed Operations", logger)
    import time
    with LogTimer("Heavy computation", logger):
        time.sleep(1)

    print("\n✓ Log file created at: logs/demo_*.log")
