Testing
=======

PDB Prepare Wizard uses pytest for testing.

Running Tests
-------------

.. code-block:: bash

   # Run all tests
   pytest tests/

   # With coverage
   pytest tests/ --cov=. --cov-report=html --cov-report=term

   # Verbose output
   pytest tests/ -v

   # Stop on first failure
   pytest tests/ -x

   # Run specific test file
   pytest tests/test_security.py

Test Organization
-----------------

Tests are organized by module:

.. code-block:: text

   tests/
   ├── conftest.py              # Shared fixtures
   ├── test_security.py         # Security tests
   ├── test_file_validators.py  # File validation tests
   ├── test_core_pipeline.py    # Pipeline tests
   ├── test_rmsd_optimizer.py   # RMSD optimization tests
   └── test_config.py           # Configuration tests

Test Categories
---------------

Use markers to categorize tests:

.. code-block:: python

   import pytest

   @pytest.mark.unit
   def test_simple_function():
       pass

   @pytest.mark.integration
   def test_full_pipeline():
       pass

   @pytest.mark.slow
   def test_large_dataset():
       pass

Run by marker:

.. code-block:: bash

   # Unit tests only
   pytest -m unit

   # Skip slow tests
   pytest -m "not slow"

Writing Tests
-------------

Example test:

.. code-block:: python

   import pytest
   from disk_space_checker import DiskSpaceChecker

   def test_disk_usage():
       checker = DiskSpaceChecker()
       info = checker.get_disk_usage()

       assert info.total_mb > 0
       assert info.free_mb >= 0
       assert 0 <= info.percent_used <= 100

   def test_insufficient_space_error():
       checker = DiskSpaceChecker()

       with pytest.raises(InsufficientDiskSpaceError):
           checker.check_space_available(
               required_mb=999999999,
               raise_on_insufficient=True
           )

Fixtures
--------

Use fixtures for test data:

.. code-block:: python

   import pytest
   from pathlib import Path

   @pytest.fixture
   def sample_pdb(tmp_path):
       """Create sample PDB file."""
       pdb_file = tmp_path / "test.pdb"
       pdb_file.write_text(
           "ATOM      1  CA  ALA A   1      10.0  10.0  10.0\\n"
       )
       return pdb_file

   def test_with_fixture(sample_pdb):
       assert sample_pdb.exists()

Coverage Requirements
---------------------

Aim for high coverage:

- Overall: > 80%
- Critical modules: > 90%
- New code: 100%

Check coverage:

.. code-block:: bash

   pytest tests/ --cov=. --cov-report=term-missing

CI Testing
----------

Tests run automatically on:

- Push to main/develop
- Pull requests
- Multiple Python versions (3.8, 3.9, 3.10, 3.11)
- Multiple OS (Linux, macOS, Windows)

See ``.github/workflows/ci.yml``
