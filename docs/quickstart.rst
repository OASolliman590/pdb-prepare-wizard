Quick Start Guide
=================

This guide will help you get started with PDB Prepare Wizard in minutes.

Basic Workflow
--------------

The typical workflow involves:

1. **Download PDB structure** from RCSB
2. **Extract ligand** from the structure
3. **Prepare structures** for docking
4. **Analyze binding pocket** and interactions
5. **Generate reports** and visualizations

Example 1: Simple Analysis
---------------------------

Process a single PDB structure with known ligand:

.. code-block:: python

   from core_pipeline import ProteinLigandPipeline

   # Initialize pipeline
   pipeline = ProteinLigandPipeline(output_dir="output_7CMD")

   # Run analysis
   results = pipeline.run_full_pipeline(
       pdb_id="7CMD",
       ligand_name="ATP",
       chain_id="A",
       res_id=500
   )

   # Check results
   print(f"Binding pocket center: {results['pocket_center']}")
   print(f"Druggability score: {results['druggability_score']:.2f}")
   print(f"Number of interactions: {results['n_interactions']}")

Example 2: With Configuration
------------------------------

Use custom configuration for scientific parameters:

.. code-block:: python

   from core_pipeline import ProteinLigandPipeline
   from unified_config import PipelineConfig

   # Load configuration
   config = PipelineConfig.from_yaml("my_config.yaml")

   # Or create with overrides
   config = PipelineConfig()
   config.scientific.interaction_cutoff = 6.0
   config.scientific.pocket_radius = 12.0

   # Initialize pipeline with config
   pipeline = ProteinLigandPipeline(
       output_dir="output",
       config=config
   )

   # Run analysis
   results = pipeline.run_full_pipeline(
       pdb_id="1A2B",
       ligand_name="NAD",
       chain_id="A",
       res_id=300
   )

Example 3: Batch Processing
----------------------------

Process multiple PDB structures:

.. code-block:: python

   from batch_pdb_preparation import BatchProcessor

   # Define structures to process
   structures = [
       {"pdb_id": "7CMD", "ligand": "ATP", "chain": "A", "res_id": 500},
       {"pdb_id": "1ATP", "ligand": "ATP", "chain": "A", "res_id": 500},
       {"pdb_id": "2ATP", "ligand": "ATP", "chain": "A", "res_id": 500},
   ]

   # Initialize batch processor
   batch = BatchProcessor(output_dir="batch_output")

   # Process all structures
   results = batch.process_batch(structures, n_jobs=4)

   # Generate summary
   batch.generate_batch_summary(results)

Example 4: With Disk Space Checking
------------------------------------

Check disk space before processing:

.. code-block:: python

   from core_pipeline import ProteinLigandPipeline
   from disk_space_checker import check_disk_space
   from pathlib import Path

   output_dir = Path("output")

   # Check disk space
   disk_info = check_disk_space(
       output_dir=output_dir,
       n_pdb_files=10  # Processing 10 structures
   )

   print(f"Available space: {disk_info.free_mb:.1f} MB")

   # Proceed with pipeline
   pipeline = ProteinLigandPipeline(output_dir=str(output_dir))
   # ... process structures

Example 5: Optimized RMSD Analysis
-----------------------------------

Use optimized RMSD calculations for large datasets:

.. code-block:: python

   from rmsd_optimizer import CachedRMSDCalculator
   import numpy as np

   # Prepare pose data (example)
   n_poses = 100
   n_atoms = 50
   poses = [np.random.rand(n_atoms, 3) for _ in range(n_poses)]

   # Calculate RMSD matrix with caching
   calculator = CachedRMSDCalculator(cache_dir=".cache")
   rmsd_matrix = calculator.calculate_rmsd_optimized(
       poses_data=poses,
       use_cache=True,
       cache_key="my_protein_poses"
   )

   # Get memory statistics
   stats = rmsd_matrix.get_memory_usage()
   print(f"Memory saved: {stats['savings_percent']:.1f}%")

Command-Line Interface
----------------------

Run from command line:

.. code-block:: bash

   # Single structure
   python main.py --pdb 7CMD --ligand ATP --chain A --res-id 500

   # With custom output directory
   python main.py --pdb 7CMD --ligand ATP --chain A --res-id 500 \\
                  --output my_output

   # Batch processing
   python batch_pdb_preparation.py --input structures.txt --jobs 4

   # With verbose logging
   python main.py --pdb 7CMD --ligand ATP --chain A --res-id 500 --verbose

Output Files
------------

After running the pipeline, you'll find:

**Structure Files**
~~~~~~~~~~~~~~~~~~~

- ``{pdb_id}.pdb`` - Downloaded PDB structure
- ``{ligand_name}.pdb`` - Extracted ligand
- ``{ligand_name}.pdbqt`` - AutoDock-ready ligand
- ``protein.pdbqt`` - AutoDock-ready protein

**Analysis Reports**
~~~~~~~~~~~~~~~~~~~~

- ``{pdb_id}_analysis.csv`` - Detailed results
- ``{pdb_id}_analysis.xlsx`` - Excel format with metadata
- ``{pdb_id}_analysis.json`` - Machine-readable format
- ``{pdb_id}_metadata.json`` - Version and provenance info

**Visualizations**
~~~~~~~~~~~~~~~~~~

- ``{pdb_id}_pocket.png`` - Binding pocket visualization
- ``{pdb_id}_interactions.png`` - Interaction diagram
- ``{pdb_id}_structure.pse`` - PyMOL session (if available)

**Logs**
~~~~~~~~

- ``logs/pdb_prepare_wizard_*.log`` - Detailed execution logs

Understanding Results
---------------------

Key Metrics
~~~~~~~~~~~

**Pocket Properties:**

- ``pocket_center``: 3D coordinates of pocket center (Å)
- ``pocket_volume``: Estimated pocket volume (Å³)
- ``pocket_residues``: List of residues forming the pocket

**Druggability:**

- ``druggability_score``: 0.0-1.0 (higher = more druggable)
  - Excellent: > 0.7
  - Good: 0.5-0.7
  - Moderate: 0.3-0.5
  - Poor: < 0.3

**Interactions:**

- ``n_interactions``: Total number of interactions
- ``hydrogen_bonds``: Number of H-bonds
- ``hydrophobic_contacts``: Number of hydrophobic interactions
- ``salt_bridges``: Number of electrostatic interactions

Next Steps
----------

- :doc:`configuration`: Learn about configuration options
- :doc:`tutorials`: Follow detailed tutorials
- :doc:`api/core_pipeline`: Explore the API reference
- :doc:`contributing`: Contribute to the project
