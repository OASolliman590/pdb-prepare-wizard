"""
Simplified CLI for Post-Docking Analysis Pipeline.

New simplified interface:
- sdf_folder: Folder with SDF pose files
- log_folder: Folder with log files (can be same as sdf_folder)
- receptors_folder: Folder with receptor PDBQT files
- pairlist_file: Optional pairlist.csv
"""
import argparse
import sys
from pathlib import Path

from .simplified_pipeline import SimplifiedPostDockingPipeline


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Simplified Post-Docking Analysis Pipeline (GNINA Focus)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with 3 folders
  python -m post_docking_analysis.simplified_cli \\
    --sdf-folder /path/to/sdf \\
    --log-folder /path/to/logs \\
    --receptors-folder /path/to/receptors \\
    --output /path/to/output
  
  # With pairlist.csv
  python -m post_docking_analysis.simplified_cli \\
    --sdf-folder /path/to/sdf \\
    --log-folder /path/to/logs \\
    --receptors-folder /path/to/receptors \\
    --output /path/to/output \\
    --pairlist /path/to/pairlist.csv
  
  # Log folder same as SDF folder
  python -m post_docking_analysis.simplified_cli \\
    --sdf-folder /path/to/docking_results \\
    --log-folder /path/to/docking_results \\
    --receptors-folder /path/to/receptors \\
    --output /path/to/output
        """
    )
    
    # Required arguments
    parser.add_argument(
        "--sdf-folder",
        required=True,
        help="Folder containing SDF pose files"
    )
    parser.add_argument(
        "--log-folder",
        required=True,
        help="Folder containing log files (can be same as sdf-folder)"
    )
    parser.add_argument(
        "--receptors-folder",
        required=True,
        help="Folder containing receptor PDBQT files"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output directory for results"
    )
    
    # Optional arguments
    parser.add_argument(
        "--pairlist",
        help="Path to pairlist.csv for receptor-ligand mapping"
    )
    
    # Analysis options
    parser.add_argument(
        "--no-rmsd",
        action="store_true",
        help="Skip RMSD analysis"
    )
    parser.add_argument(
        "--no-visualizations",
        action="store_true",
        help="Skip visualization generation"
    )
    
    args = parser.parse_args()
    
    # Validate paths
    sdf_folder = Path(args.sdf_folder)
    log_folder = Path(args.log_folder)
    receptors_folder = Path(args.receptors_folder)
    
    if not sdf_folder.exists():
        print(f"❌ SDF folder does not exist: {sdf_folder}")
        return 1
    
    if not log_folder.exists():
        print(f"❌ Log folder does not exist: {log_folder}")
        return 1
    
    if not receptors_folder.exists():
        print(f"❌ Receptors folder does not exist: {receptors_folder}")
        return 1
    
    # Initialize and run pipeline
    pipeline = SimplifiedPostDockingPipeline(
        sdf_folder=str(sdf_folder),
        log_folder=str(log_folder),
        receptors_folder=str(receptors_folder),
        output_dir=str(args.output),
        pairlist_file=args.pairlist
    )
    
    success = pipeline.run()
    
    if success:
        print("\n✅ Post-docking analysis completed successfully!")
        print(f"📂 Results saved to: {args.output}")
        return 0
    else:
        print("\n❌ Post-docking analysis failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())

