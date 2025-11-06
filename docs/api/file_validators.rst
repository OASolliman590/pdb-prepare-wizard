File Validators
===============

Comprehensive file format validation.

.. automodule:: file_validators
   :members:
   :undoc-members:
   :show-inheritance:

Quick Start
-----------

.. code-block:: python

   from file_validators import FileValidator

   # Validate PDB file
   result = FileValidator.validate_file(
       "structure.pdb",
       format_type="pdb",
       check_structure=True
   )

   if result['valid']:
       print("File is valid")
       print(f"Atoms: {result['atoms']}")
   else:
       print(f"Errors: {result['errors']}")

Main Class
----------

.. autoclass:: file_validators.FileValidator
   :members:
   :undoc-members:
