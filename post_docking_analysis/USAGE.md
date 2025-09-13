# Post-Docking Analysis Pipeline - Usage Guide

## Installation

The post-docking analysis pipeline is part of the PDB Prepare Wizard package. To install:

```bash
# Navigate to the pdb-prepare-wizard directory
cd /path/to/pdb-prepare-wizard

# Install in development mode
pip install -e .
```

## Quick Start

### Basic Usage

Run the pipeline with default settings:

```bash
python -m post_docking_analysis
```

### Specify Input and Output Directories

```bash
python -m post_docking_analysis -i /path/to/docking/results -o /path/to/output
```

### Use a Configuration File

Create a JSON configuration file (see example below) and run:

```bash
python -m post_docking_analysis --config my_config.json
```

## Command-Line Options

### Input/Output Options
- `-i, --input DIR` : Input directory containing docking results
- `-o, --output DIR` : Output directory for results
- `--config FILE` : Configuration file path

### Processing Options
- `--no-split` : Skip complex splitting step
- `--no-apo` : Skip apo protein extraction
- `--no-ligands` : Skip ligand extraction
- `--no-analysis` : Skip binding affinity analysis
- `--no-visualizations` : Skip visualization generation
- `--no-reports` : Skip report generation
- `--fix-chains` : Fix chain issues in structures

### Directory Structure
- `--structure {auto,single,multi}` : Directory structure type

### Scoring Options
- `--no-cnn` : Disable CNN scoring

### Output Format Options
- `--no-csv` : Disable CSV output
- `--no-excel` : Disable Excel output
- `--no-pdb` : Disable PDB output
- `--no-mol2` : Disable MOL2 output

### Help and Info
- `-v, --verbose` : Enable verbose output
- `--version` : Show version information
- `-h, --help` : Show help message

## Configuration File

Create a JSON configuration file to customize the pipeline behavior:

```json
{
  "input_dir": "/path/to/docking/results",
  "output_dir": "./my_analysis_results",
  "split_complexes": true,
  "extract_apo_proteins": true,
  "extract_ligands": true,
  "analyze_binding_affinity": true,
  "generate_visualizations": true,
  "create_summary_reports": true,
  "output_csv": true,
  "output_excel": true,
  "output_pdb": true,
  "output_mol2": true,
  "fix_chains": false,
  "run_additional_docking": false,
  "use_vina_score": true,
  "use_cnn_score": true,
  "directory_structure": "AUTO",
  "receptor_pattern": "*receptor*.pdb",
  "ligand_pattern": "*ligand*.sdf",
  "docking_result_pattern": "*out*.pdbqt"
}
```

## Examples

### Analyze a Single Directory of Results

```bash
python -m post_docking_analysis -i ./sample_data -o ./results
```

### Process Without Visualizations

```bash
python -m post_docking_analysis -i ./sample_data --no-visualizations
```

### Use Multi-Folder Structure

```bash
python -m post_docking_analysis -i ./complexes --structure multi
```

### Generate Only Reports

```bash
python -m post_docking_analysis -i ./sample_data --no-split --no-apo --no-ligands --no-visualizations
```

## Output Structure

The pipeline generates the following output structure:

```
output_directory/
├── split_complexes/          # Split receptor-ligand complexes
├── apo_proteins/             # Extracted apo proteins
├── ligands_mol2/             # Extracted ligands in MOL2 format
├── reports/                  # Summary reports
│   ├── best_poses.csv        # Best poses for each complex
│   ├── summary_stats.csv     # Statistical summaries
│   ├── top_overall.csv       # Top performing complexes
│   ├── best_per_protein.csv  # Best performers by protein
│   ├── best_per_ligand.csv   # Best performers by ligand
│   ├── docking_analysis_results.xlsx  # Comprehensive Excel report
│   └── summary_report.txt    # Text summary of key findings
├── visualizations/           # Generated plots and charts
│   ├── binding_affinity_distribution.png
│   ├── top_performers.png
│   └── vina_cnn_comparison.png
└── pipeline.log              # Pipeline execution log
```

## Supported File Formats

### Input Formats
- PDBQT: Docking result files
- PDB: Protein structure files
- SDF: Ligand structure files

### Output Formats
- CSV: Tabular data files
- Excel (XLSX): Spreadsheet files
- PDB: Protein structure files
- MOL2: Ligand structure files
- PNG: Visualization images
- TXT: Summary reports
- JSON: Structured data files

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   - Ensure all required packages are installed
   - Install Open Babel for ligand processing
   - Install openpyxl for Excel output

2. **File Not Found Errors**
   - Check that input directory exists and contains docking results
   - Verify file naming conventions match expected patterns

3. **Memory Issues**
   - Process smaller datasets first
   - Disable unnecessary steps (visualizations, reports)
   - Increase system memory if possible

### Error Messages

- `⚠️ Open Babel not available`: Install Open Babel for ligand processing
- `⚠️ openpyxl not available`: Install openpyxl for Excel output
- `❌ Input directory does not exist`: Verify input directory path
- `⚠️ Configuration file not found`: Check configuration file path

## Customization

The pipeline can be customized by:

1. Modifying the configuration file
2. Extending the pipeline modules
3. Adding custom analysis functions
4. Implementing new output formats

For advanced customization, refer to the source code in the `post_docking_analysis` directory.