"""
Research-specific adapter for post-docking analysis pipeline.

This module handles the specific directory structure and naming conventions
used in the research project.
"""
from pathlib import Path
import re
from typing import List, Dict

# Research-specific constants
RESEARCH_BASE_PATH = Path("/Users/omara.soliman/Desktop/Research/25- From Antiretroviral to Antibacterial Deep-Learning-Accelerated Repurposing and In Vitro Validation of Efavirenz Against Gram-Positive Bacteria -F/5-Results")

def find_research_directories() -> List[Path]:
    """
    Find directories containing docking results in the research project structure.
    
    Returns
    -------
    List[Path]
        List of directories containing docking results
    """
    # Common subdirectories in the research project
    common_paths = [
        "gnina_out",
        "vina_out",
        "docking_results",
        "results"
    ]
    
    directories = []
    
    # Check for common subdirectories
    for path in common_paths:
        full_path = RESEARCH_BASE_PATH / path
        if full_path.exists():
            directories.append(full_path)
    
    # Also check for any directory containing docking result files
    # Look for typical file patterns
    patterns = ["*out*.pdbqt", "*docked*.pdbqt", "*result*.pdbqt"]
    
    for pattern in patterns:
        files = list(RESEARCH_BASE_PATH.rglob(pattern))
        for file in files:
            if file.parent not in directories:
                directories.append(file.parent)
    
    return directories

def parse_research_filename(filename: str) -> Dict[str, str]:
    """
    Parse a research-specific filename to extract protein, ligand, and other information.
    
    Parameters
    ----------
    filename : str
        Filename to parse
        
    Returns
    -------
    Dict[str, str]
        Dictionary containing parsed information
    """
    # Common naming patterns in the research:
    # PBP1_Catalytic_Amoxacillin_vina_out.pdbqt
    # AgrA_1_Efavarinz_gnina_out.pdbqt
    
    info = {
        "protein": "",
        "binding_site": "",
        "ligand": "",
        "program": "",
        "type": ""
    }
    
    # Split filename by underscores
    parts = filename.split('_')
    
    if len(parts) >= 3:
        info["protein"] = parts[0]
        info["binding_site"] = parts[1]
        # Ligand is everything between binding site and program identifier
        program_index = -1
        program_indicators = ["vina", "gnina", "out", "result"]
        for i, part in enumerate(parts):
            if any(indicator in part.lower() for indicator in program_indicators):
                program_index = i
                if "vina" in part.lower():
                    info["program"] = "vina"
                elif "gnina" in part.lower():
                    info["program"] = "gnina"
                break
        
        if program_index > 2:
            info["ligand"] = "_".join(parts[2:program_index])
    
    return info

def adapt_research_structure(input_dir: Path) -> List[Dict[str, Path]]:
    """
    Adapt the research project structure to the pipeline format.
    
    Parameters
    ----------
    input_dir : Path
        Input directory containing research results
        
    Returns
    -------
    List[Dict[str, Path]]
        List of complexes in pipeline format
    """
    print(f"🔄 Adapting research structure from: {input_dir}")
    
    complexes = []
    
    # Look for PDBQT files
    pdbqt_files = list(input_dir.rglob("*out*.pdbqt"))
    
    # Group files by complex
    complex_groups = {}
    for pdbqt_file in pdbqt_files:
        # Parse filename to get complex name
        info = parse_research_filename(pdbqt_file.stem)
        complex_name = f"{info['protein']}_{info['binding_site']}_{info['ligand']}"
        
        if complex_name not in complex_groups:
            complex_groups[complex_name] = {
                "name": complex_name,
                "directory": pdbqt_file.parent,
                "info": info
            }
        
        # Add docking result file
        complex_groups[complex_name]["docking_result"] = pdbqt_file
    
    # Convert to list format
    complexes = list(complex_groups.values())
    
    print(f"✅ Adapted {len(complexes)} complexes from research structure")
    return complexes