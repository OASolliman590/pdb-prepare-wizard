"""
PDB Code Extraction and Matching for Comparative Benchmarking.

Extracts 4-letter PDB codes from filenames and matches receptors to ligands
for comparative benchmarking using pairlist.csv.
"""
import re
from pathlib import Path
from typing import Optional, Dict, List
import pandas as pd


def extract_pdb_code(filename: str) -> Optional[str]:
    """
    Extract 4-letter PDB code from filename using regex.
    
    Examples:
    - VEGFR2_4AG8_cleaned.pdbqt → 4AG8
    - 4AG8_ligand_AXI_A_2000.pdbqt → 4AG8
    - 4WZV_cleaned.pdbqt → 4WZV
    - complex_3H0E_receptor.pdbqt → 3H0E
    
    Parameters
    ----------
    filename : str
        Filename to extract PDB code from
        
    Returns
    -------
    str or None
        4-letter PDB code if found, None otherwise
    """
    # PDB codes are 4 characters: typically 1 digit + 3 letters
    # Pattern: digit followed by 3 alphanumeric (usually letters)
    # Examples: 4AG8, 3H0E, 7DXL, 1IAN, 5K4I
    
    # Convert to uppercase for matching
    filename_upper = filename.upper()
    
    # Pattern: digit + 3 alphanumeric characters (not word boundary, allow underscores)
    # Look for patterns like: _4AG8_, 4AG8_, _4AG8, or standalone 4AG8
    pattern = r'[^A-Z0-9]([0-9][A-Z0-9]{3})[^A-Z0-9]|^([0-9][A-Z0-9]{3})[^A-Z0-9]|[^A-Z0-9]([0-9][A-Z0-9]{3})$'
    
    matches = re.findall(pattern, filename_upper)
    
    # Flatten matches (pattern returns tuples)
    for match_group in matches:
        for match in match_group:
            if match and len(match) == 4:
                return match
    
    # Fallback: look for any 4-character sequence starting with digit
    pattern2 = r'([0-9][A-Z0-9]{3})'
    matches = re.findall(pattern2, filename_upper)
    
    if matches:
        # Return first valid 4-character match
        for match in matches:
            if len(match) == 4:
                return match
    
    return None


def load_pairlist(pairlist_file: Path) -> pd.DataFrame:
    """
    Load pairlist.csv and return as DataFrame.
    
    Parameters
    ----------
    pairlist_file : Path
        Path to pairlist.csv
        
    Returns
    -------
    pd.DataFrame
        Pairlist DataFrame with columns: receptor, site_id, ligand, etc.
    """
    if not pairlist_file.exists():
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(pairlist_file)
        return df
    except Exception as e:
        print(f"⚠️  Warning: Could not load pairlist.csv: {e}")
        return pd.DataFrame()


def find_comparative_reference(
    receptor_file: Path,
    ligand_files: List[Path],
    pairlist_df: pd.DataFrame = None
) -> Optional[Dict[str, str]]:
    """
    Find comparative reference ligand by matching PDB codes.
    
    Logic:
    1. Extract PDB code from receptor filename
    2. Extract PDB code from each ligand filename
    3. Match if PDB codes are the same
    4. Use pairlist.csv for site_id if available
    
    Example:
    - Receptor: VEGFR2_4AG8_cleaned.pdbqt → PDB code: 4AG8
    - Ligand: 4AG8_ligand_AXI_A_2000.pdbqt → PDB code: 4AG8
    - Match! Use this ligand as comparative reference
    
    Parameters
    ----------
    receptor_file : Path
        Path to receptor PDBQT file
    ligand_files : List[Path]
        List of ligand file paths to search
    pairlist_df : pd.DataFrame, optional
        Pairlist DataFrame for site_id lookup
        
    Returns
    -------
    dict or None
        Dictionary with 'ligand_file', 'pdb_code', 'site_id' if match found
    """
    receptor_pdb_code = extract_pdb_code(receptor_file.name)
    
    if not receptor_pdb_code:
        return None
    
    # Search for matching ligand
    for ligand_file in ligand_files:
        ligand_pdb_code = extract_pdb_code(ligand_file.name)
        
        if ligand_pdb_code == receptor_pdb_code:
            # Found match! Now get site_id
            site_id = None
            
            # Try to get site_id from pairlist
            if pairlist_df is not None and not pairlist_df.empty:
                # Match receptor and ligand in pairlist
                receptor_name = receptor_file.stem.replace('.pdbqt', '').replace('_cleaned', '')
                ligand_name = ligand_file.stem.replace('.pdbqt', '').replace('_ligand_', '_')
                
                # Try to match in pairlist
                matches = pairlist_df[
                    (pairlist_df['receptor'].str.contains(receptor_pdb_code, case=False, na=False)) |
                    (pairlist_df['ligand'].str.contains(ligand_pdb_code, case=False, na=False))
                ]
                
                if not matches.empty and 'site_id' in matches.columns:
                    site_id = matches.iloc[0]['site_id']
            
            # If no site_id from pairlist, try to extract from filename
            if not site_id:
                # Look for common site patterns in filename
                site_patterns = ['catalytic', 'allosteric', 'active', 'binding']
                filename_lower = ligand_file.name.lower()
                for pattern in site_patterns:
                    if pattern in filename_lower:
                        site_id = pattern
                        break
            
            return {
                'ligand_file': ligand_file,
                'pdb_code': ligand_pdb_code,
                'site_id': site_id or 'unknown'
            }
    
    return None


def match_receptors_to_ligands(
    receptor_files: List[Path],
    ligand_files: List[Path],
    pairlist_file: Optional[Path] = None
) -> Dict[str, Dict]:
    """
    Match receptors to ligands using PDB codes and pairlist.
    
    Parameters
    ----------
    receptor_files : List[Path]
        List of receptor PDBQT files
    ligand_files : List[Path]
        List of ligand files
    pairlist_file : Path, optional
        Path to pairlist.csv
        
    Returns
    -------
    dict
        Dictionary mapping receptor files to matched ligand info
    """
    pairlist_df = load_pairlist(pairlist_file) if pairlist_file else pd.DataFrame()
    
    matches = {}
    
    for receptor_file in receptor_files:
        match = find_comparative_reference(receptor_file, ligand_files, pairlist_df)
        if match:
            matches[str(receptor_file)] = match
    
    return matches

