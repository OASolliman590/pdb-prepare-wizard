#!/usr/bin/env python3
"""
Disk Space Checker Module
=========================

Checks available disk space before pipeline execution to prevent
failures due to insufficient storage.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from logging_config import get_logger
from exceptions import InsufficientDiskSpaceError, ResourceError

logger = get_logger(__name__)


@dataclass
class DiskSpaceInfo:
    """Disk space information."""
    total_mb: float
    used_mb: float
    free_mb: float
    percent_used: float
    path: str

    def __str__(self) -> str:
        return (
            f"Disk Space at {self.path}:\n"
            f"  Total: {self.total_mb:.1f} MB ({self.total_mb/1024:.1f} GB)\n"
            f"  Used: {self.used_mb:.1f} MB ({self.percent_used:.1f}%)\n"
            f"  Free: {self.free_mb:.1f} MB ({self.free_mb/1024:.1f} GB)"
        )


class DiskSpaceChecker:
    """
    Checks disk space availability for pipeline operations.
    """

    # Estimated space requirements (MB)
    SPACE_ESTIMATES = {
        'pdb_download': 1.0,          # ~1 MB per PDB file
        'ligand_extraction': 0.5,     # ~0.5 MB per ligand
        'pdbqt_conversion': 0.5,      # ~0.5 MB per PDBQT
        'pocket_analysis': 2.0,       # ~2 MB for analysis outputs
        'visualization': 5.0,          # ~5 MB per visualization
        'report_generation': 10.0,     # ~10 MB for reports (CSV, Excel, JSON)
        'temp_files': 20.0,           # ~20 MB for temporary files
        'safety_margin': 100.0,       # 100 MB safety margin
    }

    # Minimum free space (MB)
    MIN_FREE_SPACE_MB = 50.0

    # Warning threshold (%)
    WARNING_THRESHOLD_PERCENT = 90.0

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize disk space checker.

        Args:
            base_path: Base path to check (defaults to current directory)
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()

    def get_disk_usage(self, path: Optional[Path] = None) -> DiskSpaceInfo:
        """
        Get disk usage statistics for a path.

        Args:
            path: Path to check (defaults to base_path)

        Returns:
            DiskSpaceInfo object with usage statistics

        Raises:
            ResourceError: If path doesn't exist or is inaccessible
        """
        if path is None:
            path = self.base_path

        path = Path(path)

        # Ensure path exists
        if not path.exists():
            # Check parent directory if path doesn't exist yet
            path = path.parent
            if not path.exists():
                raise ResourceError(f"Path does not exist: {path}")

        try:
            stat = shutil.disk_usage(str(path))

            total_mb = stat.total / (1024 * 1024)
            used_mb = stat.used / (1024 * 1024)
            free_mb = stat.free / (1024 * 1024)
            percent_used = (stat.used / stat.total) * 100 if stat.total > 0 else 0

            return DiskSpaceInfo(
                total_mb=total_mb,
                used_mb=used_mb,
                free_mb=free_mb,
                percent_used=percent_used,
                path=str(path)
            )
        except (OSError, PermissionError) as e:
            raise ResourceError(f"Cannot access disk usage for {path}: {e}")

    def estimate_required_space(
        self,
        n_pdb_files: int = 1,
        n_ligands: int = 1,
        generate_visualizations: bool = True,
        generate_reports: bool = True
    ) -> float:
        """
        Estimate required disk space for pipeline operation.

        Args:
            n_pdb_files: Number of PDB files to process
            n_ligands: Estimated number of ligands per PDB
            generate_visualizations: Whether visualizations will be generated
            generate_reports: Whether reports will be generated

        Returns:
            Estimated space requirement in MB
        """
        required = 0.0

        # Per-PDB requirements
        required += n_pdb_files * self.SPACE_ESTIMATES['pdb_download']
        required += n_pdb_files * n_ligands * self.SPACE_ESTIMATES['ligand_extraction']
        required += n_pdb_files * n_ligands * self.SPACE_ESTIMATES['pdbqt_conversion']
        required += n_pdb_files * self.SPACE_ESTIMATES['pocket_analysis']

        # Visualization
        if generate_visualizations:
            required += n_pdb_files * self.SPACE_ESTIMATES['visualization']

        # Reports
        if generate_reports:
            required += n_pdb_files * self.SPACE_ESTIMATES['report_generation']

        # Temporary files and safety margin
        required += self.SPACE_ESTIMATES['temp_files']
        required += self.SPACE_ESTIMATES['safety_margin']

        return required

    def check_space_available(
        self,
        required_mb: float,
        path: Optional[Path] = None,
        raise_on_insufficient: bool = True
    ) -> Tuple[bool, DiskSpaceInfo]:
        """
        Check if sufficient disk space is available.

        Args:
            required_mb: Required space in MB
            path: Path to check (defaults to base_path)
            raise_on_insufficient: Raise exception if insufficient space

        Returns:
            Tuple of (is_sufficient, disk_info)

        Raises:
            InsufficientDiskSpaceError: If space is insufficient and raise_on_insufficient=True
        """
        disk_info = self.get_disk_usage(path)

        is_sufficient = disk_info.free_mb >= required_mb

        if not is_sufficient:
            logger.error(
                f"Insufficient disk space!\n"
                f"Required: {required_mb:.1f} MB\n"
                f"Available: {disk_info.free_mb:.1f} MB\n"
                f"Shortfall: {required_mb - disk_info.free_mb:.1f} MB"
            )

            if raise_on_insufficient:
                raise InsufficientDiskSpaceError(
                    required_mb=required_mb,
                    available_mb=disk_info.free_mb,
                    path=str(disk_info.path)
                )

        return is_sufficient, disk_info

    def check_pipeline_requirements(
        self,
        output_dir: Path,
        n_pdb_files: int = 1,
        n_ligands: int = 1,
        generate_visualizations: bool = True,
        generate_reports: bool = True
    ) -> DiskSpaceInfo:
        """
        Check disk space requirements for pipeline execution.

        Args:
            output_dir: Output directory path
            n_pdb_files: Number of PDB files to process
            n_ligands: Estimated number of ligands per PDB
            generate_visualizations: Whether visualizations will be generated
            generate_reports: Whether reports will be generated

        Returns:
            DiskSpaceInfo for the output directory

        Raises:
            InsufficientDiskSpaceError: If insufficient space available
        """
        # Estimate required space
        required_mb = self.estimate_required_space(
            n_pdb_files=n_pdb_files,
            n_ligands=n_ligands,
            generate_visualizations=generate_visualizations,
            generate_reports=generate_reports
        )

        logger.info(f"Estimated space requirement: {required_mb:.1f} MB ({required_mb/1024:.1f} GB)")

        # Check space availability
        is_sufficient, disk_info = self.check_space_available(
            required_mb=required_mb,
            path=output_dir,
            raise_on_insufficient=True
        )

        logger.info(f"Disk space check passed: {disk_info.free_mb:.1f} MB available")

        # Warn if disk is getting full
        if disk_info.percent_used >= self.WARNING_THRESHOLD_PERCENT:
            logger.warning(
                f"Disk usage is high ({disk_info.percent_used:.1f}% used). "
                f"Consider freeing up space."
            )

        return disk_info

    def monitor_space_during_execution(
        self,
        path: Optional[Path] = None,
        min_free_mb: Optional[float] = None
    ) -> DiskSpaceInfo:
        """
        Monitor disk space during pipeline execution.

        Args:
            path: Path to monitor (defaults to base_path)
            min_free_mb: Minimum free space threshold (defaults to MIN_FREE_SPACE_MB)

        Returns:
            Current disk space information

        Raises:
            InsufficientDiskSpaceError: If free space drops below minimum
        """
        if min_free_mb is None:
            min_free_mb = self.MIN_FREE_SPACE_MB

        disk_info = self.get_disk_usage(path)

        if disk_info.free_mb < min_free_mb:
            logger.critical(
                f"Disk space critically low during execution!\n"
                f"Free: {disk_info.free_mb:.1f} MB\n"
                f"Minimum: {min_free_mb:.1f} MB"
            )
            raise InsufficientDiskSpaceError(
                required_mb=min_free_mb,
                available_mb=disk_info.free_mb,
                path=str(disk_info.path)
            )

        return disk_info

    def get_space_summary(self, paths: Optional[list] = None) -> Dict[str, DiskSpaceInfo]:
        """
        Get disk space summary for multiple paths.

        Args:
            paths: List of paths to check (defaults to [base_path])

        Returns:
            Dictionary mapping path to DiskSpaceInfo
        """
        if paths is None:
            paths = [self.base_path]

        summary = {}
        for path in paths:
            try:
                disk_info = self.get_disk_usage(Path(path))
                summary[str(path)] = disk_info
            except ResourceError as e:
                logger.warning(f"Could not get disk info for {path}: {e}")

        return summary

    def suggest_cleanup_actions(self, disk_info: DiskSpaceInfo) -> list:
        """
        Suggest cleanup actions based on disk usage.

        Args:
            disk_info: Current disk space information

        Returns:
            List of suggested cleanup actions
        """
        suggestions = []

        if disk_info.percent_used >= 95:
            suggestions.append("CRITICAL: Disk almost full! Free up space immediately.")
            suggestions.append("- Delete old pipeline output directories")
            suggestions.append("- Clean up temporary files in logs/ and .cache/")
            suggestions.append("- Remove unnecessary PDB files")
        elif disk_info.percent_used >= 90:
            suggestions.append("WARNING: Disk usage high. Consider cleanup:")
            suggestions.append("- Review and remove old output directories")
            suggestions.append("- Clear cache files")
        elif disk_info.percent_used >= 75:
            suggestions.append("INFO: Disk usage moderate. Monitor space usage.")

        if disk_info.free_mb < 1000:  # Less than 1 GB free
            suggestions.append(f"Only {disk_info.free_mb/1024:.1f} GB free. Recommend freeing at least 2 GB.")

        return suggestions


# Convenience functions
def check_disk_space(
    output_dir: Path,
    n_pdb_files: int = 1,
    raise_on_insufficient: bool = True
) -> DiskSpaceInfo:
    """
    Quick disk space check for pipeline execution.

    Args:
        output_dir: Output directory path
        n_pdb_files: Number of PDB files to process
        raise_on_insufficient: Raise exception if insufficient space

    Returns:
        DiskSpaceInfo object

    Raises:
        InsufficientDiskSpaceError: If insufficient space and raise_on_insufficient=True
    """
    checker = DiskSpaceChecker()
    return checker.check_pipeline_requirements(
        output_dir=output_dir,
        n_pdb_files=n_pdb_files
    )


def get_disk_usage(path: Optional[Path] = None) -> DiskSpaceInfo:
    """
    Get disk usage for a path.

    Args:
        path: Path to check (defaults to current directory)

    Returns:
        DiskSpaceInfo object
    """
    checker = DiskSpaceChecker(base_path=path)
    return checker.get_disk_usage()


if __name__ == "__main__":
    from logging_config import setup_logger

    setup_logger(level="INFO")

    print("=== Disk Space Checker Demo ===\n")

    checker = DiskSpaceChecker()

    # Get current disk usage
    print("Current Disk Usage:")
    disk_info = checker.get_disk_usage()
    print(disk_info)
    print()

    # Estimate requirements
    print("Space Requirements Estimate:")
    print("Single PDB:")
    required_single = checker.estimate_required_space(n_pdb_files=1, n_ligands=3)
    print(f"  {required_single:.1f} MB ({required_single/1024:.1f} GB)")

    print("Batch (10 PDBs):")
    required_batch = checker.estimate_required_space(n_pdb_files=10, n_ligands=3)
    print(f"  {required_batch:.1f} MB ({required_batch/1024:.1f} GB)")

    print("Large Batch (100 PDBs):")
    required_large = checker.estimate_required_space(n_pdb_files=100, n_ligands=3)
    print(f"  {required_large:.1f} MB ({required_large/1024:.1f} GB)")
    print()

    # Check if space is available
    print("Space Availability Check:")
    try:
        is_sufficient, info = checker.check_space_available(
            required_mb=required_batch,
            raise_on_insufficient=False
        )
        if is_sufficient:
            print(f"✓ Sufficient space for batch processing ({required_batch:.1f} MB required)")
        else:
            print(f"✗ Insufficient space for batch processing ({required_batch:.1f} MB required)")
    except Exception as e:
        print(f"Error: {e}")
    print()

    # Get cleanup suggestions
    print("Cleanup Suggestions:")
    suggestions = checker.suggest_cleanup_actions(disk_info)
    if suggestions:
        for suggestion in suggestions:
            print(f"  {suggestion}")
    else:
        print("  No cleanup needed - disk space is healthy")
    print()

    # Test pipeline requirements check
    print("Pipeline Requirements Check:")
    try:
        output_dir = Path("pipeline_output")
        pipeline_info = checker.check_pipeline_requirements(
            output_dir=output_dir,
            n_pdb_files=5,
            n_ligands=2
        )
        print("✓ Sufficient space for pipeline execution")
    except InsufficientDiskSpaceError as e:
        print(f"✗ {e}")

    print("\n✓ Disk space checker demo complete!")
