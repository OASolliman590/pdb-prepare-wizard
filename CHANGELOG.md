# Changelog

All notable changes to PDB Prepare Wizard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2025-01-15

### Major PLIP Integration
- **🆕 Advanced PLIP Integration**: Research-grade protein-ligand interaction analysis
  - **Text-based PLIP parsing**: Reliable interaction detection using PLIP's official report format
  - **Comprehensive interaction types**: All PLIP interaction types supported
    - Hydrophobic interactions
    - Hydrogen bonds
    - Halogen bonds
    - π-stacking interactions
    - Water bridges
    - Salt bridges (configuration ready)
    - Metal complexes (configuration ready)
    - π-cation interactions (configuration ready)
  - **Perfect PLIP web server match**: Results exactly match the official PLIP web server
  - **Future-proof design**: Automatically detects unknown interaction types
  - **Robust error handling**: Graceful fallback to distance-based methods

### Enhanced Analysis
- **🆕 PLIP-Enhanced Coordinate Extraction**: Advanced binding site analysis
  - **Comprehensive interaction detection**: Uses PLIP's sophisticated algorithms
  - **Detailed interaction breakdowns**: Residue-level analysis with interaction type classification
  - **Enhanced accuracy**: Research-grade results matching PLIP web server
  - **Automatic fallback**: Distance-based method when PLIP is unavailable

### Documentation
- **🆕 PLIP Interaction Types Guide**: Comprehensive documentation of all PLIP interaction types
- **🆕 Future-proofing documentation**: Guide for handling new interaction types
- **🆕 Enhanced README**: Updated with PLIP integration features

## [2.1.0] - 2025-01-15

### Major Restructuring
- **🔄 Modular Architecture**: Complete codebase reorganization to eliminate duplication
  - **Consolidated Core Pipeline**: `core_pipeline.py` - Unified core functionality
  - **Interactive Mode**: `interactive_pipeline.py` - User-friendly interactive interface
  - **CLI Mode**: `cli_pipeline.py` - Command-line interface with configuration support
  - **Main Entry Point**: `main.py` - Unified entry point for all modes
  - **Batch Processing**: Enhanced `batch_pdb_preparation.py` with residue-level analysis

### Added
- **🆕 Enhanced Coordinate Extraction**: Residue-level binding site analysis
  - **Residue-Level Analysis**: `extract_residue_level_coordinates()` function
  - **Individual Residue Averages**: Calculate average coordinates for each interacting residue
  - **Comprehensive Binding Site Data**: Overall center, residue details, and atom counts
  - **Excel Integration**: Enhanced Excel reporting with residue-level data
- **🆕 Post-Docking Analysis Module**: Comprehensive analysis of molecular docking results
  - **Binding Affinity Analysis**: Parse and analyze Vina/GNINA docking results from PDBQT files
  - **Best Pose Selection**: Automatically identify highest binding affinity poses using `idxmin()`
  - **PDB Extraction**: Extract best poses as complete receptor-ligand complex PDB files
  - **Statistical Analysis**: Generate comprehensive statistics and rankings
  - **Multi-format Visualization**: Binding affinity distributions and top performer plots
  - **Comprehensive Reporting**: CSV, Excel, and text summary reports
  - **Open Babel Integration**: For ligand processing and PDBQT to PDB conversion
  - **Flexible Input Detection**: Auto-detects single-folder or multi-folder directory structures
  - **Command-line Interface**: Full CLI with configuration file support
  - **Python API**: Programmatic access to all analysis functions
- **🆕 CLI Configuration System**: JSON-based configuration for automated processing
  - **Ligand Selection**: Specify target ligands per PDB
  - **Cleaning Strategies**: Define cleaning approaches per PDB or globally
  - **Analysis Options**: Configure analysis parameters
  - **Sample Config Generation**: `--create-config` option

### Improved
- **📈 Better Error Handling**: Improved error messages and graceful failure handling
- **🚀 Performance**: Optimized coordinate extraction algorithms
- **📊 Enhanced Reporting**: More detailed Excel reports with residue-level data
- **🔧 Batch Processing**: Fixed PLIP dependencies and improved reliability

### Fixed
- **❌ PLIP Dependency Issues**: Replaced unreliable PLIP calls with robust distance-based analysis
- **🔄 Code Duplication**: Eliminated duplication between PDP_prep.py and PDP_prep_improved.py
- **📝 Batch Processing**: Fixed coordinate extraction errors in batch_pdb_preparation.py

### Removed
- **Old Files**: Removed `PDP_prep.py` and `PDP_prep_improved.py` (replaced by modular structure)

### Dependencies
- **Added Open Babel**: Required for post-docking analysis ligand processing

### Migration Guide
- **From 2.0.0 to 2.1.0**:
  - Update imports: `from core_pipeline import MolecularDockingPipeline`
  - Use new entry points: `python main.py` instead of `python PDP_prep_improved.py`
  - CLI users: Use `python main.py cli` with new configuration options
  - Batch users: Updated `batch_pdb_preparation.py` with enhanced coordinate extraction

## [2.0.0] - 2024-12-19

### Added
- **Multi-PDB Analysis**: Analyze multiple PDB structures in a single session
- **Excel Integration**: Generate comprehensive Excel reports with all results
- **Enhanced HETATM Enumeration**: Grouped display with counts and smart selection
- **Smart Cleaning Options**: 
  - Remove ALL HETATMs at once
  - Remove water only (`WATER`)
  - Remove ions only (`IONS`)
  - Remove common residues only (`COMMON`)
- **Removal Summary**: Shows exactly what will be removed before confirmation
- **Warning System**: Alerts when removing selected ligand
- **Smart Fallback**: Uses original structure if ligand was removed during cleaning
- **Professional Excel Reports**: Formatted output with headers and styling
- **Comprehensive Documentation**: README, contributing guide, and feature docs

### Changed
- **Improved User Experience**: Better prompts and error handling
- **Enhanced Error Handling**: Graceful handling of failed PDBs
- **Better Progress Feedback**: Real-time status updates
- **Flexible Exit Options**: Can quit anytime with 'quit' command

### Fixed
- **Ligand Detection**: Proper handling when ligand is removed during cleaning
- **Active Site Analysis**: Fallback to original structure when needed
- **HETATM Selection**: Grouped display prevents confusion with many similar residues
- **Cleaning Workflow**: Warning system prevents accidental ligand removal

### Technical
- **Type Hints**: Comprehensive type annotations throughout
- **Error Validation**: Better input validation and error messages
- **Dependency Management**: Updated requirements and environment files
- **Code Organization**: Modular design with clear separation of concerns

## [1.0.0] - 2024-12-19

### Added
- **Core Pipeline**: Basic PDB download and processing
- **Ligand Extraction**: Identify and extract HETATM residues
- **Structure Cleaning**: Remove water molecules and ions
- **Active Site Analysis**: Extract binding site coordinates
- **Pocket Analysis**: Electrostatic and hydrophobic analysis
- **Druggability Scoring**: Predict drug binding potential
- **CSV Reports**: Generate detailed analysis reports
- **Interactive Mode**: User-friendly command-line interface

### Features
- PDB file download from RCSB PDB database
- Chain filtering and selection
- HETATM enumeration and selection
- Structure cleaning with customizable residue removal
- Distance-based interaction detection
- Pocket property analysis (electrostatic, hydrophobic, volume)
- Druggability scoring algorithm
- Comprehensive CSV reporting

## [Unreleased]

### Planned
- **Visualization**: 3D structure visualization capabilities
- **Docking Integration**: Direct integration with AutoDock/Vina
- **Batch Processing**: Command-line batch processing mode
- **API Mode**: Programmatic API for integration
- **Web Interface**: Web-based user interface
- **Advanced Analysis**: More sophisticated pocket analysis methods
- **Machine Learning**: ML-based druggability prediction
- **Cloud Support**: Cloud-based processing capabilities

---

## Version History

- **2.0.0**: Major release with multi-PDB analysis and Excel integration
- **1.0.0**: Initial release with core functionality

## Migration Guide

### From 1.0.0 to 2.0.0
- **Backward Compatible**: All existing functionality preserved
- **New Features**: Multi-PDB analysis and Excel integration added
- **Enhanced UX**: Improved HETATM enumeration and cleaning options
- **Better Error Handling**: More robust error handling and warnings

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 