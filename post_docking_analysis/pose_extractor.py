"""
Utilities to extract best poses as PDB files from GNINA outputs.

This supports the common research layout where the input directory contains:
- a "gnina_out" folder with per-complex "*_top.sdf" and ".log"
- a "receptors" folder with prepared receptor PDBQT files "<TARGET>_<SITE>_prep.pdbqt"

For each complex (identified by the GNINA log/tag), the best mode is selected
based on the most negative Vina affinity in gnina_out/all_scores.csv, the
corresponding conformer is extracted from the top SDF, and combined with the
matching receptor (chain A) into a complex PDB with ligand set as chain B.
"""
from pathlib import Path
from typing import Optional
import csv


def _infer_receptor_path_from_tag(receptors_dir: Path, tag: str) -> Optional[Path]:
    """
    Infer receptor PDBQT file path from a GNINA tag/filename stem.

    Expected tag examples:
      3LN1_COX2_prep_catalytic_ML8CF3
      2X22_INHA_prep_catalytic_MS8CF3

    We construct a candidate like "<first>_<second>_prep.pdbqt" and look it up.
    Fallback to any receptor containing the first two parts.
    """
    parts = tag.split('_')
    if len(parts) < 2:
        return None
    base = f"{parts[0]}_{parts[1]}_prep"

    # Exact match
    cand = receptors_dir / f"{base}.pdbqt"
    if cand.exists():
        return cand

    # Fallback: glob for any file that contains the base
    matches = list(receptors_dir.glob(f"*{parts[0]}*{parts[1]}*_prep*.pdbqt"))
    if matches:
        return matches[0]

    # Final fallback: any pdbqt file
    generic = list(receptors_dir.glob("*.pdbqt"))
    return generic[0] if generic else None


def _write_complex_pdb_from_sdf_and_receptor(
    sdf_file: Path,
    receptor_pdbqt: Optional[Path],
    mode_index: int,
    out_pdb: Path,
) -> bool:
    """
    Extract a specific conformer (1-based index) from SDF and merge with receptor PDBQT.
    Ligand is written as chain B (resname UNK), receptor as chain A.
    """
    try:
        from openbabel import pybel  # type: ignore
    except Exception:
        print("⚠️  Open Babel (pybel) not available; skipping PDB extraction")
        return False

    try:
        # Read all ligand conformers from SDF
        ligands = list(pybel.readfile("sdf", str(sdf_file)))
        if mode_index < 1 or mode_index > len(ligands):
            print(f"⚠️  Mode {mode_index} out of range for {sdf_file} (has {len(ligands)})")
            return False
        ligand = ligands[mode_index - 1]

        # Convert ligand to PDB lines, chain B, resname UNK
        ligand_pdb = ligand.write("pdb")
        ligand_lines = []
        for line in ligand_pdb.split('\n'):
            if not (line.startswith('ATOM') or line.startswith('HETATM')):
                continue
            line = line.ljust(80)
            new_line = f"HETATM{line[6:21]}B{line[22:]}"
            new_line = new_line[:17] + "UNK" + new_line[20:]
            ligand_lines.append(new_line)

        receptor_lines = []
        if receptor_pdbqt and receptor_pdbqt.exists():
            try:
                rec = next(pybel.readfile("pdbqt", str(receptor_pdbqt)))
                rec_pdb = rec.write("pdb")
                for line in rec_pdb.split('\n'):
                    if line.startswith('ATOM'):
                        line = line.ljust(80)
                        new_line = f"ATOM  {line[6:21]}A{line[22:]}"
                        receptor_lines.append(new_line)
            except Exception as e:
                print(f"⚠️  Failed reading receptor {receptor_pdbqt}: {e}")

        lines = receptor_lines + ligand_lines + ["END"]
        out_pdb.write_text('\n'.join(lines))
        return True
    except Exception as e:
        print(f"❌ Error composing complex PDB from {sdf_file}: {e}")
        return False


def extract_best_poses_from_gnina(input_dir: Path, output_dir: Path) -> int:
    """
    Extract best poses as PDB files using GNINA outputs in input_dir.

    - Reads gnina_out/all_scores.csv to determine the best mode per tag
    - For each tag, uses corresponding "<tag>_top.sdf" for ligand conformers
    - Matches receptor from "receptors" directory
    - Writes PDB complexes to output_dir/best_poses_pdb

    Returns the number of PDBs written.
    """
    gnina_dir = input_dir / "gnina_out"
    receptors_dir = input_dir / "receptors"
    scores_csv = gnina_dir / "all_scores.csv"

    if not scores_csv.exists():
        print(f"❌ Scores CSV not found: {scores_csv}")
        return 0

    out_dir = output_dir / "best_poses_pdb"
    out_dir.mkdir(parents=True, exist_ok=True)

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
    best_by_tag = {}
    for r in rows:
        tag = r['tag']
        if tag not in best_by_tag or r['vina_affinity'] < best_by_tag[tag]['vina_affinity']:
            best_by_tag[tag] = r

    written = 0
    for tag, r in best_by_tag.items():
        sdf_file = gnina_dir / f"{tag}_top.sdf"
        if not sdf_file.exists():
            print(f"⚠️  SDF not found for tag {tag}: {sdf_file}")
            continue
        receptor = _infer_receptor_path_from_tag(receptors_dir, tag)
        out_pdb = out_dir / f"{tag}_pose{int(r['mode'])}.pdb"
        ok = _write_complex_pdb_from_sdf_and_receptor(sdf_file, receptor, int(r['mode']), out_pdb)
        if ok:
            written += 1
            print(f"✅ Extracted {out_pdb.name}")

    print(f"✅ Extracted {written} best poses to: {out_dir}")
    return written


