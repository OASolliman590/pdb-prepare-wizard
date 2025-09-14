# PDB Prepare Wizard - Molecular Docking Pipeline v3.0

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Conda](https://img.shields.io/badge/conda-forge-blue.svg)](https://conda-forge.org/)
[![Biopython](https://img.shields.io/badge/Biopython-1.79+-green.svg)](https://biopython.org/)

A comprehensive tool for preparing PDB files for molecular docking studies with advanced PLIP integration. This pipeline provides automated analysis of protein-ligand complexes, comprehensive interaction analysis, and druggability predictions with research-grade accuracy matching the official PLIP web server.

## 🚀 Features

### Core Functionality
- **PDB Download**: Automatically fetch PDB files from RCSB PDB database
- **Ligand Extraction**: Identify and extract HETATM residues (ligands) from structures
  - **Grouped Display**: HETATMs grouped by type with counts
  - **Smart Selection**: Choose by type, then specific instance
- **Chain Management**: Filter and select specific protein chains
- **Structure Cleaning**: Remove water molecules, ions, and other unwanted residues
  - **Smart Cleaning Options**: Remove specific residues, ALL HETATMs, or common residues only
  - **Removal Summary**: Shows exactly what will be removed before confirmation

### Enhanced Analysis (v3.0)
- **🆕 Advanced PLIP Integration**: Research-grade protein-ligand interaction analysis
  - **Text-based PLIP parsing**: Reliable interaction detection using PLIP's official report format
  - **Comprehensive interaction types**: Hydrophobic, hydrogen bonds, halogen bonds, π-stacking, water bridges, salt bridges, metal complexes, π-cation interactions
  - **Perfect PLIP web server match**: Results exactly match the official PLIP web server
  - **Future-proof design**: Automatically detects unknown interaction types
- **🆕 Residue-Level Coordinate Extraction**: Enhanced `extract_residue_level_coordinates()` function
  - Individual residue averages for detailed binding site analysis
  - Overall binding site center calculation
  - Comprehensive statistics (residue count, atom count)
  - PLIP-enhanced interaction detection with detailed breakdowns
- **Active Site Analysis**: Extract binding site coordinates using PLIP-enhanced or distance-based methods
- **Pocket Analysis**: Comprehensive analysis of pocket properties including:
  - Electrostatic potential
  - Hydrophobic character
  - Pocket volume estimation
  - Druggability scoring

### Multiple Interface Options (v2.1.0)
- **🆕 Interactive Mode**: User-friendly interactive pipeline with guided prompts
- **🆕 CLI Mode**: Command-line interface with configuration file support
- **🆕 Batch Processing**: Enhanced batch processing with configuration-driven automation
- **🆕 Unified Entry Point**: Single `main.py` entry point for all modes

### Reporting & Analysis
- **Multi-PDB Analysis**: Analyze multiple PDB structures in a single session
- **Excel Integration**: Generate comprehensive Excel reports with all results
- **Report Generation**: Generate detailed CSV and Excel reports with all analysis results
- **🆕 Post-Docking Analysis**: Comprehensive analysis of molecular docking results
  - **Binding Affinity Analysis**: Parse and analyze Vina/GNINA docking results
  - **Best Pose Selection**: Automatically identify highest binding affinity poses
  - **PDB Extraction**: Extract best poses as complete receptor-ligand complex PDB files
  - **Statistical Analysis**: Generate comprehensive statistics and rankings
  - **Visualization**: Create binding affinity distributions and top performer plots
  - **Multi-format Reports**: CSV, Excel, and text summary reports

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
- **Post-Docking Analysis**: openbabel (for ligand processing and PDBQT conversion)
- **Development**: jupyter

## 🛠️ Installation

### Option 1: Using Conda (Recommended)

```bash
# Create and activate conda environment
conda env create -f environment.yml
conda activate pdb-prepare-wizard

# Install the package
pip install -e .

# Verify installation
python main.py --help
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

### Main Entry Point (v2.1.0)

```bash
# Interactive mode (default) - User-friendly guided interface
python main.py
python main.py interactive

# CLI mode for batch processing with configuration support
python main.py cli -p 7CMD
python main.py cli -p "7CMD,6WX4,1ABC" -o results/
python main.py cli -p 7CMD -c config.json

# Or use the installed commands (after pip install -e .)
pdb-prepare-wizard                    # Main entry point
pdb-wizard-interactive               # Interactive mode only
pdb-wizard-cli -p 7CMD               # CLI mode only
pdb-wizard-batch                     # Batch processing only
```

### Python API Usage

```python
from core_pipeline import MolecularDockingPipeline, extract_residue_level_coordinates

# Initialize pipeline
pipeline = MolecularDockingPipeline(output_dir="my_analysis")

# Download and process PDB
pdb_file = pipeline.fetch_pdb("1ABC")
hetatm_details, unique_hetatms = pipeline.enumerate_hetatms(pdb_file)

# Extract specific ligand
ligand_pdb = pipeline.save_hetatm_as_pdb(pdb_file, "LIG", "A", 1)

# Clean structure
cleaned_pdb = pipeline.clean_pdb(pdb_file, to_remove_list=['HOH', 'NA', 'CL'])

# Analyze binding site with enhanced coordinates
residue_analysis = extract_residue_level_coordinates(cleaned_pdb, "LIG", "A", 1)
if residue_analysis:
    coords = residue_analysis['overall_center']
    pocket_results = pipeline.analyze_pocket_properties(cleaned_pdb, coords)
```

### CLI Configuration (v2.1.0)

Create a configuration file for automated processing:

```bash
# Generate sample config
python cli_pipeline.py --create-config

# Use configuration file
python main.py cli -p "7CMD,6WX4" -c config.json
```

Example configuration:
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

### Advanced Usage - Residue-Level Analysis (v2.1.0)

The new version includes enhanced coordinate extraction at the residue level:

```python
from core_pipeline import MolecularDockingPipeline, extract_residue_level_coordinates

# Initialize pipeline
pipeline = MolecularDockingPipeline()

# Process PDB
pdb_file = pipeline.fetch_pdb("1ABC")
hetatm_details, unique_hetatms = pipeline.enumerate_hetatms(pdb_file)
cleaned_pdb = pipeline.clean_pdb(pdb_file, to_remove_list=['HOH', 'NA', 'CL'])

# Enhanced residue-level coordinate extraction
residue_analysis = extract_residue_level_coordinates(cleaned_pdb, "LIG", "A", 1)

if residue_analysis:
    print(f"Binding site center: {residue_analysis['overall_center']}")
    print(f"Interacting residues: {residue_analysis['num_interacting_residues']}")
    print(f"Total atoms: {residue_analysis['num_interacting_atoms']}")
    
    # Individual residue averages
    for residue, coord in residue_analysis['residue_averages'].items():
        print(f"  {residue}: {coord}")
    
    # Analyze pocket properties
    pocket_results = pipeline.analyze_pocket_properties(
        cleaned_pdb, residue_analysis['overall_center']
    )
```

### Post-Docking Analysis Usage

The post-docking analysis module provides comprehensive analysis of molecular docking results from AutoDock Vina or GNINA.

#### Command Line Usage

```bash
# Basic usage - analyze docking results in a directory
python -m post_docking_analysis -i /path/to/docking/results -o /path/to/output

# With verbose output
python -m post_docking_analysis -i /path/to/docking/results -o /path/to/output -v

# Skip visualizations (faster processing)
python -m post_docking_analysis -i /path/to/docking/results --no-visualizations

# Use configuration file
python -m post_docking_analysis --config my_config.json
```

#### Python API Usage

```python
from post_docking_analysis.pipeline import PostDockingAnalysisPipeline

# Initialize pipeline
pipeline = PostDockingAnalysisPipeline(
    input_dir="/path/to/docking/results",
    output_dir="/path/to/output"
)

# Run complete analysis
success = pipeline.run_pipeline()

# Access results
if success:
    best_poses = pipeline.results['best_poses']
    print(f"Best binding affinity: {best_poses['vina_affinity'].min():.2f} kcal/mol")
```

#### Expected Input Structure

The pipeline automatically detects and processes docking results in the following formats:

```
docking_results/
├── complex_1/
│   ├── ligand_vina_out.pdbqt    # Vina docking results
│   ├── ligand.sdf               # Ligand structure
│   └── complex_1.pdb            # Optional: receptor structure
├── complex_2/
│   ├── ligand_vina_out.pdbqt
│   └── ligand.sdf
└── receptors/                   # Optional: shared receptor files
    └── receptor.pdbqt
```

#### Output Structure

```
output_directory/
├── reports/                     # Analysis reports
│   ├── best_poses.csv          # Best pose for each complex
│   ├── full_data.csv           # All poses with scores
│   ├── summary_stats.csv       # Statistical summaries
│   ├── docking_analysis_results.xlsx  # Comprehensive Excel report
│   └── summary_report.txt      # Human-readable summary
├── visualizations/              # Generated plots
│   ├── binding_affinity_distribution.png
│   └── top_performers.png
└── best_poses_pdb/             # Best poses as PDB files
    ├── complex_1_pose1.pdb
    ├── complex_2_pose1.pdb
    └── ...
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

**Version**: 2.1.0  
**Last Updated**: 2024  
**Python Compatibility**: 3.8+

## 🔄 Migration from v2.0.0

If you're upgrading from v2.0.0, see the [Reorganization Summary](REORGANIZATION_SUMMARY.md) for details on the new architecture and migration guide. 