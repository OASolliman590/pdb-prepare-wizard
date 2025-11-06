#!/usr/bin/env python3
"""
Custom Exceptions Module
========================

Provides specific exception classes for better error handling and debugging.
"""

import logging

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Base exception for all pipeline errors."""
    pass


class NetworkError(PipelineError):
    """Exception raised for network-related errors."""
    pass


class PDBDownloadError(NetworkError):
    """Exception raised when PDB download fails."""

    def __init__(self, pdb_id: str, message: str = None):
        self.pdb_id = pdb_id
        self.message = message or f"Failed to download PDB {pdb_id}"
        super().__init__(self.message)


class ValidationError(PipelineError):
    """Exception raised when validation fails."""
    pass


class FileFormatError(ValidationError):
    """Exception raised when file format is invalid."""

    def __init__(self, file_path: str, format_type: str, reason: str):
        self.file_path = file_path
        self.format_type = format_type
        self.reason = reason
        message = f"Invalid {format_type.upper()} file: {file_path}\nReason: {reason}"
        super().__init__(message)


class LigandError(PipelineError):
    """Exception raised for ligand-related errors."""
    pass


class LigandNotFoundError(LigandError):
    """Exception raised when ligand cannot be found."""

    def __init__(self, ligand_name: str, chain_id: str, res_id: int):
        self.ligand_name = ligand_name
        self.chain_id = chain_id
        self.res_id = res_id
        message = f"Ligand not found: {ligand_name} chain {chain_id} residue {res_id}"
        super().__init__(message)


class StructureError(PipelineError):
    """Exception raised for structure-related errors."""
    pass


class MissingAtomsError(StructureError):
    """Exception raised when required atoms are missing."""

    def __init__(self, file_path: str, atom_type: str = "ATOM/HETATM"):
        self.file_path = file_path
        self.atom_type = atom_type
        message = f"No {atom_type} records found in structure: {file_path}"
        super().__init__(message)


class CoordinateError(StructureError):
    """Exception raised for coordinate-related errors."""

    def __init__(self, message: str, line_number: int = None):
        self.line_number = line_number
        if line_number:
            message = f"Line {line_number}: {message}"
        super().__init__(message)


class AnalysisError(PipelineError):
    """Exception raised for analysis failures."""
    pass


class PocketAnalysisError(AnalysisError):
    """Exception raised when pocket analysis fails."""

    def __init__(self, reason: str):
        self.reason = reason
        message = f"Pocket analysis failed: {reason}"
        super().__init__(message)


class InteractionAnalysisError(AnalysisError):
    """Exception raised when interaction analysis fails."""

    def __init__(self, method: str, reason: str):
        self.method = method
        self.reason = reason
        message = f"Interaction analysis failed ({method}): {reason}"
        super().__init__(message)


class ConfigurationError(PipelineError):
    """Exception raised for configuration errors."""
    pass


class InvalidParameterError(ConfigurationError):
    """Exception raised when parameter value is invalid."""

    def __init__(self, parameter: str, value, reason: str):
        self.parameter = parameter
        self.value = value
        self.reason = reason
        message = f"Invalid parameter '{parameter}' = {value}: {reason}"
        super().__init__(message)


class DependencyError(PipelineError):
    """Exception raised when required dependency is missing."""

    def __init__(self, dependency: str, feature: str = None):
        self.dependency = dependency
        self.feature = feature
        if feature:
            message = f"Missing dependency '{dependency}' required for {feature}"
        else:
            message = f"Missing required dependency: {dependency}"
        message += f"\nInstall with: pip install {dependency}"
        super().__init__(message)


class OutputError(PipelineError):
    """Exception raised for output-related errors."""
    pass


class OutputWriteError(OutputError):
    """Exception raised when output file cannot be written."""

    def __init__(self, file_path: str, reason: str):
        self.file_path = file_path
        self.reason = reason
        message = f"Cannot write output file {file_path}: {reason}"
        super().__init__(message)


class CheckpointError(PipelineError):
    """Exception raised for checkpoint/resume errors."""
    pass


class CheckpointNotFoundError(CheckpointError):
    """Exception raised when checkpoint file is not found."""

    def __init__(self, checkpoint_path: str):
        self.checkpoint_path = checkpoint_path
        message = f"Checkpoint not found: {checkpoint_path}"
        super().__init__(message)


class ResourceError(PipelineError):
    """Exception raised for resource-related errors."""
    pass


class InsufficientDiskSpaceError(ResourceError):
    """Exception raised when disk space is insufficient."""

    def __init__(self, required_mb: float, available_mb: float, path: str):
        self.required_mb = required_mb
        self.available_mb = available_mb
        self.path = path
        message = (
            f"Insufficient disk space at {path}\n"
            f"Required: {required_mb:.1f} MB, Available: {available_mb:.1f} MB"
        )
        super().__init__(message)


class MemoryError(ResourceError):
    """Exception raised when memory is insufficient."""

    def __init__(self, required_mb: float, available_mb: float):
        self.required_mb = required_mb
        self.available_mb = available_mb
        message = (
            f"Insufficient memory\n"
            f"Required: {required_mb:.1f} MB, Available: {available_mb:.1f} MB"
        )
        super().__init__(message)


def log_exception(exc: Exception, logger_instance: logging.Logger = None):
    """
    Log exception with full stack trace.

    Args:
        exc: Exception to log
        logger_instance: Logger to use (defaults to module logger)
    """
    if logger_instance is None:
        logger_instance = logger

    logger_instance.exception(f"Exception occurred: {type(exc).__name__}: {exc}")


def handle_pipeline_error(exc: Exception, context: str = "") -> bool:
    """
    Centralized error handler for pipeline errors.

    Args:
        exc: Exception that occurred
        context: Context string describing where error occurred

    Returns:
        True if error was handled, False if it should propagate
    """
    if context:
        logger.error(f"Error in {context}")

    if isinstance(exc, PipelineError):
        # Our custom exceptions - log and handle
        logger.error(f"{type(exc).__name__}: {exc}")
        logger.exception("Stack trace:")
        return True
    elif isinstance(exc, (KeyboardInterrupt, SystemExit)):
        # Don't suppress user interrupts
        logger.info("Pipeline interrupted by user")
        return False
    else:
        # Unknown exception - log with full trace
        logger.exception(f"Unexpected error: {exc}")
        return False


# Exception hierarchy for reference:
#
# PipelineError (base)
# ├── NetworkError
# │   └── PDBDownloadError
# ├── ValidationError
# │   └── FileFormatError
# ├── LigandError
# │   └── LigandNotFoundError
# ├── StructureError
# │   ├── MissingAtomsError
# │   └── CoordinateError
# ├── AnalysisError
# │   ├── PocketAnalysisError
# │   └── InteractionAnalysisError
# ├── ConfigurationError
# │   ├── InvalidParameterError
# │   └── DependencyError
# ├── OutputError
# │   └── OutputWriteError
# ├── CheckpointError
# │   └── CheckpointNotFoundError
# └── ResourceError
#     ├── InsufficientDiskSpaceError
#     └── MemoryError


if __name__ == "__main__":
    # Example usage
    import sys

    logging.basicConfig(level=logging.INFO)

    print("=== Exception Examples ===\n")

    # Example 1: PDB Download Error
    try:
        raise PDBDownloadError("1ABC", "Network timeout")
    except PDBDownloadError as e:
        print(f"Caught: {e}")
        print(f"PDB ID: {e.pdb_id}\n")

    # Example 2: File Format Error
    try:
        raise FileFormatError("/path/to/file.pdb", "PDB", "No ATOM records found")
    except FileFormatError as e:
        print(f"Caught: {e}")
        print(f"File: {e.file_path}, Format: {e.format_type}\n")

    # Example 3: Ligand Not Found
    try:
        raise LigandNotFoundError("ATP", "A", 500)
    except LigandNotFoundError as e:
        print(f"Caught: {e}")
        print(f"Ligand: {e.ligand_name}, Chain: {e.chain_id}, Res: {e.res_id}\n")

    # Example 4: Using error handler
    try:
        raise InvalidParameterError("cutoff", -5.0, "Must be positive")
    except Exception as e:
        handled = handle_pipeline_error(e, context="parameter validation")
        print(f"Error handled: {handled}\n")

    print("=== Exception Hierarchy ===")
    print("PipelineError")
    print("  └─ NetworkError → PDBDownloadError")
    print("  └─ ValidationError → FileFormatError")
    print("  └─ LigandError → LigandNotFoundError")
    print("  └─ StructureError → MissingAtomsError, CoordinateError")
    print("  └─ AnalysisError → PocketAnalysisError, InteractionAnalysisError")
    print("  └─ ConfigurationError → InvalidParameterError, DependencyError")
    print("  └─ OutputError → OutputWriteError")
    print("  └─ CheckpointError → CheckpointNotFoundError")
    print("  └─ ResourceError → InsufficientDiskSpaceError, MemoryError")
