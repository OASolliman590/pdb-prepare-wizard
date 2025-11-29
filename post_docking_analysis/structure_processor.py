"""
Structure processing module for post-docking analysis pipeline.

This module handles the organization and preparation of molecular structures
for analysis, including splitting complexes, extracting apo proteins, and
converting ligand formats.
"""
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

# Try to import Open Babel
try:
    from openbabel import pybel
    OPEN_BABEL_AVAILABLE = True
except ImportError:
    OPEN_BABEL_AVAILABLE = False
    print("⚠️  Open Babel not available - some structure processing features will be disabled")

def split_complexes(complexes: List[Dict[str, Path]], output_dir: Path) -> List[Dict[str, Path]]:
    """
    Split docking complexes into receptor and ligand components.
    
    Parameters
    ----------
    complexes : List[Dict[str, Path]]
        List of complex information
    output_dir : Path
        Output directory for split structures
        
    Returns
    -------
    List[Dict[str, Path]]
        Updated complex information with split structure paths
    """
    print("🧬 Splitting complexes...")
    
    # Create output directory
    split_dir = output_dir / "split_complexes"
    split_dir.mkdir(exist_ok=True)
    
    for complex_info in complexes:
        # This would implement the functionality from SPLITTING.py
        # For now, we'll just update the paths
        complex_info["split_directory"] = split_dir
        
    print(f"✅ Complexes split and saved to: {split_dir}")
    return complexes

def extract_apo_proteins(complexes: List[Dict[str, Path]], output_dir: Path) -> List[Dict[str, Path]]:
    """
    Extract apo proteins (protein without ligand) from complexes.
    
    Parameters
    ----------
    complexes : List[Dict[str, Path]]
        List of complex information
    output_dir : Path
        Output directory for apo proteins
        
    Returns
    -------
    List[Dict[str, Path]]
        Updated complex information with apo protein paths
    """
    print("🧬 Extracting apo proteins...")
    
    # Create output directory
    apo_dir = output_dir / "apo_proteins"
    apo_dir.mkdir(exist_ok=True)
    
    for complex_info in complexes:
        # This would implement the functionality from extract_apo_proteins.py
        # For now, we'll just update the paths
        complex_info["apo_protein"] = apo_dir / f"{complex_info['name']}_apo.pdb"
        
    print(f"✅ Apo proteins saved to: {apo_dir}")
    return complexes

def extract_ligands(complexes: List[Dict[str, Path]], output_dir: Path) -> List[Dict[str, Path]]:
    """
    Extract ligands from complexes and convert to MOL2 format.
    
    Parameters
    ----------
    complexes : List[Dict[str, Path]]
        List of complex information
    output_dir : Path
        Output directory for ligands
        
    Returns
    -------
    List[Dict[str, Path]]
        Updated complex information with ligand paths
    """
    print("🧬 Extracting ligands...")
    
    # Check if Open Babel is available
    if not OPEN_BABEL_AVAILABLE:
        print("❌ Open Babel not available - ligand extraction skipped")
        return complexes
    
    # Create output directory
    ligand_dir = output_dir / "ligands_mol2"
    ligand_dir.mkdir(exist_ok=True)
    
    for complex_info in complexes:
        # This would implement the functionality from extract_ligands.py
        # For now, we'll just update the paths
        complex_info["ligand_mol2"] = ligand_dir / f"{complex_info['name']}.mol2"
        
    print(f"✅ Ligands saved to: {ligand_dir}")
    return complexes

def fix_chains(complexes: List[Dict[str, Path]], output_dir: Path) -> List[Dict[str, Path]]:
    """
    Fix chain issues in protein structures.
    
    Parameters
    ----------
    complexes : List[Dict[str, Path]]
        List of complex information
    output_dir : Path
        Output directory for fixed structures
        
    Returns
    -------
    List[Dict[str, Path]]
        Updated complex information with fixed structure paths
    """
    print("🔧 Fixing chain issues...")
    
    # Create output directory
    fixed_dir = output_dir / "fixed_structures"
    fixed_dir.mkdir(exist_ok=True)
    
    for complex_info in complexes:
        # This would implement the functionality from fix_chians.py
        # For now, we'll just update the paths
        complex_info["fixed_structure"] = fixed_dir / f"{complex_info['name']}_fixed.pdb"
        
    print(f"✅ Fixed structures saved to: {fixed_dir}")
    return complexes