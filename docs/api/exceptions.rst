Exceptions
==========

Custom exception hierarchy for better error handling.

.. automodule:: exceptions
   :members:
   :undoc-members:
   :show-inheritance:

Exception Hierarchy
-------------------

.. code-block:: text

   PipelineError (base)
   ├── NetworkError
   │   └── PDBDownloadError
   ├── ValidationError
   │   └── FileFormatError
   ├── LigandError
   │   └── LigandNotFoundError
   ├── StructureError
   │   ├── MissingAtomsError
   │   └── CoordinateError
   ├── AnalysisError
   │   ├── PocketAnalysisError
   │   └── InteractionAnalysisError
   ├── ConfigurationError
   │   ├── InvalidParameterError
   │   └── DependencyError
   ├── OutputError
   │   └── OutputWriteError
   ├── CheckpointError
   │   └── CheckpointNotFoundError
   └── ResourceError
       ├── InsufficientDiskSpaceError
       └── MemoryError

Base Exception
--------------

PipelineError
~~~~~~~~~~~~~

.. autoclass:: exceptions.PipelineError
   :members:
   :show-inheritance:

Network Exceptions
------------------

NetworkError
~~~~~~~~~~~~

.. autoclass:: exceptions.NetworkError
   :members:
   :show-inheritance:

PDBDownloadError
~~~~~~~~~~~~~~~~

.. autoclass:: exceptions.PDBDownloadError
   :members:
   :show-inheritance:

Validation Exceptions
---------------------

ValidationError
~~~~~~~~~~~~~~~

.. autoclass:: exceptions.ValidationError
   :members:
   :show-inheritance:

FileFormatError
~~~~~~~~~~~~~~~

.. autoclass:: exceptions.FileFormatError
   :members:
   :show-inheritance:

Resource Exceptions
-------------------

ResourceError
~~~~~~~~~~~~~

.. autoclass:: exceptions.ResourceError
   :members:
   :show-inheritance:

InsufficientDiskSpaceError
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: exceptions.InsufficientDiskSpaceError
   :members:
   :show-inheritance:

Utility Functions
-----------------

log_exception
~~~~~~~~~~~~~

.. autofunction:: exceptions.log_exception

handle_pipeline_error
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: exceptions.handle_pipeline_error

Usage Examples
--------------

Catching Specific Exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from exceptions import PDBDownloadError, LigandNotFoundError

   try:
       pipeline.run_full_pipeline(pdb_id="7CMD", ...)
   except PDBDownloadError as e:
       print(f"Download failed: {e.pdb_id}")
   except LigandNotFoundError as e:
       print(f"Ligand {e.ligand_name} not found")

Raising Custom Exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from exceptions import InvalidParameterError

   def validate_cutoff(cutoff):
       if cutoff < 0:
           raise InvalidParameterError(
               parameter="cutoff",
               value=cutoff,
               reason="Must be positive"
           )

Error Handler
~~~~~~~~~~~~~

.. code-block:: python

   from exceptions import handle_pipeline_error

   try:
       # Pipeline operations
       results = process_structure()
   except Exception as e:
       handled = handle_pipeline_error(e, context="structure processing")
       if not handled:
           raise
