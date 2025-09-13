"""
Example execution script for post-docking analysis pipeline.

This script demonstrates how to run the pipeline with different configurations.
"""
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the pipeline
sys.path.insert(0, str(Path(__file__).parent.parent))

from post_docking_analysis.pipeline import PostDockingAnalysisPipeline
from post_docking_analysis.config_manager import ConfigManager

def example_basic_run():
    """Example of a basic pipeline run."""
    print("=== Basic Pipeline Run ===")
    
    # Initialize pipeline with default settings
    pipeline = PostDockingAnalysisPipeline(
        input_dir="./sample_data",
        output_dir="./results_basic"
    )
    
    # Run the pipeline
    success = pipeline.run_pipeline()
    
    if success:
        print("✅ Basic run completed successfully!")
    else:
        print("❌ Basic run failed!")

def example_config_run():
    """Example of running the pipeline with a configuration file."""
    print("\n=== Configuration-Based Run ===")
    
    # Create a sample configuration
    config = ConfigManager()
    config.update({
        "input_dir": "./sample_data",
        "output_dir": "./results_config",
        "split_complexes": True,
        "extract_apo_proteins": True,
        "extract_ligands": True,
        "analyze_binding_affinity": True,
        "generate_visualizations": True,
        "create_summary_reports": True,
        "fix_chains": False
    })
    
    # Save configuration to file
    config.save_config("./example_config.json")
    
    # Initialize pipeline with configuration
    pipeline = PostDockingAnalysisPipeline(
        input_dir=config.get("input_dir"),
        output_dir=config.get("output_dir")
    )
    
    # Run the pipeline
    success = pipeline.run_pipeline()
    
    if success:
        print("✅ Configuration-based run completed successfully!")
    else:
        print("❌ Configuration-based run failed!")

def example_minimal_run():
    """Example of a minimal pipeline run."""
    print("\n=== Minimal Pipeline Run ===")
    
    # Create a minimal configuration
    config = ConfigManager()
    config.update({
        "input_dir": "./sample_data",
        "output_dir": "./results_minimal",
        "split_complexes": False,
        "extract_apo_proteins": False,
        "extract_ligands": False,
        "analyze_binding_affinity": True,
        "generate_visualizations": False,
        "create_summary_reports": True
    })
    
    # Initialize pipeline
    pipeline = PostDockingAnalysisPipeline(
        input_dir=config.get("input_dir"),
        output_dir=config.get("output_dir")
    )
    
    # Run the pipeline
    success = pipeline.run_pipeline()
    
    if success:
        print("✅ Minimal run completed successfully!")
    else:
        print("❌ Minimal run failed!")

if __name__ == "__main__":
    # Run examples
    example_basic_run()
    example_config_run()
    example_minimal_run()
    
    print("\n🎉 All examples completed!")
