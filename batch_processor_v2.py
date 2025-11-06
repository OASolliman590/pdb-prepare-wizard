#!/usr/bin/env python3
"""
Enhanced Batch Processor V2
============================

Advanced batch processing with:
- Parallel processing support
- Memory management
- Checkpoint/resume capability
- Configuration management
- Progress tracking
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict

from core_pipeline import MolecularDockingPipeline
from unified_config import PipelineConfig
from parallel_batch_processor import (
    ParallelBatchProcessor,
    ProcessingTask,
    create_tasks_from_list
)
from logging_config import setup_logger, get_logger
from disk_space_checker import check_disk_space

logger = get_logger(__name__)


def process_single_structure(task: ProcessingTask) -> Dict:
    """
    Process a single structure using the pipeline.

    Args:
        task: ProcessingTask with PDB information

    Returns:
        Dictionary with results
    """
    # Create output directory for this task
    output_dir = Path("batch_output") / task.pdb_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load config if specified in task metadata
    config = None
    if task.metadata and 'config_file' in task.metadata:
        config = PipelineConfig.from_yaml(task.metadata['config_file'])

    # Initialize pipeline
    pipeline = MolecularDockingPipeline(
        output_dir=str(output_dir),
        config=config,
        enable_memory_monitor=True
    )

    try:
        # Run full pipeline
        results = pipeline.run_full_pipeline(
            pdb_id=task.pdb_id,
            ligand_name=task.ligand_name,
            chain_id=task.chain_id,
            res_id=task.res_id
        )

        # Generate report
        pipeline.generate_summary_report(results, task.pdb_id)

        return {
            'pdb_id': task.pdb_id,
            'ligand': task.ligand_name,
            'status': 'success',
            'druggability': results.get('druggability_score', 'N/A'),
            'pocket_volume': results.get('pocket_volume_A3', 'N/A'),
            'output_dir': str(output_dir)
        }

    except Exception as e:
        logger.error(f"Error processing {task.pdb_id}: {e}")
        raise


def load_tasks_from_file(input_file: Path) -> List[ProcessingTask]:
    """
    Load tasks from input file (JSON or text).

    Args:
        input_file: Path to input file

    Returns:
        List of ProcessingTask objects
    """
    if input_file.suffix == '.json':
        # JSON format
        with open(input_file, 'r') as f:
            task_data = json.load(f)

        if isinstance(task_data, list):
            tasks = create_tasks_from_list(task_data)
        elif isinstance(task_data, dict) and 'tasks' in task_data:
            tasks = create_tasks_from_list(task_data['tasks'])
        else:
            raise ValueError("Invalid JSON format. Expected list or {'tasks': [...]}")

    else:
        # Text format: PDB_ID,LIGAND,CHAIN,RES_ID
        tasks = []
        with open(input_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split(',')
                if len(parts) != 4:
                    logger.warning(f"Skipping invalid line: {line}")
                    continue

                pdb_id, ligand, chain, res_id = parts
                tasks.append(ProcessingTask(
                    pdb_id=pdb_id.strip(),
                    ligand_name=ligand.strip(),
                    chain_id=chain.strip(),
                    res_id=int(res_id.strip())
                ))

    logger.info(f"Loaded {len(tasks)} tasks from {input_file}")
    return tasks


def main():
    """Main entry point for batch processing."""
    parser = argparse.ArgumentParser(
        description="Enhanced Batch Processor for PDB structures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sequential processing
  %(prog)s --input tasks.txt

  # Parallel processing with 4 jobs
  %(prog)s --input tasks.txt --jobs 4

  # Resume from checkpoint
  %(prog)s --input tasks.txt --jobs 4 --resume

  # With custom configuration
  %(prog)s --input tasks.txt --config my_config.yaml

  # Disable checkpoints
  %(prog)s --input tasks.txt --jobs 4 --no-checkpoints

Input file formats:
  Text file (one per line): PDB_ID,LIGAND,CHAIN,RES_ID
  JSON file: [{"pdb_id": "7CMD", "ligand_name": "ATP", "chain_id": "A", "res_id": 500}, ...]
        """
    )

    parser.add_argument(
        '--input', '-i',
        type=Path,
        required=True,
        help='Input file with tasks (JSON or text format)'
    )

    parser.add_argument(
        '--jobs', '-j',
        type=int,
        default=1,
        help='Number of parallel jobs (1=sequential, -1=all CPUs, default: 1)'
    )

    parser.add_argument(
        '--config', '-c',
        type=Path,
        help='Configuration file (YAML)'
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('batch_output'),
        help='Output directory (default: batch_output)'
    )

    parser.add_argument(
        '--resume', '-r',
        action='store_true',
        help='Resume from checkpoint'
    )

    parser.add_argument(
        '--no-checkpoints',
        action='store_true',
        help='Disable checkpoint/resume functionality'
    )

    parser.add_argument(
        '--checkpoint-freq',
        type=int,
        default=10,
        help='Save checkpoint every N tasks (default: 10)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose logging'
    )

    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bars'
    )

    parser.add_argument(
        '--check-space',
        action='store_true',
        help='Check disk space before starting'
    )

    args = parser.parse_args()

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logger(level=log_level)

    logger.info("=" * 60)
    logger.info("Enhanced Batch Processor V2")
    logger.info("=" * 60)

    # Validate input file
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    # Load tasks
    try:
        tasks = load_tasks_from_file(args.input)
    except Exception as e:
        logger.error(f"Error loading tasks: {e}")
        sys.exit(1)

    if not tasks:
        logger.error("No tasks to process")
        sys.exit(1)

    # Load configuration
    config = None
    if args.config:
        if not args.config.exists():
            logger.error(f"Config file not found: {args.config}")
            sys.exit(1)

        try:
            config = PipelineConfig.from_yaml(args.config)
            config.validate()
            logger.info(f"Loaded configuration from {args.config}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            sys.exit(1)

    # Add config to task metadata if provided
    if config:
        for task in tasks:
            task.metadata = task.metadata or {}
            task.metadata['config_file'] = str(args.config)

    # Check disk space
    if args.check_space:
        try:
            disk_info = check_disk_space(
                output_dir=args.output,
                n_pdb_files=len(tasks),
                raise_on_insufficient=True
            )
            logger.info(f"Disk space OK: {disk_info.free_mb:.1f} MB available")
        except Exception as e:
            logger.error(f"Insufficient disk space: {e}")
            sys.exit(1)

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    # Initialize batch processor
    processor = ParallelBatchProcessor(
        n_jobs=args.jobs,
        checkpoint_dir=args.output / ".checkpoints",
        enable_checkpoints=not args.no_checkpoints,
        checkpoint_frequency=args.checkpoint_freq,
        memory_monitor=True
    )

    logger.info(f"Processing {len(tasks)} tasks")
    logger.info(f"Parallel jobs: {args.jobs}")
    logger.info(f"Checkpoints: {'enabled' if not args.no_checkpoints else 'disabled'}")
    logger.info(f"Output directory: {args.output}")

    # Process batch
    try:
        results = processor.process_batch(
            tasks=tasks,
            process_func=process_single_structure,
            resume=args.resume,
            show_progress=not args.no_progress
        )

        # Generate summary
        summary = processor.generate_summary(results)

        logger.info("=" * 60)
        logger.info("Batch Processing Complete")
        logger.info("=" * 60)
        logger.info(f"Total tasks: {summary['total_tasks']}")
        logger.info(f"Successful: {summary['successful']}")
        logger.info(f"Failed: {summary['failed']}")
        logger.info(f"Success rate: {summary['success_rate']*100:.1f}%")
        logger.info(f"Total time: {summary['total_time_seconds']:.1f}s")
        logger.info(f"Average time: {summary['average_time_seconds']:.1f}s per task")

        # Save results
        results_file = args.output / "batch_results.json"
        processor.save_results(results, results_file, include_errors=True)
        logger.info(f"Results saved to: {results_file}")

        # Print failed tasks
        if summary['failed'] > 0:
            logger.warning("\nFailed tasks:")
            for failed in summary['failed_tasks']:
                logger.warning(f"  {failed['pdb_id']}: {failed['error']}")

        # Exit code
        sys.exit(0 if summary['failed'] == 0 else 1)

    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
