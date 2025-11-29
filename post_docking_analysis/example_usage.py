#!/usr/bin/env python3
"""
Example script demonstrating how to use the Post-Docking Analysis System.

This script shows both command-line and programmatic usage patterns.
"""

import sys
from pathlib import Path

# Add the post_docking_analysis directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from post_docking_analysis import PostDockingAnalysisPipeline

def example_basic_usage():
    """Example of basic usage with minimal configuration."""
    print("🧪 Running basic post-docking analysis example...")
    
    # Initialize pipeline with basic configuration
    pipeline = PostDockingAnalysisPipeline(
        input_dir="./example_data",  # Replace with your data path
        output_dir="./results/basic_analysis"
    )
    
    # Run the analysis
    success = pipeline.run_pipeline()
    
    if success:
        print("✅ Basic analysis completed successfully!")
        print(f"📁 Results saved to: {pipeline.output_dir}")
    else:
        print("❌ Basic analysis failed!")
    
    return success

def example_advanced_usage():
    """Example of advanced usage with custom configuration."""
    print("\n🧪 Running advanced post-docking analysis example...")
    
    # Custom configuration
    config = {
        "analysis": {
            "docking_types": ["gnina"],
            "comparative_benchmark": "*",  # Analyze all complexes
            "binding_affinity_analysis": True,
            "rmsd_analysis": True,
            "generate_visualizations": True,
            "extract_poses": True
        },
        "binding_affinity": {
            "strong_binder_threshold": -8.0,
            "top_performers_count": 10,
            "analyze_by_protein": True,
            "analyze_by_ligand": True
        },
        "rmsd": {
            "clustering_method": "kmeans",
            "kmeans_clusters": 3
        },
        "visualization": {
            "dpi": 300,
            "generate_3d": True,
            "generate_2d_interactions": True
        },
        "advanced": {
            "enable_plugins": True,
            "log_level": "INFO"
        }
    }
    
    # Initialize pipeline
    pipeline = PostDockingAnalysisPipeline(
        input_dir="./example_data",  # Replace with your data path
        output_dir="./results/advanced_analysis"
    )
    
    # Update configuration
    pipeline.config.update(config)
    
    # Run the analysis
    success = pipeline.run_pipeline()
    
    if success:
        print("✅ Advanced analysis completed successfully!")
        print(f"📁 Results saved to: {pipeline.output_dir}")
        
        # Show some results
        if 'best_poses' in pipeline.results:
            best_poses = pipeline.results['best_poses']
            print(f"📊 Analyzed {len(best_poses)} complexes")
            print(f"🏆 Best binding affinity: {best_poses['vina_affinity'].min():.2f} kcal/mol")
    else:
        print("❌ Advanced analysis failed!")
    
    return success

def example_targeted_analysis():
    """Example of targeted analysis focusing on specific proteins."""
    print("\n🧪 Running targeted post-docking analysis example...")
    
    # Configuration for targeted analysis
    config = {
        "analysis": {
            "docking_types": ["gnina"],
            "comparative_benchmark": "COX2",  # Focus on COX2 complexes
            "binding_affinity_analysis": True,
            "rmsd_analysis": True
        },
        "binding_affinity": {
            "strong_binder_threshold": -9.0,  # Stricter threshold for strong binders
            "top_performers_count": 5
        },
        "visualization": {
            "dpi": 600,  # High-resolution images
            "generate_3d": True
        }
    }
    
    # Initialize pipeline
    pipeline = PostDockingAnalysisPipeline(
        input_dir="./example_data",  # Replace with your data path
        output_dir="./results/targeted_analysis"
    )
    
    # Update configuration
    pipeline.config.update(config)
    
    # Run the analysis
    success = pipeline.run_pipeline()
    
    if success:
        print("✅ Targeted analysis completed successfully!")
        print(f"📁 Results saved to: {pipeline.output_dir}")
    else:
        print("❌ Targeted analysis failed!")
    
    return success

def main():
    """Run all examples."""
    print("🚀 Post-Docking Analysis System Examples")
    print("=" * 50)
    
    # Run examples
    examples = [
        example_basic_usage,
        example_advanced_usage,
        example_targeted_analysis
    ]
    
    results = []
    for example_func in examples:
        try:
            result = example_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Example failed with error: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Example Results Summary:")
    print(f"   Successful examples: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 All examples completed successfully!")
        return 0
    else:
        print("⚠️  Some examples failed. Check the logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())