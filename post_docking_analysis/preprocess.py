#!/usr/bin/env python3
"""
Comprehensive preprocessing script for the post-docking analysis pipeline.

This script handles all the necessary preprocessing steps:
1. Generates all_scores.csv from GNINA log files if needed
2. Identifies receptor-ligand pairs using pairlist.csv
3. Validates directory structure
4. Creates any missing directories
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project directory to the path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from post_docking_analysis.generate_scores_csv import generate_all_scores_csv
from post_docking_analysis.identify_pairs import identify_receptor_ligand_pairs

def validate_directory_structure(input_dir, receptors_dir=None):
    """
    Validate the directory structure for GNINA analysis.
    
    Parameters
    ----------
    input_dir : Path
        Input directory containing docking results
    receptors_dir : Path, optional
        Directory containing receptor files
        
    Returns
    -------
    dict
        Dictionary with validation results
    """
    results = {
        'valid': True,
        'issues': [],
        'gnina_out_dir': None,
        'receptors_dir': None,
        'pairlist_file': None
    }
    
    # Check for gnina_out directory
    gnina_out_dir = input_dir / "gnina_out"
    if gnina_out_dir.exists():
        results['gnina_out_dir'] = gnina_out_dir
        print(f"✅ Found GNINA output directory: {gnina_out_dir}")
        
        # Check for log files or SDF files
        log_files = list(gnina_out_dir.glob("*.log"))
        sdf_files = list(gnina_out_dir.glob("*_top.sdf"))
        
        if not log_files and not sdf_files:
            results['valid'] = False
            results['issues'].append(f"No log or SDF files found in {gnina_out_dir}")
        else:
            print(f"📊 Found {len(log_files)} log files and {len(sdf_files)} SDF files")
    else:
        results['valid'] = False
        results['issues'].append(f"GNINA output directory not found: {gnina_out_dir}")
    
    # Check for receptors directory if specified
    if receptors_dir:
        if receptors_dir.exists():
            results['receptors_dir'] = receptors_dir
            receptor_files = list(receptors_dir.glob("*.pdbqt"))
            print(f"✅ Found receptors directory: {receptors_dir}")
            print(f"📊 Found {len(receptor_files)} receptor files")
        else:
            results['issues'].append(f"Receptors directory not found: {receptors_dir}")
    else:
        # Try to find receptors directory automatically
        possible_receptors_dirs = [
            input_dir / "receptors",
            input_dir.parent / "receptors",
            input_dir / "receptors_prep"
        ]
        
        for receptors_dir in possible_receptors_dirs:
            if receptors_dir.exists():
                results['receptors_dir'] = receptors_dir
                receptor_files = list(receptors_dir.glob("*.pdbqt"))
                print(f"✅ Found receptors directory: {receptors_dir}")
                print(f"📊 Found {len(receptor_files)} receptor files")
                break
    
    # Look for pairlist.csv
    possible_pairlist_files = [
        input_dir / "pairlist.csv",
        input_dir.parent / "pairlist.csv"
    ]
    
    for pairlist_file in possible_pairlist_files:
        if pairlist_file.exists():
            results['pairlist_file'] = pairlist_file
            print(f"✅ Found pairlist file: {pairlist_file}")
            break
    
    return results

def preprocess_analysis(input_dir, output_dir=None, receptors_dir=None, force_regeneration=False):
    """
    Preprocess the analysis by handling all necessary setup steps.
    
    Parameters
    ----------
    input_dir : str
        Input directory containing docking results
    output_dir : str, optional
        Output directory for results
    receptors_dir : str, optional
        Directory containing receptor files
    force_regeneration : bool
        Force regeneration of all_scores.csv even if it exists
        
    Returns
    -------
    bool
        True if preprocessing successful, False otherwise
    """
    input_dir = Path(input_dir).resolve()
    
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return False
        
    print(f"🔄 Starting preprocessing for: {input_dir}")
    
    # Validate directory structure
    validation = validate_directory_structure(input_dir, receptors_dir and Path(receptors_dir))
    
    if not validation['valid']:
        print("❌ Directory structure validation failed:")
        for issue in validation['issues']:
            print(f"  - {issue}")
        return False
    
    gnina_out_dir = validation['gnina_out_dir']
    receptors_dir = validation['receptors_dir']
    pairlist_file = validation['pairlist_file']
    
    # Create output directory if specified
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created output directory: {output_dir}")
    
    # Check for all_scores.csv and generate if needed
    all_scores_file = gnina_out_dir / "all_scores.csv"
    
    if not all_scores_file.exists() or force_regeneration:
        print("🔄 Generating all_scores.csv from log files...")
        if not generate_all_scores_csv(gnina_out_dir, all_scores_file, pairlist_file):
            print("❌ Failed to generate all_scores.csv")
            return False
        print("✅ Successfully generated all_scores.csv")
    else:
        print("✅ Found existing all_scores.csv")
    
    # Identify receptor-ligand pairs
    print("🔍 Identifying receptor-ligand pairs...")
    pairs = identify_receptor_ligand_pairs(gnina_out_dir, receptors_dir, pairlist_file)
    
    if pairs:
        pairs_file = gnina_out_dir / "receptor_ligand_pairs.json"
        try:
            import json
            with open(pairs_file, 'w') as f:
                json.dump(pairs, f, indent=2)
            print(f"✅ Saved receptor-ligand pairs to: {pairs_file}")
        except Exception as e:
            print(f"⚠️  Failed to save pairs file: {e}")
    else:
        print("⚠️  No receptor-ligand pairs identified")
    
    print("✅ Preprocessing completed successfully!")
    return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Preprocess GNINA docking results for analysis")
    parser.add_argument("input_dir", help="Input directory containing docking results")
    parser.add_argument("-o", "--output", help="Output directory for results")
    parser.add_argument("-r", "--receptors", help="Directory containing receptor files")
    parser.add_argument("-f", "--force", action="store_true", 
                        help="Force regeneration of all_scores.csv even if it exists")
    parser.add_argument("-v", "--verbose", action="store_true", 
                        help="Enable verbose output")
    
    args = parser.parse_args()
    
    success = preprocess_analysis(
        args.input_dir, 
        args.output, 
        args.receptors, 
        args.force
    )
    
    if success:
        print("\n🎉 Preprocessing completed successfully!")
        return 0
    else:
        print("\n❌ Preprocessing failed!")
        return 1

if __name__ == "__main__":
    exit(main())