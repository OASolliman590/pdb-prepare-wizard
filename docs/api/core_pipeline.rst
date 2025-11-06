Core Pipeline
=============

The ``core_pipeline`` module provides the main pipeline class for processing
protein-ligand complexes.

.. automodule:: core_pipeline
   :members:
   :undoc-members:
   :show-inheritance:

ProteinLigandPipeline
---------------------

.. autoclass:: core_pipeline.ProteinLigandPipeline
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Main Methods
~~~~~~~~~~~~

run_full_pipeline
^^^^^^^^^^^^^^^^^

.. automethod:: core_pipeline.ProteinLigandPipeline.run_full_pipeline

download_pdb
^^^^^^^^^^^^

.. automethod:: core_pipeline.ProteinLigandPipeline.download_pdb

extract_ligand
^^^^^^^^^^^^^^

.. automethod:: core_pipeline.ProteinLigandPipeline.extract_ligand

prepare_for_docking
^^^^^^^^^^^^^^^^^^^

.. automethod:: core_pipeline.ProteinLigandPipeline.prepare_for_docking

analyze_pocket
^^^^^^^^^^^^^^

.. automethod:: core_pipeline.ProteinLigandPipeline.analyze_pocket

analyze_interactions
^^^^^^^^^^^^^^^^^^^^

.. automethod:: core_pipeline.ProteinLigandPipeline.analyze_interactions

generate_summary_report
^^^^^^^^^^^^^^^^^^^^^^^

.. automethod:: core_pipeline.ProteinLigandPipeline.generate_summary_report

Usage Example
-------------

Basic usage:

.. code-block:: python

   from core_pipeline import ProteinLigandPipeline

   # Initialize pipeline
   pipeline = ProteinLigandPipeline(output_dir="my_output")

   # Process structure
   results = pipeline.run_full_pipeline(
       pdb_id="7CMD",
       ligand_name="ATP",
       chain_id="A",
       res_id=500
   )

   # Access results
   print(f"Pocket center: {results['pocket_center']}")
   print(f"Druggability: {results['druggability_score']:.2f}")

   # Generate report
   pipeline.generate_summary_report(results, "7CMD")

With Configuration
------------------

Using custom configuration:

.. code-block:: python

   from core_pipeline import ProteinLigandPipeline
   from unified_config import PipelineConfig

   # Create configuration
   config = PipelineConfig()
   config.scientific.interaction_cutoff = 6.0
   config.output.visualization_dpi = 600

   # Initialize with config
   pipeline = ProteinLigandPipeline(
       output_dir="output",
       config=config
   )

   results = pipeline.run_full_pipeline(
       pdb_id="7CMD",
       ligand_name="ATP",
       chain_id="A",
       res_id=500
   )

Return Values
-------------

The ``run_full_pipeline`` method returns a dictionary containing:

Structure Information
~~~~~~~~~~~~~~~~~~~~~

- ``pdb_id``: PDB identifier
- ``ligand_name``: Ligand residue name
- ``chain_id``: Chain identifier
- ``res_id``: Residue ID

Pocket Properties
~~~~~~~~~~~~~~~~~

- ``pocket_center``: (x, y, z) coordinates of pocket center
- ``pocket_volume``: Estimated volume in Ų
- ``pocket_residues``: List of residue IDs
- ``n_pocket_residues``: Number of pocket residues

Druggability
~~~~~~~~~~~~

- ``druggability_score``: 0.0-1.0 score
- ``druggability_classification``: "Excellent", "Good", "Moderate", or "Poor"

Interactions
~~~~~~~~~~~~

- ``n_interactions``: Total interaction count
- ``hydrogen_bonds``: Number of H-bonds
- ``hydrophobic_contacts``: Number of hydrophobic interactions
- ``salt_bridges``: Number of salt bridges
- ``pi_stacking``: Number of π-stacking interactions
- ``interaction_residues``: List of interacting residues

File Paths
~~~~~~~~~~

- ``pdb_file``: Path to downloaded PDB
- ``ligand_pdb``: Path to extracted ligand
- ``ligand_pdbqt``: Path to PDBQT ligand
- ``protein_pdbqt``: Path to PDBQT protein

Error Handling
--------------

The pipeline raises specific exceptions for different error types:

.. code-block:: python

   from core_pipeline import ProteinLigandPipeline
   from exceptions import (
       PDBDownloadError,
       LigandNotFoundError,
       PocketAnalysisError
   )

   pipeline = ProteinLigandPipeline()

   try:
       results = pipeline.run_full_pipeline(
           pdb_id="INVALID",
           ligand_name="UNK",
           chain_id="Z",
           res_id=999
       )
   except PDBDownloadError as e:
       print(f"Download failed: {e}")
   except LigandNotFoundError as e:
       print(f"Ligand not found: {e}")
   except PocketAnalysisError as e:
       print(f"Analysis failed: {e}")

See Also
--------

- :doc:`../quickstart`: Quick start guide
- :doc:`../configuration`: Configuration options
- :doc:`exceptions`: Exception reference
- :doc:`unified_config`: Configuration API
