#!/usr/bin/env python3
"""
Enhanced AutoDock Preparation Module
Integrates with PDB Prepare Wizard for comprehensive molecular docking preparation
"""

import os
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import shutil

@dataclass
class PreparationConfig:
    """Configuration for AutoDock preparation"""
    ligands_input: str
    receptors_input: str
    ligands_output: str
    receptors_output: str
    force_field: str = "AMBER"
    ph: float = 7.4
    allow_bad_res: bool = True
    default_altloc: str = "A"
    plip_enabled: bool = True
    plip_binding_site_detection: bool = True
    validate_outputs: bool = True
    min_file_size_kb: int = 1

class AutoDockPreparationPipeline:
    """
    Enhanced AutoDock preparation pipeline with PLIP integration
    """
    
    def __init__(self, config: Optional[PreparationConfig] = None):
        self.config = config or PreparationConfig(
            ligands_input="./ligands_raw",
            receptors_input="./receptors_raw", 
            ligands_output="./ligands_prep",
            receptors_output="./receptors_prep"
        )
        self.logger = self._setup_logging()
        self.script_dir = Path(__file__).parent
        self.enhanced_script = self.script_dir / "prep_autodock_enhanced.sh"
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the preparation pipeline"""
        logger = logging.getLogger('autodock_preparation')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def create_config_file(self, config_path: str = "autodock_config.json") -> str:
        """
        Create a configuration file for the enhanced bash script
        
        Args:
            config_path: Path to save the configuration file
            
        Returns:
            Path to the created configuration file
        """
        config = {
            "input": {
                "ligands": {
                    "path": self.config.ligands_input,
                    "formats": ["sdf", "mol2", "pdb"],
                    "in_same_folder": False
                },
                "receptors": {
                    "path": self.config.receptors_input,
                    "formats": ["pdb"],
                    "in_same_folder": False
                }
            },
            "output": {
                "ligands": self.config.ligands_output,
                "receptors": self.config.receptors_output,
                "logs": "./logs"
            },
            "preparation": {
                "force_field": self.config.force_field,
                "ph": self.config.ph,
                "allow_bad_res": self.config.allow_bad_res,
                "default_altloc": self.config.default_altloc
            },
            "plip": {
                "enabled": self.config.plip_enabled,
                "binding_site_detection": self.config.plip_binding_site_detection,
                "interaction_analysis": True
            },
            "quality_control": {
                "validate_outputs": self.config.validate_outputs,
                "check_file_sizes": True,
                "min_file_size_kb": self.config.min_file_size_kb
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        self.logger.info(f"Configuration file created: {config_path}")
        return config_path
    
    def check_dependencies(self) -> Tuple[bool, List[str]]:
        """
        Check if all required dependencies are available
        
        Returns:
            Tuple of (all_available, missing_dependencies)
        """
        required_tools = [
            "mk_prepare_ligand.py",
            "mk_prepare_receptor.py", 
            "pdb2pqr30",
            "obabel"
        ]
        
        missing = []
        for tool in required_tools:
            if not shutil.which(tool):
                missing.append(tool)
                
        if missing:
            self.logger.error(f"Missing dependencies: {missing}")
            return False, missing
            
        self.logger.info("All required dependencies found")
        return True, []
    
    def prepare_ligands_from_pdb(self, pdb_file: str, output_dir: str) -> Optional[str]:
        """
        Extract ligands from PDB file and prepare them for AutoDock
        
        Args:
            pdb_file: Path to PDB file
            output_dir: Output directory for prepared ligands
            
        Returns:
            Path to prepared ligand file or None if failed
        """
        try:
            from core_pipeline import MolecularDockingPipeline
            
            # Initialize pipeline
            pipeline = MolecularDockingPipeline(output_dir=output_dir)
            
            # Enumerate HETATMs
            hetatm_details, unique_hetatms = pipeline.enumerate_hetatms(pdb_file)
            
            if not unique_hetatms:
                self.logger.warning(f"No ligands found in {pdb_file}")
                return None
                
            # Get the first ligand (or let user choose)
            ligand_name = unique_hetatms[0]
            ligand_info = hetatm_details[ligand_name][0]
            
            # Extract ligand
            ligand_pdb = pipeline.save_hetatm_as_pdb(
                pdb_file, 
                ligand_name, 
                ligand_info['chain'], 
                ligand_info['res_id']
            )
            
            if ligand_pdb:
                # Convert PDB to PDBQT
                base_name = Path(ligand_pdb).stem
                pdbqt_file = Path(output_dir) / f"{base_name}.pdbqt"
                
                # Use obabel to convert PDB to SDF first, then to PDBQT
                sdf_file = Path(output_dir) / f"{base_name}_temp.sdf"
                
                try:
                    # PDB → SDF (with explicit hydrogens)
                    subprocess.run([
                        "obabel", ligand_pdb, "-O", str(sdf_file), "-h"
                    ], check=True, capture_output=True)
                    
                    # SDF → PDBQT
                    subprocess.run([
                        "mk_prepare_ligand.py", "-i", str(sdf_file), "-o", str(pdbqt_file)
                    ], check=True, capture_output=True)
                    
                    # Clean up intermediate file
                    sdf_file.unlink()
                    
                except subprocess.CalledProcessError as e:
                    # Clean up intermediate file if it exists
                    if sdf_file.exists():
                        sdf_file.unlink()
                    raise e
                
                self.logger.info(f"Prepared ligand: {pdbqt_file}")
                return str(pdbqt_file)
                
        except Exception as e:
            self.logger.error(f"Failed to prepare ligand from PDB: {e}")
            return None
    
    def run_enhanced_preparation(self, config_path: Optional[str] = None) -> bool:
        """
        Run the enhanced AutoDock preparation script
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            True if successful, False otherwise
        """
        if not config_path:
            config_path = self.create_config_file()
            
        if not self.enhanced_script.exists():
            self.logger.error(f"Enhanced script not found: {self.enhanced_script}")
            return False
            
        try:
            # Make script executable
            os.chmod(self.enhanced_script, 0o755)
            
            # Run the enhanced script
            result = subprocess.run([
                str(self.enhanced_script), config_path
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("AutoDock preparation completed successfully")
                self.logger.info(f"Output: {result.stdout}")
                return True
            else:
                self.logger.error(f"Preparation failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to run preparation script: {e}")
            return False
    
    def analyze_preparation_results(self, output_dir: str) -> Dict:
        """
        Analyze the results of AutoDock preparation
        
        Args:
            output_dir: Directory containing prepared files
            
        Returns:
            Dictionary with analysis results
        """
        output_path = Path(output_dir)
        
        results = {
            "ligands": {
                "count": 0,
                "files": [],
                "total_size_mb": 0
            },
            "receptors": {
                "count": 0,
                "files": [],
                "total_size_mb": 0
            },
            "plip_analysis": {
                "available": False,
                "reports": []
            }
        }
        
        # Analyze ligands
        ligand_files = list(output_path.glob("*.pdbqt"))
        results["ligands"]["count"] = len(ligand_files)
        results["ligands"]["files"] = [str(f) for f in ligand_files]
        results["ligands"]["total_size_mb"] = sum(f.stat().st_size for f in ligand_files) / (1024 * 1024)
        
        # Analyze receptors
        receptor_files = list(output_path.glob("*.pdbqt"))
        results["receptors"]["count"] = len(receptor_files)
        results["receptors"]["files"] = [str(f) for f in receptor_files]
        results["receptors"]["total_size_mb"] = sum(f.stat().st_size for f in receptor_files) / (1024 * 1024)
        
        # Check for PLIP analysis
        plip_dirs = list(output_path.glob("*/plip_analysis"))
        if plip_dirs:
            results["plip_analysis"]["available"] = True
            results["plip_analysis"]["reports"] = [str(d / "report.txt") for d in plip_dirs if (d / "report.txt").exists()]
        
        return results
    
    def generate_preparation_report(self, results: Dict, output_file: str = "preparation_report.json"):
        """
        Generate a comprehensive report of the preparation process
        
        Args:
            results: Results from analyze_preparation_results
            output_file: Path to save the report
        """
        report = {
            "preparation_summary": {
                "timestamp": str(Path().cwd()),
                "config": {
                    "force_field": self.config.force_field,
                    "ph": self.config.ph,
                    "plip_enabled": self.config.plip_enabled
                },
                "results": results
            },
            "recommendations": self._generate_recommendations(results)
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.logger.info(f"Preparation report saved: {output_file}")
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations based on preparation results"""
        recommendations = []
        
        if results["ligands"]["count"] == 0:
            recommendations.append("No ligands were prepared. Check input directory and file formats.")
        
        if results["receptors"]["count"] == 0:
            recommendations.append("No receptors were prepared. Check input directory and file formats.")
        
        if not results["plip_analysis"]["available"] and self.config.plip_enabled:
            recommendations.append("PLIP analysis was not performed. Check PLIP installation.")
        
        if results["ligands"]["count"] > 0 and results["receptors"]["count"] > 0:
            recommendations.append("Ready for AutoDock Vina docking. Use the prepared PDBQT files.")
        
        return recommendations

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced AutoDock Preparation Pipeline")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--ligands-input", help="Input directory for ligands")
    parser.add_argument("--receptors-input", help="Input directory for receptors")
    parser.add_argument("--ligands-output", help="Output directory for prepared ligands")
    parser.add_argument("--receptors-output", help="Output directory for prepared receptors")
    parser.add_argument("--force-field", default="AMBER", help="Force field for PDB2PQR")
    parser.add_argument("--ph", type=float, default=7.4, help="pH for protonation")
    parser.add_argument("--no-plip", action="store_true", help="Disable PLIP analysis")
    parser.add_argument("--create-config", action="store_true", help="Create configuration file and exit")
    
    args = parser.parse_args()
    
    # Create configuration
    config = PreparationConfig(
        ligands_input=args.ligands_input or "./ligands_raw",
        receptors_input=args.receptors_input or "./receptors_raw",
        ligands_output=args.ligands_output or "./ligands_prep", 
        receptors_output=args.receptors_output or "./receptors_prep",
        force_field=args.force_field,
        ph=args.ph,
        plip_enabled=not args.no_plip
    )
    
    # Initialize pipeline
    pipeline = AutoDockPreparationPipeline(config)
    
    if args.create_config:
        config_path = pipeline.create_config_file()
        print(f"Configuration file created: {config_path}")
        return
    
    # Check dependencies
    deps_ok, missing = pipeline.check_dependencies()
    if not deps_ok:
        print(f"Missing dependencies: {missing}")
        return 1
    
    # Run preparation
    success = pipeline.run_enhanced_preparation(args.config)
    
    if success:
        # Analyze results
        results = pipeline.analyze_preparation_results(config.receptors_output)
        pipeline.generate_preparation_report(results)
        
        print(f"Preparation completed successfully!")
        print(f"Ligands prepared: {results['ligands']['count']}")
        print(f"Receptors prepared: {results['receptors']['count']}")
        if results['plip_analysis']['available']:
            print(f"PLIP analysis reports: {len(results['plip_analysis']['reports'])}")
        
        return 0
    else:
        print("Preparation failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    exit(main())
