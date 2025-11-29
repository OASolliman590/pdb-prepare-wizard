"""
Command-line interface for post-docking analysis pipeline.
"""
import argparse
import sys
from pathlib import Path

# Use relative imports when run as module, absolute when run directly
try:
    from . import config_manager
    from . import pipeline
except ImportError:
    import config_manager
    import pipeline

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
  
  # Run preprocessing to generate all_scores.csv
  python -m post_docking_analysis.preprocess /path/to/docking/results
  
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
    
    # Preprocessing options
    parser.add_argument("--preprocess", action="store_true",
                        help="Run preprocessing to generate all_scores.csv and identify pairs")
    parser.add_argument("--force", action="store_true",
                        help="Force regeneration of all_scores.csv during preprocessing")
    parser.add_argument("--pairlist", 
                        help="Path to pairlist.csv for accurate receptor-ligand mapping")
    
    # Help and info
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output")
    parser.add_argument("--version", action="version", version="Post-Docking Analysis Pipeline 1.0")
    
    args = parser.parse_args()
    
    # If preprocessing is requested, run the preprocessing script
    if args.preprocess:
        from .preprocess import preprocess_analysis
        success = preprocess_analysis(
            args.input or ".",
            args.output,
            args.pairlist,
            args.force
        )
        sys.exit(0 if success else 1)
    
    # Load configuration
    config_manager_instance = config_manager.ConfigManager(args.config)
    
    # Override configuration with command-line arguments
    if args.input:
        config_manager_instance.set("paths.input_dir", args.input)
    if args.output:
        config_manager_instance.set("paths.output_dir", args.output)
        
    # Processing options
    if args.no_split:
        config_manager_instance.set("analysis.split_complexes", False)
    if args.no_apo:
        config_manager_instance.set("analysis.extract_apo_proteins", False)
    if args.no_ligands:
        config_manager_instance.set("analysis.extract_ligands", False)
    if args.no_analysis:
        config_manager_instance.set("analysis.binding_affinity_analysis", False)
    if args.no_visualizations:
        config_manager_instance.set("analysis.generate_visualizations", False)
    if args.no_reports:
        config_manager_instance.set("analysis.create_summary_reports", False)
    if args.fix_chains:
        config_manager_instance.set("advanced.fix_chains", True)
        
    # Directory structure
    if args.structure:
        structure_map = {"auto": "AUTO", "single": "SINGLE_FOLDER", "multi": "MULTI_FOLDER"}
        config_manager_instance.set("advanced.directory_structure", structure_map[args.structure])
        
    # Scoring options
    if args.no_cnn:
        config_manager_instance.set("analysis.use_cnn_score", False)
        
    # Output format options
    if args.no_csv:
        config_manager_instance.set("output.csv", False)
    if args.no_excel:
        config_manager_instance.set("output.excel", False)
    if args.no_pdb:
        config_manager_instance.set("output.pdb", False)
    if args.no_mol2:
        config_manager_instance.set("output.mol2", False)
    
    # Initialize pipeline
    pipeline_instance = pipeline.PostDockingAnalysisPipeline(
        input_dir=config_manager_instance.get("paths.input_dir"),
        output_dir=config_manager_instance.get("paths.output_dir"),
        config_file=args.config
    )
    
    # Update pipeline with configuration
    # (In a full implementation, you would pass the config manager to the pipeline)
    
    # Run pipeline
    success = pipeline_instance.run_pipeline()
    
    if success:
        print("\n🎉 Pipeline completed successfully!")
        print(f"📁 Results saved to: {pipeline_instance.output_dir}")
    else:
        print("\n❌ Pipeline failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()