"""
Command-line interface for post-docking analysis pipeline.
"""
import argparse
import sys
from pathlib import Path

from .pipeline import PostDockingAnalysisPipeline
from .config_manager import ConfigManager

def main():
    """
    Main function to run the pipeline from command line.
    """
    parser = argparse.ArgumentParser(
        description="Post-Docking Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings
  python -m post_docking_analysis
  
  # Specify input and output directories
  python -m post_docking_analysis -i /path/to/docking/results -o /path/to/output
  
  # Use a configuration file
  python -m post_docking_analysis --config my_config.json
  
  # Run with specific options
  python -m post_docking_analysis -i /path/to/results --no-visualizations
        """
    )
    
    # Input/Output arguments
    parser.add_argument("-i", "--input", 
                        help="Input directory containing docking results")
    parser.add_argument("-o", "--output", 
                        help="Output directory for results")
    parser.add_argument("--config", 
                        help="Configuration file path")
    
    # Processing options
    parser.add_argument("--no-split", action="store_true",
                        help="Skip complex splitting step")
    parser.add_argument("--no-apo", action="store_true",
                        help="Skip apo protein extraction")
    parser.add_argument("--no-ligands", action="store_true",
                        help="Skip ligand extraction")
    parser.add_argument("--no-analysis", action="store_true",
                        help="Skip binding affinity analysis")
    parser.add_argument("--no-visualizations", action="store_true",
                        help="Skip visualization generation")
    parser.add_argument("--no-reports", action="store_true",
                        help="Skip report generation")
    parser.add_argument("--fix-chains", action="store_true",
                        help="Fix chain issues in structures")
    
    # Directory structure
    parser.add_argument("--structure", choices=["auto", "single", "multi"],
                        help="Directory structure type (auto/single/multi)")
    
    # Scoring options
    parser.add_argument("--no-cnn", action="store_true",
                        help="Disable CNN scoring")
    
    # Output format options
    parser.add_argument("--no-csv", action="store_true",
                        help="Disable CSV output")
    parser.add_argument("--no-excel", action="store_true",
                        help="Disable Excel output")
    parser.add_argument("--no-pdb", action="store_true",
                        help="Disable PDB output")
    parser.add_argument("--no-mol2", action="store_true",
                        help="Disable MOL2 output")
    
    # Help and info
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output")
    parser.add_argument("--version", action="version", version="Post-Docking Analysis Pipeline 1.0")
    
    args = parser.parse_args()
    
    # Load configuration
    config_manager = ConfigManager(args.config)
    
    # Override configuration with command-line arguments
    if args.input:
        config_manager.set("input_dir", args.input)
    if args.output:
        config_manager.set("output_dir", args.output)
        
    # Processing options
    if args.no_split:
        config_manager.set("split_complexes", False)
    if args.no_apo:
        config_manager.set("extract_apo_proteins", False)
    if args.no_ligands:
        config_manager.set("extract_ligands", False)
    if args.no_analysis:
        config_manager.set("analyze_binding_affinity", False)
    if args.no_visualizations:
        config_manager.set("generate_visualizations", False)
    if args.no_reports:
        config_manager.set("create_summary_reports", False)
    if args.fix_chains:
        config_manager.set("fix_chains", True)
        
    # Directory structure
    if args.structure:
        structure_map = {"auto": "AUTO", "single": "SINGLE_FOLDER", "multi": "MULTI_FOLDER"}
        config_manager.set("directory_structure", structure_map[args.structure])
        
    # Scoring options
    if args.no_cnn:
        config_manager.set("use_cnn_score", False)
        
    # Output format options
    if args.no_csv:
        config_manager.set("output_csv", False)
    if args.no_excel:
        config_manager.set("output_excel", False)
    if args.no_pdb:
        config_manager.set("output_pdb", False)
    if args.no_mol2:
        config_manager.set("output_mol2", False)
    
    # Initialize pipeline
    pipeline = PostDockingAnalysisPipeline(
        input_dir=config_manager.get("input_dir"),
        output_dir=config_manager.get("output_dir")
    )
    
    # Update pipeline with configuration
    # (In a full implementation, you would pass the config manager to the pipeline)
    
    # Run pipeline
    success = pipeline.run_pipeline()
    
    if success:
        print("\n🎉 Pipeline completed successfully!")
        print(f"📁 Results saved to: {pipeline.output_dir}")
    else:
        print("\n❌ Pipeline failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()