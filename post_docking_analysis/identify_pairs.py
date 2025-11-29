#!/usr/bin/env python3
"""
Script to identify receptor-ligand pairs from GNINA output files.

This script analyzes the naming patterns in GNINA output files and uses
the pairlist.csv file to accurately identify which receptor files 
correspond to which ligand files.
"""

import os
import re
import json
import csv
import argparse
from pathlib import Path
from collections import defaultdict

def load_pairlist(pairlist_file):
    """
    Load receptor-ligand pairs from pairlist.csv file.
    
    Parameters
    ----------
    pairlist_file : Path
        Path to pairlist.csv file
        
    Returns
    -------
    dict
        Dictionary mapping complexes to their receptor-ligand pairs
    """
    pairs = {}
    
    try:
        with open(pairlist_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                receptor = row['receptor']
                ligand = row['ligand']
                site_id = row['site_id']
                
                # Create complex identifier
                complex_name = f"{receptor}_{site_id}_{ligand}"
                pairs[complex_name] = {
                    'receptor': receptor,
                    'site_id': site_id,
                    'ligand': ligand
                }
                
        print(f"✅ Loaded {len(pairs)} receptor-ligand pairs from {pairlist_file}")
        return pairs
        
    except Exception as e:
        print(f"⚠️  Error loading pairlist.csv: {e}")
        return {}

def identify_receptor_ligand_pairs(gnina_out_dir, receptors_dir=None, pairlist_file=None):
    """
    Identify receptor-ligand pairs from GNINA output files.
    
    Parameters
    ----------
    gnina_out_dir : Path
        Directory containing GNINA output files (_top.sdf and .log files)
    receptors_dir : Path, optional
        Directory containing receptor files (.pdbqt files)
    pairlist_file : Path, optional
        Path to pairlist.csv file for accurate mapping
        
    Returns
    -------
    dict
        Dictionary mapping complexes to their receptor-ligand pairs
    """
    gnina_out_dir = Path(gnina_out_dir)
    
    # Load pairs from pairlist.csv if available
    if pairlist_file and Path(pairlist_file).exists():
        print("🔍 Using pairlist.csv for accurate receptor-ligand mapping...")
        pairs = load_pairlist(pairlist_file)
        if pairs:
            # Enhance pairs with file information
            sdf_files = list(gnina_out_dir.glob("*_top.sdf"))
            log_files = list(gnina_out_dir.glob("*.log"))
            
            # Match files to pairs
            for complex_name, pair_info in pairs.items():
                # Look for matching SDF file
                sdf_matches = [f for f in sdf_files if complex_name in f.stem]
                if sdf_matches:
                    pair_info['sdf_file'] = sdf_matches[0].name
                    
                # Look for matching log file
                log_matches = [f for f in log_files if complex_name in f.stem]
                if log_matches:
                    pair_info['log_file'] = log_matches[0].name
                    
            return pairs
    
    # Fallback to filename pattern matching if no pairlist or pairlist failed
    print("🔍 Using filename pattern matching for receptor-ligand identification...")
    
    # Find all SDF and log files
    sdf_files = list(gnina_out_dir.glob("*_top.sdf"))
    log_files = list(gnina_out_dir.glob("*.log"))
    
    print(f"📊 Found {len(sdf_files)} SDF files and {len(log_files)} log files")
    
    # Extract complex names from filenames
    complexes = set()
    
    # From SDF files
    for sdf_file in sdf_files:
        # Remove _top.sdf suffix
        complex_name = sdf_file.stem.replace('_top', '')
        complexes.add(complex_name)
        
    # From log files
    for log_file in log_files:
        # Remove .log suffix
        complex_name = log_file.stem
        complexes.add(complex_name)
        
    print(f"🔍 Identified {len(complexes)} unique complexes")
    
    # Try to identify receptor-ligand patterns
    pairs = {}
    
    for complex_name in complexes:
        # Try to parse the complex name to identify receptor and ligand
        receptor_name = None
        ligand_name = None
        site_id = "unknown"
        
        # Common patterns:
        # 1. RECEPTOR_LIGAND (e.g., 3LN1_COX2_CEL)
        # 2. RECEPTOR_prep_catalytic_LIGAND (e.g., 3LN1_COX2_prep_catalytic_3LN1_COX2_CEL)
        # 3. RECEPTOR_SITE_LIGAND (e.g., 4TRO_INHA_prep_catalytic_4TRO_INHA_NAD)
        
        parts = complex_name.split('_')
        
        if len(parts) >= 3:
            # Look for patterns like RECEPTOR_prep_catalytic_LIGAND
            if 'prep' in parts and 'catalytic' in parts:
                # Find receptor (before 'prep')
                prep_index = parts.index('prep')
                if prep_index > 0:
                    receptor_name = '_'.join(parts[:prep_index])
                
                # Site ID is typically after 'prep'
                site_id = parts[prep_index + 1] if prep_index + 1 < len(parts) else "catalytic"
                
                # Find ligand (after 'catalytic')
                try:
                    catalytic_index = parts.index('catalytic')
                    if catalytic_index + 1 < len(parts):
                        ligand_name = '_'.join(parts[catalytic_index + 1:])
                except ValueError:
                    # 'catalytic' not found, try to infer ligand
                    if receptor_name and len(parts) > prep_index + 2:
                        ligand_name = '_'.join(parts[prep_index + 2:])
            else:
                # Simpler pattern: RECEPTOR_LIGAND or RECEPTOR_SITE_LIGAND
                receptor_name = parts[0]
                site_id = parts[1] if len(parts) > 2 else "catalytic"
                ligand_name = '_'.join(parts[2:]) if len(parts) > 2 else parts[-1]
        elif len(parts) == 2:
            receptor_name = parts[0]
            ligand_name = parts[1]
        else:
            # Single part name
            receptor_name = complex_name
            ligand_name = complex_name
            
        pairs[complex_name] = {
            'receptor': receptor_name,
            'site_id': site_id,
            'ligand': ligand_name,
            'sdf_file': f"{complex_name}_top.sdf" if f"{complex_name}_top.sdf" in [f.name for f in sdf_files] else None,
            'log_file': f"{complex_name}.log" if f"{complex_name}.log" in [f.name for f in log_files] else None
        }
        
    # If receptors directory is provided, try to match receptor files
    if receptors_dir and Path(receptors_dir).exists():
        receptor_files = list(Path(receptors_dir).glob("*.pdbqt"))
        print(f"🔍 Found {len(receptor_files)} receptor files")
        
        # Try to match receptor names with receptor files
        for complex_name, pair_info in pairs.items():
            receptor_name = pair_info['receptor']
            
            # Look for exact match
            exact_matches = [f for f in receptor_files if f.stem == receptor_name]
            if exact_matches:
                pair_info['receptor_file'] = exact_matches[0].name
                continue
                
            # Look for partial matches
            partial_matches = [f for f in receptor_files if receptor_name in f.stem]
            if partial_matches:
                pair_info['receptor_file'] = partial_matches[0].name
                continue
                
            # Try removing common suffixes
            cleaned_receptor = receptor_name.replace('_prep', '').replace('_catalytic', '')
            cleaned_matches = [f for f in receptor_files if cleaned_receptor in f.stem]
            if cleaned_matches:
                pair_info['receptor_file'] = cleaned_matches[0].name
                
    return pairs

def save_pairs_to_file(pairs, output_file):
    """
    Save receptor-ligand pairs to a JSON file.
    
    Parameters
    ----------
    pairs : dict
        Dictionary of receptor-ligand pairs
    output_file : Path
        Output JSON file
    """
    try:
        with open(output_file, 'w') as f:
            json.dump(pairs, f, indent=2)
        print(f"✅ Pairs saved to {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving pairs to file: {e}")
        return False

def print_pairs_summary(pairs):
    """
    Print a summary of the identified pairs.
    
    Parameters
    ----------
    pairs : dict
        Dictionary of receptor-ligand pairs
    """
    print("\n📋 Receptor-Ligand Pairs Summary:")
    print("=" * 50)
    
    for complex_name, info in pairs.items():
        print(f"\nComplex: {complex_name}")
        print(f"  Receptor: {info['receptor']}")
        print(f"  Ligand: {info['ligand']}")
        if 'receptor_file' in info:
            print(f"  Receptor File: {info['receptor_file']}")
        if info['sdf_file']:
            print(f"  SDF File: {info['sdf_file']}")
        if info['log_file']:
            print(f"  Log File: {info['log_file']}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Identify receptor-ligand pairs from GNINA output files")
    parser.add_argument("gnina_out_dir", help="Directory containing GNINA output files")
    parser.add_argument("-r", "--receptors", help="Directory containing receptor files")
    parser.add_argument("-o", "--output", help="Output JSON file to save pairs")
    
    args = parser.parse_args()
    
    pairs = identify_receptor_ligand_pairs(args.gnina_out_dir, args.receptors)
    
    if pairs:
        print_pairs_summary(pairs)
        
        if args.output:
            save_pairs_to_file(pairs, args.output)
            
        print(f"\n🎉 Identified {len(pairs)} receptor-ligand pairs")
        return 0
    else:
        print("\n❌ No pairs identified")
        return 1

if __name__ == "__main__":
    exit(main())