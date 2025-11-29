# PDB Preparation Usage Guide

## Overview

The PDB Prepare Wizard provides three main ways to prepare PDB files for molecular docking:

1. **Interactive Mode** - User-friendly guided interface with prompts
2. **CLI Mode** - Command-line interface for single or multiple PDBs
3. **Batch Mode** - Configuration-driven batch processing of multiple PDBs
4. **Python API** - Programmatic access for custom workflows

---

## 🎯 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or use conda
conda env create -f environment.yml
conda activate pdb-prepare-wizard
pip install -e .
```

### Basic Usage

```bash
# Interactive mode (easiest for beginners)
python main.py

# Or explicitly
python main.py interactive
```

---

## 1. Interactive Mode

**Best for:** First-time users, exploring PDB structures, single PDB analysis

### How It Works

The interactive mode guides you through each step with prompts:

```bash
python main.py interactive
```

### Step-by-Step Process

1. **Enter PDB ID**: You'll be prompted to enter a 4-character PDB ID (e.g., `7CMD`)

2. **Select Ligand**: The system will:
   - Download the PDB file automatically
   - Show all available ligands (HETATMs) grouped by type
   - Let you select which ligand to extract
   - Example output:
     ```
     📋 Available HETATM types:
        1. TTT (1 instance(s))
        2. HOH (150 instance(s))
        3. NA (2 instance(s))
     
     Select HETATM type (1-3): 1
     ```

3. **Select Chains**: Choose which protein chains to keep
   - Shows available chains
   - You can select specific chains or keep all

4. **Cleaning Options**: Choose what to remove:
   - **Specific residues**: Enter comma-separated list (e.g., `HOH,NA,CL`)
   - **ALL HETATMs**: Enter `ALL` to remove all non-protein residues
   - **Common residues**: Enter `COMMON` to remove water, ions, etc.
   - **Skip cleaning**: Enter `SKIP` to keep everything

5. **Analysis**: The system automatically:
   - Extracts binding site coordinates
   - Analyzes pocket properties
   - Generates reports

6. **Output**: Results are saved in a directory named after the PDB ID

### Example Interactive Session

```bash
$ python main.py interactive

🔬 PDB Prepare Wizard v2.1.0
========================================
Starting Interactive Mode...

Enter PDB ID: 7CMD
✓ PDB file downloaded: 7CMD.pdb

📋 Available HETATM types:
   1. TTT (1 instance(s))
   2. HOH (150 instance(s))
   3. NA (2 instance(s))

Select HETATM type (1-3): 1
✓ Selected: TTT in chain A, residue 601

Available chains: A, B
Select chains to keep (comma-separated, or 'all'): all
✓ Selected chains: A, B

📝 Cleaning Options:
   1. Remove specific residues (enter comma-separated list)
   2. Remove ALL HETATMs (enter 'ALL')
   3. Remove common residues only (enter 'COMMON')
   4. Skip cleaning (enter 'SKIP')

Enter cleaning choice: COMMON
✓ Removed: HOH (150), NA (2)

🔬 Analyzing binding site...
✓ Analysis complete!

Results saved in: 7CMD/
```

---

## 2. CLI Mode

**Best for:** Command-line users, processing multiple PDBs quickly, automation scripts

### Basic Usage

```bash
# Single PDB
python main.py cli -p 7CMD

# Multiple PDBs (comma-separated)
python main.py cli -p "7CMD,6WX4,1ABC"

# Specify output directory
python main.py cli -p "7CMD,6WX4" -o my_results/

# Use configuration file
python main.py cli -p 7CMD -c config.json
```

### Command-Line Options

```bash
python main.py cli --help

Options:
  -p, --pdb PDB_ID          PDB ID(s) - comma-separated or file path
  -o, --output OUTPUT_DIR   Output directory (default: current directory)
  -c, --config CONFIG_FILE  Configuration file (JSON)
  --ligand LIGAND_NAME      Specific ligand to extract (optional)
  --chain CHAIN_ID          Specific chain to keep (optional)
  --clean CLEAN_LIST        Residues to remove (comma-separated)
  --no-clean                Skip cleaning step
  --no-analysis             Skip analysis step
  --excel                   Generate Excel report (if multiple PDBs)
```

### Examples

#### Example 1: Single PDB with Auto-Selection

```bash
python main.py cli -p 7CMD
```

This will:
- Download 7CMD.pdb
- Auto-select the first non-common ligand
- Use default cleaning (common residues)
- Perform analysis
- Save results in `7CMD/`

#### Example 2: Multiple PDBs with Custom Output

```bash
python main.py cli -p "7CMD,6WX4,1ABC" -o batch_results/
```

This will:
- Process all three PDBs sequentially
- Save results in `batch_results/`
- Generate Excel summary report

#### Example 3: Specific Ligand Selection

```bash
python main.py cli -p 7CMD --ligand TTT --chain A
```

This will:
- Extract only the TTT ligand from chain A
- Skip other ligands

#### Example 4: Custom Cleaning

```bash
python main.py cli -p 7CMD --clean "HOH,NA,CL,SO4"
```

This will:
- Remove only specified residues
- Keep all other HETATMs

#### Example 5: Using Configuration File

Create `config.json`:
```json
{
  "ligand_selection": {
    "7cmd": "TTT",
    "6wx4": "LIG"
  },
  "cleaning": {
    "default": "common",
    "7cmd": ["HOH", "NA", "CL"]
  },
  "analysis": {
    "use_enhanced_coordinates": true,
    "distance_cutoff": 5.0
  }
}
```

Run:
```bash
python main.py cli -p "7CMD,6WX4" -c config.json
```

---

## 3. Batch Mode

**Best for:** Processing many PDBs, reproducible workflows, production pipelines

### Configuration File Formats

Batch mode supports two configuration formats:

#### YAML Format (Recommended)

Create `pdb_batch_config.yaml`:

```yaml
# Global settings applied to all PDB entries
global_settings:
  output_directory: "batch_docking_preparation"
  
  # Default cleaning strategy
  cleaning:
    strategy: "common"  # Options: "all", "common", "none", or list
    common_residues: ["HOH", "NA", "CL", "SO4", "CA", "MG", "ZN", "FE", "CU", "MN"]
  
  # Active site analysis settings
  analysis:
    use_enhanced_coordinates: true
    distance_cutoff: 5.0
    method: "plip"  # Options: "plip", "distance"
  
  # AutoDock preparation settings
  autodock:
    force_field: "AMBER"
    ph: 7.4
    allow_bad_res: true
    default_altloc: "A"

# List of PDB entries to process
pdb_entries:
  - pdb_id: "7CMD"
    ligand_selection:
      ligand_name: "TTT"
      # chain_id: "A"  # Optional
      # res_id: 601    # Optional
    cleaning:
      # Override global cleaning for this PDB
      strategy: ["HOH", "NA", "CL"]
    analysis:
      use_enhanced_coordinates: true
    autodock:
      prepare_as: "ligand"  # Options: "ligand", "receptor", "both"
  
  - pdb_id: "6WX4"
    ligand_selection:
      ligand_name: "LIG"
    cleaning:
      strategy: "common"
    autodock:
      prepare_as: "receptor"

# Processing options
processing:
  continue_on_error: true
```

#### TXT Format (Simple)

Create `pdb_batch_config.txt`:

```txt
# PDB Batch Processing Configuration (TXT Format)
# Format: PDBID|LIGAND|CLEANING_STRATEGY|PREPARE_AS
# 
# PDBID: 4-character PDB identifier
# LIGAND: Specific ligand to extract (or AUTO for auto-selection)
# CLEANING_STRATEGY: all, common, none, or comma-separated list
# PREPARE_AS: ligand, receptor, both

7CMD|TTT|common|ligand
6WX4|LIG|common|receptor
1ABC|AUTO|none|both
```

### Running Batch Processing

```bash
# Using YAML configuration
python main.py batch -c pdb_batch_config.yaml

# Using TXT configuration
python main.py batch -c pdb_batch_config.txt

# Custom output directory
python main.py batch -c pdb_batch_config.yaml -o custom_output/
```

### Batch Processing Output

```
batch_docking_preparation/
├── 7CMD/
│   ├── 7CMD.pdb
│   ├── cleaned.pdb
│   ├── ligand_TTT_A_601.pdb
│   ├── 7CMD_pipeline_results.csv
│   └── ...
├── 6WX4/
│   ├── 6WX4.pdb
│   ├── cleaned.pdb
│   └── ...
├── batch_processing_results.csv
└── batch_processing_results.xlsx
```

---

## 4. Python API Usage

**Best for:** Custom workflows, integration with other tools, programmatic control

### Basic Example

```python
from core_pipeline import MolecularDockingPipeline

# Initialize pipeline
pipeline = MolecularDockingPipeline(output_dir="my_analysis")

# Download PDB file
pdb_file = pipeline.fetch_pdb("7CMD")

# Enumerate HETATMs (ligands)
hetatm_details, unique_hetatms = pipeline.enumerate_hetatms(pdb_file)
print(f"Found {len(unique_hetatms)} unique ligand types")

# Extract specific ligand
ligand_pdb = pipeline.save_hetatm_as_pdb(pdb_file, "TTT", "A", 601)

# Clean structure
cleaned_pdb = pipeline.clean_pdb(
    pdb_file, 
    to_remove_list=['HOH', 'NA', 'CL']
)

# Analyze binding site
from core_pipeline import extract_residue_level_coordinates

residue_analysis = extract_residue_level_coordinates(
    cleaned_pdb, "TTT", "A", 601
)

if residue_analysis:
    coords = residue_analysis['overall_center']
    print(f"Binding site center: {coords}")
    
    # Analyze pocket properties
    pocket_results = pipeline.analyze_pocket_properties(cleaned_pdb, coords)
    print(f"Druggability score: {pocket_results['druggability_score']}")
```

### Complete Pipeline Example

```python
from core_pipeline import MolecularDockingPipeline

# Initialize with custom settings
pipeline = MolecularDockingPipeline(
    output_dir="custom_analysis",
    use_plip=True  # Enable PLIP analysis
)

# Run complete pipeline
results = pipeline.run_complete_pipeline(
    pdb_id="7CMD",
    ligand_name="TTT",
    chain_id="A",
    res_id=601,
    cleaning_list=['HOH', 'NA', 'CL'],
    interactive=False
)

# Access results
print(f"Binding site center: {results['active_site_center']}")
print(f"Pocket volume: {results['pocket_volume']} Å³")
print(f"Druggability score: {results['druggability_score']}")
```

### Advanced Example with Multiple PDBs

```python
from core_pipeline import MolecularDockingPipeline
import pandas as pd

pdb_list = ["7CMD", "6WX4", "1ABC"]
results_list = []

pipeline = MolecularDockingPipeline()

for pdb_id in pdb_list:
    try:
        # Download and process
        pdb_file = pipeline.fetch_pdb(pdb_id)
        hetatm_details, unique_hetatms = pipeline.enumerate_hetatms(pdb_file)
        
        # Auto-select first non-common ligand
        ligand_name = None
        for resname, chain_id, res_id, _ in hetatm_details:
            if resname not in ['HOH', 'NA', 'CL', 'SO4']:
                ligand_name = resname
                break
        
        if ligand_name:
            # Clean and analyze
            cleaned = pipeline.clean_pdb(pdb_file, to_remove_list=['HOH', 'NA', 'CL'])
            analysis = extract_residue_level_coordinates(cleaned, ligand_name, chain_id, res_id)
            
            results_list.append({
                'PDB_ID': pdb_id,
                'Ligand': ligand_name,
                'Binding_Site_X': analysis['overall_center'][0],
                'Binding_Site_Y': analysis['overall_center'][1],
                'Binding_Site_Z': analysis['overall_center'][2],
            })
    except Exception as e:
        print(f"Error processing {pdb_id}: {e}")

# Create summary DataFrame
df = pd.DataFrame(results_list)
df.to_csv("multi_pdb_summary.csv", index=False)
print(df)
```

---

## 📊 Output Files

All modes generate similar output files:

```
{PDB_ID}/
├── {PDB_ID}.pdb                    # Original downloaded PDB
├── ligand_{LIGAND}_{CHAIN}_{RESID}.pdb  # Extracted ligand
├── cleaned.pdb                      # Cleaned structure
├── chain_filtered.pdb               # Chain-filtered structure (if applicable)
├── {PDB_ID}_pipeline_results.csv    # Analysis results
└── multi_pdb_analysis.xlsx          # Excel report (if multiple PDBs)
```

### CSV Report Columns

- `PDB_ID`: PDB identifier
- `Selected_Ligand`: Extracted ligand name
- `Active_Site_Center_X/Y/Z`: Binding site coordinates
- `Interacting_Atoms_Count`: Number of interacting atoms
- `Pocket_Volume_A3`: Estimated pocket volume
- `Electrostatic_Score`: Electrostatic potential score
- `Hydrophobic_Score`: Hydrophobic character score
- `Druggability_Score`: Druggability prediction (0-1 scale)

---

## 🔧 Advanced Options

### PLIP Integration

Enable PLIP for advanced interaction analysis:

```python
from core_pipeline import MolecularDockingPipeline

pipeline = MolecularDockingPipeline(use_plip=True)
# PLIP will be used automatically for binding site detection
```

### Enhanced Coordinate Extraction

Use residue-level coordinate extraction:

```python
from core_pipeline import extract_residue_level_coordinates

analysis = extract_residue_level_coordinates(
    pdb_file="cleaned.pdb",
    ligand_name="TTT",
    chain_id="A",
    res_id=601
)

# Access individual residue coordinates
for residue, coords in analysis['residue_averages'].items():
    print(f"{residue}: {coords}")

# Overall binding site center
center = analysis['overall_center']
```

### Chain Filtering

Select specific chains:

```python
# Keep only chain A
filtered_pdb = pipeline.filter_chains(pdb_file, chains=['A'])

# Keep multiple chains
filtered_pdb = pipeline.filter_chains(pdb_file, chains=['A', 'B'])
```

---

## 🐛 Troubleshooting

### Common Issues

1. **PDB Download Fails**
   ```bash
   # Check internet connection
   # Verify PDB ID exists: https://www.rcsb.org/
   ```

2. **No Ligands Found**
   ```bash
   # Some PDBs don't have ligands
   # Try a different PDB ID
   ```

3. **PLIP Not Working**
   ```bash
   # Install PLIP
   conda install -c conda-forge plip
   # Or disable PLIP: use method="distance" instead
   ```

4. **Memory Issues**
   ```bash
   # Process PDBs one at a time
   # Use smaller structures for testing
   ```

---

## 📚 Related Documentation

- [Installation Guide](INSTALLATION_GUIDE.md) - Setup instructions
- [AutoDock Preparation Guide](AUTODOCK_PREPARATION_GUIDE.md) - Preparing for docking
- [PLIP Interaction Types Guide](PLIP_INTERACTION_TYPES_GUIDE.md) - Understanding interactions

---

**Version**: 3.0.1  
**Last Updated**: 2025-01-15

