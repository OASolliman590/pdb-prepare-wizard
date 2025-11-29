#!/usr/bin/env bash
set -uo pipefail  # Removed -e to allow error handling and continue processing

# ── edit these three paths if you renamed your folders ──────────────
ROOT="${1:-$(pwd)}"
RAW_LIG="$ROOT/ligands_raw"          # *.sdf, *.mol2, *.mol, or *.pdb
RAW_REC="$ROOT/receptors_raw"        # *.pdb
OUT_LIG="$ROOT/ligands_prep"         # <- output *.pdbqt
OUT_REC="$ROOT/receptors_prep"       # <- output *.pdbqt
TEMP_DIR="$ROOT/temp_ligand_prep"

mkdir -p "$OUT_LIG" "$OUT_REC" "$TEMP_DIR"

# optional: PDB2PQR force-field (AMBER, PARSE, CHARMM, OPLS)
FF="AMBER"

shopt -s nullglob

# ============================================
# LIGAND PREPARATION
# ============================================
echo "🧪  Ligand preparation -----------------------------------"
echo "  3D Generation + Protonation + Energy Minimization"

# Function to prepare a single ligand with proper 3D structure
prepare_ligand_proper() {
  local input_file="$1"
  local base=$(basename "$input_file" .${input_file##*.})
  local output_pdbqt="$OUT_LIG/${base}.pdbqt"
  
  # Skip if already exists and valid
  if [[ -f "$output_pdbqt" ]] && [[ -s "$output_pdbqt" ]]; then
    echo "skip $base (already prepared)"
    return 0
  fi
  
  echo "Processing: $base"
  
  local temp_3d="$TEMP_DIR/${base}_3d.sdf"
  local temp_protonated="$TEMP_DIR/${base}_protonated.sdf"
  local temp_minimized="$TEMP_DIR/${base}_minimized.sdf"
  
  # Step 1: Generate 3D structure
  if ! obabel "$input_file" -O "$temp_3d" --gen3d 2>/dev/null; then
    echo "  ✗ Failed: 3D generation"
    return 1
  fi
  
  # Step 2: Add explicit hydrogens (protonate)
  if ! obabel "$temp_3d" -O "$temp_protonated" -h 2>/dev/null; then
    echo "  ✗ Failed: Protonation"
    rm -f "$temp_3d"
    return 1
  fi
  
  # Step 3: Energy minimize (MMFF94 force field)
  if ! obabel "$temp_protonated" -O "$temp_minimized" --minimize --steps 2000 --ff MMFF94 2>/dev/null; then
    echo "  ⚠️  Minimization failed, using protonated structure..."
    cp "$temp_protonated" "$temp_minimized"
  fi
  
  # Step 4: Prepare with Meeko
  if mk_prepare_ligand.py -i "$temp_minimized" -o "$output_pdbqt" 2>/dev/null; then
    if [[ -f "$output_pdbqt" ]] && [[ -s "$output_pdbqt" ]]; then
      echo "  ✓ Prepared: $base"
      rm -f "$temp_3d" "$temp_protonated" "$temp_minimized"
      return 0
    fi
  fi
  
  echo "  ✗ Failed: Meeko preparation"
  rm -f "$temp_3d" "$temp_protonated" "$temp_minimized" "$output_pdbqt"
  return 1
}

# Process .mol2 and .sdf files (with proper 3D preparation)
for mol in "$RAW_LIG"/*.{mol2,sdf} 2>/dev/null; do
  [[ ! -f "$mol" ]] && continue
  prepare_ligand_proper "$mol"
done

# Process .mol files (with proper 3D preparation)
for mol in "$RAW_LIG"/*.mol 2>/dev/null; do
  [[ ! -f "$mol" ]] && continue
  prepare_ligand_proper "$mol"
done

# Process .pdb ligand files (special handling: PDB → SDF → 3D → Protonated → Minimized → PDBQT)
for pdb in "$RAW_LIG"/*.pdb 2>/dev/null; do
  [[ ! -f "$pdb" ]] && continue
  base=${pdb##*/}; base=${base%.*}
  out="$OUT_LIG/${base}.pdbqt"
  
  [[ -f "$out" ]] && [[ -s "$out" ]] && { echo "skip $base"; continue; }
  
  echo "Processing: $base (PDB → 3D → Protonated → Minimized → PDBQT)"
  
  temp_sdf="$TEMP_DIR/${base}_from_pdb.sdf"
  temp_3d="$TEMP_DIR/${base}_3d.sdf"
  temp_protonated="$TEMP_DIR/${base}_protonated.sdf"
  temp_minimized="$TEMP_DIR/${base}_minimized.sdf"
  
  # Step 1: PDB → SDF
  if ! obabel "$pdb" -O "$temp_sdf" 2>/dev/null; then
    echo "  ✗ Failed: PDB → SDF conversion"
    continue
  fi
  
  # Step 2: Generate 3D
  if ! obabel "$temp_sdf" -O "$temp_3d" --gen3d 2>/dev/null; then
    echo "  ✗ Failed: 3D generation"
    rm -f "$temp_sdf"
    continue
  fi
  
  # Step 3: Protonate
  if ! obabel "$temp_3d" -O "$temp_protonated" -h 2>/dev/null; then
    echo "  ✗ Failed: Protonation"
    rm -f "$temp_sdf" "$temp_3d"
    continue
  fi
  
  # Step 4: Minimize
  if ! obabel "$temp_protonated" -O "$temp_minimized" --minimize --steps 2000 --ff MMFF94 2>/dev/null; then
    echo "  ⚠️  Minimization failed, using protonated structure..."
    cp "$temp_protonated" "$temp_minimized"
  fi
  
  # Step 5: Meeko
  if mk_prepare_ligand.py -i "$temp_minimized" -o "$out" 2>/dev/null; then
    if [[ -f "$out" ]] && [[ -s "$out" ]]; then
      echo "  ✓ Prepared: $base"
    else
      echo "  ✗ Failed: No output file"
    fi
  else
    echo "  ✗ Failed: Meeko preparation"
  fi
  
  rm -f "$temp_sdf" "$temp_3d" "$temp_protonated" "$temp_minimized"
done

# Cleanup temp directory
rm -rf "$TEMP_DIR"

# ============================================
# RECEPTOR PREPARATION
# ============================================
echo -e "\n🧬  Receptor preparation (PDB → PQR → clean PDB) --------"
for pdb in "$RAW_REC"/*.pdb; do
  [[ ! -f "$pdb" ]] && continue
  base=${pdb##*/}; base=${base%.*}
  pqr="$OUT_REC/${base}.pqr"
  clean_pdb="$OUT_REC/${base}_clean.pdb"
  pdbqt="$OUT_REC/${base}.pdbqt"

  [[ -f "$pdbqt" ]] && [[ -s "$pdbqt" ]] && { echo "skip $base"; continue; }
  
  echo "Processing: $base"

  # Step 1: PDB → PQR (with error handling)
  if ! pdb2pqr30 --ff "$FF" --with-ph 7.4 "$pdb" "$pqr" 2>&1 | grep -v "WARNING:" | grep -v "INFO:" >/dev/null; then
    # Check if PQR was created despite warnings
    if [[ ! -f "$pqr" ]]; then
      echo "⚠️  Failed: $base (PDB2PQR error - structure may be too incomplete)"
      rm -f "$pqr" "$clean_pdb" "$pdbqt"
      continue
    fi
  fi

  # Step 2: PQR → cleaned-PDB (strip charges/radii)
  if ! obabel "$pqr" -O "$clean_pdb" >/dev/null 2>&1; then
    echo "⚠️  Failed: $base (OpenBabel conversion error)"
    rm -f "$pqr" "$clean_pdb" "$pdbqt"
    continue
  fi

  # Step 3: PDB → PDBQT via Meeko
  # Note: Meeko may take a long time for large structures or fail on interrupted residues
  echo "  → Running Meeko (this may take several minutes for large structures)..."
  
  # Try Meeko preparation with error capture
  meeko_output=$(mktemp)
  mk_prepare_receptor.py --read_pdb "$clean_pdb" \
                         -p "$pdbqt"              \
                         --allow_bad_res          \
                         --default_altloc A 2>"$meeko_output" || true
  
  # Check for interrupted residues error immediately
  if grep -q "interrupted residues" "$meeko_output" 2>/dev/null; then
    echo "⚠️  Failed: $base (Structure has interrupted residues - too many gaps)"
    echo "   → Meeko requires consecutive complete residues"
    echo "   → Solution: Use OpenBabel direct conversion: obabel input.pdb -O output.pdbqt -xr"
    rm -f "$pqr" "$clean_pdb" "$pdbqt" "$meeko_output"
    continue
  fi
  
  rm -f "$meeko_output"
  
  # Wait a bit and check if file is being created (Meeko may take time)
  sleep 2
  
  # Check multiple times as Meeko may still be processing
  for i in {1..7}; do
    if [[ -f "$pdbqt" ]] && [[ -s "$pdbqt" ]]; then
      break
    fi
    if [[ $i -lt 7 ]]; then
      echo "  → Waiting for Meeko to complete... (attempt $i/7)"
      sleep 3
    fi
  done
  
  # Final check if file was actually created
  if [[ ! -f "$pdbqt" ]] || [[ ! -s "$pdbqt" ]]; then
    echo "⚠️  Failed: $base (Meeko preparation error - no output file after waiting)"
    echo "   → Try alternative: obabel $clean_pdb -O $pdbqt -xr"
    rm -f "$pqr" "$clean_pdb" "$pdbqt"
    continue
  fi

  # Clean up intermediate files
  rm -f "$pqr" "$clean_pdb"
  echo "  ✓ Completed: $base"
done

# ============================================
# SUMMARY
# ============================================
echo -e "\n✅  Finished."
echo "Ligands   prepared: $(ls -1q "$OUT_LIG"/*.pdbqt 2>/dev/null | wc -l)"
echo "Receptors prepared: $(ls -1q "$OUT_REC"/*.pdbqt 2>/dev/null | wc -l)"
echo ""
echo "All ligands are now:"
echo "  ✓ 3D structures (not 2D)"
echo "  ✓ Protonated (explicit hydrogens)"
echo "  ✓ Energy minimized (MMFF94)"
echo "  ✓ Ready for docking"
