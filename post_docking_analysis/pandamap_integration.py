"""
PandaMap integration module for post-docking analysis pipeline.

This module handles 2D interaction map generation using PandaMap with configuration support.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import subprocess
import json
import tempfile

class PandaMapAnalyzer:
    """
    PandaMap analyzer for creating 2D interaction maps and 3D visualizations.
    """
    
    def __init__(self, conda_env: str = "pandamap", config: Dict = None):
        """
        Initialize PandaMap analyzer.
        
        Parameters
        ----------
        conda_env : str
            Conda environment name where PandaMap is installed
        config : Dict, optional
            Configuration dictionary
        """
        self.conda_env = conda_env
        self.config = config or {}
        
    def generate_2d_interaction_map(self, pdb_file: Path, ligand_name: str = "UNK",
                                  output_dir: Path = None, map_name: str = None) -> Path:
        """
        Generate 2D interaction map for a protein-ligand complex.
        
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
            
        Returns
        -------
        Path
            Path to the generated interaction map
        """
        print(f"🐼 Generating 2D interaction map for {pdb_file.name}...")
        
        if output_dir is None:
            output_dir = pdb_file.parent
        output_dir.mkdir(exist_ok=True)
        
        if map_name is None:
            map_name = f"{pdb_file.stem}_2d_map"
            
        # Create PandaMap command
        cmd = [
            "conda", "run", "-n", self.conda_env,
            "pandamap", "generate",
            "--input", str(pdb_file),
            "--ligand", ligand_name,
            "--output", str(output_dir / f"{map_name}.svg"),
            "--format", "svg"
        ]
        
        try:
            # Execute PandaMap command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                map_file = output_dir / f"{map_name}.svg"
                print(f"✅ 2D interaction map generated: {map_file}")
                return map_file
            else:
                print(f"⚠️ PandaMap execution failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("⚠️ PandaMap execution timed out")
            return None
        except FileNotFoundError:
            print("⚠️ PandaMap not found. Please install PandaMap to use interaction analysis features.")
            return None
        except Exception as e:
            print(f"⚠️ Error generating 2D interaction map: {e}")
            return None
    
    def generate_3d_visualization(self, pdb_file: Path, ligand_name: str = "UNK",
                                output_dir: Path = None, vis_name: str = None) -> Path:
        """
        Generate 3D interactive visualization for a protein-ligand complex.
        
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
            
        Returns
        -------
        Path
            Path to the generated visualization
        """
        print(f"🌐 Generating 3D visualization for {pdb_file.name}...")
        
        if output_dir is None:
            output_dir = pdb_file.parent
        output_dir.mkdir(exist_ok=True)
        
        if vis_name is None:
            vis_name = f"{pdb_file.stem}_3d_vis"
            
        # Create PandaMap command
        cmd = [
            "conda", "run", "-n", self.conda_env,
            "pandamap", "visualize",
            "--input", str(pdb_file),
            "--ligand", ligand_name,
            "--output", str(output_dir / f"{vis_name}.html"),
            "--format", "html"
        ]
        
        try:
            # Execute PandaMap command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                vis_file = output_dir / f"{vis_name}.html"
                print(f"✅ 3D visualization generated: {vis_file}")
                return vis_file
            else:
                print(f"⚠️ PandaMap execution failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("⚠️ PandaMap execution timed out")
            return None
        except FileNotFoundError:
            print("⚠️ PandaMap not found. Please install PandaMap to use interaction analysis features.")
            return None
        except Exception as e:
            print(f"⚠️ Error generating 3D visualization: {e}")
            return None
    
    def generate_comprehensive_analysis(self, poses_dir: Path, output_dir: Path,
                                      ligand_name: str = "UNK") -> Dict:
        """
        Generate comprehensive interaction analysis for all poses in a directory.
        
        Parameters
        ----------
        poses_dir : Path
            Directory containing PDB files for poses
        output_dir : Path
            Output directory for analysis results
        ligand_name : str
            Name of the ligand residue
            
        Returns
        -------
        Dict
            Dictionary containing analysis summary
        """
        print("🐼 Generating comprehensive PandaMap analysis...")
        
        output_dir.mkdir(exist_ok=True)
        
        # Find all PDB files
        pdb_files = list(poses_dir.glob("*.pdb"))
        if not pdb_files:
            print("⚠️ No PDB files found for analysis")
            return {}
        
        # Limit to best poses only for performance
        pdb_files = pdb_files[:10]  # Analyze only first 10 poses
        
        generated_2d_maps = 0
        generated_3d_visualizations = 0
        generated_reports = 0
        
        # Generate analysis for each pose
        for pdb_file in pdb_files:
            # Generate 2D interaction map
            map_file = self.generate_2d_interaction_map(
                pdb_file, ligand_name, output_dir / "2d_interaction_maps"
            )
            if map_file:
                generated_2d_maps += 1
            
            # Generate 3D visualization
            vis_file = self.generate_3d_visualization(
                pdb_file, ligand_name, output_dir / "3d_visualizations"
            )
            if vis_file:
                generated_3d_visualizations += 1
        
        # Generate summary report
        summary = {
            'total_poses_analyzed': len(pdb_files),
            'generated_2d_maps': generated_2d_maps,
            'generated_3d_visualizations': generated_3d_visualizations,
            'generated_reports': generated_reports,
            'analysis_timestamp': pd.Timestamp.now().isoformat()
        }
        
        # Save summary to JSON
        summary_file = output_dir / "pandamap_analysis_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✅ Comprehensive PandaMap analysis completed")
        print(f"   📊 Generated {generated_2d_maps} 2D interaction maps")
        print(f"   🌐 Generated {generated_3d_visualizations} 3D visualizations")
        print(f"   📄 Generated {generated_reports} detailed reports")
        
        return summary

def run_pandamap_analysis(poses_dir: Path, output_dir: Path, 
                         ligand_name: str = "UNK", conda_env: str = "pandamap",
                         config: Dict = None) -> Dict:
    """
    Run comprehensive PandaMap analysis on poses.
    
    Parameters
    ----------
    poses_dir : Path
        Directory containing PDB files for poses
    output_dir : Path
        Output directory for analysis results
    ligand_name : str
        Name of the ligand residue
    conda_env : str
        Conda environment name where PandaMap is installed
    config : Dict, optional
        Configuration dictionary
        
    Returns
    -------
    Dict
        Dictionary containing analysis results
    """
    print("🐼 Running PandaMap interaction analysis...")
    
    # Initialize analyzer
    analyzer = PandaMapAnalyzer(conda_env, config)
    
    # Generate comprehensive analysis
    summary = analyzer.generate_comprehensive_analysis(
        poses_dir=poses_dir,
        output_dir=output_dir,
        ligand_name=ligand_name
    )
    
    return summary
