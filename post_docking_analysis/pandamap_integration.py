"""
PandaMap integration for post-docking analysis pipeline.

This module provides functionality to generate protein-ligand interaction
visualizations using PandaMap for all best poses from docking results.
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class PandaMapAnalyzer:
    """Analyzer for generating protein-ligand interaction visualizations using PandaMap."""
    
    def __init__(self, conda_env: str = "pandamap"):
        """
        Initialize PandaMap analyzer.
        
        Parameters
        ----------
        conda_env : str
            Name of the conda environment containing PandaMap
        """
        self.conda_env = conda_env
        self.pandamap_cmd = f"conda run -n {conda_env} pandamap"
    
    def generate_interaction_maps(
        self, 
        poses_dir: Path, 
        output_dir: Path,
        ligand_name: str = "UNK",
        generate_2d: bool = True,
        generate_3d: bool = True,
        generate_reports: bool = True,
        dpi: int = 300
    ) -> Tuple[int, int, int]:
        """
        Generate interaction maps for all PDB files in poses directory.
        
        Parameters
        ----------
        poses_dir : Path
            Directory containing PDB files of best poses
        output_dir : Path
            Output directory for generated files
        ligand_name : str
            Ligand residue name (default: "UNK")
        generate_2d : bool
            Generate 2D interaction maps (PNG)
        generate_3d : bool
            Generate 3D interactive HTML visualizations
        generate_reports : bool
            Generate detailed text reports
        dpi : int
            Resolution for 2D images
            
        Returns
        -------
        Tuple[int, int, int]
            Count of generated 2D maps, 3D visualizations, and reports
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        maps_2d_dir = output_dir / "interaction_maps_2d"
        maps_3d_dir = output_dir / "interaction_maps_3d"
        reports_dir = output_dir / "interaction_reports"
        
        if generate_2d:
            maps_2d_dir.mkdir(exist_ok=True)
        if generate_3d:
            maps_3d_dir.mkdir(exist_ok=True)
        if generate_reports:
            reports_dir.mkdir(exist_ok=True)
        
        pdb_files = list(poses_dir.glob("*.pdb"))
        logger.info(f"Found {len(pdb_files)} PDB files to process")
        
        count_2d = 0
        count_3d = 0
        count_reports = 0
        
        for pdb_file in pdb_files:
            basename = pdb_file.stem
            logger.info(f"Processing {basename}...")
            
            try:
                # Generate 2D interaction map
                if generate_2d:
                    success = self._generate_2d_map(
                        pdb_file, maps_2d_dir, basename, ligand_name, dpi
                    )
                    if success:
                        count_2d += 1
                
                # Generate 3D interactive visualization
                if generate_3d:
                    success = self._generate_3d_viz(
                        pdb_file, maps_3d_dir, basename, ligand_name
                    )
                    if success:
                        count_3d += 1
                
                # Generate detailed report
                if generate_reports:
                    success = self._generate_report(
                        pdb_file, reports_dir, basename, ligand_name
                    )
                    if success:
                        count_reports += 1
                        
            except Exception as e:
                logger.error(f"Error processing {basename}: {e}")
                continue
        
        logger.info(f"Generated {count_2d} 2D maps, {count_3d} 3D visualizations, {count_reports} reports")
        return count_2d, count_3d, count_reports
    
    def _generate_2d_map(
        self, 
        pdb_file: Path, 
        output_dir: Path, 
        basename: str, 
        ligand_name: str,
        dpi: int
    ) -> bool:
        """Generate 2D interaction map."""
        output_file = output_dir / f"{basename}_interaction_map.png"
        
        cmd = [
            "conda", "run", "-n", self.conda_env, "pandamap",
            str(pdb_file),
            "--ligand", ligand_name,
            "--output", str(output_file),
            "--dpi", str(dpi),
            "--title", f"Interaction Map: {basename}"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Generated 2D map: {output_file}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate 2D map for {basename}: {e.stderr}")
            return False
    
    def _generate_3d_viz(
        self, 
        pdb_file: Path, 
        output_dir: Path, 
        basename: str, 
        ligand_name: str
    ) -> bool:
        """Generate 3D interactive visualization."""
        output_file = output_dir / f"{basename}_interaction_3d.html"
        
        cmd = [
            "conda", "run", "-n", self.conda_env, "pandamap",
            str(pdb_file),
            "--ligand", ligand_name,
            "--3d",
            "--3d-output", str(output_file),
            "--width", "1024",
            "--height", "768"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Generated 3D visualization: {output_file}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate 3D viz for {basename}: {e.stderr}")
            return False
    
    def _generate_report(
        self, 
        pdb_file: Path, 
        output_dir: Path, 
        basename: str, 
        ligand_name: str
    ) -> bool:
        """Generate detailed interaction report."""
        output_file = output_dir / f"{basename}_interaction_report.txt"
        
        cmd = [
            "conda", "run", "-n", self.conda_env, "pandamap",
            str(pdb_file),
            "--ligand", ligand_name,
            "--report",
            "--report-file", str(output_file)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Generated report: {output_file}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate report for {basename}: {e.stderr}")
            return False
    
    def generate_comprehensive_analysis(
        self, 
        poses_dir: Path, 
        output_dir: Path,
        ligand_name: str = "UNK"
    ) -> dict:
        """
        Generate comprehensive analysis with all visualization types.
        
        Parameters
        ----------
        poses_dir : Path
            Directory containing PDB files of best poses
        output_dir : Path
            Output directory for generated files
        ligand_name : str
            Ligand residue name
            
        Returns
        -------
        dict
            Summary of generated files
        """
        logger.info("Starting comprehensive PandaMap analysis...")
        
        count_2d, count_3d, count_reports = self.generate_interaction_maps(
            poses_dir=poses_dir,
            output_dir=output_dir,
            ligand_name=ligand_name,
            generate_2d=True,
            generate_3d=True,
            generate_reports=True,
            dpi=300
        )
        
        summary = {
            "total_poses": len(list(poses_dir.glob("*.pdb"))),
            "generated_2d_maps": count_2d,
            "generated_3d_visualizations": count_3d,
            "generated_reports": count_reports,
            "output_directories": {
                "interaction_maps_2d": str(output_dir / "interaction_maps_2d"),
                "interaction_maps_3d": str(output_dir / "interaction_maps_3d"),
                "interaction_reports": str(output_dir / "interaction_reports")
            }
        }
        
        logger.info(f"PandaMap analysis complete: {summary}")
        return summary


def main():
    """Example usage of PandaMapAnalyzer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate PandaMap visualizations for docking poses")
    parser.add_argument("poses_dir", type=Path, help="Directory containing PDB files")
    parser.add_argument("output_dir", type=Path, help="Output directory")
    parser.add_argument("--ligand", default="UNK", help="Ligand residue name")
    parser.add_argument("--conda-env", default="pandamap", help="Conda environment name")
    
    args = parser.parse_args()
    
    analyzer = PandaMapAnalyzer(conda_env=args.conda_env)
    summary = analyzer.generate_comprehensive_analysis(
        poses_dir=args.poses_dir,
        output_dir=args.output_dir,
        ligand_name=args.ligand
    )
    
    print("PandaMap Analysis Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
