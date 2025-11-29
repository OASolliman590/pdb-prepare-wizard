# PDB Prepare Wizard v2.1.0 - Installation & Usage Guide

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd pdb-prepare-wizard

# Create conda environment
conda env create -f environment.yml
conda activate pdb-prepare-wizard

# Install the package
pip install -e .
```

### 2. Verify Installation

```bash
# Test main entry point
python main.py --help

# Test CLI mode
python cli_pipeline.py --help

# Test interactive mode (will prompt for PDB ID)
python main.py interactive
```

## 📋 Detailed Installation

### Prerequisites

- Python 3.8 or higher
- Internet connection (for PDB downloads)
- 2GB+ RAM recommended

### Option 1: Conda Installation (Recommended)

```bash
# Create environment from YAML file
conda env create -f environment.yml
conda activate pdb-prepare-wizard

# Install the package in development mode
pip install -e .

# Verify all dependencies
python -c "import numpy, pandas, Bio, openpyxl; print('All dependencies available')"
```

### Option 2: Manual Installation

```bash
# Create virtual environment
python -m venv pdb-wizard-env
source pdb-wizard-env/bin/activate  # On Windows: pdb-wizard-env\Scripts\activate

# Install core dependencies
pip install numpy>=1.21.0 pandas>=1.3.0 biopython>=1.79

# Install optional dependencies
pip install openpyxl>=3.0.0 matplotlib>=3.5.0 seaborn>=0.11.0

# Install PLIP for advanced analysis (optional)
pip install plip>=2.2.0

# Install the package
pip install -e .
```

### Option 3: Development Installation

```bash
# Clone repository
git clone <repository-url>
cd pdb-prepare-wizard

# Create development environment
conda create -n pdb-wizard-dev python=3.9
conda activate pdb-wizard-dev

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Run tests
python test_pipeline.py
```

## 🎯 Usage Modes

### 1. Interactive Mode (Recommended for Beginners)

```bash
# Start interactive mode
python main.py
# or
python main.py interactive

# Follow the prompts:
# 1. Enter output directory
# 2. Choose single or multi-PDB analysis
# 3. Enter PDB ID(s)
# 4. Select ligands interactively
# 5. Choose cleaning options
# 6. Review results
```

**Example Interactive Session:**
```
🔬 PDB Prepare Wizard v2.1.0
==================================================
Starting Interactive Mode...
Enter output directory (default: pipeline_output): my_analysis
✓ Pipeline initialized. Output directory: my_analysis
Do you want to analyze multiple PDBs? (default: n): n
Enter PDB ID (e.g., 1ABC): 7CMD
🔄 Fetching PDB 7CMD...
✓ Downloaded: my_analysis/7CMD.pdb
📋 Available HETATM types:
   1. TTT (1 instance(s))
   2. HOH (45 instance(s))
   3. NA (2 instance(s))
Select HETATM type (1-3): 1
✓ Selected: TTT in chain A, residue 1
📝 Cleaning Options:
   1. Remove specific residues (enter comma-separated list)
   2. Remove ALL HETATMs (enter 'ALL')
   3. Remove common residues only (enter 'COMMON')
   4. Skip cleaning (enter 'SKIP')
Enter your choice (1-4, comma-separated list, ALL, COMMON, or SKIP): COMMON
✓ Cleaned PDB saved as: my_analysis/cleaned.pdb
🔄 Extracting residue-level binding site coordinates for TTT...
✓ Found 12 interacting residues
✓ Total interacting atoms: 89
✓ Binding site center: X=12.34, Y=23.45, Z=34.56
✅ Analysis completed successfully for PDB 7CMD!
```

### 2. CLI Mode (Recommended for Batch Processing)

```bash
# Single PDB analysis
python main.py cli -p 7CMD

# Multiple PDBs
python main.py cli -p "7CMD,6WX4,1ABC"

# With custom output directory
python main.py cli -p 7CMD -o results/

# With configuration file
python main.py cli -p "7CMD,6WX4" -c config.json

# Generate sample configuration
python cli_pipeline.py --create-config
```

### 3. Batch Processing Mode

```bash
# Run batch processing script
python batch_pdb_preparation.py

# This will process predefined PDBs with enhanced coordinate extraction
```

### 4. Python API Usage

```python
from core_pipeline import MolecularDockingPipeline, extract_residue_level_coordinates

# Initialize pipeline
pipeline = MolecularDockingPipeline(output_dir="my_analysis")

# Download PDB
pdb_file = pipeline.fetch_pdb("7CMD")

# Enumerate HETATMs
hetatm_details, unique_hetatms = pipeline.enumerate_hetatms(pdb_file)

# Save specific ligand
ligand_pdb = pipeline.save_hetatm_as_pdb(pdb_file, "TTT", "A", 1)

# Clean structure
cleaned_pdb = pipeline.clean_pdb(pdb_file, to_remove_list=['HOH', 'NA', 'CL'])

# Enhanced coordinate extraction
residue_analysis = extract_residue_level_coordinates(cleaned_pdb, "TTT", "A", 1)

if residue_analysis:
    print(f"Binding site center: {residue_analysis['overall_center']}")
    print(f"Interacting residues: {residue_analysis['num_interacting_residues']}")
    
    # Analyze pocket properties
    pocket_results = pipeline.analyze_pocket_properties(
        cleaned_pdb, residue_analysis['overall_center']
    )
```

## ⚙️ Configuration Files

### Creating Configuration Files

```bash
# Generate sample configuration
python cli_pipeline.py --create-config
```

This creates `sample_config.json`:

```json
{
  "description": "Sample configuration for PDB Prepare Wizard CLI",
  "ligand_selection": {
    "7cmd": "TTT",
    "6wx4": "LIG",
    "1abc": "GDP"
  },
  "cleaning": {
    "default": "common",
    "7cmd": ["HOH", "NA", "CL"],
    "custom_pdb": "all"
  },
  "analysis": {
    "use_enhanced_coordinates": true,
    "distance_cutoff": 5.0
  }
}
```

### Configuration Options

- **ligand_selection**: Specify target ligands per PDB ID
- **cleaning**: Define cleaning strategies (default, PDB-specific, or custom)
- **analysis**: Control analysis parameters (enhanced coordinates, distance cutoff)

## 📊 Output Files

### Standard Output Structure

```
output_directory/
├── {PDB_ID}.pdb                    # Original downloaded PDB
├── ligand_{LIGAND}_{CHAIN}_{RESID}.pdb  # Extracted ligand
├── cleaned.pdb                     # Cleaned structure
├── {PDB_ID}_pipeline_results.csv   # Individual analysis report
└── multi_pdb_analysis.xlsx         # Multi-PDB Excel report (if applicable)
```

### Enhanced Coordinate Analysis Output

When using enhanced coordinate extraction, additional files are generated:

```
output_directory/
├── {PDB_ID}_{LIGAND}_residues.xlsx  # Residue-level coordinate analysis
└── plip_coordinates.xlsx            # Comprehensive coordinate data
```

## 🔧 Troubleshooting

### Common Installation Issues

1. **PLIP Installation Problems**
   ```bash
   # Try conda installation
   conda install -c conda-forge plip
   
   # Or skip PLIP (distance-based analysis will be used)
   pip install -r requirements.txt --no-deps plip
   ```

2. **Biopython Import Errors**
   ```bash
   # Reinstall biopython
   pip uninstall biopython
   pip install biopython>=1.79
   ```

3. **Excel Support Issues**
   ```bash
   # Install openpyxl
   pip install openpyxl>=3.0.0
   ```

### Runtime Issues

1. **PDB Download Failures**
   - Check internet connection
   - Verify PDB ID exists
   - Try alternative PDB IDs

2. **Memory Issues**
   - Use smaller structures for testing
   - Close other applications
   - Consider cloud resources for large structures

3. **Import Errors**
   ```bash
   # Verify installation
   python -c "from core_pipeline import MolecularDockingPipeline; print('Import successful')"
   ```

## 🧪 Testing Installation

### Basic Functionality Test

```bash
# Test core functionality
python -c "
from core_pipeline import MolecularDockingPipeline
pipeline = MolecularDockingPipeline()
print('✓ Core pipeline initialized successfully')
"

# Test enhanced coordinate extraction
python -c "
from core_pipeline import extract_residue_level_coordinates
print('✓ Enhanced coordinate extraction available')
"
```

### Full Pipeline Test

```bash
# Test with a simple PDB
python main.py cli -p 1ABC -o test_output

# Check if output files were created
ls test_output/
```

## 📚 Next Steps

1. **Read the Documentation**: Check [README.md](README.md) for detailed feature descriptions
2. **Try Interactive Mode**: Start with `python main.py` for guided usage
3. **Create Configuration**: Use `python cli_pipeline.py --create-config` for batch processing
4. **Explore Examples**: Look at `batch_pdb_preparation.py` for advanced usage patterns

## 🆘 Getting Help

- Check the [troubleshooting section](#troubleshooting) above
- Review error messages carefully
- Try with different PDB structures
- Open an issue with detailed error information

---

**Version**: 2.1.0  
**Last Updated**: 2024  
**Python Compatibility**: 3.8+
