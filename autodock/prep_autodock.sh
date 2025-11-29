#!/usr/bin/env bash
set -euo pipefail

# ── edit these three paths if you renamed your folders ──────────────
ROOT="${1:-$(pwd)}"
RAW_LIG="$ROOT/ligands_raw"          # *.sdf or *.mol2
RAW_REC="$ROOT/receptors_raw"        # *.pdb
OUT_LIG="$ROOT/ligands_prep"         # <- output *.pdbqt
OUT_REC="$ROOT/receptors_prep"       # <- output *.pdbqt
mkdir -p "$OUT_LIG" "$OUT_REC"

# optional: PDB2PQR force-field (AMBER, PARSE, CHARMM, OPLS)
FF="AMBER"

shopt -s nullglob

echo "🧪  Ligand preparation -----------------------------------"
for mol in "$RAW_LIG"/*.{mol2,sdf}; do
  base=${mol##*/}; base=${base%.*}
  out="$OUT_LIG/${base}.pdbqt"
  [[ -f $out ]] && { echo "skip $base"; continue; }
  mk_prepare_ligand.py -i "$mol" -o "$out"
done

echo -e "\n🧬  Receptor preparation (PDB → PQR → clean PDB) --------"
for pdb in "$RAW_REC"/*.pdb; do
  base=${pdb##*/}; base=${base%.*}
  pqr="$OUT_REC/${base}.pqr"
  clean_pdb="$OUT_REC/${base}_clean.pdb"
  pdbqt="$OUT_REC/${base}.pdbqt"

  [[ -f $pdbqt ]] && { echo "skip $base"; continue; }

  # 1) PDB → PQR  (repairs and protonates)
  pdb2pqr30 --ff "$FF" --with-ph 7.4 "$pdb" "$pqr" >/dev/null

  # 2) PQR → cleaned-PDB  (strip charges/radii)
  obabel "$pqr" -O "$clean_pdb"  >/dev/null

  # 3) PDB → PDBQT via Meeko  (still keep guard flags)
  mk_prepare_receptor.py --read_pdb "$clean_pdb" \
                         -p "$pdbqt"              \
                         --allow_bad_res          \
                         --default_altloc A
done

echo -e "\n✅  Finished."
echo "Ligands   prepared: $(ls -1q $OUT_LIG/*.pdbqt  2>/dev/null | wc -l)"
echo "Receptors prepared: $(ls -1q $OUT_REC/*.pdbqt  2>/dev/null | wc -l)"
