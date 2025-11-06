#!/usr/bin/env python3
"""
PDB Prepare Wizard - Core Pipeline Module
========================================

Consolidated core pipeline for preparing PDB files for molecular docking studies.
This module provides functionality to:
- Download PDB files from RCSB PDB database
- Extract and analyze ligands (HETATMs)
- Clean PDB files by removing unwanted residues
- Analyze pocket properties and druggability
- Generate comprehensive reports

Author: Molecular Docking Pipeline
Version: 2.1.0
"""

import os
import sys
import subprocess
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any
import warnings
import time
from file_validators import FileValidator, FileValidationError
from security_utils import SecurityValidator, SecurityError
from logging_config import get_logger, log_section, log_step, LogTimer
from version_tracker import get_metadata, save_metadata, get_version_string
from unified_config import PipelineConfig
from memory_manager import MemoryMonitor, cleanup_biopython_structure
from exceptions import (
    PDBDownloadError, LigandNotFoundError, MissingAtomsError,
    PocketAnalysisError, OutputWriteError, DependencyError
)
warnings.filterwarnings("ignore")

# Initialize logger for this module
logger = get_logger(__name__)

# Add Excel support
try:
    import openpyxl
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

try:
    from Bio.PDB import PDBList, PDBParser, Select, PDBIO
    from Bio.PDB.Structure import Structure
    from Bio.PDB.Model import Model
    from Bio.PDB.Chain import Chain
except ImportError as e:
    print(f"❌ Error importing Biopython: {e}")
    print("Please install Biopython: pip install biopython")
    sys.exit(1)

def retry_with_backoff(max_retries=4, base_delay=2.0):
    """
    Decorator to retry a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubles each retry)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                        logger.info(f"Retrying in {delay:.1f} seconds...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed")
            raise last_exception
        return wrapper
    return decorator

class MolecularDockingPipeline:
    """
    A comprehensive molecular docking pipeline for PDB file preparation and analysis.
    
    This class provides methods to:
    - Download and process PDB files
    - Extract ligands and analyze binding sites
    - Clean and prepare structures for docking
    - Analyze pocket properties and druggability
    """
    
    def __init__(
        self,
        output_dir: str = "pipeline_output",
        config: Optional[PipelineConfig] = None,
        enable_memory_monitor: bool = True
    ):
        """
        Initialize the molecular docking pipeline.

        Args:
            output_dir (str): Directory to store all output files
            config: Pipeline configuration (uses defaults if None)
            enable_memory_monitor: Enable memory monitoring
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Load or create configuration
        self.config = config or PipelineConfig()

        # Initialize memory monitor
        self.memory_monitor = None
        if enable_memory_monitor:
            self.memory_monitor = MemoryMonitor(
                auto_gc=self.config.performance.explicit_cleanup,
                gc_frequency=self.config.performance.gc_frequency
            )

        logger.info(f"Pipeline initialized. Output directory: {self.output_dir}")
        logger.info(get_version_string())
        logger.info(f"Configuration: interaction_cutoff={self.config.scientific.interaction_cutoff}Å")

        # Validate required packages
        self._validate_dependencies()

    def _validate_dependencies(self):
        """Validate that all required dependencies are available."""
        try:
            import numpy as np
            import pandas as pd
            from Bio.PDB import PDBParser
            logger.info("All core dependencies available")
        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            raise DependencyError(str(e), "core pipeline functionality")

        # Check for optional PLIP
        try:
            import plip
            logger.info("PLIP available for advanced interaction analysis")
            self.plip_available = True
        except ImportError:
            logger.warning("PLIP not available - will use distance-based analysis")
            self.plip_available = False
    
    def fetch_pdb(self, pdb_id: str) -> str:
        """
        Download PDB file from RCSB PDB database with retry logic.

        Args:
            pdb_id (str): PDB identifier (e.g., '1ABC')

        Returns:
            str: Path to downloaded PDB file

        Raises:
            PDBDownloadError: After all retry attempts are exhausted
        """
        logger.info(f"Fetching PDB {pdb_id}...")

        # Retry logic using config
        max_retries = self.config.network.max_retries
        base_delay = self.config.network.retry_base_delay
        last_exception = None

        for attempt in range(max_retries):
            try:
                pdbl = PDBList()
                filename = pdbl.retrieve_pdb_file(
                    pdb_id.lower(),
                    pdir=str(self.output_dir),
                    file_format='pdb'
                )

                # Rename to simpler format
                new_filename = self.output_dir / f"{pdb_id.upper()}.pdb"

                # Clean up any existing file first
                if new_filename.exists():
                    new_filename.unlink()

                os.rename(filename, new_filename)
                logger.info(f"Downloaded: {new_filename}")
                return str(new_filename)

            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"All {max_retries} attempts failed")

        raise PDBDownloadError(pdb_id=pdb_id, reason=str(last_exception))

    def enumerate_hetatms(self, pdb_file: str) -> Tuple[List[Tuple], List[str]]:
        """
        List all HETATM residues in the PDB file for user selection.

        Args:
            pdb_file (str): Path to PDB file

        Returns:
            Tuple[List[Tuple], List[str]]: (detailed hetatm info, unique hetatm types)
        """
        print(f"🔄 Enumerating HETATMs in {pdb_file}...")

        # Validate PDB file format
        try:
            validation_result = FileValidator.validate_file(pdb_file, 'pdb', check_structure=True)
            if validation_result['warnings']:
                for warning in validation_result['warnings']:
                    print(f"⚠️  {warning}")
        except FileValidationError as e:
            print(f"❌ PDB validation failed: {e}")
            return [], []

        try:
            parser = PDBParser(QUIET=True)
            structure = parser.get_structure('protein', pdb_file)
            
            hetatm_details = []
            hetatm_counts = {}
            
            for model in structure:
                for chain in model:
                    for residue in chain:
                        if residue.get_id()[0] != ' ':  # HETATM check
                            resname = residue.get_resname()
                            chain_id = chain.get_id()
                            res_id = residue.get_id()[1]
                            
                            hetatm_details.append((resname, chain_id, res_id, residue))
                            hetatm_counts[resname] = hetatm_counts.get(resname, 0) + 1
            
            unique_hetatms = list(hetatm_counts.keys())
            
            if not unique_hetatms:
                print("⚠️  No HETATMs found in this structure")
                return [], []
            
            print(f"✓ Found {len(hetatm_details)} HETATM instances of {len(unique_hetatms)} types:")
            for resname, count in hetatm_counts.items():
                print(f"   {resname}: {count} instance(s)")
            
            return hetatm_details, unique_hetatms
        except Exception as e:
            print(f"❌ Error enumerating HETATMs: {e}")
            return [], []

    def save_hetatm_as_pdb(self, pdb_file: str, selected_hetatm: str, 
                          chain_id: str, res_id: int, 
                          output_filename: Optional[str] = None) -> Optional[str]:
        """
        Save a specific HETATM residue as a separate PDB file.
        
        Args:
            pdb_file (str): Path to source PDB file
            selected_hetatm (str): HETATM residue name
            chain_id (str): Chain identifier
            res_id (int): Residue ID
            output_filename (str, optional): Output filename
            
        Returns:
            Optional[str]: Path to saved ligand PDB file, or None if failed
        """
        print(f"🔄 Saving HETATM {selected_hetatm}_{chain_id}_{res_id} as separate PDB...")
        
        try:
            parser = PDBParser(QUIET=True)
            structure = parser.get_structure('protein', pdb_file)
            
            # Create new structure containing only the selected HETATM
            new_structure = Structure('ligand')
            new_model = Model(0)
            new_chain = Chain(chain_id)
            
            # Find and copy the specific HETATM residue
            found_residue = None
            for model in structure:
                for chain in model:
                    if chain.get_id() == chain_id:
                        for residue in chain:
                            if (residue.get_resname() == selected_hetatm and 
                                residue.get_id()[1] == res_id and
                                residue.get_id()[0] != ' '):
                                found_residue = residue
                                break
            
            if found_residue:
                new_chain.add(found_residue.copy())
                new_model.add(new_chain)
                new_structure.add(new_model)
                
                # Save as PDB
                if output_filename is None:
                    output_filename = self.output_dir / f"ligand_{selected_hetatm}_{chain_id}_{res_id}.pdb"
                
                io = PDBIO()
                io.set_structure(new_structure)
                io.save(str(output_filename))
                print(f"✓ Ligand saved as: {output_filename}")
                return str(output_filename)
            else:
                print(f"❌ Could not find HETATM {selected_hetatm}_{chain_id}_{res_id}")
                return None
                
        except Exception as e:
            print(f"❌ Error saving HETATM: {e}")
            return None

    def clean_pdb(self, pdb_file: str, to_remove_list: List[str], 
                  output_filename: Optional[str] = None) -> str:
        """
        Clean PDB file by removing specified residues.
        
        Args:
            pdb_file (str): Path to input PDB file
            to_remove_list (List[str]): List of residue names to remove
            output_filename (str, optional): Output filename
            
        Returns:
            str: Path to cleaned PDB file
        """
        print(f"🔄 Cleaning PDB file...")
        
        try:
            parser = PDBParser(QUIET=True)
            structure = parser.get_structure('protein', pdb_file)
            
            # Create a selector to keep only desired residues
            class ResidueSelector(Select):
                def accept_residue(self, residue):
                    resname = residue.get_resname()
                    return resname not in to_remove_list
            
            if output_filename is None:
                output_filename = self.output_dir / "cleaned.pdb"
            
            io = PDBIO()
            io.set_structure(structure)
            io.save(str(output_filename), ResidueSelector())
            
            print(f"✓ Cleaned PDB saved as: {output_filename}")
            return str(output_filename)
        except Exception as e:
            print(f"❌ Error cleaning PDB: {e}")
            raise

    def distance_based_interaction_detection(self, pdb_file: str, ligand_name: str,
                                          chain_id: str, res_id: int,
                                          cutoff: Optional[float] = None) -> List[np.ndarray]:
        """
        Detect interacting residues using distance-based approach.

        Args:
            pdb_file (str): Path to PDB file
            ligand_name (str): Ligand residue name
            chain_id (str): Chain identifier
            res_id (int): Residue ID
            cutoff (float): Distance cutoff in Angstroms (uses config default if None)

        Returns:
            List[np.ndarray]: List of coordinates of interacting atoms
        """
        # Use config value if not specified
        if cutoff is None:
            cutoff = self.config.scientific.interaction_cutoff

        try:
            parser = PDBParser(QUIET=True)
            structure = parser.get_structure('protein', pdb_file)
            
            # Find ligand atoms
            ligand_atoms = []
            for model in structure:
                for chain in model:
                    if chain.get_id() == chain_id:
                        for residue in chain:
                            if (residue.get_resname() == ligand_name and 
                                residue.get_id()[1] == res_id and
                                residue.get_id()[0] != ' '):
                                ligand_atoms = [atom for atom in residue.get_atoms()]
                                break
            
            if not ligand_atoms:
                raise ValueError(f"Ligand {ligand_name} not found in chain {chain_id}")
            
            # Find interacting atoms
            all_coords = []
            interacting_residues = set()
            
            for model in structure:
                for chain in model:
                    for residue in chain:
                        if residue.get_id()[0] == ' ':  # Protein residue
                            for res_atom in residue.get_atoms():
                                for lig_atom in ligand_atoms:
                                    distance = res_atom - lig_atom  # BioPython distance calculation
                                    if distance <= cutoff:
                                        all_coords.append(res_atom.get_coord())
                                        interacting_residues.add(residue.get_resname() + str(residue.get_id()[1]))
                                        break
            
            print(f"✓ Found {len(interacting_residues)} interacting residues")
            return all_coords
            
        except Exception as e:
            raise ValueError(f"Distance-based interaction detection failed: {e}")

    def extract_active_site_coords(self, cleaned_pdb: str, ligand_name: str, 
                                 chain_id: str, res_id: int, 
                                 method: str = 'distance') -> Tuple[np.ndarray, int]:
        """
        Extract active site coordinates using specified method.
        
        Args:
            cleaned_pdb (str): Path to cleaned PDB file
            ligand_name (str): Ligand residue name
            chain_id (str): Chain identifier
            res_id (int): Residue ID
            method (str): Method to use ('plip' or 'distance')
            
        Returns:
            Tuple[np.ndarray, int]: Active site center coordinates and number of atoms
        """
        print(f"🔄 Extracting active site coordinates using {method} method...")
        
        coords = []
        
        if method == 'plip' and self.plip_available:
            try:
                from plip.structure.preparation import PDBComplex
                from plip.exchange.report import BindingSiteReport

                my_mol = PDBComplex()
                my_mol.load_pdb(cleaned_pdb)
                my_mol.analyze()

                interactions = my_mol.interaction_sets
                if not interactions:
                    print("⚠️  No interactions found with PLIP, falling back to distance method")
                    method = 'distance'
                else:
                    for site in interactions.values():
                        report = BindingSiteReport(site)
                        all_interacting_residues = report.bs_res_interacting

                        for residue in all_interacting_residues:
                            for atom in residue.atoms:
                                coords.append(atom.get_coord())

                    print(f"✓ PLIP found {len(coords)} interacting atoms")
            except Exception as e:
                print(f"⚠️  PLIP failed: {e}, using distance method")
                method = 'distance'
        
        if method == 'distance' or len(coords) == 0:
            coords = self.distance_based_interaction_detection(
                cleaned_pdb, ligand_name, chain_id, res_id
            )
        
        if not coords:
            raise ValueError("No coordinates extracted")
        
        # Calculate average XYZ
        avg_xyz = np.mean(coords, axis=0)
        print(f"✓ Active site center: X={avg_xyz[0]:.2f}, Y={avg_xyz[1]:.2f}, Z={avg_xyz[2]:.2f}")
        
        return avg_xyz, len(coords)

    def analyze_pocket_properties(self, cleaned_pdb: str, center_coords: np.ndarray, 
                                ligand_pdb: Optional[str] = None) -> Dict[str, Any]:
        """
        Comprehensive pocket analysis using multiple approaches.
        
        Args:
            cleaned_pdb (str): Path to cleaned PDB file
            center_coords (np.ndarray): Pocket center coordinates
            ligand_pdb (str, optional): Path to ligand PDB file
            
        Returns:
            Dict[str, Any]: Dictionary containing pocket analysis results
        """
        print("🔄 Starting comprehensive pocket analysis...")
        
        results = {
            'center_x': center_coords[0],
            'center_y': center_coords[1], 
            'center_z': center_coords[2]
        }
        
        try:
            parser = PDBParser(QUIET=True)
            structure = parser.get_structure('protein', cleaned_pdb)
            
            # Pocket Size and Shape Analysis
            print("📊 Analyzing pocket size and shape...")
            try:
                # Geometric estimation based on interaction sphere (using config radius)
                sphere_radius = self.config.scientific.interaction_sphere_radius
                results['pocket_volume_A3'] = 4/3 * np.pi * (sphere_radius**3)
            except Exception as e:
                print(f"⚠️  Pocket volume analysis failed: {e}")
                results['pocket_volume_A3'] = 'N/A'
            
            # Electrostatic Potential Analysis
            print("⚡ Analyzing electrostatic potential...")
            try:
                charged_residues = {'ARG': 1, 'LYS': 1, 'HIS': 0.5, 'ASP': -1, 'GLU': -1}
                electrostatic_score = 0
                nearby_charges = 0
                
                for model in structure:
                    for chain in model:
                        for residue in chain:
                            if residue.get_id()[0] == ' ':  # Protein residue
                                resname = residue.get_resname()
                                if resname in charged_residues:
                                    # Check if residue is near the pocket center
                                    try:
                                        ca_atom = residue['CA']
                                        dist = np.linalg.norm(ca_atom.get_coord() - center_coords)
                                        if dist <= self.config.scientific.pocket_radius:
                                            electrostatic_score += charged_residues[resname]
                                            nearby_charges += 1
                                    except:
                                        continue
                
                results['electrostatic_score'] = electrostatic_score
                results['nearby_charged_residues'] = nearby_charges
                print(f"✓ Electrostatic analysis: {electrostatic_score:.2f} (from {nearby_charges} charged residues)")
            except Exception as e:
                print(f"⚠️  Electrostatic analysis failed: {e}")
                results['electrostatic_score'] = 'N/A'
                results['nearby_charged_residues'] = 0
            
            # Hydrophobic Character Analysis
            print("🧪 Analyzing hydrophobic character...")
            try:
                hydrophobic_residues = {'PHE', 'TRP', 'TYR', 'LEU', 'ILE', 'VAL', 'ALA', 'MET'}
                hydrophobic_score = 0
                nearby_hydrophobic = 0
                
                for model in structure:
                    for chain in model:
                        for residue in chain:
                            if residue.get_id()[0] == ' ':  # Protein residue
                                resname = residue.get_resname()
                                if resname in hydrophobic_residues:
                                    try:
                                        ca_atom = residue['CA']
                                        dist = np.linalg.norm(ca_atom.get_coord() - center_coords)
                                        if dist <= 8.0:  # Within 8Å of pocket center
                                            hydrophobic_score += 1
                                            nearby_hydrophobic += 1
                                    except:
                                        continue
                
                results['hydrophobic_score'] = hydrophobic_score
                results['nearby_hydrophobic_residues'] = nearby_hydrophobic
                print(f"✓ Hydrophobic analysis: {hydrophobic_score} hydrophobic residues nearby")
            except Exception as e:
                print(f"⚠️  Hydrophobic analysis failed: {e}")
                results['hydrophobic_score'] = 'N/A'
                results['nearby_hydrophobic_residues'] = 0
            
            # Druggability Scoring
            print("💊 Calculating druggability score...")
            try:
                # Druggability scoring based on weighted factors from config
                druggability_components = {}

                # Factor 1: Pocket volume (normalized)
                if isinstance(results['pocket_volume_A3'], (int, float)):
                    vol_score = min(1.0, results['pocket_volume_A3'] / 1000.0)
                    druggability_components['volume'] = vol_score

                # Factor 2: Hydrophobic character (normalized)
                if isinstance(results['hydrophobic_score'], (int, float)):
                    hydro_score = min(1.0, results['hydrophobic_score'] / 10.0)
                    druggability_components['hydrophobic'] = hydro_score

                # Factor 3: Electrostatic balance (absolute value, inverted and normalized)
                if isinstance(results['electrostatic_score'], (int, float)):
                    elec_score = max(0.0, 1.0 - abs(results['electrostatic_score']) / 5.0)
                    druggability_components['electrostatic'] = elec_score

                if druggability_components:
                    # Weighted average using config weights
                    druggability_score = (
                        druggability_components.get('volume', 0) * self.config.scientific.druggability_volume_weight +
                        druggability_components.get('hydrophobic', 0) * self.config.scientific.druggability_hydrophobic_weight +
                        druggability_components.get('electrostatic', 0) * self.config.scientific.druggability_electrostatic_weight
                    )
                    results['druggability_score'] = round(druggability_score, 3)

                    # Interpretation using config thresholds
                    if druggability_score >= self.config.scientific.druggability_excellent_threshold:
                        interpretation = "Excellent"
                    elif druggability_score >= self.config.scientific.druggability_good_threshold:
                        interpretation = "Good"
                    elif druggability_score >= self.config.scientific.druggability_moderate_threshold:
                        interpretation = "Moderate"
                    else:
                        interpretation = "Poor"

                    results['druggability_interpretation'] = interpretation
                    print(f"✓ Druggability score: {druggability_score:.3f} ({interpretation})")
                else:
                    results['druggability_score'] = 'N/A'
                    results['druggability_interpretation'] = 'Unknown'
            except Exception as e:
                print(f"⚠️  Druggability scoring failed: {e}")
                results['druggability_score'] = 'N/A'
                results['druggability_interpretation'] = 'Unknown'

            print("✓ Pocket analysis completed successfully")

            # Cleanup BioPython structure
            if self.memory_monitor:
                cleanup_biopython_structure(structure)
                self.memory_monitor.track_operation("pocket_analysis")

            return results

        except Exception as e:
            print(f"❌ Pocket analysis failed: {e}")
            raise

    def generate_summary_report(self, results: Dict[str, Any], pdb_id: str) -> str:
        """
        Generate a comprehensive summary report with version metadata.

        Args:
            results (Dict[str, Any]): Analysis results
            pdb_id (str): PDB identifier

        Returns:
            str: Path to generated report file
        """
        logger.info("Generating summary report...")

        try:
            report_filename = self.output_dir / f"{pdb_id}_pipeline_results.csv"

            # Get version metadata
            metadata = get_metadata()

            # Prepare data for CSV
            report_data = []

            # Add metadata first
            report_data.append(['# Metadata', ''])
            report_data.append(['pipeline_version', metadata['pipeline_version']])
            report_data.append(['python_version', metadata['python_version']])
            report_data.append(['timestamp', metadata['timestamp']])
            report_data.append(['git_commit', metadata['git']['commit'][:8]])
            report_data.append(['', ''])  # Blank line

            # Add analysis results
            report_data.append(['# Analysis Results', ''])
            for key, value in results.items():
                report_data.append([key, value])

            # Save as CSV
            df = pd.DataFrame(report_data, columns=['Property', 'Value'])
            df.to_csv(report_filename, index=False)

            # Save separate metadata file
            save_metadata(report_filename)

            logger.info(f"Summary report saved: {report_filename}")
            return str(report_filename)
        except Exception as e:
            logger.exception(f"Error generating summary report: {e}")
            raise OutputWriteError(str(report_filename), str(e))

def parse_plip_text_report(report_file: str, ligand_name: str, chain_id: str, res_id: int) -> Optional[Dict]:
    """
    Parse PLIP text report to extract interaction data reliably.
    
    Args:
        report_file: Path to PLIP text report
        ligand_name: Name of the ligand (HETATM)
        chain_id: Chain identifier
        res_id: Residue number
    
    Returns:
        Dictionary containing parsed interaction data
    """
    try:
        with open(report_file, 'r') as f:
            content = f.read()
        
        # Find the section for our ligand
        ligand_section = f"{ligand_name}:{chain_id}:{res_id}"
        if ligand_section not in content:
            return None
        
        # Extract the section for this ligand
        start_idx = content.find(ligand_section)
        if start_idx == -1:
            return None
        
        # Find the end of this ligand's section using regex
        import re
        
        # Look for the next ligand section (format: LIGAND_NAME:CHAIN:RESID)
        pattern = rf'\n[A-Z0-9]+:{chain_id}:\d+'
        matches = list(re.finditer(pattern, content[start_idx + len(ligand_section):]))
        
        if matches:
            # Use the first match as the end
            end_idx = start_idx + len(ligand_section) + matches[0].start()
        else:
            # No next ligand found, use end of file
            end_idx = len(content)
        
        ligand_content = content[start_idx:end_idx]
        
        # Parse interactions - comprehensive list of all PLIP interaction types
        interactions = {
            'hydrophobic': [],
            'hydrogen_bonds': [],
            'halogen_bonds': [],
            'pi_stacking': [],
            'salt_bridges': [],
            'water_bridges': [],
            'metal_complexes': [],
            'pi_cation': []
        }
        
        # Define interaction type configurations
        interaction_configs = {
            '**Hydrophobic Interactions**': {
                'key': 'hydrophobic',
                'min_columns': 8,
                'distance_col': 6
            },
            '**Hydrogen Bonds**': {
                'key': 'hydrogen_bonds', 
                'min_columns': 10,
                'distance_col': 7  # DIST_H-A
            },
            '**Halogen Bonds**': {
                'key': 'halogen_bonds',
                'min_columns': 8,
                'distance_col': 7  # DIST
            },
            '**Water Bridges**': {
                'key': 'water_bridges',
                'min_columns': 10,
                'distance_col': 6  # DIST_A-W
            },
            '**pi-Stacking**': {
                'key': 'pi_stacking',
                'min_columns': 10,
                'distance_col': 7  # CENTDIST
            },
            '**Salt Bridges**': {
                'key': 'salt_bridges',
                'min_columns': 8,
                'distance_col': 6  # Estimated
            },
            '**Metal Complexes**': {
                'key': 'metal_complexes',
                'min_columns': 8,
                'distance_col': 6  # Estimated
            },
            '**pi-Cation Interactions**': {
                'key': 'pi_cation',
                'min_columns': 8,
                'distance_col': 6  # Estimated
            }
        }
        
        # Unified parsing for all interaction types
        for section_name, config in interaction_configs.items():
            if section_name in ligand_content:
                section_content = ligand_content.split(section_name)[1]
                if "**" in section_content:
                    section_content = section_content.split("**")[0]
                
                lines = section_content.split('\n')
                for line in lines:
                    if '|' in line and line.strip().startswith('|') and not line.strip().startswith('|---'):
                        parts = [p.strip() for p in line.split('|') if p.strip()]
                        if len(parts) >= config['min_columns']:
                            try:
                                resnr = int(parts[0])
                                restype = parts[1]
                                reschain = parts[2]
                                if reschain == chain_id:
                                    distance = float(parts[config['distance_col']]) if len(parts) > config['distance_col'] else 0.0
                                    interactions[config['key']].append({
                                        'resnr': resnr,
                                        'restype': restype,
                                        'reschain': reschain,
                                        'distance': distance
                                    })
                            except (ValueError, IndexError):
                                continue
        
        # Check for any unknown interaction types
        all_sections = []
        for line in ligand_content.split('\n'):
            if line.strip().startswith('**') and line.strip().endswith('**'):
                all_sections.append(line.strip())
        
        known_sections = set(interaction_configs.keys())
        found_sections = set(all_sections)
        unknown_sections = found_sections - known_sections
        
        if unknown_sections:
            print(f"⚠️ Found unknown interaction types: {unknown_sections}")
            print(f"   Please update interaction_configs to handle these types")
        
        return interactions
        
    except Exception as e:
        print(f"⚠️ Error parsing PLIP report: {e}")
        return None


def extract_residue_level_coordinates(pdb_file: str, ligand_name: str, 
                                    chain_id: str, res_id: int, cutoff: float = 5.0) -> Optional[Dict]:
    """
    Extract binding site coordinates at residue level using PLIP's text report.
    This function provides reliable analysis using PLIP's text output format.
    
    Args:
        pdb_file (str): Path to PDB file
        ligand_name (str): Ligand residue name
        chain_id (str): Chain identifier
        res_id (int): Residue ID
        cutoff (float): Distance cutoff in Angstroms (fallback method)
        
    Returns:
        Optional[Dict]: Dictionary with coordinate analysis or None if failed
    """
    print(f"🔄 Extracting residue-level binding site coordinates for {ligand_name}...")
    
    try:
        # Try PLIP text report analysis first
        print(f"🔄 Using PLIP text report analysis...")
        
        # Create temporary directory for PLIP analysis
        import tempfile
        import subprocess
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy PDB file to temp directory
            temp_pdb = os.path.join(temp_dir, os.path.basename(pdb_file))
            import shutil
            shutil.copy2(pdb_file, temp_pdb)
            
            # Run PLIP to generate text report
            try:
                result = subprocess.run(['plip', '-f', temp_pdb, '-t'], 
                                      capture_output=True, text=True, cwd=temp_dir)
                if result.returncode == 0:
                    # Find the report file
                    report_files = [f for f in os.listdir(temp_dir) if f.endswith('report.txt')]
                    if report_files:
                        report_file = os.path.join(temp_dir, report_files[0])
                        
                        # Parse the report
                        interactions = parse_plip_text_report(report_file, ligand_name, chain_id, res_id)
                        
                        if interactions:
                            # Load structure for coordinate extraction
                            parser = PDBParser(QUIET=True)
                            structure = parser.get_structure('protein', pdb_file)
                            
                            interacting_residues = set()
                            all_coords = []
                            
                            # Collect coordinates from all interaction types
                            for interaction_type, interaction_list in interactions.items():
                                for interaction in interaction_list:
                                    reskey = f"{interaction['restype']}_{interaction['resnr']}"
                                    interacting_residues.add(reskey)
                                    
                                    # Find the residue in the structure
                                    for model in structure:
                                        for chain in model:
                                            if chain.get_id() == chain_id:
                                                for residue in chain:
                                                    if (residue.get_resname() == interaction['restype'] and 
                                                        residue.get_id()[1] == interaction['resnr'] and
                                                        residue.get_id()[0] == ' '):
                                                        for atom in residue.get_atoms():
                                                            all_coords.append(atom.get_coord())
                                                        break
                            
                            if all_coords:
                                # Calculate overall center
                                overall_center = np.mean(all_coords, axis=0)
                                
                                # Calculate residue averages
                                residue_averages = {}
                                for reskey in interacting_residues:
                                    res_coords = []
                                    restype, resnr = reskey.split('_')
                                    resnr = int(resnr)
                                    
                                    for model in structure:
                                        for chain in model:
                                            if chain.get_id() == chain_id:
                                                for residue in chain:
                                                    if (residue.get_resname() == restype and 
                                                        residue.get_id()[1] == resnr and
                                                        residue.get_id()[0] == ' '):
                                                        for atom in residue.get_atoms():
                                                            res_coords.append(atom.get_coord())
                                                        break
                                    
                                    if res_coords:
                                        residue_averages[reskey] = np.mean(res_coords, axis=0)
                                
                                print(f"✓ PLIP found {len(interacting_residues)} interacting residues")
                                print(f"✓ Total interacting atoms: {len(all_coords)}")
                                print(f"✓ Binding site center: X={overall_center[0]:.2f}, Y={overall_center[1]:.2f}, Z={overall_center[2]:.2f}")
                                
                                return {
                                    'overall_center': overall_center,
                                    'residue_averages': residue_averages,
                                    'all_coords': all_coords,
                                    'ligand_center': overall_center,
                                    'num_interacting_residues': len(interacting_residues),
                                    'num_interacting_atoms': len(all_coords),
                                    'plip_enhanced': True,
                                    'interaction_types': {
                                        'hydrophobic': len(interactions['hydrophobic']),
                                        'hydrogen_bonds': len(interactions['hydrogen_bonds']),
                                        'pi_stacking': len(interactions['pi_stacking']),
                                        'salt_bridges': len(interactions['salt_bridges']),
                                        'halogen_bonds': len(interactions['halogen_bonds']),
                                        'water_bridges': len(interactions['water_bridges']),
                                        'metal_complexes': len(interactions['metal_complexes']),
                                        'pi_cation': 0
                                    },
                                    'detailed_interactions': {
                                        'hydrophobic_residues': sorted(set([f"{i['restype']}_{i['resnr']}" for i in interactions['hydrophobic']])),
                                        'hydrogen_bond_residues': sorted(set([f"{i['restype']}_{i['resnr']}" for i in interactions['hydrogen_bonds']])),
                                        'halogen_bond_residues': sorted(set([f"{i['restype']}_{i['resnr']}" for i in interactions['halogen_bonds']])),
                                        'pi_stacking_residues': sorted(set([f"{i['restype']}_{i['resnr']}" for i in interactions['pi_stacking']])),
                                        'salt_bridge_residues': sorted(set([f"{i['restype']}_{i['resnr']}" for i in interactions['salt_bridges']]))
                                    }
                                }
                            else:
                                print(f"⚠️ No interacting atoms found for {ligand_name}:{chain_id}:{res_id}")
                        else:
                            print(f"⚠️ No interactions found in PLIP report for {ligand_name}:{chain_id}:{res_id}")
                    else:
                        print(f"⚠️ PLIP report file not found")
                else:
                    print(f"⚠️ PLIP command failed: {result.stderr}")
            except FileNotFoundError:
                print(f"⚠️ PLIP command not found, using fallback method")
            except Exception as e:
                print(f"⚠️ PLIP analysis failed: {e}, using fallback method")
        
        # Fallback to distance-based method
        print(f"🔄 Using distance-based fallback method...")
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('protein', pdb_file)
        
        # Find the ligand residue
        ligand_residue = None
        for model in structure:
            for chain in model:
                if chain.get_id() == chain_id:
                    for residue in chain:
                        if (residue.get_resname() == ligand_name and 
                            residue.get_id()[1] == res_id and
                            residue.get_id()[0] != ' '):
                            ligand_residue = residue
                            break
        
        if not ligand_residue:
            raise ValueError(f"Ligand {ligand_name} not found in chain {chain_id}")
        
        # Get ligand atom coordinates
        ligand_coords = [atom.get_coord() for atom in ligand_residue.get_atoms()]
        ligand_center = np.mean(ligand_coords, axis=0)
        
        # Find interacting residues within cutoff distance
        residue_coords = {}
        
        for model in structure:
            for chain in model:
                for residue in chain:
                    if residue.get_id()[0] == ' ':  # Protein residue
                        resname = residue.get_resname()
                        resnum = residue.get_id()[1]
                        reskey = f"{resname}_{resnum}"
                        
                        # Check if any atom in this residue is within cutoff
                        for atom in residue.get_atoms():
                            dist = np.linalg.norm(atom.get_coord() - ligand_center)
                            if dist <= cutoff:
                                if reskey not in residue_coords:
                                    residue_coords[reskey] = []
                                residue_coords[reskey].append(atom.get_coord())
                                break
        
        # Calculate average coordinates for each interacting residue
        residue_averages = {}
        all_coords = []
        
        for reskey, coords in residue_coords.items():
            avg_coord = np.mean(coords, axis=0)
            residue_averages[reskey] = avg_coord
            all_coords.extend(coords)
        
        # Calculate overall average binding site center
        overall_center = np.mean(all_coords, axis=0) if all_coords else ligand_center
        
        print(f"✓ Found {len(residue_averages)} interacting residues")
        print(f"✓ Total interacting atoms: {len(all_coords)}")
        print(f"✓ Binding site center: X={overall_center[0]:.2f}, Y={overall_center[1]:.2f}, Z={overall_center[2]:.2f}")
        
        return {
            'overall_center': overall_center,
            'residue_averages': residue_averages,
            'all_coords': all_coords,
            'ligand_center': ligand_center,
            'num_interacting_residues': len(residue_averages),
            'num_interacting_atoms': len(all_coords),
            'plip_enhanced': False
        }
        
    except Exception as e:
        print(f"❌ Error in residue-level coordinate extraction: {e}")
        return None

