#!/usr/bin/env python3
"""
Example script demonstrating the use of pairlist.csv integration
in the post-docking analysis pipeline.
"""

import sys
from pathlib import Path

# Add the project directory to the path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def example_with_pairlist():
    """Example showing how to use pairlist.csv integration."""
    print("🧪 Example: Using pairlist.csv for accurate receptor-ligand mapping")
    print("=" * 60)
    
    try:
        # Import necessary modules
        from post_docking_analysis.pipeline import PostDockingAnalysisPipeline
        from post_docking_analysis.config_manager import ConfigManager
        
        # Create configuration
        config = ConfigManager()
        
        # Set up paths
        input_dir = project_dir  # Assuming current directory has GNINA output
        output_dir = project_dir / "example_results"
        
        # Configure analysis
        config.set("paths.input_dir", str(input_dir))
        config.set("paths.output_dir", str(output_dir))
        config.set("analysis.docking_types", ["gnina"])
        config.set("analysis.binding_affinity_analysis", True)
        config.set("analysis.generate_visualizations", True)
        
        # Set dynamic strong binder threshold
        config.set("binding_affinity.strong_binder_threshold", "auto")
        
        print(f"📂 Input directory: {input_dir}")
        print(f"📂 Output directory: {output_dir}")
        
        # Initialize pipeline
        pipeline = PostDockingAnalysisPipeline(
            input_dir=str(input_dir),
            output_dir=str(output_dir),
            config_file=None
        )
        
        # Update pipeline configuration
        pipeline.config = config
        
        # Check if pairlist.csv exists
        pairlist_file = input_dir / "pairlist.csv"
        if pairlist_file.exists():
            print(f"✅ Found pairlist.csv: {pairlist_file}")
            print("   Using pairlist for accurate receptor-ligand mapping")
        else:
            print("⚠️  No pairlist.csv found, using filename pattern matching")
        
        # Run analysis (commented out to avoid actual execution)
        # success = pipeline.run_pipeline()
        
        print("✅ Pipeline configured successfully!")
        print("\nTo run the actual analysis, uncomment the run_pipeline() line")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in example: {e}")
        return False

def example_preprocessing_with_pairlist():
    """Example showing preprocessing with pairlist integration."""
    print("\n🧪 Example: Preprocessing with pairlist integration")
    print("=" * 60)
    
    try:
        from post_docking_analysis.preprocess import validate_directory_structure
        
        # Validate directory structure
        input_dir = project_dir
        validation = validate_directory_structure(input_dir)
        
        print(f"📂 Validating directory: {input_dir}")
        print(f"✅ GNINA output directory: {validation['gnina_out_dir']}")
        
        if validation['pairlist_file']:
            print(f"✅ Found pairlist file: {validation['pairlist_file']}")
        else:
            print("⚠️  No pairlist.csv found")
            
        if validation['receptors_dir']:
            print(f"✅ Found receptors directory: {validation['receptors_dir']}")
            
        print("✅ Directory validation completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in preprocessing example: {e}")
        return False

def main():
    """Run examples."""
    print("🚀 Post-Docking Analysis - Pairlist Integration Examples")
    print("=" * 60)
    
    # Run examples
    examples = [
        example_with_pairlist,
        example_preprocessing_with_pairlist
    ]
    
    results = []
    for example_func in examples:
        try:
            result = example_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Example {example_func.__name__} failed: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Results: {passed}/{total} examples passed")
    
    if passed == total:
        print("🎉 All examples completed successfully!")
        return 0
    else:
        print("⚠️  Some examples had issues!")
        return 1

if __name__ == "__main__":
    sys.exit(main())