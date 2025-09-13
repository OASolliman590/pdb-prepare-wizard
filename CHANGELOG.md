# Changelog

All notable changes to PDB Prepare Wizard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-01-XX

### Added
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

### Dependencies
- **Added Open Babel**: Required for post-docking analysis ligand processing

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