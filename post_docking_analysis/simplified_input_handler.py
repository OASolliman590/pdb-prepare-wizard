"""
Simplified Input Handler for Post-Docking Analysis.

Handles the simplified 3-folder input structure:
- sdf_folder: Docking poses (SDF files)
- log_folder: Docking logs (can be same as sdf_folder)
- receptors_folder: Receptor PDBQT files
"""
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd


def find_sdf_files(sdf_folder: Path) -> List[Path]:
    """
    Find all SDF pose files in the folder.
    
    Parameters
    ----------
    sdf_folder : Path
        Folder containing SDF files
        
    Returns
    -------
    List[Path]
        List of SDF file paths
    """
    if not sdf_folder.exists():
        return []
    
    # Look for common SDF patterns
    sdf_files = list(sdf_folder.glob("*.sdf"))
    sdf_files.extend(sdf_folder.glob("*_top.sdf"))
    
    return sorted(sdf_files)


def find_log_files(log_folder: Path) -> List[Path]:
    """
    Find all log files in the folder.
    
    Parameters
    ----------
    log_folder : Path
        Folder containing log files
        
    Returns
    -------
    List[Path]
        List of log file paths
    """
    if not log_folder.exists():
        return []
    
    # Look for common log patterns
    log_files = list(log_folder.glob("*.log"))
    log_files.extend(log_folder.glob("*_log"))
    
    return sorted(log_files)


def find_receptor_files(receptors_folder: Path) -> List[Path]:
    """
    Find all receptor PDBQT files in the folder.
    
    Parameters
    ----------
    receptors_folder : Path
        Folder containing receptor PDBQT files
        
    Returns
    -------
    List[Path]
        List of receptor file paths
    """
    if not receptors_folder.exists():
        return []
    
    receptor_files = list(receptors_folder.glob("*.pdbqt"))
    
    return sorted(receptor_files)


def load_pairlist(pairlist_file: Optional[Path]) -> pd.DataFrame:
    """
    Load pairlist.csv if provided.
    
    Parameters
    ----------
    pairlist_file : Path or None
        Path to pairlist.csv
        
    Returns
    -------
    pd.DataFrame
        Pairlist DataFrame, empty if file doesn't exist
    """
    if pairlist_file is None or not pairlist_file.exists():
        return pd.DataFrame()
    
    try:
        return pd.read_csv(pairlist_file)
    except Exception as e:
        print(f"⚠️  Warning: Could not load pairlist.csv: {e}")
        return pd.DataFrame()


def match_poses_to_receptors(
    sdf_files: List[Path],
    receptor_files: List[Path],
    pairlist_df: pd.DataFrame = None
) -> List[Dict]:
    """
    Match SDF pose files to receptors using pairlist or filename patterns.
    
    Parameters
    ----------
    sdf_files : List[Path]
        List of SDF pose files
    receptor_files : List[Path]
        List of receptor PDBQT files
    pairlist_df : pd.DataFrame, optional
        Pairlist DataFrame for matching
        
    Returns
    -------
    List[Dict]
        List of matched complexes with receptor and pose info
    """
    complexes = []
    
    # If pairlist is available, use it for matching
    if pairlist_df is not None and not pairlist_df.empty:
        for _, row in pairlist_df.iterrows():
            receptor_name = row.get('receptor', '')
            ligand_name = row.get('ligand', '')
            site_id = row.get('site_id', 'unknown')
            
            # Find matching receptor file
            receptor_file = None
            for rf in receptor_files:
                if receptor_name in rf.name or rf.stem in receptor_name:
                    receptor_file = rf
                    break
            
            # Find matching SDF file
            sdf_file = None
            for sf in sdf_files:
                if ligand_name in sf.name or sf.stem.replace('_top', '') in ligand_name:
                    sdf_file = sf
                    break
            
            if receptor_file and sdf_file:
                complexes.append({
                    'complex_name': f"{receptor_name}_{site_id}_{ligand_name}",
                    'receptor_file': receptor_file,
                    'pose_file': sdf_file,
                    'site_id': site_id,
                    'receptor_name': receptor_name,
                    'ligand_name': ligand_name
                })
    else:
        # Fallback: filename pattern matching
        # Extract base names and try to match
        for sdf_file in sdf_files:
            sdf_base = sdf_file.stem.replace('_top', '')
            
            # Try to find matching receptor
            for receptor_file in receptor_files:
                receptor_base = receptor_file.stem.replace('_cleaned', '')
                
                # Simple matching: if receptor name contains part of SDF name or vice versa
                if sdf_base in receptor_base or receptor_base in sdf_base:
                    complexes.append({
                        'complex_name': sdf_base,
                        'receptor_file': receptor_file,
                        'pose_file': sdf_file,
                        'site_id': 'unknown',
                        'receptor_name': receptor_base,
                        'ligand_name': sdf_base
                    })
                    break
    
    return complexes

