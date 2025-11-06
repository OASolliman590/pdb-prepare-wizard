FAQ
===

Frequently Asked Questions about PDB Prepare Wizard.

Installation
------------

Q: What Python version is required?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: Python 3.8 or higher is required. We recommend Python 3.10+ for best performance.

Q: Do I need to install AutoDock?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: AutoDock Tools (prepare_ligand4.py, prepare_receptor4.py) are optional but recommended
for full functionality. The pipeline can still extract ligands and analyze structures without them.

Q: Can I install without optional dependencies?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: Yes, use ``pip install -e .`` for minimal installation. Add ``[optional]`` for scientific
packages or ``[all]`` for everything.

Usage
-----

Q: How do I find the ligand chain and residue ID?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: View the PDB file in PyMOL or check the RCSB PDB website. Look for HETATM records
in the ligand section.

Q: Can I process multiple structures at once?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: Yes, use ``batch_pdb_preparation.py`` or create a custom script with a loop.
Enable parallel processing with ``config.performance.enable_parallel = True``.

Q: What if my ligand is not detected?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: Check that:
- Chain ID and residue ID are correct
- Ligand name matches PDB file
- PDB file contains HETATM records

Q: How do I customize scientific parameters?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: Create a YAML configuration file or modify parameters programmatically:

.. code-block:: python

   from unified_config import PipelineConfig
   config = PipelineConfig()
   config.scientific.interaction_cutoff = 6.0

Performance
-----------

Q: Why is RMSD calculation slow?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: Enable caching and use optimized storage:

.. code-block:: python

   from rmsd_optimizer import CachedRMSDCalculator
   calculator = CachedRMSDCalculator(cache_dir=".cache")

Q: How can I speed up batch processing?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: Enable parallel processing:

.. code-block:: python

   config.performance.enable_parallel = True
   config.performance.n_jobs = 8  # Number of CPU cores

Q: The pipeline uses too much memory. What can I do?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: Enable memory management:

.. code-block:: python

   config.performance.explicit_cleanup = True
   config.performance.gc_frequency = 5

Errors
------

Q: "PDBDownloadError" - What does this mean?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: The PDB ID might be invalid or the RCSB server is unavailable. Check:
- PDB ID is correct (4 characters)
- Internet connection is working
- RCSB PDB is not under maintenance

Q: "LigandNotFoundError" - How do I fix this?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: Verify the ligand exists:
1. Open PDB file in text editor
2. Search for HETATM records
3. Check chain ID and residue number match

Q: "InsufficientDiskSpaceError" - Not enough space?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: Free up disk space or use a different output directory:

.. code-block:: bash

   # Check available space
   df -h

   # Use different directory
   pipeline = ProteinLigandPipeline(output_dir="/path/with/more/space")

Q: Import errors for optional dependencies?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: Install the package:

.. code-block:: bash

   pip install plip matplotlib seaborn openpyxl

Or install all optional dependencies:

.. code-block:: bash

   pip install -e .[all]

Output Files
------------

Q: What format are the results in?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: Results are generated in multiple formats:
- CSV: Tabular data with metadata
- Excel: Formatted workbooks
- JSON: Machine-readable format
- PDB/PDBQT: Structure files

Q: Where are log files stored?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: In the ``logs/`` directory by default. Configure with:

.. code-block:: python

   config.logging.log_dir = "my_logs"

Q: Can I disable certain output formats?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: Yes, in configuration:

.. code-block:: python

   config.output.generate_excel = False
   config.output.generate_visualizations = False

Reproducibility
---------------

Q: Are results reproducible?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: Yes, if you:
1. Set random seeds in configuration
2. Use same pipeline version
3. Use same dependency versions

Q: How do I track which version produced results?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: Check the metadata files:
- ``*_metadata.json`` contains all version info
- CSV/Excel files include metadata headers

Advanced
--------

Q: Can I use custom interaction detection methods?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: Yes, extend the pipeline:

.. code-block:: python

   from core_pipeline import ProteinLigandPipeline

   class CustomPipeline(ProteinLigandPipeline):
       def analyze_interactions(self, ...):
           # Your custom implementation
           pass

Q: How do I integrate with my existing workflow?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: Import as a library:

.. code-block:: python

   from core_pipeline import ProteinLigandPipeline
   pipeline = ProteinLigandPipeline()
   results = pipeline.run_full_pipeline(...)
   # Use results in your workflow

Q: Can I run without downloading from RCSB?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A: Yes, provide local PDB file:

.. code-block:: python

   # Extract ligand from local file
   pipeline.extract_ligand(
       pdb_file="my_structure.pdb",
       ligand_name="ATP",
       ...
   )

Still Have Questions?
---------------------

- Check documentation: https://docs.example.com
- GitHub Issues: https://github.com/user/pdb-prepare-wizard/issues
- Email: support@example.com
