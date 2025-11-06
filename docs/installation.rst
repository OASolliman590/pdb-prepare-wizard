Installation
============

Requirements
------------

- Python 3.8 or higher
- pip package manager
- Git (for development installation)

Core Dependencies
~~~~~~~~~~~~~~~~~

The following packages are required:

- numpy >= 1.21.0
- pandas >= 1.3.0
- biopython >= 1.79
- scikit-learn >= 1.0.0
- pyyaml >= 6.0

Optional Dependencies
~~~~~~~~~~~~~~~~~~~~~

For enhanced functionality:

- plip: Protein-ligand interaction analysis
- matplotlib: Visualization and plotting
- seaborn: Statistical visualizations
- openpyxl: Excel report generation

Installation Methods
--------------------

Method 1: Standard Installation (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install with all optional features:

.. code-block:: bash

   git clone https://github.com/yourusername/pdb-prepare-wizard.git
   cd pdb-prepare-wizard
   pip install -e .[all]

Method 2: Minimal Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install only core dependencies:

.. code-block:: bash

   git clone https://github.com/yourusername/pdb-prepare-wizard.git
   cd pdb-prepare-wizard
   pip install -e .

Method 3: Custom Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install with specific optional features:

.. code-block:: bash

   # With optional scientific packages
   pip install -e .[optional]

   # For development (includes testing tools)
   pip install -e .[dev]

Method 4: From PyPI (Future)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install pdb-prepare-wizard

External Dependencies
---------------------

For full functionality, install these external tools:

AutoDock Tools
~~~~~~~~~~~~~~

.. code-block:: bash

   # Linux (Ubuntu/Debian)
   sudo apt-get install autodock autodock-vina

   # macOS
   brew install autodock-vina

   # Or download from: http://autodock.scripps.edu/

Open Babel
~~~~~~~~~~

.. code-block:: bash

   # Linux (Ubuntu/Debian)
   sudo apt-get install openbabel

   # macOS
   brew install open-babel

   # Or: pip install openbabel-wheel

PyMOL (Optional)
~~~~~~~~~~~~~~~~

For structure visualization:

.. code-block:: bash

   # Linux (Ubuntu/Debian)
   sudo apt-get install pymol

   # macOS
   brew install pymol

   # Or download from: https://pymol.org/

Verification
------------

Verify installation:

.. code-block:: bash

   python -c "import core_pipeline; print('Installation successful!')"

Run tests:

.. code-block:: bash

   pytest tests/

Troubleshooting
---------------

Import Errors
~~~~~~~~~~~~~

If you encounter import errors:

.. code-block:: bash

   # Ensure all dependencies are installed
   pip install -e .[all] --upgrade

   # Check Python version
   python --version  # Should be 3.8+

Permission Issues
~~~~~~~~~~~~~~~~~

On Linux/macOS, if you encounter permission errors:

.. code-block:: bash

   # Use user installation
   pip install --user -e .[all]

Windows Issues
~~~~~~~~~~~~~~

On Windows, some dependencies may require:

- Visual C++ Build Tools
- Microsoft Visual Studio

Download from: https://visualstudio.microsoft.com/downloads/

Virtual Environment (Recommended)
---------------------------------

Use a virtual environment to avoid dependency conflicts:

.. code-block:: bash

   # Create virtual environment
   python -m venv venv

   # Activate (Linux/macOS)
   source venv/bin/activate

   # Activate (Windows)
   venv\\Scripts\\activate

   # Install
   pip install -e .[all]

Docker Installation (Alternative)
----------------------------------

Use Docker for isolated environment:

.. code-block:: bash

   # Build image
   docker build -t pdb-prepare-wizard .

   # Run container
   docker run -it pdb-prepare-wizard

Updating
--------

Update to latest version:

.. code-block:: bash

   cd pdb-prepare-wizard
   git pull origin main
   pip install -e .[all] --upgrade
