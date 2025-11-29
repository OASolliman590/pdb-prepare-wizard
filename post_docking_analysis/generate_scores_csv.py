#!/usr/bin/env python3
"""
Script to generate all_scores.csv from GNINA log files.

This script parses GNINA log files to extract docking scores and creates
the required all_scores.csv file for the post-docking analysis pipeline.
It can use pairlist.csv for accurate complex naming if available.
"""

import os
import re
import csv
import argparse
import pandas as pd
from pathlib import Path

def load_pairlist_mapping(pairlist_file):
    """
    Load pairlist mapping for accurate complex naming.
    
    Parameters
    ----------
    pairlist_file : Path
        Path to pairlist.csv file
        
    Returns
    -------
    dict
        Dictionary mapping log filenames to complex names
    """
    try:
        # Read the pairlist CSV
        df = pd.read_csv(pairlist_file)
        
        # Create mapping from receptor_site_ligand to tag names
        mapping = {}
        for _, row in df.iterrows():
            receptor = row['receptor']
            site_id = row['site_id']
            ligand = row['ligand']
            
            # Create expected log filename pattern
            log_pattern = f"{receptor}_{site_id}_{ligand}"
            tag_name = f"{receptor}_{site_id}_{ligand}"
            
            mapping[log_pattern] = tag_name
            
        print(f"✅ Loaded {len(mapping)} mappings from pairlist.csv")
        return mapping
        
    except Exception as e:
        print(f"⚠️  Warning: Could not load pairlist.csv: {e}")
        return {}

def parse_gnina_log(log_file, pairlist_mapping=None):
    """
    Parse a GNINA log file to extract docking scores.
    
    Parameters
    ----------
    log_file : Path
        Path to the GNINA log file
    pairlist_mapping : dict, optional
        Mapping from log patterns to tag names
        
    Returns
    -------
    list
        List of dictionaries containing score information
    """
    scores = []
    
    # Extract tag name from filename
    filename = log_file.stem
    
    # Use pairlist mapping if available
    tag_name = filename
    if pairlist_mapping:
        for pattern, mapped_name in pairlist_mapping.items():
            if pattern in filename or filename in pattern:
                tag_name = mapped_name
                break
    
    try:
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Look for the scoring table
        # Pattern: mode |  affinity  |  intramol  |    CNN     |   CNN
        #          | (kcal/mol) | (kcal/mol) | pose score | affinity
        # -----+------------+------------+------------+----------
        #    1      -12.53       -0.67       0.9954      7.774
        
        lines = content.split('\n')
        in_scores_section = False
        mode_line_pattern = re.compile(r'^\s*(\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)')
        
        for line in lines:
            # Detect start of scores section
            if 'mode |' in line and 'affinity' in line:
                in_scores_section = True
                continue
                
            # Process score lines
            if in_scores_section:
                match = mode_line_pattern.match(line)
                if match:
                    mode = int(match.group(1))
                    vina_affinity = float(match.group(2))
                    intramol = float(match.group(3))
                    cnn_score = float(match.group(4))
                    cnn_affinity = float(match.group(5))
                    
                    scores.append({
                        'tag': tag_name,
                        'mode': mode,
                        'vina_affinity': vina_affinity,
                        'cnn_affinity': cnn_affinity,
                        'cnn_score': cnn_score
                    })
                    
            # Stop when we reach a blank line after scores (end of table)
            if in_scores_section and line.strip() == '' and scores:
                # Check if we're still in the scores section by looking ahead
                continue
            elif in_scores_section and not line.strip().startswith((' ', '\t')) and scores:
                # We've moved past the scores section
                break
                
    except Exception as e:
        print(f"⚠️  Error parsing {log_file}: {e}")
        
    return scores

def generate_all_scores_csv(gnina_out_dir, output_file=None, pairlist_file=None):
    """
    Generate all_scores.csv from GNINA log files.
    
    Parameters
    ----------
    gnina_out_dir : Path
        Directory containing GNINA output files
    output_file : Path, optional
        Output CSV file path (default: gnina_out_dir/all_scores.csv)
    pairlist_file : Path, optional
        Path to pairlist.csv for accurate complex naming
        
    Returns
    -------
    bool
        True if successful, False otherwise
    """
    gnina_out_dir = Path(gnina_out_dir)
    
    if not gnina_out_dir.exists():
        print(f"❌ GNINA output directory not found: {gnina_out_dir}")
        return False
        
    if output_file is None:
        output_file = gnina_out_dir / "all_scores.csv"
        
    # Load pairlist mapping if provided
    pairlist_mapping = {}
    if pairlist_file and Path(pairlist_file).exists():
        print(f"🔍 Using pairlist mapping from: {pairlist_file}")
        pairlist_mapping = load_pairlist_mapping(pairlist_file)
        
    # Find all log files
    log_files = list(gnina_out_dir.glob("*.log"))
    if not log_files:
        log_files = list(gnina_out_dir.glob("*_log"))
        
    if not log_files:
        print(f"❌ No log files found in {gnina_out_dir}")
        return False
        
    print(f"📊 Found {len(log_files)} log files")
    
    # Parse all log files
    all_scores = []
    for log_file in log_files:
        print(f"🔍 Parsing {log_file.name}...")
        scores = parse_gnina_log(log_file, pairlist_mapping)
        all_scores.extend(scores)
        
    if not all_scores:
        print("❌ No scores extracted from log files")
        return False
        
    # Sort scores by tag and mode for consistency
    all_scores.sort(key=lambda x: (x['tag'], x['mode']))
        
    # Write to CSV
    try:
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['tag', 'mode', 'vina_affinity', 'cnn_affinity', 'cnn_score']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for score in all_scores:
                writer.writerow(score)
                
        print(f"✅ Successfully generated {output_file}")
        print(f"   Total scores: {len(all_scores)}")
        print(f"   Unique complexes: {len(set(score['tag'] for score in all_scores))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error writing CSV file: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate all_scores.csv from GNINA log files")
    parser.add_argument("gnina_out_dir", help="Directory containing GNINA output files")
    parser.add_argument("-o", "--output", help="Output CSV file (default: gnina_out_dir/all_scores.csv)")
    parser.add_argument("-p", "--pairlist", help="Pairlist CSV file for accurate complex naming")
    
    args = parser.parse_args()
    
    success = generate_all_scores_csv(args.gnina_out_dir, args.output, args.pairlist)
    
    if success:
        print("\n🎉 all_scores.csv generation completed successfully!")
    else:
        print("\n❌ all_scores.csv generation failed!")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())