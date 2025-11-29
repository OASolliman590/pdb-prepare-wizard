#!/usr/bin/env python3
"""
PDB Prepare Wizard - Main Entry Point
====================================

Main entry point for the PDB Prepare Wizard pipeline.
Provides access to interactive, CLI, and batch processing modes.

Author: Molecular Docking Pipeline
Version: 2.1.0
"""

import sys
import argparse
from pathlib import Path

def main():
    """Main entry point with mode selection."""
    parser = argparse.ArgumentParser(
        description="PDB Prepare Wizard - Molecular Docking Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  interactive    Interactive mode with user prompts (default)
  cli           Command-line interface for batch processing
  batch         Batch processing of multiple PDB files using configuration files
  
Examples:
  # Interactive mode
  python main.py
  python main.py interactive
  
  # CLI mode
  python main.py cli -p 7CMD
  python main.py cli -p "7CMD,6WX4,1ABC" -o results/
  
  # Batch mode
  python main.py batch -c pdb_batch_config.yaml
  python main.py batch -c pdb_batch_config.txt -o batch_results/
  
  # Get help for specific mode
  python main.py cli --help
  python main.py batch --help
        """
    )
    
    parser.add_argument('mode', nargs='?', default='interactive',
                       choices=['interactive', 'cli', 'batch'],
                       help='Pipeline mode (default: interactive)')
    
    # Add output directory option for interactive mode
    parser.add_argument('-o', '--output', dest='output_dir',
                       help='Output directory for interactive mode')
    
    # Parse known args to handle mode-specific arguments
    args, remaining_args = parser.parse_known_args()
    
    print("🔬 PDB Prepare Wizard v2.1.0")
    print("=" * 40)
    
    if args.mode == 'interactive':
        print("Starting Interactive Mode...")
        try:
            from interactive_pipeline import run_interactive_pipeline
            # Use output directory from argument if provided
            run_interactive_pipeline(output_dir=getattr(args, 'output_dir', None))
        except ImportError as e:
            print(f"❌ Failed to import interactive pipeline: {e}")
            sys.exit(1)
            
    elif args.mode == 'cli':
        print("Starting CLI Mode...")
        try:
            from cli_pipeline import main as cli_main
            # Replace sys.argv with remaining args for CLI parsing
            sys.argv = ['cli_pipeline.py'] + remaining_args
            cli_main()
        except ImportError as e:
            print(f"❌ Failed to import CLI pipeline: {e}")
            sys.exit(1)
            
    elif args.mode == 'batch':
        print("Starting Batch Processing Mode...")
        try:
            from batch_pdb_preparation import main as batch_main
            # Replace sys.argv with remaining args for batch parsing
            sys.argv = ['batch_pdb_preparation.py'] + remaining_args
            batch_main()
        except ImportError as e:
            print(f"❌ Failed to import batch processing pipeline: {e}")
            sys.exit(1)
    
    else:
        parser.error(f"Unknown mode: {args.mode}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

