# PDBQT Preparation Scripts - Complete Explanation

## Overview

The repository contains **three different approaches** to prepare molecules for AutoDock Vina docking:

1. **`autodock_preparation.py`** - Python module (most flexible, recommended)
2. **`prep_autodock_enhanced.sh`** - Enhanced bash script (advanced features)
3. **`autodock/prep_autodock.sh`** - Basic bash script (simple use cases)

All three convert molecular structures to **PDBQT format**, which is required by AutoDock Vina.

---

## What is PDBQT Format?

**PDBQT** = PDB format + **Q** (partial charges) + **T** (atom types)

- **PDB**: Standard protein structure format
- **Q**: Partial charges for each atom (needed for docking calculations)
- **T**: Atom types (C, N, O, etc. with specific AutoDock typing)

AutoDock Vina requires both ligands and receptors in PDBQT format to perform docking.

---

## 1. Python Module: `autodock_preparation.py`

### Purpose
Python API for programmatic AutoDock preparation with PLIP integration and comprehensive error handling.

### Key Components

#### **PreparationConfig** (Data Class)
Configuration settings for preparation:
```python
@dataclass
class PreparationConfig:
    ligands_input: str          # Input directory for ligands
    receptors_input: str       # Input directory for receptors
    ligands_output: str         # Output directory for prepared ligands
    receptors_output: str       # Output directory for prepared receptors
    force_field: str = "AMBER"  # Force field for protonation
    ph: float = 7.4            # pH for protonation
    plip_enabled: bool = True  # Enable PLIP analysis
```

#### **AutoDockPreparationPipeline** (Main Class)

**Key Methods:**

1. **`check_dependencies()`**
   - Checks for required tools: `mk_prepare_ligand.py`, `mk_prepare_receptor.py`, `pdb2pqr30`, `obabel`
   - Returns list of missing dependencies

2. **`prepare_ligands_from_pdb(pdb_file, output_dir)`**
   - Extracts ligands from PDB files using PDB Prepare Wizard
   - Converts PDB → SDF → PDBQT
   - Handles explicit hydrogens requirement

3. **`run_enhanced_preparation(config_path)`**
   - Runs the enhanced bash script (`prep_autodock_enhanced.sh`)
   - Uses JSON configuration file
   - Returns success/failure status

4. **`analyze_preparation_results(output_dir)`**
   - Counts prepared files
   - Calculates total file sizes
   - Checks for PLIP analysis reports

5. **`create_config_file(config_path)`**
   - Generates JSON configuration file
   - Includes all preparation settings

### Usage Example

```python
from autodock_preparation import AutoDockPreparationPipeline, PreparationConfig

# Create configuration
config = PreparationConfig(
    ligands_input="./ligands_raw",
    receptors_input="./receptors_raw",
    ligands_output="./ligands_prep",
    receptors_output="./receptors_prep",
    force_field="AMBER",
    ph=7.4
)

# Initialize pipeline
pipeline = AutoDockPreparationPipeline(config)

# Check dependencies
deps_ok, missing = pipeline.check_dependencies()
if not deps_ok:
    print(f"Missing: {missing}")
    exit(1)

# Run preparation
success = pipeline.run_enhanced_preparation()

# Analyze results
if success:
    results = pipeline.analyze_preparation_results("./receptors_prep")
    print(f"Ligands: {results['ligands']['count']}")
    print(f"Receptors: {results['receptors']['count']}")
```

---

## 2. Enhanced Bash Script: `prep_autodock_enhanced.sh`

### Purpose
Advanced bash script with JSON configuration, PLIP integration, progress tracking, and comprehensive error handling.

### Key Features

#### **Configuration Management**
- Uses JSON configuration file (`autodock_config.json`)
- Requires `jq` for JSON parsing
- Creates default config if missing

#### **Ligand Preparation Workflow**

```
Input Formats: SDF, MOL2, PDB
     ↓
For SDF/MOL2:
  Direct conversion via Meeko
  SDF/MOL2 → PDBQT
  
For PDB:
  PDB → SDF (with explicit hydrogens) → PDBQT
  (Meeko requires explicit hydrogens)
```

**Key Steps:**
1. Find all ligand files in input directory
2. For each file:
   - Skip if PDBQT already exists and is valid
   - Convert format if needed (PDB → SDF)
   - Run `mk_prepare_ligand.py` to create PDBQT
   - Validate output file
3. Show progress bar
4. Report success count

#### **Receptor Preparation Workflow**

```
PDB → PQR → Clean PDB → PDBQT
```

**Detailed Steps:**

1. **PDB → PQR** (using PDB2PQR)
   ```bash
   pdb2pqr30 --ff AMBER --with-ph 7.4 input.pdb output.pqr
   ```
   - Repairs missing atoms
   - Adds hydrogens
   - Assigns partial charges
   - Uses specified force field (AMBER, CHARMM, PARSE, OPLS)

2. **PQR → Clean PDB** (using OpenBabel)
   ```bash
   obabel input.pqr -O output_clean.pdb
   ```
   - Strips charges and radii (PDBQT needs clean PDB)
   - Removes PQR-specific metadata

3. **Clean PDB → PDBQT** (using Meeko)
   ```bash
   mk_prepare_receptor.py --read_pdb clean.pdb -p output.pdbqt \
                          --allow_bad_res --default_altloc A
   ```
   - Assigns AutoDock atom types
   - Adds partial charges
   - Handles alternate locations
   - Creates PDBQT format

4. **PLIP Analysis** (optional)
   - Runs PLIP on original PDB file
   - Generates binding site report
   - Validates binding sites

#### **Quality Control**

- **File Size Validation**: Checks minimum file size (default: 1 KB)
- **Format Validation**: Verifies PDBQT contains ATOM/HETATM records
- **Skip Existing**: Skips files that already exist and are valid
- **Error Recovery**: Continues processing even if individual files fail

#### **Progress Tracking**

- Shows percentage completion
- Displays current file number / total files
- Updates in real-time

### Usage

```bash
# Create default config
./prep_autodock_enhanced.sh

# Edit config file
nano autodock_config.json

# Run preparation
./prep_autodock_enhanced.sh autodock_config.json
```

### Configuration File Structure

```json
{
  "input": {
    "ligands": {
      "path": "./ligands_raw",
      "formats": ["sdf", "mol2", "pdb"],
      "in_same_folder": false
    },
    "receptors": {
      "path": "./receptors_raw",
      "formats": ["pdb"]
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
    "binding_site_detection": true
  },
  "quality_control": {
    "validate_outputs": true,
    "min_file_size_kb": 1
  }
}
```

---

## 3. Basic Bash Script: `autodock/prep_autodock.sh`

### Purpose
Simple, straightforward script for basic preparation without advanced features.

### Workflow

**Ligand Preparation:**
```bash
# For each SDF/MOL2 file:
mk_prepare_ligand.py -i input.sdf -o output.pdbqt
```

**Receptor Preparation:**
```bash
# Step 1: PDB → PQR
pdb2pqr30 --ff AMBER --with-ph 7.4 input.pdb temp.pqr

# Step 2: PQR → Clean PDB
obabel temp.pqr -O clean.pdb

# Step 3: Clean PDB → PDBQT
mk_prepare_receptor.py --read_pdb clean.pdb -p output.pdbqt \
                       --allow_bad_res --default_altloc A
```

### Usage

```bash
# Edit paths in script (lines 5-9)
ROOT="/path/to/project"
RAW_LIG="$ROOT/ligands_raw"
RAW_REC="$ROOT/receptors_raw"
OUT_LIG="$ROOT/ligands_prep"
OUT_REC="$ROOT/receptors_prep"

# Run script
./autodock/prep_autodock.sh
```

### Features
- ✅ Simple and fast
- ✅ No configuration file needed
- ✅ Direct file processing
- ❌ No progress tracking
- ❌ No PLIP integration
- ❌ Limited error handling

---

## Comparison Table

| Feature | Python Module | Enhanced Script | Basic Script |
|---------|--------------|-----------------|--------------|
| **Configuration** | Python dataclass | JSON file | Hardcoded paths |
| **PLIP Integration** | ✅ Yes | ✅ Yes | ❌ No |
| **Progress Tracking** | ✅ Yes | ✅ Yes | ❌ No |
| **Error Handling** | ✅ Comprehensive | ✅ Comprehensive | ⚠️ Basic |
| **File Validation** | ✅ Yes | ✅ Yes | ❌ No |
| **Logging** | ✅ Yes | ✅ Yes | ⚠️ Minimal |
| **PDB Ligand Extraction** | ✅ Yes | ❌ No | ❌ No |
| **Flexibility** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Ease of Use** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## Why Three Different Scripts?

1. **Python Module** (`autodock_preparation.py`)
   - Best for: Programmatic use, integration with other Python code
   - Use when: Building custom workflows, need PDB ligand extraction

2. **Enhanced Script** (`prep_autodock_enhanced.sh`)
   - Best for: Production workflows, batch processing
   - Use when: Need PLIP analysis, comprehensive logging, quality control

3. **Basic Script** (`autodock/prep_autodock.sh`)
   - Best for: Quick one-off preparations, simple use cases
   - Use when: Just need basic conversion, no advanced features needed

---

## Required Tools & Dependencies

### Core Tools
1. **Meeko** (`mk_prepare_ligand.py`, `mk_prepare_receptor.py`)
   ```bash
   pip install meeko
   ```

2. **OpenBabel** (`obabel`)
   ```bash
   conda install -c conda-forge openbabel
   ```

3. **PDB2PQR** (`pdb2pqr30`)
   ```bash
   conda install -c conda-forge pdb2pqr
   ```

### Optional Tools
4. **PLIP** (for binding site analysis)
   ```bash
   conda install -c conda-forge plip
   ```

5. **jq** (for JSON parsing in bash script)
   ```bash
   brew install jq  # macOS
   apt-get install jq  # Ubuntu
   ```

---

## Common Workflows

### Workflow 1: Prepare Ligands from SDF Files

```bash
# Using enhanced script
# 1. Create config
python autodock_preparation.py --create-config

# 2. Edit config to point to SDF files
# "ligands": {"path": "./my_ligands", "formats": ["sdf"]}

# 3. Run
./prep_autodock_enhanced.sh autodock_config.json
```

### Workflow 2: Prepare Receptors from PDB Files

```bash
# Using Python API
from autodock_preparation import AutoDockPreparationPipeline, PreparationConfig

config = PreparationConfig(
    receptors_input="./receptors_raw",
    receptors_output="./receptors_prep",
    force_field="AMBER",
    ph=7.4
)

pipeline = AutoDockPreparationPipeline(config)
pipeline.run_enhanced_preparation()
```

### Workflow 3: Extract Ligands from PDB and Prepare

```python
# Using Python module
from autodock_preparation import AutoDockPreparationPipeline

pipeline = AutoDockPreparationPipeline()

# Extract ligand from PDB and prepare
ligand_pdbqt = pipeline.prepare_ligands_from_pdb(
    "protein_with_ligand.pdb",
    "./ligands_prep"
)
```

---

## Troubleshooting

### Issue: "RDKit molecule has implicit Hs. Need explicit Hs."

**Solution:** The enhanced script handles this automatically:
- For PDB files: Uses `obabel -h` to add explicit hydrogens
- For SDF/MOL2: Usually already have explicit hydrogens

### Issue: "mk_prepare_ligand.py: command not found"

**Solution:**
```bash
pip install meeko
# Verify installation
which mk_prepare_ligand.py
```

### Issue: "pdb2pqr30: command not found"

**Solution:**
```bash
conda install -c conda-forge pdb2pqr
# Verify installation
which pdb2pqr30
```

### Issue: "obabel: command not found"

**Solution:**
```bash
conda install -c conda-forge openbabel
# Verify installation
which obabel
```

### Issue: PLIP Analysis Fails

**Solution:**
- Install PLIP: `conda install -c conda-forge plip`
- Or disable PLIP in config: `"plip": {"enabled": false}`

---

## Output Files

### Ligand Output
- **Format**: `{filename}.pdbqt`
- **Location**: `ligands_prep/` directory
- **Content**: Ligand structure with charges and atom types

### Receptor Output
- **Format**: `{filename}.pdbqt`
- **Location**: `receptors_prep/` directory
- **Content**: Receptor structure with charges and atom types
- **PLIP Reports**: `receptors_prep/plip_analysis/report.txt` (if enabled)

### Log Files
- **Enhanced Script**: `autodock_prep_YYYYMMDD_HHMMSS.log`
- **Summary Report**: `receptors_prep/preparation_summary.txt`

---

## Best Practices

1. **Always validate outputs** before docking
2. **Use PLIP analysis** to verify binding sites
3. **Check file sizes** - very small files may indicate errors
4. **Keep original files** - PDBQT is one-way conversion
5. **Use appropriate force field** - AMBER for most cases, CHARMM for membrane proteins
6. **Set correct pH** - Match experimental conditions (usually 7.4)

---

## Integration with PDB Prepare Wizard

The AutoDock preparation integrates seamlessly with PDB Prepare Wizard:

```python
# Complete workflow: PDB → Clean → AutoDock Preparation
from core_pipeline import MolecularDockingPipeline
from autodock_preparation import AutoDockPreparationPipeline

# 1. Prepare PDB structure
pdb_pipeline = MolecularDockingPipeline()
cleaned_pdb = pdb_pipeline.clean_pdb("protein.pdb", ["HOH", "NA", "CL"])

# 2. Prepare for AutoDock
autodock_pipeline = AutoDockPreparationPipeline()
autodock_pipeline.run_enhanced_preparation()

# 3. Ready for docking!
```

---

**Version**: 3.0.1  
**Last Updated**: 2025-01-15

