PDB Prepare Wizard Documentation
=================================

Welcome to PDB Prepare Wizard's documentation! This pipeline automates the preparation
of protein-ligand complexes for molecular docking studies.

.. image:: https://img.shields.io/badge/version-3.1.0-blue.svg
   :target: https://github.com/yourusername/pdb-prepare-wizard
   :alt: Version

.. image:: https://img.shields.io/badge/python-3.8+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python Version

.. image:: https://img.shields.io/badge/license-MIT-green.svg
   :target: LICENSE
   :alt: License

Features
--------

- **Automated PDB Download**: Fetches protein structures from RCSB PDB with retry logic
- **Ligand Extraction**: Identifies and extracts ligands from protein structures
- **Structure Preparation**: Converts structures to AutoDock-compatible formats
- **Pocket Analysis**: Analyzes binding pockets and druggability
- **Interaction Analysis**: Identifies protein-ligand interactions (PLIP integration)
- **RMSD Analysis**: Calculates structural similarity with optimized algorithms
- **Comprehensive Reports**: Generates CSV, Excel, and JSON reports with metadata
- **Visualization**: Creates 3D visualizations with PyMOL and matplotlib plots

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   # Clone repository
   git clone https://github.com/yourusername/pdb-prepare-wizard.git
   cd pdb-prepare-wizard

   # Install with all optional dependencies
   pip install -e .[all]

   # Or minimal installation
   pip install -e .

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from core_pipeline import ProteinLigandPipeline

   # Initialize pipeline
   pipeline = ProteinLigandPipeline(output_dir="my_output")

   # Process a PDB structure
   results = pipeline.run_full_pipeline(
       pdb_id="7CMD",
       ligand_name="ATP",
       chain_id="A",
       res_id=500
   )

   # Generate reports
   pipeline.generate_summary_report(results, "7CMD")

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   configuration
   tutorials
   faq

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/core_pipeline
   api/file_validators
   api/security_utils
   api/logging_config
   api/version_tracker
   api/exceptions
   api/disk_space_checker
   api/unified_config
   api/rmsd_optimizer

.. toctree::
   :maxdepth: 2
   :caption: Development

   contributing
   testing
   changelog
   roadmap

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
