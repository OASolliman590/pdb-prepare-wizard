Changelog
=========

All notable changes to this project are documented here.

Version 3.1.0 (2025-11-06)
--------------------------

Added
~~~~~

**Phase 3: Performance & Configuration**

- **RMSD Optimizer** (``rmsd_optimizer.py``)
  - Triangular matrix storage (51% memory savings)
  - Pickle-based caching system
  - Incremental update capability
  - Memory usage statistics

- **Unified Configuration** (``unified_config.py``)
  - YAML-based configuration management
  - Six configuration categories (Network, Scientific, Clustering, Output, Logging, Performance)
  - Configuration validation and merging
  - Dot-notation parameter access
  - Configuration profiles

- **Disk Space Checker** (``disk_space_checker.py``)
  - Pre-execution space validation
  - Space requirement estimation
  - Runtime monitoring
  - Cleanup suggestions

**Phase 4: Infrastructure**

- **CI/CD Pipeline** (``.github/workflows/``)
  - Multi-platform testing (Linux, macOS, Windows)
  - Multi-version Python testing (3.8-3.11)
  - Code quality checks (Black, Flake8, MyPy)
  - Security scanning (Bandit, Safety)
  - Documentation building and deployment

- **Comprehensive Documentation** (``docs/``)
  - Sphinx-based documentation
  - Installation guide
  - Quick start guide
  - Configuration guide
  - Tutorials
  - Complete API reference
  - FAQ
  - Contributing guide

Version 3.0.0 (2025-11-05)
--------------------------

Added
~~~~~

**Phase 1: Critical Fixes**

- **Network Retry Logic**
  - Exponential backoff (2s, 4s, 8s, 16s)
  - Configurable max retries
  - Timeout handling

- **File Validation System** (``file_validators.py``)
  - Magic number verification
  - Structure validation
  - MD5/SHA256 checksums
  - Support for PDB, PDBQT, SDF, MOL2

- **Security Utilities** (``security_utils.py``)
  - PDB ID validation (regex)
  - Command injection prevention
  - Path traversal protection
  - Filename sanitization

- **Reproducibility**
  - Random seed configuration
  - Numpy seed control
  - Scikit-learn seed control

- **Dependency Management**
  - Separated requirements files
  - Optional dependencies
  - Development dependencies
  - setup.py extras_require

- **Test Suite** (``tests/``)
  - pytest infrastructure
  - 100+ security tests
  - File validation tests
  - Shared fixtures
  - Coverage reporting

**Phase 2: Error Handling & Logging**

- **Custom Exceptions** (``exceptions.py``)
  - 9-category exception hierarchy
  - Context preservation
  - Specific error types (PDBDownloadError, LigandNotFoundError, etc.)
  - Centralized error logging

- **Logging System** (``logging_config.py``)
  - Colored console output (ANSI codes)
  - Unicode symbols (✓, ⚠️, ❌, 🔥)
  - Dual console/file output
  - Progress tracking with step numbers
  - LogTimer context manager
  - Structured sections

- **Version Tracking** (``version_tracker.py``)
  - Pipeline version capture
  - Python version tracking
  - Dependency version logging
  - Git commit hash tracking
  - System information capture
  - Metadata JSON generation

Changed
~~~~~~~

- **Core Pipeline** (``core_pipeline.py``)
  - Integrated logging system
  - Added exception handling
  - Version metadata in reports
  - Improved error messages

- **Configuration** (``post_docking_analysis/config.py``)
  - Added reproducibility seeds
  - Parameter documentation

- **RMSD Analyzer** (``post_docking_analysis/rmsd_analyzer.py``)
  - Integrated seed configuration
  - Reproducible clustering

Fixed
~~~~~

- Network timeout handling
- File validation edge cases
- Command injection vulnerabilities
- Path traversal vulnerabilities
- Memory leaks in batch processing
- Inconsistent logging

Version 2.0.0 (Historical)
--------------------------

Added
~~~~~

- PandaMap visualization integration
- PyMOL visualization support
- Post-docking analysis modules
- RMSD analysis
- Clustering capabilities
- Druggability scoring

Version 1.0.0 (Historical)
--------------------------

Initial Release
~~~~~~~~~~~~~~~

- Basic PDB download
- Ligand extraction
- PDBQT conversion
- Binding pocket analysis
- Interaction detection
- CSV report generation
