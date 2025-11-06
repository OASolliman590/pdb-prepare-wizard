#!/usr/bin/env python3
"""
Parallel Batch Processor Module
================================

Provides parallel processing capabilities for batch PDB processing with:
- Multiprocessing support
- Progress tracking
- Error handling
- Checkpoint/resume functionality
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from multiprocessing import Pool, cpu_count
from functools import partial
import traceback

from logging_config import get_logger
from memory_manager import MemoryMonitor, MemoryManagedBatch
from exceptions import PipelineError

logger = get_logger(__name__)

# Progress bar support (optional)
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    logger.warning("tqdm not available - progress bars disabled")


@dataclass
class ProcessingTask:
    """Task specification for batch processing."""
    pdb_id: str
    ligand_name: str
    chain_id: str
    res_id: int
    task_id: str = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.task_id is None:
            self.task_id = f"{self.pdb_id}_{self.ligand_name}_{self.chain_id}_{self.res_id}"
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ProcessingResult:
    """Result of processing a single task."""
    task_id: str
    pdb_id: str
    success: bool
    results: Optional[Dict] = None
    error: Optional[str] = None
    error_traceback: Optional[str] = None
    processing_time: float = 0.0
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class CheckpointManager:
    """
    Manage checkpoints for resumable batch processing.
    """

    def __init__(self, checkpoint_dir: Path):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoint files
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / "checkpoint.json"
        self.results_file = self.checkpoint_dir / "results.pkl"

    def save_checkpoint(
        self,
        completed_tasks: List[str],
        pending_tasks: List[str],
        results: List[ProcessingResult],
        metadata: Optional[Dict] = None
    ):
        """
        Save checkpoint to disk.

        Args:
            completed_tasks: List of completed task IDs
            pending_tasks: List of pending task IDs
            results: List of processing results
            metadata: Additional metadata
        """
        checkpoint_data = {
            'timestamp': datetime.now().isoformat(),
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'n_completed': len(completed_tasks),
            'n_pending': len(pending_tasks),
            'metadata': metadata or {}
        }

        # Save checkpoint metadata
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)

        # Save results separately (can be large)
        with open(self.results_file, 'wb') as f:
            pickle.dump(results, f)

        logger.info(
            f"Checkpoint saved: {len(completed_tasks)} completed, "
            f"{len(pending_tasks)} pending"
        )

    def load_checkpoint(self) -> Optional[Dict]:
        """
        Load checkpoint from disk.

        Returns:
            Checkpoint data or None if no checkpoint exists
        """
        if not self.checkpoint_file.exists():
            logger.info("No checkpoint found")
            return None

        with open(self.checkpoint_file, 'r') as f:
            checkpoint_data = json.load(f)

        # Load results
        if self.results_file.exists():
            with open(self.results_file, 'rb') as f:
                checkpoint_data['results'] = pickle.load(f)
        else:
            checkpoint_data['results'] = []

        logger.info(
            f"Checkpoint loaded: {checkpoint_data['n_completed']} completed, "
            f"{checkpoint_data['n_pending']} pending"
        )

        return checkpoint_data

    def clear_checkpoint(self):
        """Clear checkpoint files."""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
        if self.results_file.exists():
            self.results_file.unlink()
        logger.info("Checkpoint cleared")


class ParallelBatchProcessor:
    """
    Process multiple tasks in parallel with checkpoint/resume support.
    """

    def __init__(
        self,
        n_jobs: int = 1,
        checkpoint_dir: Optional[Path] = None,
        enable_checkpoints: bool = True,
        checkpoint_frequency: int = 10,
        memory_monitor: bool = True,
        batch_size: int = 10
    ):
        """
        Initialize parallel batch processor.

        Args:
            n_jobs: Number of parallel jobs (1 = sequential, -1 = all CPUs)
            checkpoint_dir: Directory for checkpoints
            enable_checkpoints: Enable checkpoint/resume
            checkpoint_frequency: Save checkpoint every N tasks
            memory_monitor: Enable memory monitoring
            batch_size: Batch size for memory cleanup
        """
        # Determine number of jobs
        if n_jobs == -1:
            n_jobs = cpu_count()
        elif n_jobs < 1:
            n_jobs = 1

        self.n_jobs = n_jobs
        self.enable_checkpoints = enable_checkpoints
        self.checkpoint_frequency = checkpoint_frequency
        self.memory_monitor_enabled = memory_monitor
        self.batch_size = batch_size

        # Setup checkpoint manager
        if enable_checkpoints:
            if checkpoint_dir is None:
                checkpoint_dir = Path(".checkpoints")
            self.checkpoint_manager = CheckpointManager(checkpoint_dir)
        else:
            self.checkpoint_manager = None

        # Setup memory monitor
        if memory_monitor:
            self.memory_monitor = MemoryMonitor(
                auto_gc=True,
                gc_frequency=batch_size
            )
        else:
            self.memory_monitor = None

        logger.info(
            f"Batch processor initialized: {n_jobs} jobs, "
            f"checkpoints={'enabled' if enable_checkpoints else 'disabled'}"
        )

    def process_batch(
        self,
        tasks: List[ProcessingTask],
        process_func: Callable,
        resume: bool = False,
        show_progress: bool = True
    ) -> List[ProcessingResult]:
        """
        Process batch of tasks in parallel.

        Args:
            tasks: List of tasks to process
            process_func: Function to process each task (takes ProcessingTask, returns dict)
            resume: Resume from checkpoint if available
            show_progress: Show progress bar

        Returns:
            List of processing results
        """
        # Load checkpoint if resuming
        completed_task_ids = set()
        results = []

        if resume and self.checkpoint_manager:
            checkpoint = self.checkpoint_manager.load_checkpoint()
            if checkpoint:
                completed_task_ids = set(checkpoint['completed_tasks'])
                results = checkpoint['results']
                logger.info(f"Resuming from checkpoint: {len(completed_task_ids)} already completed")

        # Filter out completed tasks
        pending_tasks = [t for t in tasks if t.task_id not in completed_task_ids]

        if not pending_tasks:
            logger.info("All tasks already completed")
            return results

        logger.info(f"Processing {len(pending_tasks)} tasks ({len(completed_task_ids)} already done)")

        # Process tasks
        if self.n_jobs == 1:
            # Sequential processing
            results.extend(self._process_sequential(
                pending_tasks, process_func, show_progress
            ))
        else:
            # Parallel processing
            results.extend(self._process_parallel(
                pending_tasks, process_func, show_progress
            ))

        # Final checkpoint
        if self.checkpoint_manager:
            self.checkpoint_manager.clear_checkpoint()
            logger.info("Processing complete - checkpoint cleared")

        # Memory summary
        if self.memory_monitor:
            self.memory_monitor.log_summary()

        return results

    def _process_sequential(
        self,
        tasks: List[ProcessingTask],
        process_func: Callable,
        show_progress: bool
    ) -> List[ProcessingResult]:
        """Process tasks sequentially."""
        results = []
        completed_ids = []

        # Setup progress bar
        iterator = tqdm(tasks, desc="Processing") if (show_progress and TQDM_AVAILABLE) else tasks

        for i, task in enumerate(iterator):
            # Process task
            result = self._process_single_task(task, process_func)
            results.append(result)

            if result.success:
                completed_ids.append(task.task_id)

            # Memory tracking
            if self.memory_monitor:
                self.memory_monitor.track_operation(task.task_id)

            # Checkpoint
            if self.checkpoint_manager and (i + 1) % self.checkpoint_frequency == 0:
                pending_ids = [t.task_id for t in tasks[i+1:]]
                self.checkpoint_manager.save_checkpoint(
                    completed_tasks=completed_ids,
                    pending_tasks=pending_ids,
                    results=results
                )

        return results

    def _process_parallel(
        self,
        tasks: List[ProcessingTask],
        process_func: Callable,
        show_progress: bool
    ) -> List[ProcessingResult]:
        """Process tasks in parallel."""
        results = []
        completed_ids = []

        # Create partial function with process_func
        worker_func = partial(self._process_single_task, process_func=process_func)

        # Process in parallel
        with Pool(processes=self.n_jobs) as pool:
            # Setup progress bar
            if show_progress and TQDM_AVAILABLE:
                iterator = tqdm(
                    pool.imap(worker_func, tasks),
                    total=len(tasks),
                    desc=f"Processing ({self.n_jobs} jobs)"
                )
            else:
                iterator = pool.imap(worker_func, tasks)

            for i, result in enumerate(iterator):
                results.append(result)

                if result.success:
                    completed_ids.append(result.task_id)

                # Checkpoint
                if self.checkpoint_manager and (i + 1) % self.checkpoint_frequency == 0:
                    pending_ids = [t.task_id for t in tasks[i+1:]]
                    self.checkpoint_manager.save_checkpoint(
                        completed_tasks=completed_ids,
                        pending_tasks=pending_ids,
                        results=results
                    )

        return results

    @staticmethod
    def _process_single_task(
        task: ProcessingTask,
        process_func: Callable
    ) -> ProcessingResult:
        """
        Process a single task with error handling.

        Args:
            task: Task to process
            process_func: Processing function

        Returns:
            ProcessingResult
        """
        start_time = datetime.now()

        try:
            # Process task
            result_data = process_func(task)

            processing_time = (datetime.now() - start_time).total_seconds()

            return ProcessingResult(
                task_id=task.task_id,
                pdb_id=task.pdb_id,
                success=True,
                results=result_data,
                processing_time=processing_time
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()

            logger.error(f"Error processing {task.task_id}: {e}")

            return ProcessingResult(
                task_id=task.task_id,
                pdb_id=task.pdb_id,
                success=False,
                error=str(e),
                error_traceback=traceback.format_exc(),
                processing_time=processing_time
            )

    def generate_summary(self, results: List[ProcessingResult]) -> Dict[str, Any]:
        """
        Generate summary of batch processing results.

        Args:
            results: List of processing results

        Returns:
            Summary dictionary
        """
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        total_time = sum(r.processing_time for r in results)
        avg_time = total_time / len(results) if results else 0

        summary = {
            'total_tasks': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(results) if results else 0,
            'total_time_seconds': total_time,
            'average_time_seconds': avg_time,
            'failed_tasks': [
                {
                    'task_id': r.task_id,
                    'pdb_id': r.pdb_id,
                    'error': r.error
                }
                for r in failed
            ]
        }

        return summary

    def save_results(
        self,
        results: List[ProcessingResult],
        output_file: Path,
        include_errors: bool = True
    ):
        """
        Save results to JSON file.

        Args:
            results: Processing results
            output_file: Output file path
            include_errors: Include error details
        """
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': self.generate_summary(results),
            'results': []
        }

        for r in results:
            result_dict = asdict(r)
            if not include_errors and not r.success:
                result_dict.pop('error_traceback', None)
            output_data['results'].append(result_dict)

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Results saved to {output_file}")


# Convenience function
def create_tasks_from_list(task_list: List[Dict]) -> List[ProcessingTask]:
    """
    Create ProcessingTask objects from list of dictionaries.

    Args:
        task_list: List of task specifications

    Returns:
        List of ProcessingTask objects
    """
    tasks = []
    for task_dict in task_list:
        task = ProcessingTask(**task_dict)
        tasks.append(task)
    return tasks


if __name__ == "__main__":
    from logging_config import setup_logger
    import time

    setup_logger(level="INFO")

    print("=== Parallel Batch Processor Demo ===\n")

    # Demo processing function
    def demo_process_func(task: ProcessingTask) -> Dict:
        """Simulate processing."""
        time.sleep(0.1)  # Simulate work
        return {
            'pdb_id': task.pdb_id,
            'ligand': task.ligand_name,
            'status': 'processed'
        }

    # Create demo tasks
    tasks = [
        ProcessingTask(pdb_id=f"PDB{i:04d}", ligand_name="ATP", chain_id="A", res_id=500)
        for i in range(20)
    ]

    # Create processor
    processor = ParallelBatchProcessor(
        n_jobs=4,
        checkpoint_dir=Path(".demo_checkpoints"),
        checkpoint_frequency=5
    )

    # Process batch
    results = processor.process_batch(
        tasks=tasks,
        process_func=demo_process_func,
        show_progress=True
    )

    # Show summary
    summary = processor.generate_summary(results)
    print(f"\nSummary:")
    print(f"  Total: {summary['total_tasks']}")
    print(f"  Successful: {summary['successful']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Success Rate: {summary['success_rate']*100:.1f}%")
    print(f"  Average Time: {summary['average_time_seconds']:.2f}s")

    print("\n✓ Parallel batch processor demo complete!")
