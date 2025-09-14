#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Enhanced AutoDock Preparation Script with PLIP Integration
# =============================================================================
# This script prepares ligands and receptors for AutoDock Vina with advanced
# features including PLIP binding site detection, comprehensive error handling,
# and flexible input/output configurations.
# =============================================================================

# ── Configuration and Setup ────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${1:-$SCRIPT_DIR/autodock_config.json}"
LOG_FILE="${SCRIPT_DIR}/autodock_prep_$(date +%Y%m%d_%H%M%S).log"

# Default configuration
DEFAULT_CONFIG='{
  "input": {
    "ligands": {
      "path": "./ligands_raw",
      "formats": ["sdf", "mol2", "pdb"],
      "in_same_folder": false
    },
    "receptors": {
      "path": "./receptors_raw", 
      "formats": ["pdb"],
      "in_same_folder": false
    }
  },
  "output": {
    "ligands": "./ligands_prep",
    "receptors": "./receptors_prep",
    "logs": "./logs"
  },
  "preparation": {
    "force_field": "AMBER",
    "ph": 7.4,
    "allow_bad_res": true,
    "default_altloc": "A"
  },
  "plip": {
    "enabled": true,
    "binding_site_detection": true,
    "interaction_analysis": true
  },
  "quality_control": {
    "validate_outputs": true,
    "check_file_sizes": true,
    "min_file_size_kb": 1
  }
}'

# ── Logging Functions ──────────────────────────────────────────────────────
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

log_success() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1" | tee -a "$LOG_FILE"
}

# ── Progress Tracking ──────────────────────────────────────────────────────
show_progress() {
    local current=$1
    local total=$2
    local task=$3
    local percent=$((current * 100 / total))
    printf "\r[%3d%%] %s (%d/%d)" "$percent" "$task" "$current" "$total"
}

# ── Configuration Management ───────────────────────────────────────────────
load_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_info "Creating default configuration file: $CONFIG_FILE"
        echo "$DEFAULT_CONFIG" > "$CONFIG_FILE"
        log_info "Please edit $CONFIG_FILE and run again"
        exit 0
    fi
    
    # Load configuration using jq (install if not available)
    if ! command -v jq &> /dev/null; then
        log_error "jq is required for JSON configuration. Install with: brew install jq (macOS) or apt-get install jq (Ubuntu)"
        exit 1
    fi
    
    # Validate JSON
    if ! jq empty "$CONFIG_FILE" 2>/dev/null; then
        log_error "Invalid JSON configuration file: $CONFIG_FILE"
        exit 1
    fi
    
    log_info "Loaded configuration from: $CONFIG_FILE"
}

# ── Dependency Checking ────────────────────────────────────────────────────
check_dependencies() {
    local missing_deps=()
    
    # Check required tools
    local required_tools=("mk_prepare_ligand.py" "mk_prepare_receptor.py" "pdb2pqr30" "obabel")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_deps+=("$tool")
        fi
    done
    
    # Check optional PLIP
    if [[ "$(jq -r '.plip.enabled' "$CONFIG_FILE")" == "true" ]]; then
        if ! command -v plip &> /dev/null; then
            log_info "PLIP not found. Install with: conda install -c conda-forge plip"
            log_info "Continuing without PLIP integration..."
            jq '.plip.enabled = false' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" && mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
        fi
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_error "Install AutoDockTools and OpenBabel to continue"
        exit 1
    fi
    
    log_success "All required dependencies found"
}

# ── File Format Conversion ─────────────────────────────────────────────────
convert_ligand_format() {
    local input_file="$1"
    local output_format="$2"
    local output_file="$3"
    
    case "$output_format" in
        "sdf")
            obabel "$input_file" -O "$output_file" 2>/dev/null || return 1
            ;;
        "mol2")
            obabel "$input_file" -O "$output_file" 2>/dev/null || return 1
            ;;
        "pdb")
            obabel "$input_file" -O "$output_file" 2>/dev/null || return 1
            ;;
        *)
            log_error "Unsupported output format: $output_format"
            return 1
            ;;
    esac
}

# ── Quality Control ────────────────────────────────────────────────────────
validate_file() {
    local file="$1"
    local min_size_kb="${2:-1}"
    
    if [[ ! -f "$file" ]]; then
        log_error "File not found: $file"
        return 1
    fi
    
    local file_size_kb=$(($(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null) / 1024))
    if [[ $file_size_kb -lt $min_size_kb ]]; then
        log_error "File too small: $file (${file_size_kb}KB < ${min_size_kb}KB)"
        return 1
    fi
    
    # Check if PDBQT file has proper format
    if [[ "$file" == *.pdbqt ]]; then
        if ! grep -q "ATOM\|HETATM" "$file"; then
            log_error "Invalid PDBQT file: $file (no ATOM/HETATM records)"
            return 1
        fi
    fi
    
    return 0
}

# ── PLIP Integration ───────────────────────────────────────────────────────
run_plip_analysis() {
    local pdb_file="$1"
    local output_dir="$2"
    
    if [[ "$(jq -r '.plip.enabled' "$CONFIG_FILE")" != "true" ]]; then
        return 0
    fi
    
    log_info "Running PLIP analysis on: $pdb_file"
    
    # Create PLIP output directory
    local plip_dir="$output_dir/plip_analysis"
    mkdir -p "$plip_dir"
    
    # Run PLIP analysis
    if plip -f "$pdb_file" -t -o "$plip_dir" 2>/dev/null; then
        log_success "PLIP analysis completed for: $pdb_file"
        
        # Extract binding site information if available
        local report_file="$plip_dir/report.txt"
        if [[ -f "$report_file" ]]; then
            log_info "PLIP report generated: $report_file"
            
            # Parse binding sites (simplified)
            local binding_sites=$(grep -c "Interacting chain(s):" "$report_file" 2>/dev/null || echo "0")
            log_info "Found $binding_sites potential binding sites"
        fi
    else
        log_error "PLIP analysis failed for: $pdb_file"
        return 1
    fi
}

# ── Ligand Preparation ─────────────────────────────────────────────────────
prepare_ligands() {
    local input_dir="$1"
    local output_dir="$2"
    local formats=("$3")
    
    log_info "Starting ligand preparation..."
    mkdir -p "$output_dir"
    
    local total_files=0
    local processed_files=0
    
    # Count total files
    for format in "${formats[@]}"; do
        total_files=$((total_files + $(find "$input_dir" -name "*.${format}" -type f 2>/dev/null | wc -l)))
    done
    
    if [[ $total_files -eq 0 ]]; then
        log_info "No ligand files found in: $input_dir"
        return 0
    fi
    
    log_info "Found $total_files ligand files to process"
    
    # Process each format
    for format in "${formats[@]}"; do
        while IFS= read -r -d '' mol_file; do
            processed_files=$((processed_files + 1))
            show_progress "$processed_files" "$total_files" "Processing ligands"
            
            local base_name=$(basename "$mol_file" ".${format}")
            local output_file="$output_dir/${base_name}.pdbqt"
            
            # Skip if already exists and valid
            if [[ -f "$output_file" ]] && validate_file "$output_file"; then
                continue
            fi
            
            # Convert to PDBQT
            if mk_prepare_ligand.py -i "$mol_file" -o "$output_file" 2>/dev/null; then
                if validate_file "$output_file"; then
                    log_success "Prepared ligand: $base_name"
                else
                    log_error "Invalid output file: $output_file"
                    rm -f "$output_file"
                fi
            else
                log_error "Failed to prepare ligand: $mol_file"
            fi
            
        done < <(find "$input_dir" -name "*.${format}" -type f -print0 2>/dev/null)
    done
    
    echo # New line after progress
    local success_count=$(find "$output_dir" -name "*.pdbqt" -type f | wc -l)
    log_success "Ligand preparation completed: $success_count/$total_files files"
}

# ── Receptor Preparation ───────────────────────────────────────────────────
prepare_receptors() {
    local input_dir="$1"
    local output_dir="$2"
    local formats=("$3")
    
    log_info "Starting receptor preparation..."
    mkdir -p "$output_dir"
    
    local total_files=0
    local processed_files=0
    
    # Count total files
    for format in "${formats[@]}"; do
        total_files=$((total_files + $(find "$input_dir" -name "*.${format}" -type f 2>/dev/null | wc -l)))
    done
    
    if [[ $total_files -eq 0 ]]; then
        log_info "No receptor files found in: $input_dir"
        return 0
    fi
    
    log_info "Found $total_files receptor files to process"
    
    # Process each format
    for format in "${formats[@]}"; do
        while IFS= read -r -d '' pdb_file; do
            processed_files=$((processed_files + 1))
            show_progress "$processed_files" "$total_files" "Processing receptors"
            
            local base_name=$(basename "$pdb_file" ".${format}")
            local pqr_file="$output_dir/${base_name}.pqr"
            local clean_pdb="$output_dir/${base_name}_clean.pdb"
            local pdbqt_file="$output_dir/${base_name}.pdbqt"
            
            # Skip if already exists and valid
            if [[ -f "$pdbqt_file" ]] && validate_file "$pdbqt_file"; then
                continue
            fi
            
            # Step 1: PDB → PQR (repairs and protonates)
            if pdb2pqr30 --ff "$(jq -r '.preparation.force_field' "$CONFIG_FILE")" \
                        --with-ph "$(jq -r '.preparation.ph' "$CONFIG_FILE")" \
                        "$pdb_file" "$pqr_file" >/dev/null 2>&1; then
                
                # Step 2: PQR → Clean PDB (strip charges/radii)
                if obabel "$pqr_file" -O "$clean_pdb" >/dev/null 2>&1; then
                    
                    # Step 3: PDB → PDBQT via Meeko
                    local meeko_args=("--read_pdb" "$clean_pdb" "-p" "$pdbqt_file")
                    
                    if [[ "$(jq -r '.preparation.allow_bad_res' "$CONFIG_FILE")" == "true" ]]; then
                        meeko_args+=("--allow_bad_res")
                    fi
                    
                    meeko_args+=("--default_altloc" "$(jq -r '.preparation.default_altloc' "$CONFIG_FILE")")
                    
                    if mk_prepare_receptor.py "${meeko_args[@]}" 2>/dev/null; then
                        if validate_file "$pdbqt_file"; then
                            log_success "Prepared receptor: $base_name"
                            
                            # Run PLIP analysis if enabled
                            if [[ "$(jq -r '.plip.enabled' "$CONFIG_FILE")" == "true" ]]; then
                                run_plip_analysis "$pdb_file" "$output_dir"
                            fi
                        else
                            log_error "Invalid output file: $pdbqt_file"
                            rm -f "$pdbqt_file"
                        fi
                    else
                        log_error "Failed to prepare receptor: $pdb_file (Meeko step)"
                    fi
                else
                    log_error "Failed to prepare receptor: $pdb_file (OpenBabel step)"
                fi
            else
                log_error "Failed to prepare receptor: $pdb_file (PDB2PQR step)"
            fi
            
            # Clean up intermediate files
            rm -f "$pqr_file" "$clean_pdb"
            
        done < <(find "$input_dir" -name "*.${format}" -type f -print0 2>/dev/null)
    done
    
    echo # New line after progress
    local success_count=$(find "$output_dir" -name "*.pdbqt" -type f | wc -l)
    log_success "Receptor preparation completed: $success_count/$total_files files"
}

# ── Main Execution ─────────────────────────────────────────────────────────
main() {
    log_info "Starting Enhanced AutoDock Preparation Script"
    log_info "Configuration file: $CONFIG_FILE"
    log_info "Log file: $LOG_FILE"
    
    # Load configuration
    load_config
    
    # Check dependencies
    check_dependencies
    
    # Get configuration values
    local ligands_input=$(jq -r '.input.ligands.path' "$CONFIG_FILE")
    local receptors_input=$(jq -r '.input.receptors.path' "$CONFIG_FILE")
    local ligands_output=$(jq -r '.output.ligands' "$CONFIG_FILE")
    local receptors_output=$(jq -r '.output.receptors' "$CONFIG_FILE")
    
    # Handle same folder scenario
    local in_same_folder=$(jq -r '.input.ligands.in_same_folder' "$CONFIG_FILE")
    if [[ "$in_same_folder" == "true" ]]; then
        ligands_input="$receptors_input"
        log_info "Using same folder for ligands and receptors: $ligands_input"
    fi
    
    # Create output directories
    mkdir -p "$ligands_output" "$receptors_output" "$(dirname "$LOG_FILE")"
    
    # Prepare ligands
    local ligand_formats=($(jq -r '.input.ligands.formats[]' "$CONFIG_FILE"))
    prepare_ligands "$ligands_input" "$ligands_output" "${ligand_formats[@]}"
    
    # Prepare receptors
    local receptor_formats=($(jq -r '.input.receptors.formats[]' "$CONFIG_FILE"))
    prepare_receptors "$receptors_input" "$receptors_output" "${receptor_formats[@]}"
    
    # Final summary
    local total_ligands=$(find "$ligands_output" -name "*.pdbqt" -type f 2>/dev/null | wc -l)
    local total_receptors=$(find "$receptors_output" -name "*.pdbqt" -type f 2>/dev/null | wc -l)
    
    log_success "Preparation completed successfully!"
    log_info "Ligands prepared: $total_ligands"
    log_info "Receptors prepared: $total_receptors"
    log_info "Log file saved: $LOG_FILE"
    
    # Generate summary report
    local summary_file="$receptors_output/preparation_summary.txt"
    cat > "$summary_file" << EOF
AutoDock Preparation Summary
============================
Date: $(date)
Configuration: $CONFIG_FILE
Log File: $LOG_FILE

Results:
--------
Ligands prepared: $total_ligands
Receptors prepared: $total_receptors

Output Directories:
------------------
Ligands: $ligands_output
Receptors: $receptors_output

PLIP Analysis: $(jq -r '.plip.enabled' "$CONFIG_FILE")
Force Field: $(jq -r '.preparation.force_field' "$CONFIG_FILE")
pH: $(jq -r '.preparation.ph' "$CONFIG_FILE")
EOF
    
    log_info "Summary report saved: $summary_file"
}

# ── Error Handling ─────────────────────────────────────────────────────────
trap 'log_error "Script interrupted at line $LINENO"' INT TERM
trap 'log_error "Script failed at line $LINENO"' ERR

# ── Execute Main Function ──────────────────────────────────────────────────
main "$@"
