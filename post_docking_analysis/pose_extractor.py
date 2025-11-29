"""
Enhanced pose extractor for post-docking analysis pipeline.

This module handles the extraction of best poses from docking results,
organizing them into a centralized folder structure, and saving the
best pose for each complex into a separate folder.
"""
import pandas as pd
from pathlib import Path
import shutil
from typing import Optional, List
import csv
import re

def extract_best_poses_from_gnina(input_dir: Path, output_dir: Path, config: dict = None) -> int:
    """
    Extract best poses as PDB files using GNINA outputs in input_dir.
    
    Parameters
    ----------
    input_dir : Path
        Input directory containing GNINA outputs
    output_dir : Path
        Output directory for extracted poses
    config : dict, optional
        Configuration dictionary
        
    Returns
    -------
    int
        Number of PDBs written
    """
    # Use configuration or defaults
    if config is None:
        config = {}
    
    extract_all = config.get("pose_extraction", {}).get("extract_all_poses", False)
    criteria = config.get("pose_extraction", {}).get("best_pose_criteria", "affinity")
    
    # Try different possible GNINA directory names
    possible_gnina_dirs = [
        input_dir / "gnina_out",
        input_dir / "gnina_out_cox2",
        input_dir / "gnina_out_inha"
    ]
    
    gnina_dir = None
    for possible_dir in possible_gnina_dirs:
        if possible_dir.exists():
            gnina_dir = possible_dir
            break
    
    if gnina_dir is None:
        print(f"❌ GNINA output directory not found in {input_dir}")
        return 0
    
    receptors_dir = input_dir / "receptors"
    scores_csv = gnina_dir / "all_scores.csv"

    if not scores_csv.exists():
        print(f"❌ Scores CSV not found: {scores_csv}")
        return 0

    # Create output directories
    best_poses_dir = output_dir / "best_poses"
    all_poses_dir = output_dir / "all_poses" if extract_all else None
    
    best_poses_dir.mkdir(parents=True, exist_ok=True)
    if all_poses_dir:
        all_poses_dir.mkdir(parents=True, exist_ok=True)

    # Read CSV and pick best mode (min vina_affinity) per tag
    rows = []
    with scores_csv.open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                r['vina_affinity'] = float(r['vina_affinity'])
                r['mode'] = int(float(r['mode']))
            except Exception:
                continue
            rows.append(r)

    if not rows:
        print(f"⚠️  No rows in {scores_csv}")
        return 0

    # Group by tag
    if extract_all:
        # For extracting all poses, we'll process all rows
        poses_to_extract = rows
    else:
        # For best poses only, we'll pick the best per tag
        best_by_tag = {}
        for r in rows:
            tag = r['tag']
            if tag not in best_by_tag or r['vina_affinity'] < best_by_tag[tag]['vina_affinity']:
                best_by_tag[tag] = r
        poses_to_extract = list(best_by_tag.values())

    written = 0
    for r in poses_to_extract:
        tag = r['tag']
        sdf_file = gnina_dir / f"{tag}_top.sdf"
        if not sdf_file.exists():
            print(f"⚠️  SDF not found for tag {tag}: {sdf_file}")
            continue
            
        # Determine output directory based on extraction type
        if extract_all:
            out_dir = all_poses_dir
        else:
            # Create a separate folder for each complex
            complex_dir = best_poses_dir / tag
            complex_dir.mkdir(exist_ok=True)
            out_dir = complex_dir
            
        out_pdb = out_dir / f"{tag}_pose{int(r['mode'])}.pdb"
        
        # Extract protein name from tag (e.g., 3LN1_COX2_prep_catalytic_ML1H -> 3LN1_COX2)
        protein_name = tag.split('_prep_')[0] if '_prep_' in tag else tag.split('_')[0] + '_' + tag.split('_')[1]
        receptor_file = receptors_dir / f"{protein_name}_prep.pdbqt"
        
        if not receptor_file.exists():
            print(f"⚠️  Receptor file not found: {receptor_file}")
            continue
        
        # Try to get docking center coordinates from log file
        log_file = gnina_dir / f"{tag}.log"
        docking_center = None
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    log_content = f.read()
                    # Extract center coordinates from command line
                    import re
                    center_match = re.search(r'--center_x\s+([\d.-]+)\s+--center_y\s+([\d.-]+)\s+--center_z\s+([\d.-]+)', log_content)
                    if center_match:
                        docking_center = (float(center_match.group(1)), float(center_match.group(2)), float(center_match.group(3)))
                        print(f"📍 Found docking center: {docking_center}")
            except Exception as e:
                print(f"⚠️  Could not extract docking center: {e}")
        
        # Combine receptor and ligand to create complex using OpenBabel
        try:
            from openbabel import pybel
            
            # Read receptor PDBQT file
            receptor_lines = []
            if receptor_file.exists():
                try:
                    receptor_mol = next(pybel.readfile("pdbqt", str(receptor_file)))
                    receptor_pdb = receptor_mol.write("pdb")
                    for line in receptor_pdb.split('\n'):
                        if line.startswith('ATOM'):
                            # Fix the line format and assign chain A
                            line = line.ljust(80)
                            new_line = f"ATOM  {line[6:21]}A{line[22:]}"
                            receptor_lines.append(new_line)
                except Exception as e:
                    print(f"⚠️  Could not read receptor {receptor_file}: {e}")
                    continue
            
            # Read ligand SDF file
            ligand_lines = []
            try:
                ligand_mol = next(pybel.readfile("sdf", str(sdf_file)))
                ligand_pdb = ligand_mol.write("pdb")
                for line in ligand_pdb.split('\n'):
                    if line.startswith('ATOM') or line.startswith('HETATM'):
                        # Fix the line format and assign chain B
                        line = line.ljust(80)
                        new_line = f"HETATM{line[6:21]}B{line[22:]}"
                        new_line = new_line[:17] + "UNK" + new_line[20:]
                        ligand_lines.append(new_line)
            except Exception as e:
                print(f"⚠️  Could not read ligand {sdf_file}: {e}")
                continue
            
            # Combine receptor and ligand
            all_lines = receptor_lines + ligand_lines + ["END"]
            combined_content = '\n'.join(all_lines)
            
            # Write combined complex
            with open(out_pdb, 'w') as f:
                f.write(combined_content)
            
            written += 1
            print(f"✅ Extracted complex {out_pdb.name} (receptor + ligand)")
                    
        except ImportError:
            print(f"⚠️  OpenBabel not available, using fallback method")
            # Fallback: use simple SDF to PDB conversion
            try:
                ligand_pdb_content = _convert_sdf_to_pdb_simple(sdf_file)
                if ligand_pdb_content:
                    # Read receptor PDBQT file manually
                    with open(receptor_file, 'r') as f:
                        receptor_content = f.read()
                    
                    # Convert PDBQT to PDB format (remove Q and T columns)
                    receptor_pdb_lines = []
                    for line in receptor_content.split('\n'):
                        if line.startswith(('ATOM', 'HETATM')):
                            # Convert PDBQT to PDB format
                            if len(line) >= 66:
                                # Extract coordinates and atom info
                                atom_type = line[0:6].strip()
                                atom_num = line[6:11].strip()
                                atom_name = line[12:16].strip()
                                res_name = line[17:20].strip()
                                chain_id = line[21:22] if len(line) > 21 else ' '
                                res_num = line[22:26].strip()
                                x = line[30:38].strip()
                                y = line[38:46].strip()
                                z = line[46:54].strip()
                                occupancy = line[54:60].strip() if len(line) > 54 else '1.00'
                                temp_factor = line[60:66].strip() if len(line) > 60 else '20.00'
                                element = line[76:78].strip() if len(line) > 76 else atom_name[0]
                                
                                # Create proper PDB format line
                                pdb_line = f"{atom_type:6s}{atom_num:5s} {atom_name:4s}{res_name:3s} {chain_id:1s}{res_num:4s}    {x:8s}{y:8s}{z:8s}  {occupancy:6s}{temp_factor:6s}           {element:2s}"
                                receptor_pdb_lines.append(pdb_line)
                            else:
                                receptor_pdb_lines.append(line)
                        elif line.startswith(('REMARK', 'HEADER', 'TITLE', 'COMPND', 'SOURCE', 'AUTHOR', 'REVDAT', 'JRNL', 'SEQRES', 'HET', 'FORMUL', 'HELIX', 'SHEET', 'SSBOND', 'LINK', 'CISPEP', 'SITE', 'CRYST1', 'ORIGX1', 'ORIGX2', 'ORIGX3', 'SCALE1', 'SCALE2', 'SCALE3', 'MTRIX1', 'MTRIX2', 'MTRIX3', 'TVECT', 'MODEL', 'ENDMDL')):
                            receptor_pdb_lines.append(line)
                    
                    # Combine receptor and ligand
                    combined_content = []
                    combined_content.extend(receptor_pdb_lines)
                    combined_content.append("")  # Empty line separator
                    combined_content.extend(ligand_pdb_content.split('\n'))
                    
                    # Write combined complex
                    with open(out_pdb, 'w') as f:
                        f.write('\n'.join(combined_content))
                    
                    written += 1
                    print(f"✅ Extracted complex {out_pdb.name} (receptor + ligand, fallback method)")
                else:
                    print(f"⚠️  Failed to convert ligand from {sdf_file}")
            except Exception as e:
                print(f"⚠️  Error creating complex for {tag}: {e}")
                # Final fallback: just copy the SDF file
                try:
                    shutil.copy2(sdf_file, out_pdb)
                    written += 1
                    print(f"✅ Copied SDF as PDB: {out_pdb.name}")
                except Exception as e2:
                    print(f"❌ Failed to copy {sdf_file}: {e2}")
        except Exception as e:
            print(f"⚠️  Error creating complex for {tag}: {e}")
            # Fallback: just copy the SDF file
            try:
                shutil.copy2(sdf_file, out_pdb)
                written += 1
                print(f"✅ Copied SDF as PDB: {out_pdb.name}")
            except Exception as e2:
                print(f"❌ Failed to copy {sdf_file}: {e2}")

    print(f"✅ Extracted {written} poses to: {best_poses_dir}")
    if all_poses_dir:
        print(f"   (All poses saved to: {all_poses_dir})")
    return written

def organize_poses_by_affinity(best_poses_dir: Path, threshold: float = -8.0):
    """
    Organize extracted poses into folders based on binding affinity.
    
    Parameters
    ----------
    best_poses_dir : Path
        Directory containing extracted best poses
    threshold : float
        Affinity threshold for strong binders (kcal/mol)
    """
    strong_binders_dir = best_poses_dir / "strong_binders"
    moderate_binders_dir = best_poses_dir / "moderate_binders"
    weak_binders_dir = best_poses_dir / "weak_binders"
    
    strong_binders_dir.mkdir(exist_ok=True)
    moderate_binders_dir.mkdir(exist_ok=True)
    weak_binders_dir.mkdir(exist_ok=True)
    
    # Read the scores CSV to get affinity values
    # Try multiple possible locations for the CSV
    possible_csv_paths = [
        best_poses_dir.parent.parent / "gnina_out" / "all_scores.csv",
        best_poses_dir.parent / "reports" / "full_data.csv",
        best_poses_dir.parent.parent / "test_docking_data" / "gnina_out" / "all_scores.csv"
    ]
    
    scores_csv = None
    for path in possible_csv_paths:
        if path.exists():
            scores_csv = path
            break
    
    if not scores_csv:
        print("⚠️  Scores CSV not found for organizing poses")
        return
    
    df = pd.read_csv(scores_csv)
    
    # Filter out failed docking attempts (positive values)
    original_count = len(df)
    df = df[df['vina_affinity'] < 0]
    failed_count = original_count - len(df)
    if failed_count > 0:
        print(f"🚫 Filtered out {failed_count} failed docking attempts for pose organization")
    
    # Move pose files based on affinity
    for pdb_file in best_poses_dir.rglob("*.pdb"):
        if pdb_file.is_file() and pdb_file.parent != strong_binders_dir and \
           pdb_file.parent != moderate_binders_dir and pdb_file.parent != weak_binders_dir:
            
            # Extract tag from filename
            filename = pdb_file.stem
            # Remove _poseXX part (e.g., _pose1, _pose2, etc.)
            if filename.endswith('_pose1'):
                tag = filename[:-6]  # Remove '_pose1'
            else:
                # Fallback: remove last two parts if they look like pose numbers
                parts = filename.split("_")
                if len(parts) >= 2 and parts[-1].startswith('pose'):
                    tag = "_".join(parts[:-1])
                else:
                    tag = filename
            
            # Find affinity for this tag - try both 'tag' and 'complex_name' columns
            affinity_row = None
            if 'tag' in df.columns:
                affinity_row = df[df['tag'] == tag]
            elif 'complex_name' in df.columns:
                affinity_row = df[df['complex_name'] == tag]
            
            if affinity_row is not None and not affinity_row.empty:
                affinity = affinity_row.iloc[0]['vina_affinity']
                
                # Move to appropriate directory
                if affinity <= threshold:
                    target_dir = strong_binders_dir
                elif affinity <= -6.0:
                    target_dir = moderate_binders_dir
                else:
                    target_dir = weak_binders_dir
                    
                target_file = target_dir / pdb_file.name
                shutil.move(str(pdb_file), str(target_file))
                print(f"📁 Organized {pdb_file.name} to {target_dir.name}")

def create_pose_summary_report(best_poses_dir: Path, output_dir: Path):
    """
    Create a summary report of extracted poses.
    
    Parameters
    ----------
    best_poses_dir : Path
        Directory containing extracted best poses
    output_dir : Path
        Output directory for reports
    """
    # Read the scores CSV - try multiple possible locations
    possible_csv_paths = [
        best_poses_dir.parent.parent / "gnina_out" / "all_scores.csv",
        best_poses_dir.parent / "reports" / "full_data.csv",
        best_poses_dir.parent.parent / "test_docking_data" / "gnina_out" / "all_scores.csv"
    ]
    
    scores_csv = None
    for path in possible_csv_paths:
        if path.exists():
            scores_csv = path
            break
    
    if not scores_csv:
        print("⚠️  Scores CSV not found for creating summary report")
        return
    
    df = pd.read_csv(scores_csv)
    
    # Create summary report
    summary_data = []
    for pdb_file in best_poses_dir.rglob("*.pdb"):
        if pdb_file.is_file():
            # Extract tag from filename
            filename = pdb_file.stem
            # Remove _poseXX part (e.g., _pose1, _pose2, etc.)
            if filename.endswith('_pose1'):
                tag = filename[:-6]  # Remove '_pose1'
            else:
                # Fallback: remove last two parts if they look like pose numbers
                parts = filename.split("_")
                if len(parts) >= 2 and parts[-1].startswith('pose'):
                    tag = "_".join(parts[:-1])
                else:
                    tag = filename
            
            # Find data for this tag - try both 'tag' and 'complex_name' columns
            tag_data = None
            if 'tag' in df.columns:
                tag_data = df[df['tag'] == tag]
            elif 'complex_name' in df.columns:
                tag_data = df[df['complex_name'] == tag]
            
            if tag_data is not None and not tag_data.empty:
                row = tag_data.iloc[0]
                summary_entry = {
                    'complex': tag,
                    'vina_affinity': row['vina_affinity'],
                    'pdb_file': str(pdb_file.relative_to(best_poses_dir))
                }
                
                # Add optional columns if they exist
                if 'cnn_affinity' in row:
                    summary_entry['cnn_affinity'] = row['cnn_affinity']
                if 'cnn_score' in row:
                    summary_entry['cnn_score'] = row['cnn_score']
                if 'mode' in row:
                    summary_entry['mode'] = row['mode']
                
                summary_data.append(summary_entry)
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('vina_affinity')
        
        # Save to CSV
        summary_file = output_dir / "pose_summary.csv"
        summary_df.to_csv(summary_file, index=False)
        print(f"✅ Pose summary report saved to: {summary_file}")
        
        # Save to Excel if pandas Excel support is available
        try:
            excel_file = output_dir / "pose_summary.xlsx"
            summary_df.to_excel(excel_file, index=False)
            print(f"✅ Pose summary Excel saved to: {excel_file}")
        except ImportError:
            print("⚠️  Excel support not available, skipping Excel report")
    else:
        print("⚠️  No pose data found for summary report")

def _convert_sdf_to_pdb_simple(sdf_file: Path) -> str:
    """
    Simple SDF to PDB converter that extracts coordinates and creates basic PDB format.
    
    Parameters
    ----------
    sdf_file : Path
        Path to SDF file
        
    Returns
    -------
    str
        PDB content as string, or empty string if conversion fails
    """
    try:
        with open(sdf_file, 'r') as f:
            lines = f.readlines()
        
        # Find the counts line (line 4 in SDF format)
        if len(lines) < 4:
            return ""
        
        counts_line = lines[3].strip()
        if not counts_line or len(counts_line.split()) < 3:
            return ""
        
        # Parse atom count
        try:
            atom_count = int(counts_line.split()[0])
        except (ValueError, IndexError):
            return ""
        
        # Extract atom coordinates (lines 5 to 5+atom_count-1)
        pdb_lines = []
        atom_num = 1
        
        for i in range(4, 4 + atom_count):
            if i >= len(lines):
                break
                
            line = lines[i].strip()
            if not line:
                continue
                
            parts = line.split()
            if len(parts) >= 4:
                try:
                    x = float(parts[0])
                    y = float(parts[1])
                    z = float(parts[2])
                    element = parts[3] if len(parts) > 3 else "C"
                    
                    # Create PDB ATOM line with proper formatting
                    pdb_line = f"HETATM{atom_num:5d}  {element:2s}  LIG A{atom_num:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00 20.00           {element:2s}"
                    pdb_lines.append(pdb_line)
                    atom_num += 1
                    
                except (ValueError, IndexError):
                    continue
        
        if pdb_lines:
            return '\n'.join(pdb_lines)
        else:
            return ""
            
    except Exception as e:
        print(f"⚠️  Simple SDF conversion failed: {e}")
        return ""