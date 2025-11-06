Security Utilities
==================

Security validation and sanitization.

.. automodule:: security_utils
   :members:
   :undoc-members:
   :show-inheritance:

Quick Start
-----------

.. code-block:: python

   from security_utils import SecurityValidator

   # Validate PDB ID
   safe_id = SecurityValidator.validate_pdb_id("7CMD")

   # Sanitize file path
   safe_path = SecurityValidator.sanitize_filename("my_file.pdb")

   # Validate command args
   safe_args = SecurityValidator.sanitize_command_args([
       "obabel", "input.pdb", "-O", "output.sdf"
   ])

Main Class
----------

.. autoclass:: security_utils.SecurityValidator
   :members:
   :undoc-members:
