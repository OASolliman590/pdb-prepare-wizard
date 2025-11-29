# Post-Docking Analysis System - Complete Guide

## Overview

The Post-Docking Analysis System is a comprehensive tool for analyzing molecular docking results from both AutoDock Vina and GNINA docking programs. This system provides advanced analysis capabilities including binding affinity analysis, RMSD analysis, pose clustering, automated visualization, and comparative benchmarking.

## 🚀 Quick Start

### Installation

```bash
# Install as part of PDB Prepare Wizard package
cd /path/to/pdb-prepare-wizard
pip install -e .

# Or install dependencies separately
pip install -r post_docking_analysis/requirements.txt

# Optional: Install visualization tools
conda install -c conda-forge pymol pandamap openbabel
```

### Basic Usage

```bash
# Analyze docking results with default settings
python -m post_docking_analysis -i /path/to/docking/results -o /path/to/output

# GNINA Fast Path (recommended)
# If your project has gnina_out/all_scores.csv, the pipeline automatically uses streamlined processing
python -m post_docking_analysis -i /path/to/project

# Use configuration file
python -m post_docking_analysis --config my_config.yaml
```

## 📁 Input Data Structure

### For GNINA Results (Recommended)

```
docking_results/
├── gnina_out/
│   ├── all_scores.csv          # Auto-generated if missing
│   ├── complex1_top.sdf
│   ├── complex2_top.sdf
│   └── *.log                   # GNINA log files
├── receptors/
│   ├── receptor1.pdbqt
│   ├── receptor2.pdbqt
│   └── ...
└── pairlist.csv                # Optional: receptor-ligand mappings
```

### For Vina Results

```
docking_results/
├── complex1/
│   ├── receptor.pdbqt
│   ├── ligand.sdf
│   └── docking_output.pdbqt
├── complex2/
│   ├── receptor.pdbqt
│   ├── ligand.sdf
│   └── docking_output.pdbqt
└── ...
```

## ⚙️ Configuration

The system uses YAML configuration files for flexible control. A sample configuration is provided in `post_docking_analysis/config/sample_config.yaml`.

### Configuration Options

```yaml
# Analysis Parameters
analysis:
  docking_types: [vina, gnina]      # Which docking types to analyze
  comparative_benchmark: "*"        # "*" for all, or specific targets
  binding_affinity_analysis: true
  rmsd_analysis: true
  generate_visualizations: true
  extract_poses: true

# Input/Output Directories
paths:
  input_dir: ""
  output_dir: "./post_docking_results"
  receptors_dir: ""
  gnina_out_dir: ""

# Pose Extraction
pose_extraction:
  extract_all_poses: false
  best_pose_criteria: "affinity"
  output_formats: [pdb]

# Binding Affinity Analysis
binding_affinity:
  strong_binder_threshold: "auto"   # "auto", "comparative", or numeric value
  top_performers_count: 10
  analyze_by_protein: true
  analyze_by_ligand: true

# RMSD Analysis
rmsd:
  clustering_method: "kmeans"      # "kmeans" or "dbscan"
  kmeans_clusters: 3
  dbscan_epsilon: 2.0
  dbscan_min_samples: 2

# Visualization
visualization:
  output_formats: [png]
  dpi: 300
  generate_3d: true
  generate_2d_interactions: true

# Advanced Options
advanced:
  fix_chains: false
  directory_structure: "AUTO"      # "AUTO", "SINGLE_FOLDER", "MULTI_FOLDER"
  enable_plugins: true
  log_level: "INFO"
```

## 📊 Output Structure

```
post_docking_results/
├── best_poses/                    # Best poses organized by complex
│   ├── complex_1/
│   ├── complex_2/
│   ├── strong_binders/
│   ├── moderate_binders/
│   └── weak_binders/
├── reports/                       # Analysis reports
│   ├── best_affinities.csv
│   ├── affinity_summary.csv
│   ├── top_performers.csv
│   ├── best_per_protein.csv
│   ├── best_per_ligand.csv
│   ├── pose_summary.csv
│   └── summary_report.txt
├── visualizations/                # 2D visualizations
│   ├── binding_affinity_distribution.png
│   ├── top_10_performers.png
│   ├── vina_cnn_comparison.png
│   └── ...
├── pymol_visualizations/          # 3D PyMOL sessions
│   ├── comparative_analysis.pse
│   └── ...
├── pandamap_analysis/             # 2D/3D interaction maps
│   └── ...
└── post_docking_analysis.log      # Detailed log file
```

## 🔧 Command-Line Options

### Basic Options
- `-i, --input DIR`: Input directory containing docking results
- `-o, --output DIR`: Output directory for results
- `--config FILE`: Configuration file path
- `-v, --verbose`: Enable verbose output

### Processing Options
- `--no-visualizations`: Skip visualization generation
- `--no-analysis`: Skip binding affinity analysis
- `--no-reports`: Skip report generation
- `--fix-chains`: Fix chain issues in structures

### Help
- `-h, --help`: Show help message
- `--version`: Show version information

## 💻 Programmatic Usage

```python
from post_docking_analysis.pipeline import PostDockingAnalysisPipeline

# Initialize pipeline
pipeline = PostDockingAnalysisPipeline(
    input_dir="/path/to/docking/results",
    output_dir="/path/to/output",
    config_file="/path/to/config.yaml"
)

# Run complete analysis
success = pipeline.run_pipeline()

# Access results
if success:
    best_poses = pipeline.results['best_poses']
    print(f"Best binding affinity: {best_poses['vina_affinity'].min():.2f} kcal/mol")
```

## 🎯 Key Features

### 1. Binding Affinity Analysis
- Identify top-performing compounds based on binding affinity
- Comparative benchmarking against specified targets
- Dynamic threshold calculation ("auto" mode)
- Categorization as strong, moderate, or weak binders
- Protein and ligand breakdown analysis

### 2. Pose Extraction and Organization
- Extract best poses into centralized folders
- Organize by binding affinity categories
- Support for multiple output formats (PDB, SDF, MOL2)
- Automatic complex reconstruction from receptor + ligand

### 3. RMSD Analysis
- Pose clustering using K-means or DBSCAN
- Conformational diversity analysis
- Comparative benchmarking integration
- Pose similarity matrices

### 4. Visualization
- Automated 2D visualizations (binding affinity distributions, heatmaps)
- 3D visualizations with PyMOL
- 2D interaction maps with PandaMap
- Customizable output formats and DPI

### 5. Automatic Data Preparation
- Auto-generates `all_scores.csv` from GNINA log files
- Uses `pairlist.csv` for accurate receptor-ligand mapping
- Handles missing files gracefully

### 6. Plugin System
- Extensible architecture for custom analysis modules
- Built-in example plugins (binding mode, enrichment)
- Easy integration of new analysis methods

## 📋 Pairlist Integration

The system leverages `pairlist.csv` for accurate receptor-ligand mapping:

```csv
receptor,site_id,ligand,center_x,center_y,center_z,size_x,size_y,size_z
4TRO_INHA_prep,catalytic,4TRO_INHA_NAD,0.075,-32.509,15.694,20,20,20
3LN1_COX2_prep,catalytic,3LN1_COX2_CEL,27.9222,-24.2043,-14.4593,20,20,20
```

Benefits:
- Accurate complex naming
- Consistent tag names across analyses
- Eliminates filename pattern matching errors
- Better data organization

## 🔄 Dynamic Strong Binder Threshold

Three options for determining strong binders:

1. **"auto"** (default): Automatically calculates threshold based on data distribution
2. **"comparative"**: Uses average binding affinity of comparative benchmark
3. **Numeric value**: Fixed threshold (e.g., -8.0 kcal/mol)

## 🛠️ Preprocessing

The system can automatically prepare your data:

```bash
# Preprocess GNINA results (generate all_scores.csv, identify pairs)
python -m post_docking_analysis.preprocess /path/to/docking/results

# Force regeneration
python -m post_docking_analysis.preprocess /path/to/docking/results --force

# Use pairlist.csv
python -m post_docking_analysis.preprocess /path/to/docking/results --pairlist /path/to/pairlist.csv
```

## 📚 Examples

### Example 1: Basic GNINA Analysis

```bash
python -m post_docking_analysis -i ./gnina_results -o ./analysis_output
```

### Example 2: Custom Configuration

```bash
# Create custom config
cp post_docking_analysis/config/sample_config.yaml my_config.yaml

# Edit my_config.yaml, then run
python -m post_docking_analysis --config my_config.yaml -i ./data -o ./results
```

### Example 3: Python API

```python
from post_docking_analysis.pipeline import PostDockingAnalysisPipeline

config = {
    "analysis": {
        "docking_types": ["gnina"],
        "comparative_benchmark": "COX2",
        "binding_affinity_analysis": True
    },
    "binding_affinity": {
        "strong_binder_threshold": -9.0,
        "top_performers_count": 20
    }
}

pipeline = PostDockingAnalysisPipeline(
    input_dir="/path/to/data",
    output_dir="/path/to/results"
)
pipeline.config.update(config)
success = pipeline.run_pipeline()
```

## 🐛 Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install -r post_docking_analysis/requirements.txt
   conda install -c conda-forge pymol pandamap openbabel
   ```

2. **File Not Found Errors**
   - Check input directory structure matches expected format
   - Verify file paths in configuration
   - Ensure `all_scores.csv` exists or can be auto-generated

3. **Memory Issues**
   - Reduce number of complexes being analyzed
   - Set `extract_all_poses: false` to analyze only best poses
   - Process in smaller batches

### Logging

Detailed logs are generated in the output directory:
- `post_docking_analysis.log` - Main log file with analysis progress
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## 🔌 Extending the System

### Creating Custom Plugins

1. Create plugin file in `post_docking_analysis/plugins/`:

```python
PLUGIN_NAME = "My Custom Analyzer"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Description of my plugin"

def analyze(data: dict, output_dir: Path, config: dict) -> dict:
    # Your analysis code here
    results = {
        "plugin": PLUGIN_NAME,
        "status": "completed",
        "results": []
    }
    return results
```

2. Enable in configuration:
```yaml
advanced:
  enable_plugins: true
  plugin_directories: ["./plugins"]
```

## 📖 Requirements

- Python 3.8+
- Pandas, NumPy
- Matplotlib, Seaborn
- Scikit-learn
- PyYAML
- Open Babel (for pose extraction)
- PyMOL (optional, for 3D visualizations)
- PandaMap (optional, for interaction analysis)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Version**: 3.0.0  
**Last Updated**: 2025-01-15  
**Compatibility**: Python 3.8+, AutoDock Vina, GNINA

