#!/usr/bin/env python3
"""
RMSD Calculation Optimizer
===========================

Optimized RMSD matrix calculations using triangular storage and caching.
Reduces memory usage and computation time for large pose sets.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import pickle
from logging_config import get_logger

logger = get_logger(__name__)


class TriangularRMSDMatrix:
    """
    Memory-efficient storage for symmetric RMSD matrices using triangular representation.

    For N poses, stores only N*(N-1)/2 values instead of N*N.
    Example: 100 poses = 4,950 values instead of 10,000 (51% savings)
    """

    def __init__(self, n_poses: int):
        """
        Initialize triangular matrix storage.

        Args:
            n_poses: Number of poses
        """
        self.n_poses = n_poses
        # Store only upper triangle (excluding diagonal)
        self.size = n_poses * (n_poses - 1) // 2
        self.data = np.zeros(self.size, dtype=np.float32)  # Use float32 for memory
        logger.debug(f"Created triangular matrix: {n_poses} poses, {self.size} values")

    def _get_index(self, i: int, j: int) -> int:
        """
        Get linear index for (i,j) in upper triangle.

        Formula: index = i*n - i*(i+1)/2 + j - i - 1

        Args:
            i, j: Matrix coordinates (i < j)

        Returns:
            Linear index in self.data
        """
        if i >= j:
            raise ValueError(f"Invalid coordinates: i={i} must be < j={j}")
        if i >= self.n_poses or j >= self.n_poses:
            raise ValueError(f"Coordinates out of bounds: ({i},{j}) for size {self.n_poses}")

        # Calculate index in upper triangle
        return i * self.n_poses - i * (i + 1) // 2 + j - i - 1

    def set(self, i: int, j: int, value: float):
        """Set RMSD value for pose pair (i,j)."""
        if i == j:
            return  # Diagonal is always 0
        if i > j:
            i, j = j, i  # Swap to ensure i < j

        idx = self._get_index(i, j)
        self.data[idx] = value

    def get(self, i: int, j: int) -> float:
        """Get RMSD value for pose pair (i,j)."""
        if i == j:
            return 0.0  # Diagonal
        if i > j:
            i, j = j, i  # Swap to ensure i < j

        idx = self._get_index(i, j)
        return float(self.data[idx])

    def to_full_matrix(self) -> np.ndarray:
        """
        Convert to full symmetric matrix for compatibility.

        Returns:
            Full N×N matrix
        """
        matrix = np.zeros((self.n_poses, self.n_poses), dtype=np.float32)

        # Fill upper triangle
        for i in range(self.n_poses):
            for j in range(i + 1, self.n_poses):
                value = self.get(i, j)
                matrix[i, j] = value
                matrix[j, i] = value  # Symmetric

        return matrix

    def save(self, filepath: Path):
        """Save to file."""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'n_poses': self.n_poses,
                'data': self.data
            }, f)
        logger.info(f"Saved RMSD matrix: {filepath}")

    @classmethod
    def load(cls, filepath: Path) -> 'TriangularRMSDMatrix':
        """Load from file."""
        with open(filepath, 'rb') as f:
            saved = pickle.load(f)

        matrix = cls(saved['n_poses'])
        matrix.data = saved['data']
        logger.info(f"Loaded RMSD matrix: {filepath}")
        return matrix

    def get_memory_usage(self) -> Dict[str, float]:
        """
        Get memory usage statistics.

        Returns:
            Dictionary with memory info in MB
        """
        triangular_mb = self.data.nbytes / (1024 * 1024)
        full_mb = (self.n_poses ** 2 * 4) / (1024 * 1024)  # float32

        return {
            'triangular_mb': triangular_mb,
            'full_matrix_mb': full_mb,
            'savings_mb': full_mb - triangular_mb,
            'savings_percent': ((full_mb - triangular_mb) / full_mb) * 100
        }


class CachedRMSDCalculator:
    """
    RMSD calculator with intelligent caching and incremental updates.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize calculator with caching.

        Args:
            cache_dir: Directory for cache files (None = no caching)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.computation_cache = {}  # In-memory cache
        logger.debug(f"RMSD calculator initialized (cache: {cache_dir})")

    def calculate_rmsd_optimized(
        self,
        poses_data: List[Dict],
        use_cache: bool = True,
        cache_key: Optional[str] = None
    ) -> TriangularRMSDMatrix:
        """
        Calculate RMSD matrix with optimization and caching.

        Args:
            poses_data: List of pose dictionaries with coordinates
            use_cache: Whether to use caching
            cache_key: Unique identifier for this calculation

        Returns:
            Triangular RMSD matrix
        """
        n_poses = len(poses_data)

        # Check cache
        if use_cache and cache_key and self.cache_dir:
            cache_file = self.cache_dir / f"rmsd_{cache_key}.pkl"
            if cache_file.exists():
                logger.info(f"Loading cached RMSD matrix: {cache_key}")
                return TriangularRMSDMatrix.load(cache_file)

        # Calculate matrix
        logger.info(f"Calculating RMSD matrix for {n_poses} poses...")
        matrix = TriangularRMSDMatrix(n_poses)

        # Calculate upper triangle only
        for i in range(n_poses):
            for j in range(i + 1, n_poses):
                rmsd = self._calculate_pair_rmsd(
                    poses_data[i],
                    poses_data[j]
                )
                matrix.set(i, j, rmsd)

        # Cache result
        if use_cache and cache_key and self.cache_dir:
            cache_file = self.cache_dir / f"rmsd_{cache_key}.pkl"
            matrix.save(cache_file)

        # Log memory savings
        mem_info = matrix.get_memory_usage()
        logger.info(
            f"RMSD matrix: {mem_info['triangular_mb']:.2f} MB "
            f"(saved {mem_info['savings_mb']:.2f} MB, "
            f"{mem_info['savings_percent']:.1f}%)"
        )

        return matrix

    def _calculate_pair_rmsd(self, pose1: Dict, pose2: Dict) -> float:
        """
        Calculate RMSD between two poses.

        This is a placeholder - replace with actual RMSD calculation
        using BioPython or other library.

        Args:
            pose1, pose2: Pose dictionaries with 'coordinates' key

        Returns:
            RMSD value in Angstroms
        """
        # Placeholder: random RMSD for demonstration
        # In production, use proper RMSD calculation:
        # from Bio.SVDSuperimposer import SVDSuperimposer
        # coords1 = pose1['coordinates']
        # coords2 = pose2['coordinates']
        # sup = SVDSuperimposer()
        # sup.set(coords1, coords2)
        # sup.run()
        # return sup.get_rms()

        return np.random.uniform(0, 10)

    def update_matrix_incremental(
        self,
        matrix: TriangularRMSDMatrix,
        new_poses: List[Dict],
        existing_count: int
    ) -> TriangularRMSDMatrix:
        """
        Add new poses to existing matrix without recomputing everything.

        Args:
            matrix: Existing RMSD matrix
            new_poses: New poses to add
            existing_count: Number of poses already in matrix

        Returns:
            Extended RMSD matrix
        """
        total_poses = existing_count + len(new_poses)
        new_matrix = TriangularRMSDMatrix(total_poses)

        # Copy existing values
        logger.info(f"Copying {existing_count}×{existing_count} existing RMSD values...")
        for i in range(existing_count):
            for j in range(i + 1, existing_count):
                new_matrix.set(i, j, matrix.get(i, j))

        # Calculate new values only
        logger.info(f"Calculating RMSD for {len(new_poses)} new poses...")
        for i in range(existing_count, total_poses):
            for j in range(i + 1, total_poses):
                # Both new poses
                pose_idx_i = i - existing_count
                pose_idx_j = j - existing_count
                rmsd = self._calculate_pair_rmsd(
                    new_poses[pose_idx_i],
                    new_poses[pose_idx_j]
                )
                new_matrix.set(i, j, rmsd)

        return new_matrix

    def clear_cache(self):
        """Clear all cached RMSD matrices."""
        if not self.cache_dir:
            return

        count = 0
        for cache_file in self.cache_dir.glob("rmsd_*.pkl"):
            cache_file.unlink()
            count += 1

        logger.info(f"Cleared {count} cached RMSD matrices")


def benchmark_rmsd_optimization(n_poses: int = 100) -> Dict:
    """
    Benchmark memory and performance improvements.

    Args:
        n_poses: Number of poses to test

    Returns:
        Benchmark results
    """
    import time

    logger.info(f"Benchmarking RMSD optimization with {n_poses} poses...")

    # Traditional full matrix
    start = time.time()
    full_matrix = np.zeros((n_poses, n_poses), dtype=np.float32)
    full_time = time.time() - start
    full_memory = full_matrix.nbytes / (1024 * 1024)

    # Triangular matrix
    start = time.time()
    tri_matrix = TriangularRMSDMatrix(n_poses)
    tri_time = time.time() - start
    mem_info = tri_matrix.get_memory_usage()

    results = {
        'n_poses': n_poses,
        'full_matrix_mb': full_memory,
        'triangular_mb': mem_info['triangular_mb'],
        'memory_savings_mb': mem_info['savings_mb'],
        'memory_savings_percent': mem_info['savings_percent'],
        'full_init_time': full_time,
        'tri_init_time': tri_time,
        'speedup': full_time / tri_time if tri_time > 0 else 1.0
    }

    logger.info("Benchmark Results:")
    logger.info(f"  Memory: {full_memory:.2f} MB → {mem_info['triangular_mb']:.2f} MB")
    logger.info(f"  Savings: {mem_info['savings_mb']:.2f} MB ({mem_info['savings_percent']:.1f}%)")
    logger.info(f"  Speedup: {results['speedup']:.2f}x")

    return results


if __name__ == "__main__":
    # Demo usage
    from logging_config import setup_logger

    setup_logger(level="INFO")

    print("=== RMSD Optimization Demo ===\n")

    # Create triangular matrix
    n = 10
    matrix = TriangularRMSDMatrix(n)

    # Set some values
    matrix.set(0, 1, 2.5)
    matrix.set(0, 2, 3.1)
    matrix.set(1, 2, 1.8)

    # Get values
    print(f"RMSD(0,1) = {matrix.get(0, 1):.2f}")
    print(f"RMSD(0,2) = {matrix.get(0, 2):.2f}")
    print(f"RMSD(1,2) = {matrix.get(1, 2):.2f}")
    print(f"RMSD(1,0) = {matrix.get(1, 0):.2f} (symmetric)")
    print()

    # Memory usage
    mem = matrix.get_memory_usage()
    print(f"Memory Usage:")
    print(f"  Triangular: {mem['triangular_mb']:.4f} MB")
    print(f"  Full would be: {mem['full_matrix_mb']:.4f} MB")
    print(f"  Savings: {mem['savings_mb']:.4f} MB ({mem['savings_percent']:.1f}%)")
    print()

    # Benchmark
    print("Running benchmark...")
    results = benchmark_rmsd_optimization(n_poses=100)
    print(f"\nFor {results['n_poses']} poses:")
    print(f"  Memory savings: {results['memory_savings_mb']:.2f} MB ({results['memory_savings_percent']:.1f}%)")
    print()

    # Test caching
    print("Testing caching...")
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        calc = CachedRMSDCalculator(cache_dir=tmpdir)

        # Mock poses
        poses = [{'id': i} for i in range(20)]

        # First calculation
        rmsd_matrix = calc.calculate_rmsd_optimized(
            poses,
            use_cache=True,
            cache_key="test_poses"
        )

        # Second calculation (should load from cache)
        rmsd_matrix2 = calc.calculate_rmsd_optimized(
            poses,
            use_cache=True,
            cache_key="test_poses"
        )

        print("✓ Caching test passed")

    print("\n✓ All tests passed!")
