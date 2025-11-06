Version Tracking
================

Version and provenance tracking for reproducibility.

.. automodule:: version_tracker
   :members:
   :undoc-members:
   :show-inheritance:

Quick Start
-----------

.. code-block:: python

   from version_tracker import get_metadata, save_metadata

   # Get metadata
   metadata = get_metadata()
   print(metadata['pipeline_version'])
   print(metadata['git']['commit'])

   # Save to file
   save_metadata("output.csv")

Main Class
----------

.. autoclass:: version_tracker.VersionTracker
   :members:
   :undoc-members:

Convenience Functions
---------------------

.. autofunction:: version_tracker.get_metadata
.. autofunction:: version_tracker.save_metadata
.. autofunction:: version_tracker.get_version_string
