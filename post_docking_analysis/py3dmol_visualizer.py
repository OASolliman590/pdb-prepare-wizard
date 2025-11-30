"""
3D Visualization using py3Dmol (inspired by Jupyter_Dock).

Creates interactive 3D visualizations for:
- Individual best poses/complexes
- Aggregated ligands for the same protein
"""
from pathlib import Path
from typing import List, Dict, Optional
import logging

try:
    import py3Dmol
    PY3DMOL_AVAILABLE = True
except ImportError:
    PY3DMOL_AVAILABLE = False

logger = logging.getLogger(__name__)


class Py3DmolVisualizer:
    """
    3D visualization using py3Dmol for protein-ligand complexes.
    """
    
    def __init__(self, width: int = 800, height: int = 600):
        """
        Initialize py3Dmol visualizer.
        
        Parameters
        ----------
        width : int
            Width of visualization in pixels
        height : int
            Height of visualization in pixels
        """
        if not PY3DMOL_AVAILABLE:
            logger.warning("py3Dmol not available. Install with: conda install -c conda-forge py3dmol")
        
        self.width = width
        self.height = height
    
    def visualize_complex(
        self,
        complex_pdb: Path,
        output_html: Path,
        style_protein: Dict = None,
        style_ligand: Dict = None
    ) -> bool:
        """
        Visualize a single protein-ligand complex.
        
        Parameters
        ----------
        complex_pdb : Path
            Path to complex PDB file
        output_html : Path
            Output HTML file path
        style_protein : Dict, optional
            Protein styling options
        style_ligand : Dict, optional
            Ligand styling options
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        if not PY3DMOL_AVAILABLE:
            logger.error("py3Dmol not available")
            return False
        
        if not complex_pdb.exists():
            logger.error(f"Complex PDB file not found: {complex_pdb}")
            return False
        
        try:
            # Read PDB file
            with open(complex_pdb, 'r') as f:
                pdb_content = f.read()
            
            # Initialize viewer
            view = py3Dmol.view(width=self.width, height=self.height)
            
            # Add model
            view.addModel(pdb_content, 'pdb')
            
            # Style protein (default: cartoon with spectrum coloring)
            if style_protein is None:
                view.setStyle({'cartoon': {'color': 'spectrum'}})
            else:
                view.setStyle(style_protein)
            
            # Style ligand (default: stick representation)
            if style_ligand is None:
                view.setStyle({'hetflag': True}, {'stick': {'colorscheme': 'greenCarbon'}})
            else:
                view.setStyle({'hetflag': True}, style_ligand)
            
            # Zoom to fit
            view.zoomTo()
            
            # Render to HTML
            view.render()
            html_content = view._make_html()
            
            # Write HTML file
            output_html.parent.mkdir(parents=True, exist_ok=True)
            with open(output_html, 'w') as f:
                f.write(html_content)
            
            logger.info(f"✅ Created 3D visualization: {output_html.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating 3D visualization: {e}", exc_info=True)
            return False
    
    def visualize_multiple_ligands_same_protein(
        self,
        receptor_pdb: Path,
        ligand_pdbs: List[Path],
        ligand_names: List[str],
        output_html: Path,
        style_protein: Dict = None,
        ligand_colors: List[str] = None
    ) -> bool:
        """
        Visualize multiple ligands docked to the same protein in one figure.
        
        Parameters
        ----------
        receptor_pdb : Path
            Path to receptor PDB file
        ligand_pdbs : List[Path]
            List of ligand PDB file paths
        ligand_names : List[str]
            List of ligand names (for legend)
        output_html : Path
            Output HTML file path
        style_protein : Dict, optional
            Protein styling options
        ligand_colors : List[str], optional
            Colors for each ligand (default: rainbow colors)
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        if not PY3DMOL_AVAILABLE:
            logger.error("py3Dmol not available")
            return False
        
        if not receptor_pdb.exists():
            logger.error(f"Receptor PDB file not found: {receptor_pdb}")
            return False
        
        if len(ligand_pdbs) != len(ligand_names):
            logger.error("Number of ligand files must match number of ligand names")
            return False
        
        try:
            # Read receptor PDB
            with open(receptor_pdb, 'r') as f:
                receptor_content = f.read()
            
            # Initialize viewer
            view = py3Dmol.view(width=self.width, height=self.height)
            
            # Add receptor model
            view.addModel(receptor_content, 'pdb')
            
            # Style protein (default: cartoon with spectrum coloring)
            if style_protein is None:
                view.setStyle({'cartoon': {'color': 'spectrum'}})
            else:
                view.setStyle(style_protein)
            
            # Default colors (rainbow)
            if ligand_colors is None:
                import colorsys
                n = len(ligand_pdbs)
                ligand_colors = [
                    '#%02x%02x%02x' % tuple(int(c * 255) for c in colorsys.hsv_to_rgb(i/n, 1, 1))
                    for i in range(n)
                ]
            
            # Add each ligand with different color
            model_index = 1  # Start from 1 (0 is receptor)
            for ligand_pdb, ligand_name, color in zip(ligand_pdbs, ligand_names, ligand_colors):
                if not ligand_pdb.exists():
                    logger.warning(f"Ligand file not found: {ligand_pdb}, skipping...")
                    continue
                
                # Read ligand PDB
                with open(ligand_pdb, 'r') as f:
                    ligand_content = f.read()
                
                # Add ligand model
                view.addModel(ligand_content, 'pdb')
                
                # Style ligand with specific color
                view.setStyle({'model': model_index}, {'stick': {'color': color}})
                model_index += 1
            
            # Zoom to fit
            view.zoomTo()
            
            # Render to HTML
            view.render()
            html_content = view._make_html()
            
            # Add legend to HTML
            legend_html = self._create_legend_html(ligand_names, ligand_colors)
            html_content = html_content.replace('</body>', f'{legend_html}</body>')
            
            # Write HTML file
            output_html.parent.mkdir(parents=True, exist_ok=True)
            with open(output_html, 'w') as f:
                f.write(html_content)
            
            logger.info(f"✅ Created aggregated 3D visualization: {output_html.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating aggregated visualization: {e}", exc_info=True)
            return False
    
    def _create_legend_html(self, ligand_names: List[str], colors: List[str]) -> str:
        """
        Create HTML legend for ligands.
        
        Parameters
        ----------
        ligand_names : List[str]
            List of ligand names
        colors : List[str]
            List of colors (hex codes)
            
        Returns
        -------
        str
            HTML string for legend
        """
        legend_items = []
        for name, color in zip(ligand_names, colors):
            legend_items.append(
                f'<div style="display: inline-block; margin: 5px;">'
                f'<span style="display: inline-block; width: 20px; height: 20px; '
                f'background-color: {color}; border: 1px solid black; margin-right: 5px;"></span>'
                f'<span>{name}</span></div>'
            )
        
        legend_html = f'''
        <div style="position: absolute; top: 10px; right: 10px; background: white; 
                    padding: 10px; border: 2px solid black; border-radius: 5px; 
                    font-family: Arial, sans-serif; font-size: 12px; z-index: 1000;">
            <strong>Ligands:</strong><br>
            {'<br>'.join(legend_items)}
        </div>
        '''
        return legend_html


def visualize_all_complexes(
    complexes_dir: Path,
    output_dir: Path,
    width: int = 800,
    height: int = 600
) -> Dict[str, Path]:
    """
    Visualize all complexes in a directory.
    
    Parameters
    ----------
    complexes_dir : Path
        Directory containing complex PDB files
    output_dir : Path
        Output directory for HTML files
    width : int
        Width of visualization
    height : int
        Height of visualization
        
    Returns
    -------
    Dict[str, Path]
        Dictionary mapping complex names to HTML file paths
    """
    visualizer = Py3DmolVisualizer(width=width, height=height)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    complex_files = list(complexes_dir.glob("*.pdb"))
    created_files = {}
    
    for complex_file in complex_files:
        output_html = output_dir / f"{complex_file.stem}_3d.html"
        if visualizer.visualize_complex(complex_file, output_html):
            created_files[complex_file.stem] = output_html
    
    return created_files


def visualize_ligands_by_protein(
    complexes_dir: Path,
    receptors_dir: Path,
    scores_df,
    output_dir: Path,
    width: int = 1000,
    height: int = 800
) -> Dict[str, Path]:
    """
    Aggregate and visualize all ligands for each protein.
    
    Parameters
    ----------
    complexes_dir : Path
        Directory containing complex PDB files
    receptors_dir : Path
        Directory containing receptor PDBQT files
    scores_df : pd.DataFrame
        DataFrame with scores and protein/ligand info
    output_dir : Path
        Output directory for HTML files
    width : int
        Width of visualization
    height : int
        Height of visualization
        
    Returns
    -------
    Dict[str, Path]
        Dictionary mapping protein names to HTML file paths
    """
    visualizer = Py3DmolVisualizer(width=width, height=height)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    created_files = {}
    
    # Group complexes by protein
    if 'protein' not in scores_df.columns:
        logger.warning("No 'protein' column in scores_df, cannot aggregate by protein")
        return created_files
    
    for protein in scores_df['protein'].unique():
        protein_complexes = scores_df[scores_df['protein'] == protein]
        
        # Get best pose for each ligand
        best_poses = protein_complexes.loc[
            protein_complexes.groupby('ligand')['vina_affinity'].idxmin()
        ]
        
        # Find receptor file
        receptor_file = None
        for rf in receptors_dir.glob(f"*{protein}*.pdbqt"):
            receptor_file = rf
            break
        
        if receptor_file is None:
            logger.warning(f"Receptor file not found for {protein}")
            continue
        
        # Convert receptor PDBQT to PDB (simplified - would need OpenBabel)
        # For now, look for receptor PDB file
        receptor_pdb = receptors_dir / f"{protein}_cleaned.pdb"
        if not receptor_pdb.exists():
            logger.warning(f"Receptor PDB file not found: {receptor_pdb}")
            continue
        
        # Get ligand PDB files from complexes
        ligand_pdbs = []
        ligand_names = []
        
        for _, row in best_poses.iterrows():
            tag = row.get('tag', '')
            complex_file = complexes_dir / f"{tag}.pdb"
            
            if complex_file.exists():
                ligand_pdbs.append(complex_file)
                ligand_name = row.get('ligand', tag)
                ligand_names.append(ligand_name)
        
        if len(ligand_pdbs) == 0:
            logger.warning(f"No ligand complexes found for {protein}")
            continue
        
        # Create aggregated visualization
        output_html = output_dir / f"{protein}_all_ligands_3d.html"
        if visualizer.visualize_multiple_ligands_same_protein(
            receptor_pdb,
            ligand_pdbs,
            ligand_names,
            output_html
        ):
            created_files[protein] = output_html
    
    return created_files

