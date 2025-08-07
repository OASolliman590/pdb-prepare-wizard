import os
import sys
import subprocess
import numpy as np
import pandas as pd
from pathlib import Path
from Bio.PDB import PDBList, PDBParser, Select, PDBIO
from Bio.PDB.Structure import Structure
from Bio.PDB.Model import Model
from Bio.PDB.Chain import Chain
import warnings
warnings.filterwarnings("ignore")

class MolecularDockingPipeline:
    def __init__(self, output_dir="pipeline_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        print(f"✓ Pipeline initialized. Output directory: {self.output_dir}")
        
    def fetch_pdb(self, pdb_id):
        """Download PDB file from RCSB PDB database"""
        print(f"🔄 Fetching PDB {pdb_id}...")
        pdbl = PDBList()
        filename = pdbl.retrieve_pdb_file(pdb_id.lower(), pdir=str(self.output_dir), file_format='pdb')
        # Rename to simpler format
        new_filename = self.output_dir / f"{pdb_id.upper()}.pdb"
        os.rename(filename, new_filename)
        print(f"✓ Downloaded: {new_filename}")
        return str(new_filename)
    
    def enumerate_hetatms(self, pdb_file):
        """List all HETATM residues in the PDB file for user selection"""
        print(f"🔄 Enumerating HETATMs in {pdb_file}...")
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('protein', pdb_file)
        
        hetatms = []
        hetatm_details = []
        
        for model in structure:
            for chain in model:
                for residue in chain:
                    if residue.get_id()[0] != ' ':  # HETATM check
                        resname = residue.get_resname()
                        chain_id = chain.get_id()
                        res_id = residue.get_id()[1]
                        detail = f"{resname}_{chain_id}_{res_id}"
                        hetatms.append(resname)
                        hetatm_details.append((resname, chain_id, res_id, residue))
        
        unique_hetatms = list(set(hetatms))
        print(f"✓ Found HETATMs: {unique_hetatms}")
        print(f"✓ Total HETATM instances: {len(hetatm_details)}")
        
        return hetatm_details, unique_hetatms
    
    def save_hetatm_as_pdb(self, pdb_file, selected_hetatm, chain_id, res_id, output_filename=None):
        """Save selected HETATM as separate PDB file"""
        print(f"🔄 Saving HETATM {selected_hetatm}_{chain_id}_{res_id} as separate PDB...")
        
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

    def manage_chains(self, pdb_file, output_filename=None):
        """Allow user to select which chains to keep or remove"""
        print("🔄 Chain Management...")
        
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('protein', pdb_file)
        
        # List all available chains
        all_chains = []
        for model in structure:
            for chain in model:
                chain_id = chain.get_id()
                num_residues = len([r for r in chain if r.get_id()[0] == ' '])
                num_hetatms = len([r for r in chain if r.get_id()[0] != ' '])
                all_chains.append((chain_id, num_residues, num_hetatms))
        
        print("📋 Available chains:")
        for chain_id, num_res, num_het in all_chains:
            print(f"   Chain {chain_id}: {num_res} protein residues, {num_het} HETATMs")
        
        keep_chains = input("Enter chains to KEEP (comma-separated, e.g., A,B): ").strip().upper().split(',')
        keep_chains = [c.strip() for c in keep_chains if c.strip()]
        
        print(f"✓ Keeping chains: {keep_chains}")
        
        # Create new structure with only selected chains
        new_structure = Structure('filtered')
        new_model = Model(0)
        
        for model in structure:
            for chain in model:
                if chain.get_id() in keep_chains:
                    new_model.add(chain.copy())
        
        new_structure.add(new_model)
        
        if output_filename is None:
            output_filename = self.output_dir / "chain_filtered.pdb"
        
        io = PDBIO()
        io.set_structure(new_structure)
        io.save(str(output_filename))
        
        print(f"✓ Filtered PDB saved as: {output_filename}")
        return str(output_filename)

    def clean_pdb(self, pdb_file, to_remove_list=None, output_filename=None):
        """Clean PDB by removing specified residues (e.g., water, ions)"""
        if to_remove_list is None:
            print("📝 Available common residues to remove:")
            print("   - HOH (water)")
            print("   - NA (sodium)")
            print("   - CL (chloride)")
            print("   - SO4 (sulfate)")
            to_remove_input = input("Enter residues to remove (comma-separated, e.g., HOH,NA): ")
            to_remove_list = [r.strip().upper() for r in to_remove_input.split(',') if r.strip()]
        
        print(f"🔄 Cleaning PDB - removing: {to_remove_list}")
        
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('protein', pdb_file)
        
        if output_filename is None:
            output_filename = self.output_dir / "cleaned.pdb"
        
        class RemoveSelect(Select):
            def __init__(self, to_remove):
                self.to_remove = to_remove
            
            def accept_residue(self, residue):
                return residue.get_resname() not in self.to_remove
        
        io = PDBIO()
        io.set_structure(structure)
        io.save(str(output_filename), RemoveSelect(to_remove_list))
        
        print(f"✓ Cleaned PDB saved as: {output_filename}")
        return str(output_filename)

    def distance_based_interaction_detection(self, pdb_file, ligand_name, chain_id, res_id, cutoff=5.0):
        """Alternative method to detect interactions when PLIP is not available"""
        print(f"🔄 Using distance-based interaction detection (cutoff: {cutoff}Å)...")
        
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('protein', pdb_file)
        
        # Find the ligand
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
            raise ValueError(f"Ligand {ligand_name}_{chain_id}_{res_id} not found")
        
        # Get ligand atom coordinates
        ligand_coords = []
        for atom in ligand_residue:
            ligand_coords.append(atom.get_coord())
        
        # Find interacting protein residues
        interacting_residues = []
        all_coords = []
        
        for model in structure:
            for chain in model:
                for residue in chain:
                    if residue.get_id()[0] == ' ':  # Protein residue
                        for atom in residue:
                            atom_coord = atom.get_coord()
                            # Check distance to any ligand atom
                            for lig_coord in ligand_coords:
                                dist = np.linalg.norm(atom_coord - lig_coord)
                                if dist <= cutoff:
                                    if residue not in interacting_residues:
                                        interacting_residues.append(residue)
                                    all_coords.append(atom_coord)
                                    break
        
        print(f"✓ Found {len(interacting_residues)} interacting residues")
        return all_coords

    def extract_active_site_coords(self, cleaned_pdb, ligand_name, chain_id, res_id, method='distance'):
        """Extract active site coordinates using specified method"""
        print(f"🔄 Extracting active site coordinates using {method} method...")
        
        coords = []
        
        if method == 'plip':
            try:
                # Try using PLIP first
                from plip.structure.preparation import PDBComplex
                
                my_mol = PDBComplex()
                my_mol.load_pdb(cleaned_pdb)
                my_mol.analyze()
                
                interactions = my_mol.interaction_sets
                if not interactions:
                    print("⚠️  No interactions found with PLIP, falling back to distance method")
                    method = 'distance'
                else:
                    for site in interactions.values():
                        # Get all atoms from interacting residues
                        for res_atoms in site.nearby_residues:
                            for atom in res_atoms:
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

    def analyze_pocket_properties(self, cleaned_pdb, center_coords, ligand_pdb=None):
        """Comprehensive pocket analysis using multiple approaches"""
        print("🔄 Starting comprehensive pocket analysis...")
        
        results = {
            'center_x': center_coords[0],
            'center_y': center_coords[1], 
            'center_z': center_coords[2]
        }
        
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('protein', cleaned_pdb)
        
        # 1. Pocket Size and Shape Analysis
        print("📊 Analyzing pocket size and shape...")
        try:
            # Geometric estimation based on interaction sphere
            results['pocket_volume_A3'] = 4/3 * np.pi * (5.0**3)  # Assume 5Å interaction sphere
        except Exception as e:
            print(f"⚠️  Pocket volume analysis failed: {e}")
            results['pocket_volume_A3'] = 'N/A'
        
        # 2. Electrostatic Potential Analysis
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
                                    if dist <= 10.0:  # Within 10Å of pocket center
                                        electrostatic_score += charged_residues[resname]
                                        nearby_charges += 1
                                except:
                                    continue
            
            results['electrostatic_score'] = electrostatic_score
            results['nearby_charged_residues'] = nearby_charges
            print(f"✓ Electrostatic analysis completed (score: {electrostatic_score})")
            
        except Exception as e:
            print(f"⚠️  Electrostatic analysis failed: {e}")
            results['electrostatic_score'] = 'N/A'
        
        # 3. Hydrophobic Potential Analysis
        print("💧 Analyzing hydrophobic potential...")
        try:
            hydrophobic_residues = ['ALA', 'VAL', 'LEU', 'ILE', 'MET', 'PHE', 'TRP', 'TYR', 'PRO']
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
            print(f"✓ Hydrophobic analysis completed (score: {hydrophobic_score})")
            
        except Exception as e:
            print(f"⚠️  Hydrophobic analysis failed: {e}")
            results['hydrophobic_score'] = 'N/A'
        
        # 4. Druggability Prediction
        print("💊 Calculating druggability score...")
        try:
            druggability_score = 0.0
            
            # Volume contribution
            if isinstance(results.get('pocket_volume_A3'), (int, float)):
                if results['pocket_volume_A3'] > 200:
                    druggability_score += 0.3
                elif results['pocket_volume_A3'] > 100:
                    druggability_score += 0.2
            
            # Hydrophobic contribution
            if isinstance(results.get('hydrophobic_score'), (int, float)):
                if results['hydrophobic_score'] > 5:
                    druggability_score += 0.4
                elif results['hydrophobic_score'] > 3:
                    druggability_score += 0.3
            
            # Balance of charged residues
            if isinstance(results.get('electrostatic_score'), (int, float)):
                abs_charge = abs(results['electrostatic_score'])
                if abs_charge <= 2:
                    druggability_score += 0.3
                elif abs_charge <= 4:
                    druggability_score += 0.2
            
            results['druggability_score'] = min(druggability_score, 1.0)
            print(f"✓ Druggability score: {results['druggability_score']:.2f}")
            
        except Exception as e:
            print(f"⚠️  Druggability calculation failed: {e}")
            results['druggability_score'] = 'N/A'
        
        return results

    def generate_summary_report(self, results, pdb_id):
        """Generate comprehensive summary report"""
        print("\n📊 Generating Summary Report...")
        
        # Create DataFrame for easy CSV export
        summary_data = []
        
        # Basic information
        summary_data.append(['PDB_ID', pdb_id])
        summary_data.append(['Selected_Ligand', results.get('selected_ligand', 'N/A')])
        summary_data.append(['Active_Site_Center_X', f"{results.get('center_x', 0):.3f}"])
        summary_data.append(['Active_Site_Center_Y', f"{results.get('center_y', 0):.3f}"])
        summary_data.append(['Active_Site_Center_Z', f"{results.get('center_z', 0):.3f}"])
        summary_data.append(['Interacting_Atoms_Count', results.get('num_interacting_atoms', 'N/A')])
        
        # Pocket properties
        summary_data.append(['Pocket_Volume_A3', results.get('pocket_volume_A3', 'N/A')])
        summary_data.append(['Electrostatic_Score', results.get('electrostatic_score', 'N/A')])
        summary_data.append(['Nearby_Charged_Residues', results.get('nearby_charged_residues', 'N/A')])
        summary_data.append(['Hydrophobic_Score', results.get('hydrophobic_score', 'N/A')])
        summary_data.append(['Nearby_Hydrophobic_Residues', results.get('nearby_hydrophobic_residues', 'N/A')])
        summary_data.append(['Druggability_Score', results.get('druggability_score', 'N/A')])
        
        # File paths
        summary_data.append(['Original_PDB', results.get('original_pdb', 'N/A')])
        summary_data.append(['Cleaned_PDB', results.get('cleaned_pdb', 'N/A')])
        summary_data.append(['Ligand_PDB', results.get('ligand_pdb', 'N/A')])
        
        # Save as CSV
        df = pd.DataFrame(summary_data, columns=['Property', 'Value'])
        csv_filename = self.output_dir / f"{pdb_id}_pipeline_results.csv"
        df.to_csv(csv_filename, index=False)
        
        # Display summary
        print("\n📋 Pipeline Summary:")
        print("-" * 40)
        for prop, value in summary_data[:12]:  # Show main results
            print(f"{prop:<25}: {value}")
        
        print(f"\n✓ Detailed results saved to: {csv_filename}")

    def run_complete_pipeline(self, pdb_id, interactive=True):
        """Run the complete molecular docking pipeline"""
        print("🚀 Starting Complete Molecular Docking Pipeline")
        print("=" * 50)
        
        results = {}
        
        try:
            # Step 1: Fetch PDB
            pdb_file = self.fetch_pdb(pdb_id)
            results['original_pdb'] = pdb_file
            
            # Step 2: Chain Management (optional)
            if interactive:
                manage_chains_choice = input("Do you want to filter chains? (y/n): ").lower().strip()
                if manage_chains_choice == 'y':
                    pdb_file = self.manage_chains(pdb_file)
                    results['chain_filtered_pdb'] = pdb_file
            
            # Step 3: Enumerate HETATMs
            hetatm_details, unique_hetatms = self.enumerate_hetatms(pdb_file)
            
            if not hetatm_details:
                raise ValueError("No HETATMs found in the structure")
            
            # Step 4: Select ligand interactively
            if interactive:
                print("\n📋 Available HETATMs with details:")
                for i, (resname, chain_id, res_id, residue) in enumerate(hetatm_details):
                    print(f"   {i+1}. {resname}_{chain_id}_{res_id}")
                
                while True:
                    try:
                        choice = int(input(f"Select HETATM (1-{len(hetatm_details)}): ")) - 1
                        if 0 <= choice < len(hetatm_details):
                            selected_hetatm, chain_id, res_id, residue = hetatm_details[choice]
                            break
                        else:
                            print("Invalid choice, please try again.")
                    except ValueError:
                        print("Please enter a valid number.")
            else:
                # For non-interactive mode, select first HETATM
                selected_hetatm, chain_id, res_id, residue = hetatm_details[0]
            
            print(f"✓ Selected ligand: {selected_hetatm}_{chain_id}_{res_id}")
            results['selected_ligand'] = f"{selected_hetatm}_{chain_id}_{res_id}"
            
            # Step 5: Save ligand as separate PDB
            ligand_pdb = self.save_hetatm_as_pdb(pdb_file, selected_hetatm, chain_id, res_id)
            results['ligand_pdb'] = ligand_pdb
            
            # Step 6: Clean PDB
            if interactive:
                cleaned_pdb = self.clean_pdb(pdb_file)
            else:
                # Default cleaning - remove water and common ions
                cleaned_pdb = self.clean_pdb(pdb_file, to_remove_list=['HOH', 'NA', 'CL'])
            results['cleaned_pdb'] = cleaned_pdb
            
            # Step 7: Extract active site coordinates
            try:
                avg_coords, num_atoms = self.extract_active_site_coords(
                    cleaned_pdb, selected_hetatm, chain_id, res_id, method='distance'
                )
                results['active_site_center'] = avg_coords.tolist()
                results['num_interacting_atoms'] = num_atoms
            except Exception as e:
                print(f"❌ Failed to extract active site coordinates: {e}")
                return results
            
            # Step 8: Comprehensive pocket analysis
            pocket_results = self.analyze_pocket_properties(
                cleaned_pdb, avg_coords, ligand_pdb
            )
            results.update(pocket_results)
            
            # Step 9: Generate summary report
            self.generate_summary_report(results, pdb_id)
            
            print("\n🎉 Pipeline completed successfully!")
            print(f"📁 All files saved in: {self.output_dir}")
            
            return results
            
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            return results
