"""
Publication-Quality PandaMap Integration for Post-Docking Analysis.

Enhanced PandaMap integration with high-quality figure settings for publications:
- High DPI (300-600)
- Publication-ready formats (PDF, SVG, PNG)
- Customizable styling
- Consistent color schemes
- Proper figure sizing
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import subprocess
import json
import tempfile
import logging


class PublicationPandaMapAnalyzer:
    """
    Publication-quality PandaMap analyzer with enhanced figure settings.
    """
    
    # Publication-quality default settings
    PUBLICATION_CONFIG = {
        'dpi': 300,  # High resolution for print
        'formats': ['pdf', 'svg', 'png'],  # Multiple formats
        'figure_width': 10,  # inches
        'figure_height': 8,  # inches
        'font_size': 12,
        'font_family': 'Arial',
        'line_width': 2.0,
        'marker_size': 8,
        'color_scheme': 'publication',  # Consistent color scheme
        'background': 'white',
        'transparent': False,
        'bbox_inches': 'tight',
        'pad_inches': 0.1
    }
    
    def __init__(
        self,
        conda_env: str = "pandamap",
        config: Dict = None,
        publication_mode: bool = True
    ):
        """
        Initialize publication-quality PandaMap analyzer.
        
        Parameters
        ----------
        conda_env : str
            Conda environment name where PandaMap is installed
        config : Dict, optional
            Configuration dictionary (will merge with PUBLICATION_CONFIG)
        publication_mode : bool
            Enable publication-quality settings
        """
        self.conda_env = conda_env
        self.publication_mode = publication_mode
        
        # Merge user config with publication defaults
        if config:
            self.config = {**self.PUBLICATION_CONFIG, **config}
        else:
            self.config = self.PUBLICATION_CONFIG.copy()
        
        self.logger = logging.getLogger(__name__)
    
    def generate_publication_2d_map(
        self,
        pdb_file: Path,
        ligand_name: str = "UNK",
        output_dir: Path = None,
        map_name: str = None,
        dpi: int = None,
        formats: List[str] = None
    ) -> Dict[str, Path]:
        """
        Generate publication-quality 2D interaction map.
        
        Parameters
        ----------
        pdb_file : Path
            Path to the PDB file containing the complex
        ligand_name : str
            Name of the ligand residue
        output_dir : Path, optional
            Output directory for the map
        map_name : str, optional
            Name for the map file
        dpi : int, optional
            Resolution (default: from config, typically 300)
        formats : List[str], optional
            Output formats (default: ['pdf', 'svg', 'png'])
            
        Returns
        -------
        Dict[str, Path]
            Dictionary mapping format names to generated file paths
        """
        self.logger.info(f"🐼 Generating publication-quality 2D interaction map for {pdb_file.name}...")
        
        if output_dir is None:
            output_dir = pdb_file.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if map_name is None:
            map_name = f"{pdb_file.stem}_2d_map"
        
        dpi = dpi or self.config['dpi']
        formats = formats or self.config['formats']
        
        generated_files = {}
        
        for fmt in formats:
            output_file = output_dir / f"{map_name}.{fmt}"
            
            # Create PandaMap command with publication settings
            cmd = [
                "conda", "run", "-n", self.conda_env,
                "pandamap", "generate",
                "--input", str(pdb_file),
                "--ligand", ligand_name,
                "--output", str(output_file),
                "--format", fmt,
                "--dpi", str(dpi),
                "--width", str(self.config['figure_width']),
                "--height", str(self.config['figure_height']),
                "--font-size", str(self.config['font_size']),
                "--font-family", self.config['font_family'],
                "--line-width", str(self.config['line_width']),
                "--background", self.config['background']
            ]
            
            # Add transparency option if requested
            if self.config.get('transparent', False) and fmt in ['png', 'svg']:
                cmd.extend(["--transparent"])
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=False
                )
                
                if result.returncode == 0 and output_file.exists():
                    generated_files[fmt] = output_file
                    self.logger.info(f"  ✅ Generated {fmt.upper()}: {output_file.name}")
                else:
                    self.logger.warning(f"  ⚠️  Failed to generate {fmt}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                self.logger.warning(f"  ⚠️  Generation timed out for {fmt}")
            except FileNotFoundError:
                self.logger.error("  ❌ PandaMap not found. Please install PandaMap.")
                break
            except Exception as e:
                self.logger.warning(f"  ⚠️  Error generating {fmt}: {e}")
        
        if generated_files:
            self.logger.info(f"✅ Generated {len(generated_files)} format(s) for {map_name}")
        else:
            self.logger.error(f"❌ Failed to generate any formats for {map_name}")
        
        return generated_files
    
    def generate_publication_3d_visualization(
        self,
        pdb_file: Path,
        ligand_name: str = "UNK",
        output_dir: Path = None,
        vis_name: str = None,
        interactive: bool = True
    ) -> Optional[Path]:
        """
        Generate publication-quality 3D visualization.
        
        Parameters
        ----------
        pdb_file : Path
            Path to the PDB file containing the complex
        ligand_name : str
            Name of the ligand residue
        output_dir : Path, optional
            Output directory for the visualization
        vis_name : str, optional
            Name for the visualization file
        interactive : bool
            Generate interactive HTML visualization
            
        Returns
        -------
        Path or None
            Path to generated visualization file
        """
        self.logger.info(f"🌐 Generating publication-quality 3D visualization for {pdb_file.name}...")
        
        if output_dir is None:
            output_dir = pdb_file.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if vis_name is None:
            vis_name = f"{pdb_file.stem}_3d_vis"
        
        if interactive:
            # Generate interactive HTML
            output_file = output_dir / f"{vis_name}.html"
            
            cmd = [
                "conda", "run", "-n", self.conda_env,
                "pandamap", "visualize",
                "--input", str(pdb_file),
                "--ligand", ligand_name,
                "--output", str(output_file),
                "--format", "html",
                "--quality", "high"
            ]
        else:
            # Generate static image
            output_file = output_dir / f"{vis_name}.png"
            
            cmd = [
                "conda", "run", "-n", self.conda_env,
                "pandamap", "visualize",
                "--input", str(pdb_file),
                "--ligand", ligand_name,
                "--output", str(output_file),
                "--format", "png",
                "--dpi", str(self.config['dpi']),
                "--width", str(self.config['figure_width']),
                "--height", str(self.config['figure_height'])
            ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                check=False
            )
            
            if result.returncode == 0 and output_file.exists():
                self.logger.info(f"✅ 3D visualization generated: {output_file.name}")
                return output_file
            else:
                self.logger.warning(f"⚠️  PandaMap execution failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.warning("⚠️  PandaMap execution timed out")
            return None
        except FileNotFoundError:
            self.logger.error("⚠️  PandaMap not found. Please install PandaMap.")
            return None
        except Exception as e:
            self.logger.warning(f"⚠️  Error generating 3D visualization: {e}")
            return None
    
    def generate_comprehensive_publication_analysis(
        self,
        complexes_dir: Path,
        output_dir: Path,
        ligand_name: str = "UNK",
        max_complexes: int = None,
        generate_2d: bool = True,
        generate_3d: bool = True
    ) -> Dict:
        """
        Generate comprehensive publication-quality interaction analysis.
        
        Parameters
        ----------
        complexes_dir : Path
            Directory containing PDB complex files
        output_dir : Path
            Output directory for analysis results
        ligand_name : str
            Name of the ligand residue
        max_complexes : int, optional
            Maximum number of complexes to analyze (for performance)
        generate_2d : bool
            Generate 2D interaction maps
        generate_3d : bool
            Generate 3D visualizations
            
        Returns
        -------
        Dict
            Dictionary containing analysis summary
        """
        self.logger.info("🐼 Generating comprehensive publication-quality PandaMap analysis...")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all PDB files
        pdb_files = sorted(list(complexes_dir.glob("*.pdb")))
        
        if not pdb_files:
            self.logger.warning("⚠️  No PDB files found for analysis")
            return {}
        
        # Limit to max_complexes if specified
        if max_complexes:
            pdb_files = pdb_files[:max_complexes]
        
        self.logger.info(f"📊 Analyzing {len(pdb_files)} complexes...")
        
        # Create output subdirectories
        maps_2d_dir = output_dir / "2d_interaction_maps" if generate_2d else None
        vis_3d_dir = output_dir / "3d_visualizations" if generate_3d else None
        
        if maps_2d_dir:
            maps_2d_dir.mkdir(exist_ok=True)
        if vis_3d_dir:
            vis_3d_dir.mkdir(exist_ok=True)
        
        generated_2d_maps = 0
        generated_3d_visualizations = 0
        analysis_results = []
        
        # Generate analysis for each complex
        for i, pdb_file in enumerate(pdb_files, 1):
            self.logger.info(f"  [{i}/{len(pdb_files)}] Processing {pdb_file.name}...")
            
            complex_name = pdb_file.stem
            
            # Generate 2D interaction map
            if generate_2d:
                maps = self.generate_publication_2d_map(
                    pdb_file,
                    ligand_name,
                    maps_2d_dir,
                    map_name=complex_name
                )
                if maps:
                    generated_2d_maps += 1
                    analysis_results.append({
                        'complex': complex_name,
                        '2d_maps': list(maps.keys()),
                        '3d_vis': False
                    })
            
            # Generate 3D visualization
            if generate_3d:
                vis_file = self.generate_publication_3d_visualization(
                    pdb_file,
                    ligand_name,
                    vis_3d_dir,
                    vis_name=complex_name,
                    interactive=True
                )
                if vis_file:
                    generated_3d_visualizations += 1
                    if analysis_results:
                        analysis_results[-1]['3d_vis'] = True
                    else:
                        analysis_results.append({
                            'complex': complex_name,
                            '2d_maps': [],
                            '3d_vis': True
                        })
        
        # Generate summary report
        summary = {
            'total_poses_analyzed': len(pdb_files),
            'generated_2d_maps': generated_2d_maps,
            'generated_3d_visualizations': generated_3d_visualizations,
            'analysis_results': analysis_results,
            'publication_settings': {
                'dpi': self.config['dpi'],
                'formats': self.config['formats'],
                'figure_size': f"{self.config['figure_width']}x{self.config['figure_height']} inches"
            },
            'analysis_timestamp': pd.Timestamp.now().isoformat()
        }
        
        # Save summary to JSON
        summary_file = output_dir / "pandamap_publication_analysis_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save detailed results to CSV
        if analysis_results:
            results_df = pd.DataFrame(analysis_results)
            results_csv = output_dir / "pandamap_analysis_results.csv"
            results_df.to_csv(results_csv, index=False)
        
        self.logger.info("✅ Comprehensive publication-quality PandaMap analysis completed")
        self.logger.info(f"   📊 Generated {generated_2d_maps} 2D interaction maps")
        self.logger.info(f"   🌐 Generated {generated_3d_visualizations} 3D visualizations")
        self.logger.info(f"   📄 Summary saved to: {summary_file}")
        
        return summary


def run_publication_pandamap_analysis(
    complexes_dir: Path,
    output_dir: Path,
    ligand_name: str = "UNK",
    conda_env: str = "pandamap",
    config: Dict = None,
    max_complexes: int = None
) -> Dict:
    """
    Run comprehensive publication-quality PandaMap analysis on complexes.
    
    Parameters
    ----------
    complexes_dir : Path
        Directory containing PDB complex files
    output_dir : Path
        Output directory for analysis results
    ligand_name : str
        Name of the ligand residue
    conda_env : str
        Conda environment name where PandaMap is installed
    config : Dict, optional
        Configuration dictionary for publication settings
    max_complexes : int, optional
        Maximum number of complexes to analyze
        
    Returns
    -------
    Dict
        Dictionary containing analysis results
    """
    logger = logging.getLogger(__name__)
    logger.info("🐼 Running publication-quality PandaMap interaction analysis...")
    
    # Initialize analyzer
    analyzer = PublicationPandaMapAnalyzer(conda_env, config, publication_mode=True)
    
    # Generate comprehensive analysis
    summary = analyzer.generate_comprehensive_publication_analysis(
        complexes_dir=complexes_dir,
        output_dir=output_dir,
        ligand_name=ligand_name,
        max_complexes=max_complexes
    )
    
    return summary

