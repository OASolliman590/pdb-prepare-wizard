#!/usr/bin/env python3
"""
Security Utilities Module
=========================

Provides security functions for input sanitization and safe file operations.
Prevents command injection, path traversal, and other security vulnerabilities.
"""

import os
import re
import shlex
from pathlib import Path
from typing import List, Union, Optional
import logging

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Exception raised when security validation fails."""
    pass


class SecurityValidator:
    """
    Validates inputs and file paths for security concerns.
    """

    # Allowed characters for PDB IDs (alphanumeric only)
    PDB_ID_PATTERN = re.compile(r'^[A-Za-z0-9]{4}$')

    # Dangerous patterns that might indicate command injection
    DANGEROUS_PATTERNS = [
        r'[;&|`$]',  # Shell metacharacters
        r'\$\(',     # Command substitution
        r'\.\.',     # Path traversal
        r'~',        # Home directory expansion
        r'[\r\n]',   # Newlines (command injection)
    ]

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        'pdb', 'pdbqt', 'sdf', 'mol2', 'mol', 'xyz',
        'csv', 'xlsx', 'json', 'txt', 'log'
    }

    @staticmethod
    def validate_pdb_id(pdb_id: str) -> str:
        """
        Validate PDB ID format and sanitize.

        Args:
            pdb_id: PDB identifier to validate

        Returns:
            Sanitized PDB ID

        Raises:
            SecurityError: If PDB ID is invalid or suspicious
        """
        if not pdb_id:
            raise SecurityError("PDB ID cannot be empty")

        if len(pdb_id) != 4:
            raise SecurityError(f"PDB ID must be exactly 4 characters: {pdb_id}")

        if not SecurityValidator.PDB_ID_PATTERN.match(pdb_id):
            raise SecurityError(
                f"PDB ID contains invalid characters: {pdb_id}\n"
                f"Only alphanumeric characters are allowed"
            )

        # Convert to uppercase for consistency
        return pdb_id.upper()

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and injection attacks.

        Args:
            filename: Filename to sanitize

        Returns:
            Sanitized filename

        Raises:
            SecurityError: If filename is suspicious
        """
        if not filename:
            raise SecurityError("Filename cannot be empty")

        # Check for dangerous patterns
        for pattern in SecurityValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, filename):
                raise SecurityError(
                    f"Filename contains dangerous pattern '{pattern}': {filename}"
                )

        # Remove leading/trailing whitespace and dots
        filename = filename.strip().strip('.')

        # Replace any remaining dangerous characters with underscores
        filename = re.sub(r'[^\w\s\-\.]', '_', filename)

        # Limit filename length
        if len(filename) > 255:
            raise SecurityError(f"Filename too long (> 255 chars): {filename[:50]}...")

        return filename

    @staticmethod
    def validate_path(file_path: Union[str, Path],
                     base_dir: Optional[Union[str, Path]] = None,
                     must_exist: bool = False,
                     allow_symlinks: bool = False) -> Path:
        """
        Validate file path for security issues.

        Args:
            file_path: Path to validate
            base_dir: Base directory that path must be within
            must_exist: Whether path must already exist
            allow_symlinks: Whether to allow symbolic links

        Returns:
            Resolved Path object

        Raises:
            SecurityError: If path is unsafe
        """
        try:
            path = Path(file_path).resolve()
        except Exception as e:
            raise SecurityError(f"Invalid path: {file_path} - {e}")

        # Check for path traversal outside base directory
        if base_dir:
            base = Path(base_dir).resolve()
            try:
                path.relative_to(base)
            except ValueError:
                raise SecurityError(
                    f"Path traversal detected: {file_path} is outside {base_dir}"
                )

        # Check if path exists when required
        if must_exist and not path.exists():
            raise SecurityError(f"Path does not exist: {file_path}")

        # Check for symbolic links if not allowed
        if not allow_symlinks and path.is_symlink():
            raise SecurityError(f"Symbolic links not allowed: {file_path}")

        # Check file extension
        if path.is_file():
            extension = path.suffix.lstrip('.').lower()
            if extension and extension not in SecurityValidator.ALLOWED_EXTENSIONS:
                logger.warning(f"Unusual file extension: {extension} for {file_path}")

        return path

    @staticmethod
    def sanitize_command_args(args: List[str]) -> List[str]:
        """
        Sanitize command-line arguments for subprocess calls.

        Args:
            args: List of command arguments

        Returns:
            Sanitized argument list

        Raises:
            SecurityError: If arguments contain dangerous patterns
        """
        sanitized = []

        for arg in args:
            # Convert to string if not already
            arg = str(arg)

            # Check for dangerous patterns
            for pattern in SecurityValidator.DANGEROUS_PATTERNS:
                if re.search(pattern, arg) and not arg.startswith('-'):
                    # Allow dashes for command options, but check others
                    raise SecurityError(
                        f"Argument contains dangerous pattern: {arg}"
                    )

            # For file paths, validate them
            if os.path.sep in arg or arg.startswith('.'):
                try:
                    SecurityValidator.validate_path(arg, allow_symlinks=False)
                except SecurityError:
                    raise SecurityError(f"Unsafe path in arguments: {arg}")

            sanitized.append(arg)

        return sanitized

    @staticmethod
    def safe_subprocess_args(command: str, *args, **kwargs) -> List[str]:
        """
        Prepare safe subprocess arguments list.

        Args:
            command: Command to execute
            *args: Command arguments
            **kwargs: Additional arguments (converted to --key=value format)

        Returns:
            Safe argument list for subprocess.run()

        Raises:
            SecurityError: If command or arguments are unsafe
        """
        # Validate command exists and is safe
        command_path = shutil.which(command)
        if not command_path:
            raise SecurityError(f"Command not found: {command}")

        cmd_list = [command_path]

        # Add positional arguments
        for arg in args:
            if arg is not None:
                cmd_list.append(str(arg))

        # Add keyword arguments as --key=value
        for key, value in kwargs.items():
            if value is not None:
                key = key.replace('_', '-')
                cmd_list.append(f"--{key}={value}")

        # Sanitize all arguments
        return SecurityValidator.sanitize_command_args(cmd_list)


def validate_output_directory(output_dir: Union[str, Path],
                              create: bool = True) -> Path:
    """
    Validate and optionally create output directory.

    Args:
        output_dir: Output directory path
        create: Whether to create directory if it doesn't exist

    Returns:
        Validated Path object

    Raises:
        SecurityError: If directory is unsafe
    """
    try:
        path = Path(output_dir).resolve()
    except Exception as e:
        raise SecurityError(f"Invalid output directory: {output_dir} - {e}")

    # Check for dangerous paths
    dangerous_paths = [
        Path('/'),
        Path('/bin'),
        Path('/sbin'),
        Path('/usr'),
        Path('/etc'),
        Path('/var'),
        Path('/sys'),
        Path('/proc'),
        Path.home(),  # Root home directory
    ]

    for dangerous in dangerous_paths:
        try:
            if path == dangerous or path.is_relative_to(dangerous):
                raise SecurityError(
                    f"Output directory in protected location: {output_dir}"
                )
        except AttributeError:
            # Python < 3.9 doesn't have is_relative_to
            try:
                path.relative_to(dangerous)
                raise SecurityError(
                    f"Output directory in protected location: {output_dir}"
                )
            except ValueError:
                pass

    # Create directory if needed
    if create and not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created output directory: {path}")
        except Exception as e:
            raise SecurityError(f"Cannot create output directory: {path} - {e}")

    # Verify it's a directory
    if path.exists() and not path.is_dir():
        raise SecurityError(f"Output path is not a directory: {output_dir}")

    # Check write permissions
    if path.exists() and not os.access(path, os.W_OK):
        raise SecurityError(f"Output directory not writable: {output_dir}")

    return path


# Convenience import
import shutil

if __name__ == "__main__":
    # Example usage
    import sys

    logging.basicConfig(level=logging.INFO)

    print("=== Security Validation Examples ===\n")

    # Test PDB ID validation
    test_ids = ["1ABC", "7CMD", "12AB", "ABC!", "../../etc/passwd"]
    print("Testing PDB ID validation:")
    for pdb_id in test_ids:
        try:
            validated = SecurityValidator.validate_pdb_id(pdb_id)
            print(f"  ✓ {pdb_id} -> {validated}")
        except SecurityError as e:
            print(f"  ✗ {pdb_id}: {e}")

    print("\nTesting path validation:")
    # Test path validation
    test_paths = [
        "./output/test.pdb",
        "../../etc/passwd",
        "/tmp/test.pdb",
        "output/../../../etc/passwd"
    ]
    for path in test_paths:
        try:
            validated = SecurityValidator.validate_path(path, base_dir="./output")
            print(f"  ✓ {path} -> {validated}")
        except SecurityError as e:
            print(f"  ✗ {path}: {e}")

    print("\nTesting command argument sanitization:")
    # Test command sanitization
    test_commands = [
        ["obabel", "input.pdb", "-O", "output.sdf"],
        ["plip", "-f", "structure.pdb; rm -rf /"],
        ["mk_prepare_ligand.py", "-i", "$(cat /etc/passwd)"]
    ]
    for cmd in test_commands:
        try:
            sanitized = SecurityValidator.sanitize_command_args(cmd)
            print(f"  ✓ {cmd[0]}: {len(sanitized)} args")
        except SecurityError as e:
            print(f"  ✗ {cmd[0]}: {e}")
