#!/usr/bin/env python3
"""
Memory Management Module
=========================

Monitors and manages memory usage during pipeline execution to prevent
out-of-memory errors in batch processing.
"""

import gc
import os
import sys
import psutil
from typing import Optional, Dict, Callable, Any
from dataclasses import dataclass
from pathlib import Path
from logging_config import get_logger
from exceptions import MemoryError as PipelineMemoryError

logger = get_logger(__name__)


@dataclass
class MemoryInfo:
    """Memory usage information."""
    process_rss_mb: float  # Resident Set Size (actual physical memory)
    process_vms_mb: float  # Virtual Memory Size
    process_percent: float  # Percentage of system memory used by process
    system_total_mb: float
    system_available_mb: float
    system_percent: float

    def __str__(self) -> str:
        return (
            f"Memory Usage:\n"
            f"  Process RSS: {self.process_rss_mb:.1f} MB ({self.process_percent:.1f}%)\n"
            f"  Process VMS: {self.process_vms_mb:.1f} MB\n"
            f"  System Total: {self.system_total_mb:.1f} MB\n"
            f"  System Available: {self.system_available_mb:.1f} MB ({100-self.system_percent:.1f}% free)"
        )


class MemoryMonitor:
    """
    Monitor and manage memory usage during pipeline execution.
    """

    # Memory thresholds
    WARNING_THRESHOLD_PERCENT = 75.0  # Warn when process uses >75% of system memory
    CRITICAL_THRESHOLD_PERCENT = 90.0  # Critical when >90%

    # GC settings
    DEFAULT_GC_FREQUENCY = 10  # Run GC every N structures

    def __init__(
        self,
        warning_threshold_percent: float = WARNING_THRESHOLD_PERCENT,
        critical_threshold_percent: float = CRITICAL_THRESHOLD_PERCENT,
        auto_gc: bool = True,
        gc_frequency: int = DEFAULT_GC_FREQUENCY
    ):
        """
        Initialize memory monitor.

        Args:
            warning_threshold_percent: Warn when system memory exceeds this percentage
            critical_threshold_percent: Critical threshold for system memory
            auto_gc: Automatically run garbage collection
            gc_frequency: Run GC every N operations
        """
        self.warning_threshold = warning_threshold_percent
        self.critical_threshold = critical_threshold_percent
        self.auto_gc = auto_gc
        self.gc_frequency = gc_frequency

        self.operation_count = 0
        self.peak_memory_mb = 0.0
        self.baseline_memory_mb = 0.0

        # Get process handle
        self.process = psutil.Process(os.getpid())

        # Record baseline
        self.baseline_memory_mb = self.get_current_memory().process_rss_mb
        logger.info(f"Memory monitor initialized. Baseline: {self.baseline_memory_mb:.1f} MB")

    def get_current_memory(self) -> MemoryInfo:
        """
        Get current memory usage.

        Returns:
            MemoryInfo object with current usage
        """
        # Process memory
        mem_info = self.process.memory_info()
        process_rss_mb = mem_info.rss / (1024 * 1024)
        process_vms_mb = mem_info.vms / (1024 * 1024)

        # System memory
        system_mem = psutil.virtual_memory()
        system_total_mb = system_mem.total / (1024 * 1024)
        system_available_mb = system_mem.available / (1024 * 1024)
        system_percent = system_mem.percent

        # Process percentage of system
        process_percent = (process_rss_mb / system_total_mb) * 100

        return MemoryInfo(
            process_rss_mb=process_rss_mb,
            process_vms_mb=process_vms_mb,
            process_percent=process_percent,
            system_total_mb=system_total_mb,
            system_available_mb=system_available_mb,
            system_percent=system_percent
        )

    def check_memory(self, raise_on_critical: bool = True) -> MemoryInfo:
        """
        Check current memory usage and log warnings/errors.

        Args:
            raise_on_critical: Raise exception if critical threshold exceeded

        Returns:
            Current MemoryInfo

        Raises:
            PipelineMemoryError: If critical threshold exceeded and raise_on_critical=True
        """
        mem_info = self.get_current_memory()

        # Update peak
        if mem_info.process_rss_mb > self.peak_memory_mb:
            self.peak_memory_mb = mem_info.process_rss_mb

        # Check thresholds
        if mem_info.system_percent >= self.critical_threshold:
            logger.critical(
                f"CRITICAL: System memory usage at {mem_info.system_percent:.1f}%!\n"
                f"{mem_info}"
            )

            if raise_on_critical:
                raise PipelineMemoryError(
                    f"System memory usage critical: {mem_info.system_percent:.1f}%",
                    required_mb=0,
                    available_mb=mem_info.system_available_mb
                )

        elif mem_info.system_percent >= self.warning_threshold:
            logger.warning(
                f"WARNING: System memory usage at {mem_info.system_percent:.1f}%\n"
                f"Process using {mem_info.process_rss_mb:.1f} MB"
            )

        return mem_info

    def cleanup(self, explicit: bool = True) -> Dict[str, float]:
        """
        Perform garbage collection and cleanup.

        Args:
            explicit: Force full garbage collection

        Returns:
            Dictionary with memory info before and after cleanup
        """
        before = self.get_current_memory()

        if explicit:
            # Force full GC
            collected = gc.collect()
            logger.debug(f"Garbage collection: collected {collected} objects")

        after = self.get_current_memory()

        freed_mb = before.process_rss_mb - after.process_rss_mb

        if freed_mb > 1.0:  # Only log if freed >1 MB
            logger.info(f"Cleanup freed {freed_mb:.1f} MB")

        return {
            'before_mb': before.process_rss_mb,
            'after_mb': after.process_rss_mb,
            'freed_mb': freed_mb
        }

    def track_operation(self, operation_name: str = "operation") -> MemoryInfo:
        """
        Track an operation and perform periodic cleanup.

        Args:
            operation_name: Name of operation for logging

        Returns:
            Current memory info
        """
        self.operation_count += 1

        # Check memory
        mem_info = self.check_memory(raise_on_critical=False)

        # Periodic GC
        if self.auto_gc and self.operation_count % self.gc_frequency == 0:
            logger.debug(f"Periodic cleanup after {self.operation_count} operations")
            self.cleanup(explicit=True)

        return mem_info

    def get_memory_summary(self) -> Dict[str, Any]:
        """
        Get summary of memory usage.

        Returns:
            Dictionary with memory statistics
        """
        current = self.get_current_memory()

        return {
            'baseline_mb': self.baseline_memory_mb,
            'current_mb': current.process_rss_mb,
            'peak_mb': self.peak_memory_mb,
            'delta_mb': current.process_rss_mb - self.baseline_memory_mb,
            'operations_tracked': self.operation_count,
            'system_percent': current.system_percent,
            'system_available_mb': current.system_available_mb
        }

    def log_summary(self):
        """Log memory usage summary."""
        summary = self.get_memory_summary()

        logger.info(
            f"\nMemory Usage Summary:\n"
            f"  Baseline: {summary['baseline_mb']:.1f} MB\n"
            f"  Current: {summary['current_mb']:.1f} MB\n"
            f"  Peak: {summary['peak_mb']:.1f} MB\n"
            f"  Delta: {summary['delta_mb']:+.1f} MB\n"
            f"  Operations: {summary['operations_tracked']}\n"
            f"  System Usage: {summary['system_percent']:.1f}%"
        )


class MemoryManagedBatch:
    """
    Context manager for batch processing with memory management.
    """

    def __init__(
        self,
        batch_size: int = 10,
        cleanup_frequency: int = 5,
        monitor: Optional[MemoryMonitor] = None
    ):
        """
        Initialize batch processor.

        Args:
            batch_size: Number of items to process before cleanup
            cleanup_frequency: Run cleanup every N items
            monitor: MemoryMonitor instance (creates new if None)
        """
        self.batch_size = batch_size
        self.cleanup_frequency = cleanup_frequency
        self.monitor = monitor or MemoryMonitor(
            auto_gc=True,
            gc_frequency=cleanup_frequency
        )
        self.processed = 0

    def __enter__(self):
        """Enter context."""
        logger.info(
            f"Starting batch processing (batch_size={self.batch_size}, "
            f"cleanup_freq={self.cleanup_frequency})"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and log summary."""
        self.monitor.log_summary()

        if exc_type is None:
            logger.info(f"Batch processing complete: {self.processed} items processed")
        else:
            logger.error(f"Batch processing failed after {self.processed} items")

        # Final cleanup
        self.monitor.cleanup(explicit=True)

        return False

    def process_item(self, item_name: str = "item") -> MemoryInfo:
        """
        Track processing of an item.

        Args:
            item_name: Name of item for logging

        Returns:
            Current memory info
        """
        self.processed += 1
        mem_info = self.monitor.track_operation(item_name)

        # Cleanup at batch boundaries
        if self.processed % self.batch_size == 0:
            logger.info(f"Batch boundary: {self.processed} items processed")
            self.monitor.cleanup(explicit=True)

        return mem_info

    def should_cleanup(self) -> bool:
        """Check if cleanup should be performed."""
        return self.processed % self.cleanup_frequency == 0


def cleanup_biopython_structure(structure) -> None:
    """
    Explicitly cleanup BioPython Structure object.

    Args:
        structure: BioPython Structure object
    """
    try:
        # Clear internal data structures
        if hasattr(structure, 'child_dict'):
            structure.child_dict.clear()
        if hasattr(structure, 'child_list'):
            structure.child_list.clear()

        # Delete structure
        del structure

    except Exception as e:
        logger.debug(f"Error cleaning up BioPython structure: {e}")


def monitor_memory_usage(func: Callable) -> Callable:
    """
    Decorator to monitor memory usage of a function.

    Args:
        func: Function to monitor

    Returns:
        Wrapped function
    """
    def wrapper(*args, **kwargs):
        monitor = MemoryMonitor(auto_gc=False)

        logger.debug(f"Memory before {func.__name__}: {monitor.get_current_memory().process_rss_mb:.1f} MB")

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            mem_after = monitor.get_current_memory()
            delta = mem_after.process_rss_mb - monitor.baseline_memory_mb

            logger.debug(
                f"Memory after {func.__name__}: {mem_after.process_rss_mb:.1f} MB "
                f"(Δ {delta:+.1f} MB)"
            )

            # Cleanup
            monitor.cleanup(explicit=True)

    return wrapper


# Convenience functions
def get_current_memory_mb() -> float:
    """
    Get current process memory usage in MB.

    Returns:
        Memory usage in MB
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def get_available_memory_mb() -> float:
    """
    Get available system memory in MB.

    Returns:
        Available memory in MB
    """
    return psutil.virtual_memory().available / (1024 * 1024)


def force_cleanup():
    """Force garbage collection and cleanup."""
    collected = gc.collect()
    logger.debug(f"Force cleanup: collected {collected} objects")


if __name__ == "__main__":
    from logging_config import setup_logger

    setup_logger(level="INFO")

    print("=== Memory Manager Demo ===\n")

    # Initialize monitor
    monitor = MemoryMonitor()

    print("Current Memory:")
    print(monitor.get_current_memory())
    print()

    # Simulate batch processing
    print("Simulating Batch Processing:")
    with MemoryManagedBatch(batch_size=5, cleanup_frequency=3) as batch:
        for i in range(20):
            # Simulate work by allocating some memory
            dummy_data = [0] * 1000000  # Allocate ~8 MB

            # Track operation
            batch.process_item(f"structure_{i}")

            # Clean up dummy data
            del dummy_data

    print("\n✓ Memory manager demo complete!")
