Disk Space Checker
==================

Check disk space before pipeline execution.

.. automodule:: disk_space_checker
   :members:
   :undoc-members:
   :show-inheritance:

Quick Start
-----------

.. code-block:: python

   from disk_space_checker import check_disk_space
   from pathlib import Path

   # Check disk space
   disk_info = check_disk_space(
       output_dir=Path("output"),
       n_pdb_files=10
   )

   print(f"Free: {disk_info.free_mb:.1f} MB")

Main Classes
------------

.. autoclass:: disk_space_checker.DiskSpaceChecker
   :members:
   :undoc-members:

.. autoclass:: disk_space_checker.DiskSpaceInfo
   :members:
   :undoc-members:

Convenience Functions
---------------------

.. autofunction:: disk_space_checker.check_disk_space
.. autofunction:: disk_space_checker.get_disk_usage
