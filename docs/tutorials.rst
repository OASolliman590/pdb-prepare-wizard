Tutorials
=========

Step-by-step tutorials for common use cases.

Tutorial 1: Basic Protein-Ligand Analysis
------------------------------------------

Analyze a single protein-ligand complex from RCSB PDB.

**Goal**: Analyze ATP binding in protein kinase (PDB: 7CMD)

Step 1: Import and Setup
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from core_pipeline import ProteinLigandPipeline
   from logging_config import setup_logger

   # Setup logging
   logger = setup_logger(level="INFO")

   # Initialize pipeline
   pipeline = ProteinLigandPipeline(output_dir="tutorial1_output")

Step 2: Run Analysis
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Run full pipeline
   results = pipeline.run_full_pipeline(
       pdb_id="7CMD",
       ligand_name="ATP",
       chain_id="A",
       res_id=500
   )

Step 3: Examine Results
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Print key results
   print(f"Pocket center: {results['pocket_center']}")
   print(f"Druggability: {results['druggability_score']:.2f}")
   print(f"Classification: {results['druggability_classification']}")
   print(f"Interactions: {results['n_interactions']}")

Step 4: Generate Reports
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Generate comprehensive report
   pipeline.generate_summary_report(results, "7CMD")

   # Check output files
   import os
   print("Output files:")
   for f in os.listdir("tutorial1_output"):
       print(f"  {f}")

Tutorial 2: Batch Processing
-----------------------------

Process multiple structures efficiently.

**Goal**: Analyze 10 kinase structures with ATP

Step 1: Define Structures
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   structures = [
       {"pdb_id": "7CMD", "ligand": "ATP", "chain": "A", "res_id": 500},
       {"pdb_id": "1ATP", "ligand": "ATP", "chain": "A", "res_id": 500},
       {"pdb_id": "2ATP", "ligand": "ATP", "chain": "A", "res_id": 500},
       # ... more structures
   ]

Step 2: Configure Parallelization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from unified_config import PipelineConfig

   config = PipelineConfig()
   config.performance.enable_parallel = True
   config.performance.n_jobs = 4

Step 3: Process Batch
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from core_pipeline import ProteinLigandPipeline

   results_list = []
   for struct in structures:
       try:
           pipeline = ProteinLigandPipeline(
               output_dir=f"batch_output/{struct['pdb_id']}",
               config=config
           )
           results = pipeline.run_full_pipeline(**struct)
           results_list.append(results)
       except Exception as e:
           print(f"Failed {struct['pdb_id']}: {e}")
           continue

Step 4: Compare Results
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pandas as pd

   # Create comparison DataFrame
   comparison = pd.DataFrame([
       {
           'pdb_id': r.get('pdb_id'),
           'druggability': r.get('druggability_score'),
           'interactions': r.get('n_interactions'),
           'h_bonds': r.get('hydrogen_bonds', 0)
       }
       for r in results_list
   ])

   print(comparison.sort_values('druggability', ascending=False))

Tutorial 3: Custom Configuration
---------------------------------

Customize scientific parameters for your specific needs.

**Goal**: Analyze with larger pocket radius and custom cutoffs

Step 1: Create Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from unified_config import PipelineConfig

   config = PipelineConfig()

   # Customize scientific parameters
   config.scientific.pocket_radius = 15.0  # Larger pocket
   config.scientific.interaction_cutoff = 6.0  # Longer range
   config.scientific.clash_cutoff = 1.5  # Stricter clashes

   # Customize output
   config.output.visualization_dpi = 600  # High resolution
   config.output.generate_excel = True

   # Save configuration
   config.to_yaml("custom_config.yaml")

Step 2: Use Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Load configuration
   config = PipelineConfig.from_yaml("custom_config.yaml")

   # Initialize with config
   pipeline = ProteinLigandPipeline(
       output_dir="custom_output",
       config=config
   )

Step 3: Run Analysis
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   results = pipeline.run_full_pipeline(
       pdb_id="7CMD",
       ligand_name="ATP",
       chain_id="A",
       res_id=500
   )

Tutorial 4: Optimized RMSD Analysis
------------------------------------

Use optimized RMSD calculations for large conformational ensembles.

**Goal**: Analyze 100 protein conformations efficiently

Step 1: Prepare Data
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import numpy as np
   from Bio.PDB import PDBParser

   # Load multiple conformations
   parser = PDBParser(QUIET=True)
   conformations = []

   for i in range(100):
       structure = parser.get_structure(f'conf_{i}', f'conf_{i}.pdb')
       coords = []
       for atom in structure.get_atoms():
           coords.append(atom.coord)
       conformations.append(np.array(coords))

Step 2: Calculate RMSD Matrix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from rmsd_optimizer import CachedRMSDCalculator

   calculator = CachedRMSDCalculator(cache_dir=".cache")

   rmsd_matrix = calculator.calculate_rmsd_optimized(
       poses_data=conformations,
       use_cache=True,
       cache_key="my_protein_ensemble"
   )

Step 3: Check Performance
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get memory statistics
   stats = rmsd_matrix.get_memory_usage()
   print(f"Memory used: {stats['triangular_mb']:.1f} MB")
   print(f"Memory saved: {stats['savings_mb']:.1f} MB ({stats['savings_percent']:.1f}%)")

Step 4: Access RMSD Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get RMSD between conformations
   rmsd_0_50 = rmsd_matrix.get(0, 50)
   print(f"RMSD between conf 0 and 50: {rmsd_0_50:.2f} Å")

   # Convert to full matrix for analysis
   full_matrix = rmsd_matrix.to_full_matrix()
   print(f"Matrix shape: {full_matrix.shape}")

Tutorial 5: Error Handling
---------------------------

Handle errors gracefully in production workflows.

**Goal**: Robust pipeline with proper error handling

Step 1: Import Exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from core_pipeline import ProteinLigandPipeline
   from exceptions import (
       PDBDownloadError,
       LigandNotFoundError,
       InsufficientDiskSpaceError,
       PipelineError
   )

Step 2: Implement Error Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def safe_analysis(pdb_id, ligand_name, chain_id, res_id):
       try:
           pipeline = ProteinLigandPipeline()
           results = pipeline.run_full_pipeline(
               pdb_id=pdb_id,
               ligand_name=ligand_name,
               chain_id=chain_id,
               res_id=res_id
           )
           return results, None

       except PDBDownloadError as e:
           return None, f"Download failed: {e}"

       except LigandNotFoundError as e:
           return None, f"Ligand not found: {e}"

       except InsufficientDiskSpaceError as e:
           return None, f"Disk full: {e}"

       except PipelineError as e:
           return None, f"Pipeline error: {e}"

       except Exception as e:
           return None, f"Unexpected error: {e}"

Step 3: Use Safe Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   structures = [...]  # List of structures

   successful = []
   failed = []

   for struct in structures:
       results, error = safe_analysis(**struct)

       if error:
           failed.append((struct, error))
           print(f"✗ {struct['pdb_id']}: {error}")
       else:
           successful.append(results)
           print(f"✓ {struct['pdb_id']}: Success")

   # Summary
   print(f"\nSuccessful: {len(successful)}")
   print(f"Failed: {len(failed)}")

Next Steps
----------

- Explore :doc:`api/core_pipeline` for advanced features
- Check :doc:`configuration` for all options
- See :doc:`contributing` to contribute
