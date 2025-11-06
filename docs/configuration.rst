Configuration Guide
===================

PDB Prepare Wizard uses a YAML-based configuration system for managing
all pipeline parameters.

Configuration Structure
-----------------------

The configuration is organized into six main sections:

1. **Network**: Download and connection settings
2. **Scientific**: Scientific analysis parameters
3. **Clustering**: RMSD clustering configuration
4. **Output**: Output format and file settings
5. **Logging**: Logging system configuration
6. **Performance**: Parallel processing and caching

Default Configuration
---------------------

Create a default configuration file:

.. code-block:: python

   from unified_config import ConfigurationManager

   manager = ConfigurationManager(config_dir=".config")
   config = manager.create_default_config()

This creates ``.config/default.yaml`` with all default values.

Network Configuration
---------------------

Controls network operations and retry logic:

.. code-block:: yaml

   network:
     max_retries: 4                # Maximum retry attempts
     retry_base_delay: 2.0         # Base delay in seconds
     connection_timeout: 30        # Connection timeout (seconds)
     download_timeout: 300         # Download timeout (seconds)

**Parameters:**

- ``max_retries``: Number of retry attempts (1-10)
- ``retry_base_delay``: Base delay for exponential backoff (0.5-10.0s)
- ``connection_timeout``: Timeout for establishing connection
- ``download_timeout``: Timeout for download operations

Scientific Parameters
---------------------

Control scientific analysis behavior:

.. code-block:: yaml

   scientific:
     # Distance parameters (Angstroms)
     interaction_cutoff: 5.0       # Interaction detection cutoff
     pocket_radius: 10.0           # Binding pocket radius
     clash_cutoff: 2.0             # Clash detection cutoff

     # Pocket analysis
     interaction_sphere_radius: 5.0
     hydrophobic_cutoff: 8.0

     # Druggability scoring weights (must sum to 1.0)
     druggability_volume_weight: 0.33
     druggability_hydrophobic_weight: 0.33
     druggability_electrostatic_weight: 0.34

     # Thresholds
     druggability_excellent_threshold: 0.7
     druggability_good_threshold: 0.5
     druggability_moderate_threshold: 0.3

**Distance Parameters:**

- ``interaction_cutoff``: Maximum distance for interaction detection (2.0-15.0 Å)
- ``pocket_radius``: Radius for pocket residue selection (5.0-20.0 Å)
- ``clash_cutoff``: Minimum distance for clash detection (1.0-5.0 Å)

**Druggability Weights:**

Adjust the importance of different factors in druggability scoring.
All weights must sum to 1.0.

Clustering Configuration
------------------------

Configure RMSD clustering algorithms:

.. code-block:: yaml

   clustering:
     method: kmeans                # kmeans or dbscan
     n_clusters: 3                 # Number of clusters (for kmeans)
     rmsd_cutoff: 2.0              # RMSD threshold (Angstroms)

     # DBSCAN parameters
     eps: 2.0                      # DBSCAN epsilon
     min_samples: 2                # DBSCAN minimum samples

     # Reproducibility seeds
     random_seed: 42
     numpy_seed: 42
     sklearn_seed: 42

**Methods:**

- ``kmeans``: K-means clustering (requires n_clusters)
- ``dbscan``: Density-based clustering (requires eps, min_samples)

**Reproducibility:**

Set seeds to ensure reproducible results:

.. code-block:: python

   config.clustering.random_seed = 42
   config.clustering.numpy_seed = 42
   config.clustering.sklearn_seed = 42

Output Configuration
--------------------

Control output file formats and content:

.. code-block:: yaml

   output:
     # File formats
     generate_csv: true
     generate_excel: true
     generate_json: true
     generate_pdb: true

     # Visualization
     generate_visualizations: true
     visualization_dpi: 300
     pymol_ray_trace: false

     # Metadata
     include_metadata: true
     include_git_info: true
     include_environment: false    # May contain sensitive data

**Format Options:**

- ``generate_csv``: CSV reports with metadata
- ``generate_excel``: Excel workbooks with formatted sheets
- ``generate_json``: Machine-readable JSON format
- ``generate_pdb``: Structure files (PDB, PDBQT)

**Visualization:**

- ``visualization_dpi``: Image resolution (72-600 DPI)
- ``pymol_ray_trace``: High-quality ray-traced images (slow)

Logging Configuration
---------------------

Configure the logging system:

.. code-block:: yaml

   logging:
     level: INFO                   # DEBUG, INFO, WARNING, ERROR, CRITICAL
     console_output: true
     file_output: true
     use_colors: true
     log_dir: logs

**Levels:**

- ``DEBUG``: Detailed debugging information
- ``INFO``: General informational messages
- ``WARNING``: Warning messages
- ``ERROR``: Error messages
- ``CRITICAL``: Critical failures

Performance Configuration
-------------------------

Optimize performance for your system:

.. code-block:: yaml

   performance:
     # Parallel processing
     enable_parallel: false        # Enable multiprocessing
     n_jobs: 4                     # Number of parallel jobs
     batch_size: 10                # Batch size for processing

     # Memory management
     explicit_cleanup: true        # Force garbage collection
     gc_frequency: 10              # GC every N structures

     # Caching
     enable_rmsd_cache: true
     cache_dir: .cache

**Parallel Processing:**

Enable for batch processing:

.. code-block:: python

   config.performance.enable_parallel = True
   config.performance.n_jobs = 8  # Use 8 CPU cores

**Memory Management:**

For large datasets:

.. code-block:: python

   config.performance.explicit_cleanup = True
   config.performance.gc_frequency = 5  # More frequent cleanup

Loading Configurations
----------------------

From YAML File
~~~~~~~~~~~~~~

.. code-block:: python

   from unified_config import PipelineConfig

   # Load from file
   config = PipelineConfig.from_yaml("my_config.yaml")

From Dictionary
~~~~~~~~~~~~~~~

.. code-block:: python

   config_dict = {
       'scientific': {
           'interaction_cutoff': 6.0,
           'pocket_radius': 12.0
       }
   }

   config = PipelineConfig.from_dict(config_dict)

With Overrides
~~~~~~~~~~~~~~

.. code-block:: python

   # Load base configuration
   config = PipelineConfig.from_yaml("base.yaml")

   # Apply overrides
   overrides = {
       'clustering': {'n_clusters': 5},
       'output': {'visualization_dpi': 600}
   }

   config = config.merge(overrides)

Saving Configurations
---------------------

To YAML File
~~~~~~~~~~~~

.. code-block:: python

   config = PipelineConfig()
   config.to_yaml("my_config.yaml")

Named Profiles
~~~~~~~~~~~~~~

.. code-block:: python

   from unified_config import ConfigurationManager

   manager = ConfigurationManager()

   # Save as named profile
   manager.save_config(config, name="high_resolution")

   # Load named profile
   config = manager.load_config("high_resolution.yaml")

Accessing Parameters
--------------------

Dot Notation
~~~~~~~~~~~~

.. code-block:: python

   # Get parameter
   cutoff = config.get_parameter('scientific.interaction_cutoff')
   # Returns: 5.0

   # Set parameter
   config.set_parameter('scientific.interaction_cutoff', 6.0)

Direct Access
~~~~~~~~~~~~~

.. code-block:: python

   # Access nested attributes
   cutoff = config.scientific.interaction_cutoff
   config.scientific.interaction_cutoff = 6.0

Validation
----------

All parameters are validated automatically:

.. code-block:: python

   config = PipelineConfig()

   # This will raise AssertionError
   config.scientific.interaction_cutoff = 100.0  # Out of range
   config.validate()  # Validation fails

Configuration Summary
---------------------

Print configuration summary:

.. code-block:: python

   config = PipelineConfig()
   print(config.summary())

Output:

.. code-block:: text

   Pipeline Configuration Summary
   ============================================================
   Version: 3.1.0
   Output Directory: pipeline_output

   Network:
     Max Retries: 4
     Retry Delay: 2.0s

   Scientific Parameters:
     Interaction Cutoff: 5.0 Å
     Pocket Radius: 10.0 Å
     Clash Cutoff: 2.0 Å
   ...

Example Configurations
----------------------

High-Throughput Screening
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   scientific:
     interaction_cutoff: 4.0
     pocket_radius: 8.0

   clustering:
     method: dbscan
     eps: 1.5

   output:
     generate_visualizations: false
     generate_excel: false

   performance:
     enable_parallel: true
     n_jobs: 16
     batch_size: 50

High-Precision Analysis
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   scientific:
     interaction_cutoff: 6.0
     pocket_radius: 15.0

   output:
     visualization_dpi: 600
     pymol_ray_trace: true

   performance:
     enable_parallel: false

Best Practices
--------------

1. **Version Control**: Store configuration files in version control
2. **Validation**: Always call ``config.validate()`` after modifications
3. **Documentation**: Comment your YAML files to explain choices
4. **Profiles**: Create named profiles for different use cases
5. **Testing**: Test configurations with small datasets first

Troubleshooting
---------------

Validation Errors
~~~~~~~~~~~~~~~~~

If validation fails:

.. code-block:: python

   try:
       config.validate()
   except AssertionError as e:
       print(f"Configuration error: {e}")
       # Fix the problematic parameter

Missing Files
~~~~~~~~~~~~~

If configuration file is missing:

.. code-block:: python

   from unified_config import ConfigurationManager

   manager = ConfigurationManager()
   # Automatically creates default if missing
   config = manager.load_config()

See Also
--------

- :doc:`api/unified_config`: Configuration API reference
- :doc:`quickstart`: Quick start examples
- :doc:`tutorials`: Detailed tutorials
