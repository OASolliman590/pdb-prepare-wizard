"""
Input handler for post-docking analysis pipeline.

This module handles different input directory structures and file organizations.
"""
import os
from pathlib import Path
from typing import List, Dict, Tuple
import re

def detect_directory_structure(input_dir: Path) -> str:
    """
    Detect whether the input directory has a single-folder or multi-folder structure.
    
    Parameters
    ----------
    input_dir : Path
        Path to the input directory
        
    Returns
    -------
    str
        "SINGLE_FOLDER" or "MULTI_FOLDER"
    """
    # Count subdirectories
    subdirs = [f for f in input_dir.iterdir() if f.is_dir()]
    
    # If there are many subdirectories, assume multi-folder structure
    if len(subdirs) > 5:
        return "MULTI_FOLDER"
    
    # Check for typical multi-folder patterns
    multi_folder_indicators = [
        "PBP", "Agr", "Gyr",  # Common protein names from the research
        "Active", "Catalytic", "Entero",  # Common binding site names
    ]
    
    for subdir in subdirs:
        for indicator in multi_folder_indicators:
            if indicator in subdir.name:
                return "MULTI_FOLDER"
    
    # Default to single folder
    return "SINGLE_FOLDER"

def find_docking_files(input_dir: Path, structure_type: str = "AUTO") -> List[Dict[str, Path]]:
    """
    Find docking files in the input directory.
    
    Parameters
    ----------
    input_dir : Path
        Path to the input directory
    structure_type : str
        "SINGLE_FOLDER", "MULTI_FOLDER", or "AUTO" to detect automatically
        
    Returns
    -------
    List[Dict[str, Path]]
        List of dictionaries containing file paths for each complex
    """
    if structure_type == "AUTO":
        structure_type = detect_directory_structure(input_dir)
    
    if structure_type == "SINGLE_FOLDER":
        return find_files_single_folder(input_dir)
    else:
        return find_files_multi_folder(input_dir)

def find_files_single_folder(input_dir: Path) -> List[Dict[str, Path]]:
    """
    Find docking files in a single folder structure.
    
    Parameters
    ----------
    input_dir : Path
        Path to the input directory
        
    Returns
    -------
    List[Dict[str, Path]]
        List of dictionaries containing file paths for each complex
    """
    complexes = []
    
    # Look for common file patterns
    pdbqt_files = list(input_dir.glob("*out*.pdbqt"))
    pdb_files = list(input_dir.glob("*.pdb"))
    sdf_files = list(input_dir.glob("*.sdf"))
    
    # Group files by complex name
    complex_names = set()
    
    # Extract complex names from PDBQT files
    for pdbqt_file in pdbqt_files:
        name = extract_complex_name(pdbqt_file.stem)
        complex_names.add(name)
    
    # Create complex entries
    for name in complex_names:
        complex_info = {
            "name": name,
            "directory": input_dir,
        }
        
        # Find matching files
        pdbqt_matches = [f for f in pdbqt_files if name in f.stem]
        pdb_matches = [f for f in pdb_files if name in f.stem]
        sdf_matches = [f for f in sdf_files if name in f.stem]
        
        if pdbqt_matches:
            complex_info["docking_result"] = pdbqt_matches[0]
        if pdb_matches:
            complex_info["receptor"] = pdb_matches[0]
        if sdf_matches:
            complex_info["ligand"] = sdf_matches[0]
            
        complexes.append(complex_info)
    
    return complexes

def find_files_multi_folder(input_dir: Path) -> List[Dict[str, Path]]:
    """
    Find docking files in a multi-folder structure.
    
    Parameters
    ----------
    input_dir : Path
        Path to the input directory
        
    Returns
    -------
    List[Dict[str, Path]]
        List of dictionaries containing file paths for each complex
    """
    complexes = []
    
    # Look for receptor directory
    receptor_dir = input_dir / "receptors"
    if not receptor_dir.exists():
        print("⚠️  Receptors directory not found, looking for receptor files in subdirectories")
    
    # Iterate through subdirectories recursively
    for subdir in input_dir.rglob("*"):
        if not subdir.is_dir():
            continue
            
        # Skip common non-relevant directories
        if any(skip_name in subdir.name.lower() for skip_name in 
               ['charmm', 'apo', 'holo', '__pycache__', '.git', 'receptors']):
            continue
            
        complex_info = {
            "name": subdir.name,
            "directory": subdir,
        }
        
        # Look for docking result files (ending with _vina_out.pdbqt or _out.pdbqt)
        pdbqt_files = list(subdir.glob("*_out*.pdbqt"))
        if not pdbqt_files:
            pdbqt_files = list(subdir.glob("*out*.pdbqt"))
        
        # Look for receptor files in the receptors directory or subdirectory
        receptor_files = []
        if receptor_dir.exists():
            # Try to match receptor file based on complex name
            receptor_name = subdir.name.split('x')[-1]  # Get ligand name part
            receptor_files = list(receptor_dir.glob(f"*{receptor_name}*.pdbqt"))
            if not receptor_files:
                # Try alternative matching
                receptor_files = list(receptor_dir.glob("*.pdbqt"))
        
        # If no receptors in main directory, look in subdirectory
        if not receptor_files:
            receptor_files = list(subdir.glob("*.pdbqt"))
            # Filter out docking result files
            receptor_files = [f for f in receptor_files if "_out" not in f.name and "ligand" not in f.name]
        
        sdf_files = list(subdir.glob("*.sdf"))
        
        # Take the first file of each type if available
        if pdbqt_files:
            complex_info["docking_result"] = pdbqt_files[0]
        if receptor_files:
            complex_info["receptor"] = receptor_files[0]
        if sdf_files:
            complex_info["ligand"] = sdf_files[0]
            
        # Only add complexes that have at least a docking result
        if "docking_result" in complex_info:
            complexes.append(complex_info)
    
    return complexes

def extract_complex_name(filename: str) -> str:
    """
    Extract complex name from a filename.
    
    Parameters
    ----------
    filename : str
        Filename to extract complex name from
        
    Returns
    -------
    str
        Complex name
    """
    # Common patterns for complex names
    patterns = [
        r"([A-Za-z0-9]+_[A-Za-z0-9]+)",  # e.g., PBP1_Catalytic
        r"([A-Za-z0-9]+)_",  # e.g., PBP1_
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            return match.group(1)
    
    # Fallback to full filename without extension
    return filename.split(".")[0]

def validate_complex_files(complexes: List[Dict[str, Path]]) -> List[Dict[str, Path]]:
    """
    Validate that each complex has the required files.
    
    Parameters
    ----------
    complexes : List[Dict[str, Path]]
        List of complex information
        
    Returns
    -------
    List[Dict[str, Path]]
        List of valid complexes
    """
    valid_complexes = []
    
    for complex_info in complexes:
        required_files = ["docking_result"]
        missing_files = [f for f in required_files if f not in complex_info]
        
        if not missing_files:
            valid_complexes.append(complex_info)
        else:
            print(f"⚠️  Skipping complex {complex_info['name']}: missing {', '.join(missing_files)}")
    
    return valid_complexes