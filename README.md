# PDB Prepare Wizard - Molecular Docking Pipeline

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Conda](https://img.shields.io/badge/conda-forge-blue.svg)](https://conda-forge.org/)
[![Biopython](https://img.shields.io/badge/Biopython-1.79+-green.svg)](https://biopython.org/)

A comprehensive tool for preparing PDB files for molecular docking studies. This pipeline provides automated analysis of protein-ligand complexes, pocket properties, and druggability predictions.

## 🚀 Features

- **PDB Download**: Automatically fetch PDB files from RCSB PDB database
- **Ligand Extraction**: Identify and extract HETATM residues (ligands) from structures
  - **Grouped Display**: HETATMs grouped by type with counts
  - **Smart Selection**: Choose by type, then specific instance
- **Chain Management**: Filter and select specific protein chains
- **Structure Cleaning**: Remove water molecules, ions, and other unwanted residues
  - **Smart Cleaning Options**: Remove specific residues, ALL HETATMs, or common residues only
  - **Removal Summary**: Shows exactly what will be removed before confirmation
- **Active Site Analysis**: Extract binding site coordinates using distance-based or PLIP methods
- **Pocket Analysis**: Comprehensive analysis of pocket properties including:
  - Electrostatic potential
  - Hydrophobic character
  - Pocket volume estimation
  - Druggability scoring
- **Multi-PDB Analysis**: Analyze multiple PDB structures in a single session
- **Excel Integration**: Generate comprehensive Excel reports with all results
- **Report Generation**: Generate detailed CSV and Excel reports with all analysis results

## 📋 Requirements

### System Requirements
- Python 3.8 or higher
- Internet connection (for PDB downloads)
- 2GB+ RAM recommended for large structures

### Dependencies
- **Core**: numpy, pandas, biopython
- **Optional**: plip (for advanced interaction analysis)
- **Visualization**: matplotlib, seaborn
- **Excel Support**: openpyxl (for Excel report generation)
- **Development**: jupyter

## 🛠️ Installation

### Option 1: Using Conda (Recommended)

```bash
# Create and activate conda environment
conda env create -f environment.yml
conda activate pdb-prepare-wizard

# Verify installation
python PDP_prep_improved.py
```

### Option 2: Using pip

```bash
# Create virtual environment
python -m venv pdb-wizard-env
source pdb-wizard-env/bin/activate  # On Windows: pdb-wizard-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Option 3: Manual Installation

```bash
# Install core dependencies
pip install numpy pandas biopython

# Install optional PLIP for advanced analysis
pip install plip

# Install visualization tools
pip install matplotlib seaborn

# Install Excel support
pip install openpyxl
```

## 🎯 Usage

### Basic Usage

```python
from PDP_prep_improved import MolecularDockingPipeline

# Initialize pipeline
pipeline = MolecularDockingPipeline(output_dir="my_analysis")

# Run complete pipeline
results = pipeline.run_complete_pipeline("1ABC", interactive=True)
```

### Command Line Usage

```bash
# Run interactively (single PDB)
python PDP_prep_improved.py

# Multi-PDB analysis with Excel output
python PDP_prep_improved.py
# Then choose 'y' for multiple PDBs

# Or use the installed command
pdb-prepare-wizard
```

### Step-by-Step Usage

```python
# 1. Initialize pipeline
pipeline = MolecularDockingPipeline()

# 2. Download PDB file
pdb_file = pipeline.fetch_pdb("1ABC")

# 3. Enumerate available ligands
hetatm_details, unique_hetatms = pipeline.enumerate_hetatms(pdb_file)

# 4. Extract specific ligand
ligand_pdb = pipeline.save_hetatm_as_pdb(pdb_file, "LIG", "A", 1)

# 5. Clean structure
cleaned_pdb = pipeline.clean_pdb(pdb_file, to_remove_list=['HOH', 'NA', 'CL'])

# 6. Analyze pocket
coords, num_atoms = pipeline.extract_active_site_coords(cleaned_pdb, "LIG", "A", 1)
pocket_results = pipeline.analyze_pocket_properties(cleaned_pdb, coords)

# 7. Generate report
pipeline.generate_summary_report(pocket_results, "1ABC")
```

## 📊 Output Files

The pipeline generates several output files:

- `{PDB_ID}.pdb`: Original downloaded PDB file
- `ligand_{LIGAND}_{CHAIN}_{RESID}.pdb`: Extracted ligand structure
- `cleaned.pdb`: Structure with unwanted residues removed
- `chain_filtered.pdb`: Structure with selected chains only
- `{PDB_ID}_pipeline_results.csv`: Individual PDB analysis report
- `multi_pdb_analysis.xlsx`: **Comprehensive Excel report** (when analyzing multiple PDBs)

## 🔬 Analysis Methods

### Active Site Detection
- **Distance-based**: Uses 5Å cutoff to identify interacting residues
- **PLIP-based**: Uses PLIP library for advanced interaction analysis (if available)

### Pocket Analysis
- **Electrostatic Analysis**: Calculates charge distribution around binding site
- **Hydrophobic Analysis**: Identifies hydrophobic residues within 8Å of pocket center
- **Volume Estimation**: Estimates pocket volume based on interaction sphere
- **Druggability Scoring**: Combines multiple factors to predict druggability (0-1 scale)

## 📈 Example Results

```
📋 Pipeline Summary:
----------------------------------------
PDB_ID                    : 1ABC
Selected_Ligand           : LIG_A_1
Active_Site_Center_X      : 12.345
Active_Site_Center_Y      : 23.456
Active_Site_Center_Z      : 34.567
Interacting_Atoms_Count   : 156
Pocket_Volume_A3          : 523.6
Electrostatic_Score       : 2.5
Nearby_Charged_Residues   : 8
Hydrophobic_Score         : 6
Nearby_Hydrophobic_Residues: 12
Druggability_Score        : 0.85
```

## 🧪 Testing

### Test with Example PDB

```python
# Test with a well-known structure
pipeline = MolecularDockingPipeline()
results = pipeline.run_complete_pipeline("1ABC", interactive=False)
```

### Validation

The pipeline includes several validation steps:
- PDB ID format validation
- File existence checks
- Dependency availability checks
- Error handling for missing ligands

## 🔧 Troubleshooting

### Common Issues

1. **PLIP Installation Issues**
   ```bash
   # Try installing from conda-forge
   conda install -c conda-forge plip
   ```

2. **PDB Download Failures**
   - Check internet connection
   - Verify PDB ID exists in database
   - Try alternative PDB IDs

3. **Memory Issues**
   - Use smaller structures for testing
   - Close other applications
   - Consider using cloud resources for large structures

### Error Messages

- `❌ Error importing Biopython`: Install biopython with `pip install biopython`
- `❌ Missing dependency`: Install missing package from requirements.txt
- `❌ Could not find HETATM`: Structure may not contain ligands

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Quick Start for Contributors

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/pdb-prepare-wizard.git
cd pdb-prepare-wizard

# Set up development environment
conda env create -f environment.yml
conda activate pdb-prepare-wizard
pip install -e .

# Run tests
python test_pipeline.py
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Biopython team for the excellent structural biology library
- PLIP developers for protein-ligand interaction analysis
- RCSB PDB for providing structural data

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review error messages carefully
3. Try with different PDB structures
4. Open an issue with detailed error information

## 📚 Documentation

- [Enhanced Features](ENHANCED_FEATURES.md) - Multi-PDB analysis and Excel integration
- [Cleaning Features](CLEANING_FEATURES.md) - Smart cleaning options and removal summary
- [Setup Summary](SETUP_SUMMARY.md) - Complete setup and testing guide
- [Changelog](CHANGELOG.md) - Version history and changes

---

**Version**: 2.0.0  
**Last Updated**: 2024  
**Python Compatibility**: 3.8+ 