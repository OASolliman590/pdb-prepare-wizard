"""
Docking result parser for post-docking analysis pipeline.

This module handles parsing of PDBQT files to extract binding affinity and RMSD values.
"""
import re
from pathlib import Path
import pandas as pd
from typing import List, Dict

def parse_vina_pdbqt(pdbqt_file: Path) -> pd.DataFrame:
    """
    Parse a Vina PDBQT file and extract binding affinity and RMSD values.
    
    Parameters
    ----------
    pdbqt_file : Path
        Path to the PDBQT file
        
    Returns
    -------
    pd.DataFrame
        DataFrame containing pose information
    """
    results = []
    
    with open(pdbqt_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Look for lines starting with "REMARK VINA RESULT:"
            if line.startswith("REMARK VINA RESULT:"):
                parts = line.split()
                # Expected format: REMARK VINA RESULT: <affinity> <rmsd_lb> <rmsd_ub>
                if len(parts) >= 6:
                    try:
                        affinity = float(parts[3])
                        rmsd_lb = float(parts[4])
                        rmsd_ub = float(parts[5])
                        # Extract model number from MODEL line if possible
                        model_number = len(results) + 1
                        results.append({
                            'pose': model_number,
                            'vina_affinity': affinity,
                            'rmsd_lb': rmsd_lb,
                            'rmsd_ub': rmsd_ub
                        })
                    except ValueError:
                        # Skip if conversion fails
                        continue
    
    return pd.DataFrame(results)

def parse_all_docking_results(complexes: List[Dict[str, Path]]) -> Dict[str, pd.DataFrame]:
    """
    Parse docking results for all complexes.
    
    Parameters
    ----------
    complexes : List[Dict[str, Path]]
        List of complexes with docking result files
        
    Returns
    -------
    Dict[str, pd.DataFrame]
        Dictionary mapping complex names to their parsed results
    """
    all_results = {}
    
    for complex_info in complexes:
        complex_name = complex_info["name"]
        if "docking_result" in complex_info:
            try:
                df = parse_vina_pdbqt(complex_info["docking_result"])
                if not df.empty:
                    all_results[complex_name] = df
                else:
                    print(f"⚠️  No poses found in {complex_info['docking_result']}")
            except Exception as e:
                print(f"❌ Error parsing {complex_info['docking_result']}: {e}")
        else:
            print(f"⚠️  No docking result file for {complex_name}")
    
    return all_results