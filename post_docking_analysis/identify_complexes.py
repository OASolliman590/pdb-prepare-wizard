#!/usr/bin/env python3
"""
Script to identify receptor-ligand pairs from docking file names.

This script helps identify which receptors and ligands correspond to each other
based on file naming conventions.
"""

import re
import argparse
from pathlib import Path
from collections import defaultdict

def identify_complex_pairs(gnina_out_dir, receptors_dir=None):
    """
    Identify receptor-ligand pairs from file names.
    
    Parameters
    ----------
    gnina_out_dir : Path
        Directory containing GNINA output files
    receptors_dir : Path, optional
        Directory containing receptor files
        
    Returns
    -------
    dict
        Dictionary mapping complexes to their components
    """
    gnina_out_dir = Path(gnina_out_dir)
    
    # Find all SDF files (ligand poses)
    sdf_files = list(gnina_out_dir.glob("*_top.sdf"))
    log_files = list(gnina_out_dir.glob("*_log"))
    
    if not sdf_files and not log_files:
        print("❌ No GNINA output files found")
        return {}
    
    # Extract complex names
    complexes = set()
    
    # From SDF files
    for sdf_file in sdf_files:
        name = sdf_file.stem.replace('_top', '')
        complexes.add(name)
        
    # From log files
    for log_file in log_files:
        name = log_file.stem.replace('_log', '')
        complexes.add(name)
    
    print(f"📊 Found {len(complexes)} unique complexes")
    
    # Try to parse complex names to identify receptors and ligands
    complex_info = {}
    
    for complex_name in complexes:
        # Common naming patterns:
        # 1. RECEPTOR_SITE_LIGAND (e.g., "3LN1_COX2_prep_catalytic_3LN1_COX2_CEL")
        # 2. RECEPTOR_LIGAND (e.g., "protein_ligand")
        # 3. TARGET_SITE_COMPOUND (e.g., "COX2_catalytic_aspirin")
        
        parts = complex_name.split('_')
        
        # Attempt to identify receptor and ligand
        receptor = None
        ligand = None
        site = None
        
        if len(parts) >= 3:
            # Look for common receptor patterns
            if 'prep' in parts:
                prep_index = parts.index('prep')
                if prep_index > 0:
                    receptor = '_'.join(parts[:prep_index])
                    site_start = prep_index + 1
                    if site_start < len(parts):
                        site = parts[site_start]
                        ligand = '_'.join(parts[site_start + 1:]) if site_start + 1 < len(parts) else None
            else:
                # Simpler pattern: assume first part is receptor, rest is ligand
                receptor = parts[0]
                ligand = '_'.join(parts[1:])
        else:
            # Very simple pattern
            receptor = parts[0] if parts else complex_name
            ligand = parts[1] if len(parts) > 1 else "unknown"
        
        complex_info[complex_name] = {
            'receptor': receptor or "unknown",
            'ligand': ligand or "unknown",
            'site': site or "unknown",
            'sdf_file': f"{complex_name}_top.sdf" if any(f.stem == f"{complex_name}_top" for f in sdf_files) else None,
            'log_file': f"{complex_name}_log" if any(f.stem == f"{complex_name}_log" for f in log_files) else None
        }
    
    return complex_info

def match_receptors_to_complexes(complex_info, receptors_dir):
    """
    Match receptor files to complexes based on naming.
    
    Parameters
    ----------
    complex_info : dict
        Dictionary of complex information
    receptors_dir : Path
        Directory containing receptor files
        
    Returns
    -------
    dict
        Updated complex_info with matched receptor files
    """
    if not receptors_dir or not receptors_dir.exists():
        return complex_info
        
    receptor_files = list(receptors_dir.glob("*.pdbqt"))
    
    # Create a mapping of receptor names to files
    receptor_map = {}
    for receptor_file in receptor_files:
        name = receptor_file.stem
        # Remove common suffixes
        for suffix in ['_prep', '_receptor', '_protein']:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break
        receptor_map[name] = receptor_file
    
    # Match complexes to receptors
    for complex_name, info in complex_info.items():
        receptor_name = info['receptor']
        
        # Direct match
        if receptor_name in receptor_map:
            info['receptor_file'] = str(receptor_map[receptor_name])
            continue
            
        # Partial match
        for name, file_path in receptor_map.items():
            if receptor_name in name or name in receptor_name:
                info['receptor_file'] = str(file_path)
                break
    
    return complex_info

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Identify receptor-ligand pairs from docking file names")
    parser.add_argument("gnina_out_dir", help="Directory containing GNINA output files")
    parser.add_argument("-r", "--receptors", help="Directory containing receptor files")
    
    args = parser.parse_args()
    
    # Identify complexes
    complex_info = identify_complex_pairs(args.gnina_out_dir)
    
    # Match receptors if directory provided
    if args.receptors:
        receptors_dir = Path(args.receptors)
        complex_info = match_receptors_to_complexes(complex_info, receptors_dir)
    
    # Print results
    print("\n🧬 Complex Information:")
    print("=" * 80)
    
    for complex_name, info in complex_info.items():
        print(f"\nComplex: {complex_name}")
        print(f"  Receptor: {info['receptor']}")
        print(f"  Site: {info['site']}")
        print(f"  Ligand: {info['ligand']}")
        if 'receptor_file' in info:
            print(f"  Receptor file: {info['receptor_file']}")
        if info['sdf_file']:
            print(f"  SDF file: {info['sdf_file']}")
        if info['log_file']:
            print(f"  Log file: {info['log_file']}")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"  Total complexes: {len(complex_info)}")
    
    receptors = set(info['receptor'] for info in complex_info.values())
    ligands = set(info['ligand'] for info in complex_info.values())
    
    print(f"  Unique receptors: {len(receptors)}")
    print(f"  Unique ligands: {len(ligands)}")
    
    return 0

if __name__ == "__main__":
    exit(main())