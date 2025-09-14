#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add the pdb-prepare-wizard directory to the system path
sys.path.append(os.path.abspath("pdb-prepare-wizard"))

from core_pipeline import MolecularDockingPipeline, extract_residue_level_coordinates
from Bio.PDB import PDBParser, PDBIO, Select

try:
    import openpyxl
    from openpyxl import Workbook
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

def select_chain(input_pdb, output_pdb, chain_id):
    """
    Selects a specific chain from a PDB file and saves it to a new file.
    """
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("protein", input_pdb)

    class ChainSelect(Select):
        def __init__(self, chain_id):
            self.chain_id = chain_id

        def accept_chain(self, chain):
            if chain.get_id() == self.chain_id:
                return 1
            else:
                return 0

    io = PDBIO()
    io.set_structure(structure)
    io.save(output_pdb, ChainSelect(chain_id))
    print(f"✓ Saved chain {chain_id} to {output_pdb}")


def save_coords_to_excel(workbook, pdb_id, ligand_id, coords):
    if not EXCEL_AVAILABLE:
        return

    sheet_name = f"{pdb_id}_{ligand_id}"
    if sheet_name in workbook.sheetnames:
        ws = workbook[sheet_name]
    else:
        ws = workbook.create_sheet(sheet_name)
        ws.append(["Atom", "X", "Y", "Z"])

    for i, coord in enumerate(coords):
        ws.append([i+1, coord[0], coord[1], coord[2]])

def save_residue_analysis_to_excel(workbook, pdb_id, ligand_id, residue_analysis):
    """Save detailed residue-level analysis to Excel"""
    if not EXCEL_AVAILABLE or not residue_analysis:
        return

    sheet_name = f"{pdb_id}_{ligand_id}_residues"
    if sheet_name in workbook.sheetnames:
        ws = workbook[sheet_name]
    else:
        ws = workbook.create_sheet(sheet_name)
        ws.append(["Residue", "X", "Y", "Z", "Num_Atoms"])
    
    # Add overall center
    center = residue_analysis['overall_center']
    ws.append(["OVERALL_CENTER", center[0], center[1], center[2], residue_analysis['num_interacting_atoms']])
    
    # Add residue averages
    for reskey, coord in residue_analysis['residue_averages'].items():
        ws.append([reskey, coord[0], coord[1], coord[2], "N/A"])

def main():
    """
    Main function to run the batch PDB preparation.
    """
    # --- Configuration ---
    input_dir = Path("/Users/omara.soliman/Desktop/Research/41-Sertaline_Pyrazole_derivatives/1-Pre_Limnary/1-Targets")
    output_dir = Path("/Users/omara.soliman/Desktop/Research/41-Sertaline_Pyrazole_derivatives/1-Pre_Limnary/2-Target_Prepared")
    output_dir.mkdir(exist_ok=True)

    pipeline = MolecularDockingPipeline(output_dir=str(output_dir))

    workbook = Workbook() if EXCEL_AVAILABLE else None
    if workbook:
        # Remove default sheet
        if "Sheet" in workbook.sheetnames:
            workbook.remove(workbook["Sheet"])

    # --- Process 4TRO_INHA.pdb ---
    pdb_id = "4TRO_INHA"
    input_pdb = input_dir / f"{pdb_id}.pdb"
    
    if not input_pdb.exists():
        print(f"❌ Input file not found: {input_pdb}")
    else:
        # 1. Select chain A
        chain_a_pdb = output_dir / f"{pdb_id}_chainA.pdb"
        select_chain(str(input_pdb), str(chain_a_pdb), "A")

        # 2. Enumerate HETATMs
        hetatm_details, unique_hetatms = pipeline.enumerate_hetatms(str(chain_a_pdb))

        # 3. Save HETATM ZID individually
        for resname, chain_id, res_id, _ in hetatm_details:
            if resname == "ZID":
                pipeline.save_hetatm_as_pdb(
                    pdb_file=str(chain_a_pdb),
                    selected_hetatm="ZID",
                    chain_id=chain_id,
                    res_id=res_id,
                    output_filename=str(output_dir / f"{pdb_id}_ZID.pdb")
                )
                # Extract coordinates using residue-level analysis
                try:
                    # Use the new residue-level analysis function
                    residue_analysis = extract_residue_level_coordinates(
                        str(chain_a_pdb), "ZID", chain_id, res_id
                    )
                    if residue_analysis:
                        coords = residue_analysis['overall_center']
                        print(f"Residue-level coordinates for ZID in {pdb_id}: {coords}")
                        print(f"Number of interacting residues: {residue_analysis['num_interacting_residues']}")
                        print(f"Number of interacting atoms: {residue_analysis['num_interacting_atoms']}")
                        if workbook:
                            save_residue_analysis_to_excel(workbook, pdb_id, "ZID", residue_analysis)
                    else:
                        print("❌ Failed to extract residue-level coordinates for ZID")
                except Exception as e:
                    print(f"❌ Error extracting coordinates for ZID: {e}")
                    coords = None

        # 4. Remove all HETATMs
        pipeline.clean_pdb(
            pdb_file=str(chain_a_pdb),
            to_remove_list=unique_hetatms,
            output_filename=str(output_dir / f"{pdb_id}_prep.pdb")
        )

    # --- Process 2X22_INHA.pdb ---
    pdb_id = "2X22_INHA"
    input_pdb = input_dir / f"{pdb_id}.pdb"

    if not input_pdb.exists():
        print(f"❌ Input file not found: {input_pdb}")
    else:
        # 1. Select chain A
        chain_a_pdb = output_dir / f"{pdb_id}_chainA.pdb"
        select_chain(str(input_pdb), str(chain_a_pdb), "A")

        # 2. Enumerate HETATMs
        hetatm_details, unique_hetatms = pipeline.enumerate_hetatms(str(chain_a_pdb))

        # 3. Save HETATM TCU individually and get coordinates
        for resname, chain_id, res_id, _ in hetatm_details:
            if resname == "TCU":
                pipeline.save_hetatm_as_pdb(
                    pdb_file=str(chain_a_pdb),
                    selected_hetatm="TCU",
                    chain_id=chain_id,
                    res_id=res_id,
                    output_filename=str(output_dir / f"{pdb_id}_TCU.pdb")
                )
                # Extract coordinates using residue-level analysis
                try:
                    # Use the new residue-level analysis function
                    residue_analysis = extract_residue_level_coordinates(
                        str(chain_a_pdb), "TCU", chain_id, res_id
                    )
                    if residue_analysis:
                        coords = residue_analysis['overall_center']
                        print(f"Residue-level coordinates for TCU in {pdb_id}: {coords}")
                        print(f"Number of interacting residues: {residue_analysis['num_interacting_residues']}")
                        print(f"Number of interacting atoms: {residue_analysis['num_interacting_atoms']}")
                        if workbook:
                            save_residue_analysis_to_excel(workbook, pdb_id, "TCU", residue_analysis)
                    else:
                        print("❌ Failed to extract residue-level coordinates for TCU")
                except Exception as e:
                    print(f"❌ Error extracting coordinates for TCU: {e}")
                    coords = None

        # 4. Remove all HETATMs except NAD
        to_remove = [het for het in unique_hetatms if het != "NAD"]
        pipeline.clean_pdb(
            pdb_file=str(chain_a_pdb),
            to_remove_list=to_remove,
            output_filename=str(output_dir / f"{pdb_id}_prep.pdb")
        )

    # --- Process 3LN1_COX2.pdb ---
    pdb_id = "3LN1_COX2"
    input_pdb = input_dir / f"{pdb_id}.pdb"

    if not input_pdb.exists():
        print(f"❌ Input file not found: {input_pdb}")
    else:
        # 1. Select chain A
        chain_a_pdb = output_dir / f"{pdb_id}_chainA.pdb"
        select_chain(str(input_pdb), str(chain_a_pdb), "A")

        # 2. Enumerate HETATMs
        hetatm_details, unique_hetatms = pipeline.enumerate_hetatms(str(chain_a_pdb))

        # 3. Save HETATM CEL individually and get coordinates
        for resname, chain_id, res_id, _ in hetatm_details:
            if resname == "CEL":
                pipeline.save_hetatm_as_pdb(
                    pdb_file=str(chain_a_pdb),
                    selected_hetatm="CEL",
                    chain_id=chain_id,
                    res_id=res_id,
                    output_filename=str(output_dir / f"{pdb_id}_CEL.pdb")
                )
                # Extract coordinates using residue-level analysis
                try:
                    # Use the new residue-level analysis function
                    residue_analysis = extract_residue_level_coordinates(
                        str(chain_a_pdb), "CEL", chain_id, res_id
                    )
                    if residue_analysis:
                        coords = residue_analysis['overall_center']
                        print(f"Residue-level coordinates for CEL in {pdb_id}: {coords}")
                        print(f"Number of interacting residues: {residue_analysis['num_interacting_residues']}")
                        print(f"Number of interacting atoms: {residue_analysis['num_interacting_atoms']}")
                        if workbook:
                            save_residue_analysis_to_excel(workbook, pdb_id, "CEL", residue_analysis)
                    else:
                        print("❌ Failed to extract residue-level coordinates for CEL")
                except Exception as e:
                    print(f"❌ Error extracting coordinates for CEL: {e}")
                    coords = None

        # 4. Remove all HETATMs except HEM
        to_remove = [het for het in unique_hetatms if het != "HEM"]
        pipeline.clean_pdb(
            pdb_file=str(chain_a_pdb),
            to_remove_list=to_remove,
            output_filename=str(output_dir / f"{pdb_id}_prep.pdb")
        )

    # --- Process 3IAI_CA9.pdb ---
    pdb_id = "3IAI_CA9"
    input_pdb = input_dir / f"{pdb_id}.pdb"

    if not input_pdb.exists():
        print(f"❌ Input file not found: {input_pdb}")
    else:
        # 1. Select chain A
        chain_a_pdb = output_dir / f"{pdb_id}_chainA.pdb"
        select_chain(str(input_pdb), str(chain_a_pdb), "A")

        # 2. Enumerate HETATMs
        hetatm_details, unique_hetatms = pipeline.enumerate_hetatms(str(chain_a_pdb))

        # 3. Save HETATM AZM individually and get coordinates
        for resname, chain_id, res_id, _ in hetatm_details:
            if resname == "AZM":
                pipeline.save_hetatm_as_pdb(
                    pdb_file=str(chain_a_pdb),
                    selected_hetatm="AZM",
                    chain_id=chain_id,
                    res_id=res_id,
                    output_filename=str(output_dir / f"{pdb_id}_AZM.pdb")
                )
                # Extract coordinates using residue-level analysis
                try:
                    # Use the new residue-level analysis function
                    residue_analysis = extract_residue_level_coordinates(
                        str(chain_a_pdb), "AZM", chain_id, res_id
                    )
                    if residue_analysis:
                        coords = residue_analysis['overall_center']
                        print(f"Residue-level coordinates for AZM in {pdb_id}: {coords}")
                        print(f"Number of interacting residues: {residue_analysis['num_interacting_residues']}")
                        print(f"Number of interacting atoms: {residue_analysis['num_interacting_atoms']}")
                        if workbook:
                            save_residue_analysis_to_excel(workbook, pdb_id, "AZM", residue_analysis)
                    else:
                        print("❌ Failed to extract residue-level coordinates for AZM")
                except Exception as e:
                    print(f"❌ Error extracting coordinates for AZM: {e}")
                    coords = None

        # 4. Remove all HETATMs except ZN
        to_remove = [het for het in unique_hetatms if het != "ZN"]
        pipeline.clean_pdb(
            pdb_file=str(chain_a_pdb),
            to_remove_list=to_remove,
            output_filename=str(output_dir / f"{pdb_id}_prep.pdb")
        )

    # --- Process 1DA0_DNA.pdb ---
    pdb_id = "1DA0_DNA"
    input_pdb = input_dir / f"{pdb_id}.pdb"

    if not input_pdb.exists():
        print(f"❌ Input file not found: {input_pdb}")
    else:
        # 1. Select chain A
        chain_a_pdb = output_dir / f"{pdb_id}_chainA.pdb"
        select_chain(str(input_pdb), str(chain_a_pdb), "A")

        # 2. Enumerate HETATMs
        hetatm_details, unique_hetatms = pipeline.enumerate_hetatms(str(chain_a_pdb))

        # 3. Save HETATM DM1 individually and get coordinates
        for resname, chain_id, res_id, _ in hetatm_details:
            if resname == "DM1":
                pipeline.save_hetatm_as_pdb(
                    pdb_file=str(chain_a_pdb),
                    selected_hetatm="DM1",
                    chain_id=chain_id,
                    res_id=res_id,
                    output_filename=str(output_dir / f"{pdb_id}_DM1.pdb")
                )
                # Extract coordinates using residue-level analysis
                try:
                    # Use the new residue-level analysis function
                    residue_analysis = extract_residue_level_coordinates(
                        str(chain_a_pdb), "DM1", chain_id, res_id
                    )
                    if residue_analysis:
                        coords = residue_analysis['overall_center']
                        print(f"Residue-level coordinates for DM1 in {pdb_id}: {coords}")
                        print(f"Number of interacting residues: {residue_analysis['num_interacting_residues']}")
                        print(f"Number of interacting atoms: {residue_analysis['num_interacting_atoms']}")
                        if workbook:
                            save_residue_analysis_to_excel(workbook, pdb_id, "DM1", residue_analysis)
                    else:
                        print("❌ Failed to extract residue-level coordinates for DM1")
                except Exception as e:
                    print(f"❌ Error extracting coordinates for DM1: {e}")
                    coords = None

        # 4. Remove all HETATMs
        pipeline.clean_pdb(
            pdb_file=str(chain_a_pdb),
            to_remove_list=unique_hetatms,
            output_filename=str(output_dir / f"{pdb_id}_prep.pdb")
        )
    
    if workbook:
        excel_filename = output_dir / "plip_coordinates.xlsx"
        workbook.save(excel_filename)
        print(f"✓ Excel file with coordinates saved to: {excel_filename}")

if __name__ == "__main__":
    main()
