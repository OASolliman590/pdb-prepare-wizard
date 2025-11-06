#!/usr/bin/env python3
"""
Version Tracking Module
=======================

Tracks versions and provenance information for reproducibility.
Adds metadata to all output files for scientific reproducibility.
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import json
import platform


__version__ = "3.1.0"  # Pipeline version


class VersionTracker:
    """
    Tracks versions of pipeline and dependencies for reproducibility.
    """

    def __init__(self):
        """Initialize version tracker."""
        self._cache = {}
        self._git_info = None

    def get_pipeline_version(self) -> str:
        """Get pipeline version."""
        return __version__

    def get_python_version(self) -> str:
        """Get Python version."""
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    def get_dependency_versions(self) -> Dict[str, str]:
        """
        Get versions of all installed dependencies.

        Returns:
            Dictionary mapping package name to version
        """
        if 'dependencies' in self._cache:
            return self._cache['dependencies']

        versions = {}

        # Core dependencies
        try:
            import numpy
            versions['numpy'] = numpy.__version__
        except ImportError:
            versions['numpy'] = 'not installed'

        try:
            import pandas
            versions['pandas'] = pandas.__version__
        except ImportError:
            versions['pandas'] = 'not installed'

        try:
            import Bio
            versions['biopython'] = Bio.__version__
        except ImportError:
            versions['biopython'] = 'not installed'

        try:
            import sklearn
            versions['scikit-learn'] = sklearn.__version__
        except ImportError:
            versions['scikit-learn'] = 'not installed'

        # Optional dependencies
        try:
            import plip
            versions['plip'] = getattr(plip, '__version__', 'unknown')
        except ImportError:
            versions['plip'] = 'not installed'

        try:
            import matplotlib
            versions['matplotlib'] = matplotlib.__version__
        except ImportError:
            versions['matplotlib'] = 'not installed'

        try:
            import seaborn
            versions['seaborn'] = seaborn.__version__
        except ImportError:
            versions['seaborn'] = 'not installed'

        try:
            import openpyxl
            versions['openpyxl'] = openpyxl.__version__
        except ImportError:
            versions['openpyxl'] = 'not installed'

        self._cache['dependencies'] = versions
        return versions

    def get_git_info(self) -> Dict[str, str]:
        """
        Get Git repository information if available.

        Returns:
            Dictionary with git commit, branch, and status
        """
        if self._git_info is not None:
            return self._git_info

        git_info = {
            'commit': 'unknown',
            'branch': 'unknown',
            'status': 'unknown',
            'remote': 'unknown'
        }

        try:
            # Get repository root
            repo_root = Path(__file__).parent

            # Get commit hash
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_info['commit'] = result.stdout.strip()

            # Get branch name
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_info['branch'] = result.stdout.strip()

            # Get status (clean or dirty)
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_info['status'] = 'clean' if not result.stdout.strip() else 'modified'

            # Get remote URL
            result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_info['remote'] = result.stdout.strip()

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            # Git not available or not a git repository
            pass

        self._git_info = git_info
        return git_info

    def get_system_info(self) -> Dict[str, str]:
        """
        Get system information.

        Returns:
            Dictionary with system details
        """
        return {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_implementation': platform.python_implementation(),
        }

    def get_environment_info(self) -> Dict[str, Any]:
        """
        Get environment information.

        Returns:
            Dictionary with environment details
        """
        return {
            'user': os.environ.get('USER', 'unknown'),
            'home': os.environ.get('HOME', 'unknown'),
            'pwd': os.getcwd(),
            'path': os.environ.get('PATH', 'unknown')[:200],  # Truncate long PATH
        }

    def get_full_metadata(self, include_environment: bool = False) -> Dict[str, Any]:
        """
        Get complete metadata for reproducibility.

        Args:
            include_environment: Include environment variables (may contain sensitive data)

        Returns:
            Complete metadata dictionary
        """
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'pipeline_version': self.get_pipeline_version(),
            'python_version': self.get_python_version(),
            'dependencies': self.get_dependency_versions(),
            'git': self.get_git_info(),
            'system': self.get_system_info(),
        }

        if include_environment:
            metadata['environment'] = self.get_environment_info()

        return metadata

    def format_metadata_header(self, metadata: Optional[Dict] = None) -> str:
        """
        Format metadata as text header for output files.

        Args:
            metadata: Metadata dictionary (generates new if None)

        Returns:
            Formatted header string
        """
        if metadata is None:
            metadata = self.get_full_metadata()

        lines = [
            "=" * 80,
            "PDB Prepare Wizard - Analysis Results",
            "=" * 80,
            f"Generated: {metadata['timestamp']}",
            f"Pipeline Version: {metadata['pipeline_version']}",
            f"Python Version: {metadata['python_version']}",
            "",
            "Dependencies:",
        ]

        for package, version in metadata['dependencies'].items():
            lines.append(f"  {package}: {version}")

        lines.extend([
            "",
            "Git Information:",
            f"  Commit: {metadata['git']['commit'][:8]}",
            f"  Branch: {metadata['git']['branch']}",
            f"  Status: {metadata['git']['status']}",
            "",
            "System:",
            f"  Platform: {metadata['system']['platform']} {metadata['system']['platform_release']}",
            f"  Architecture: {metadata['system']['architecture']}",
            "=" * 80,
            ""
        ])

        return "\n".join(lines)

    def save_metadata(self, output_path: Path, metadata: Optional[Dict] = None):
        """
        Save metadata to JSON file.

        Args:
            output_path: Path to save metadata (will add _metadata.json suffix)
            metadata: Metadata dictionary (generates new if None)
        """
        if metadata is None:
            metadata = self.get_full_metadata()

        # Construct metadata filename
        if output_path.is_dir():
            metadata_file = output_path / "pipeline_metadata.json"
        else:
            metadata_file = output_path.parent / f"{output_path.stem}_metadata.json"

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        return metadata_file

    def add_metadata_to_csv(self, csv_path: Path):
        """
        Add metadata header to CSV file.

        Args:
            csv_path: Path to CSV file
        """
        if not csv_path.exists():
            return

        # Read existing content
        with open(csv_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Add metadata header
        header = self.format_metadata_header()
        header_commented = "\n".join(f"# {line}" for line in header.split("\n"))

        # Write with metadata
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write(header_commented)
            f.write("\n")
            f.write(content)


# Global version tracker instance
_tracker = VersionTracker()


def get_version_tracker() -> VersionTracker:
    """Get global version tracker instance."""
    return _tracker


def get_metadata(include_environment: bool = False) -> Dict[str, Any]:
    """
    Get metadata dictionary.

    Args:
        include_environment: Include environment variables

    Returns:
        Metadata dictionary
    """
    return _tracker.get_full_metadata(include_environment)


def save_metadata(output_path: Path):
    """
    Save metadata to file.

    Args:
        output_path: Output file or directory path
    """
    return _tracker.save_metadata(output_path)


def get_version_string() -> str:
    """
    Get concise version string for logging.

    Returns:
        Version string
    """
    return (
        f"PDB Prepare Wizard v{__version__} "
        f"(Python {_tracker.get_python_version()})"
    )


if __name__ == "__main__":
    # Example usage
    print("=== Version Tracking Demo ===\n")

    tracker = VersionTracker()

    # Get version information
    print(f"Pipeline Version: {tracker.get_pipeline_version()}")
    print(f"Python Version: {tracker.get_python_version()}\n")

    # Get dependency versions
    print("Dependencies:")
    deps = tracker.get_dependency_versions()
    for package, version in deps.items():
        print(f"  {package}: {version}")
    print()

    # Get Git information
    print("Git Information:")
    git_info = tracker.get_git_info()
    for key, value in git_info.items():
        print(f"  {key}: {value}")
    print()

    # Get system information
    print("System Information:")
    sys_info = tracker.get_system_info()
    for key, value in sys_info.items():
        print(f"  {key}: {value}")
    print()

    # Get full metadata
    print("Full Metadata (JSON):")
    metadata = tracker.get_full_metadata()
    print(json.dumps(metadata, indent=2))
    print()

    # Format as header
    print("Metadata Header:")
    print(tracker.format_metadata_header())

    # Save metadata
    from pathlib import Path
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_file = tracker.save_metadata(Path(tmpdir) / "test_output.csv")
        print(f"\n✓ Metadata saved to: {metadata_file}")
