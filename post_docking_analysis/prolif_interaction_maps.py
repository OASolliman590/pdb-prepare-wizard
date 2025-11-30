"""
2D Interaction Maps using ProLif (inspired by Jupyter_Dock).

Creates 2D interaction maps for protein-ligand complexes.
"""
from pathlib import Path
from typing import List, Dict, Optional
import logging

try:
    from prolif import ProLIF
    from prolif.plotting.network import LigNetwork
    from rdkit import Chem
    from rdkit.Chem import AllChem
    PROLIF_AVAILABLE = True
except ImportError:
    PROLIF_AVAILABLE = False

logger = logging.getLogger(__name__)


class ProLifInteractionMapper:
    """
    2D interaction maps using ProLIF for protein-ligand complexes.
    """
    
    def __init__(self):
        """Initialize ProLIF interaction mapper."""
        if not PROLIF_AVAILABLE:
            logger.warning(
                "ProLIF not available. Install with:\n"
                "conda install rdkit cython\n"
                "pip install git+https://github.com/chemosim-lab/ProLIF.git"
            )
    
    def create_interaction_map(
        self,
        complex_pdb: Path,
        output_png: Path,
        ligand_resname: str = "UNK",
        dpi: int = 300,
        figsize: tuple = (12, 8)
    ) -> bool:
        """
        Create 2D interaction map for a protein-ligand complex.
        
        Parameters
        ----------
        complex_pdb : Path
            Path to complex PDB file
        output_png : Path
            Output PNG file path
        ligand_resname : str
            Residue name of the ligand
        dpi : int
            Resolution for output image
        figsize : tuple
            Figure size (width, height) in inches
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        if not PROLIF_AVAILABLE:
            logger.error("ProLIF not available")
            return False
        
        if not complex_pdb.exists():
            logger.error(f"Complex PDB file not found: {complex_pdb}")
            return False
        
        try:
            import matplotlib.pyplot as plt
            
            # Initialize ProLIF
            prolif = ProLIF()
            
            # Load complex
            prolif.load_from_pdb(str(complex_pdb))
            
            # Get ligand
            ligand = prolif.get_ligand(ligand_resname)
            if ligand is None:
                logger.warning(f"Ligand {ligand_resname} not found in complex")
                return False
            
            # Calculate interactions
            interactions = prolif.run()
            
            # Create network plot
            net = LigNetwork.from_prolif(prolif, interactions)
            
            # Create figure
            fig, ax = plt.subplots(figsize=figsize)
            
            # Plot network
            net.plot(ax=ax)
            
            # Save figure
            output_png.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_png, dpi=dpi, bbox_inches='tight')
            plt.close()
            
            logger.info(f"✅ Created interaction map: {output_png.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating interaction map: {e}", exc_info=True)
            return False
    
    def create_interaction_map_simple(
        self,
        complex_pdb: Path,
        output_png: Path,
        ligand_resname: str = "UNK",
        dpi: int = 300,
        figsize: tuple = (12, 8)
    ) -> bool:
        """
        Create 2D interaction map using simplified ProLIF API.
        
        Parameters
        ----------
        complex_pdb : Path
            Path to complex PDB file
        output_png : Path
            Output PNG file path
        ligand_resname : str
            Residue name of the ligand
        dpi : int
            Resolution for output image
        figsize : tuple
            Figure size (width, height) in inches
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        if not PROLIF_AVAILABLE:
            logger.error("ProLIF not available")
            return False
        
        if not complex_pdb.exists():
            logger.error(f"Complex PDB file not found: {complex_pdb}")
            return False
        
        try:
            import matplotlib.pyplot as plt
            from prolif import ProLIF
            from prolif.plotting.network import LigNetwork
            
            # Read PDB file
            with open(complex_pdb, 'r') as f:
                pdb_content = f.read()
            
            # Initialize ProLIF
            prolif = ProLIF()
            prolif.load_from_string(pdb_content, format='pdb')
            
            # Get ligand molecule
            ligand = prolif.get_ligand(ligand_resname)
            if ligand is None:
                logger.warning(f"Ligand {ligand_resname} not found, trying to extract...")
                # Try to extract ligand from PDB
                ligand = self._extract_ligand_from_pdb(complex_pdb, ligand_resname)
                if ligand is None:
                    return False
            
            # Calculate interactions
            interactions = prolif.run()
            
            # Create network visualization
            net = LigNetwork.from_prolif(prolif, interactions)
            
            # Create figure
            fig, ax = plt.subplots(figsize=figsize)
            
            # Plot network
            net.plot(ax=ax)
            
            # Save figure
            output_png.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_png, dpi=dpi, bbox_inches='tight')
            plt.close()
            
            logger.info(f"✅ Created interaction map: {output_png.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating interaction map: {e}", exc_info=True)
            # Fallback to basic visualization
            return self._create_basic_interaction_map(complex_pdb, output_png, ligand_resname, dpi, figsize)
    
    def _extract_ligand_from_pdb(self, pdb_file: Path, ligand_resname: str):
        """Extract ligand molecule from PDB file."""
        try:
            from rdkit import Chem
            from rdkit.Chem import AllChem
            
            # Read PDB and extract HETATM lines for ligand
            ligand_lines = []
            with open(pdb_file, 'r') as f:
                for line in f:
                    if line.startswith('HETATM') and ligand_resname in line:
                        ligand_lines.append(line)
            
            if not ligand_lines:
                return None
            
            # Convert to MOL file format (simplified)
            # This is a basic implementation - may need refinement
            mol = Chem.MolFromPDBBlock('\n'.join(ligand_lines))
            if mol:
                AllChem.Compute2DCoords(mol)
                return mol
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not extract ligand: {e}")
            return None
    
    def _create_basic_interaction_map(
        self,
        complex_pdb: Path,
        output_png: Path,
        ligand_resname: str,
        dpi: int,
        figsize: tuple
    ) -> bool:
        """
        Create basic interaction map as fallback.
        
        Parameters
        ----------
        complex_pdb : Path
            Path to complex PDB file
        output_png : Path
            Output PNG file path
        ligand_resname : str
            Residue name of the ligand
        dpi : int
            Resolution for output image
        figsize : tuple
            Figure size
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            import matplotlib.pyplot as plt
            
            # Create a simple placeholder figure
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, 
                   f'Interaction map for {complex_pdb.stem}\n'
                   f'(ProLIF visualization unavailable)',
                   ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            output_png.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_png, dpi=dpi, bbox_inches='tight')
            plt.close()
            
            logger.warning(f"Created placeholder interaction map: {output_png.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating basic interaction map: {e}")
            return False


def create_interaction_maps_for_all_complexes(
    complexes_dir: Path,
    output_dir: Path,
    ligand_resname: str = "UNK",
    dpi: int = 300
) -> Dict[str, Path]:
    """
    Create interaction maps for all complexes.
    
    Parameters
    ----------
    complexes_dir : Path
        Directory containing complex PDB files
    output_dir : Path
        Output directory for PNG files
    ligand_resname : str
        Residue name of ligands
    dpi : int
        Resolution for output images
        
    Returns
    -------
    Dict[str, Path]
        Dictionary mapping complex names to PNG file paths
    """
    mapper = ProLifInteractionMapper()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    complex_files = list(complexes_dir.glob("*.pdb"))
    created_files = {}
    
    for complex_file in complex_files:
        output_png = output_dir / f"{complex_file.stem}_interaction_map.png"
        if mapper.create_interaction_map_simple(complex_file, output_png, ligand_resname, dpi):
            created_files[complex_file.stem] = output_png
    
    return created_files

