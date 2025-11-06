Contributing
============

We welcome contributions to PDB Prepare Wizard! This document provides
guidelines for contributing to the project.

Getting Started
---------------

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your feature/fix
4. Make your changes
5. Run tests
6. Submit a pull request

Development Setup
-----------------

.. code-block:: bash

   # Clone your fork
   git clone https://github.com/yourusername/pdb-prepare-wizard.git
   cd pdb-prepare-wizard

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate

   # Install in development mode
   pip install -e .[dev]

   # Verify installation
   pytest tests/

Code Style
----------

We follow PEP 8 style guidelines with some modifications:

- Line length: 100 characters (not 79)
- Use Black for auto-formatting
- Use type hints for function arguments and returns
- Write docstrings for all public functions/classes

Formatting
~~~~~~~~~~

.. code-block:: bash

   # Format code with Black
   black .

   # Check formatting
   black --check .

Linting
~~~~~~~

.. code-block:: bash

   # Run Flake8
   flake8 .

   # Run MyPy type checking
   mypy core_pipeline.py

Testing
-------

All new features should include tests.

Writing Tests
~~~~~~~~~~~~~

Create tests in the ``tests/`` directory:

.. code-block:: python

   # tests/test_my_feature.py
   import pytest
   from my_module import my_function

   def test_my_function():
       result = my_function(input_data)
       assert result == expected_output

   def test_my_function_error():
       with pytest.raises(ValueError):
           my_function(invalid_input)

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

   # Run all tests
   pytest tests/

   # Run with coverage
   pytest tests/ --cov=. --cov-report=html

   # Run specific test file
   pytest tests/test_security.py

   # Run specific test
   pytest tests/test_security.py::test_pdb_id_validation

Documentation
-------------

Update documentation for all new features:

Building Docs
~~~~~~~~~~~~~

.. code-block:: bash

   cd docs
   make html

   # View in browser
   open _build/html/index.html

Writing Docstrings
~~~~~~~~~~~~~~~~~~

Use Google-style docstrings:

.. code-block:: python

   def my_function(param1: str, param2: int) -> bool:
       """
       Short description of function.

       Longer description with more details about what the
       function does and how to use it.

       Args:
           param1: Description of param1
           param2: Description of param2

       Returns:
           Description of return value

       Raises:
           ValueError: When param1 is empty
           TypeError: When param2 is negative

       Example:
           >>> my_function("test", 42)
           True
       """
       # Implementation

Pull Request Process
--------------------

1. **Update Documentation**: Add/update docs for your changes
2. **Add Tests**: Ensure good test coverage
3. **Run Tests**: All tests must pass
4. **Update Changelog**: Add entry to CHANGELOG.md
5. **Commit Messages**: Use clear, descriptive messages
6. **Create PR**: Submit pull request with description

Commit Messages
~~~~~~~~~~~~~~~

Follow conventional commits format:

.. code-block:: text

   feat: Add new disk space checker module
   fix: Resolve memory leak in RMSD calculations
   docs: Update configuration guide
   test: Add tests for file validators
   refactor: Simplify logging initialization
   perf: Optimize RMSD matrix storage

PR Description Template
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Performance improvement

   ## Testing
   - [ ] All tests pass
   - [ ] Added new tests
   - [ ] Manual testing completed

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Documentation updated
   - [ ] Changelog updated
   - [ ] Tests pass

Development Workflow
--------------------

Branch Naming
~~~~~~~~~~~~~

- ``feature/description`` - New features
- ``fix/description`` - Bug fixes
- ``docs/description`` - Documentation
- ``refactor/description`` - Code refactoring

Example Workflow
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create feature branch
   git checkout -b feature/add-rmsd-cache

   # Make changes and commit
   git add .
   git commit -m "feat: Add RMSD caching with pickle"

   # Run tests
   pytest tests/

   # Push to fork
   git push origin feature/add-rmsd-cache

   # Create pull request on GitHub

Code Review
-----------

All contributions go through code review:

- Reviewer checks code quality, style, tests
- Address reviewer comments
- Maintainer approves and merges

Areas for Contribution
----------------------

High Priority
~~~~~~~~~~~~~

- Performance improvements
- Memory optimization
- Additional file format support
- Enhanced visualization options
- More comprehensive tests

Medium Priority
~~~~~~~~~~~~~~~

- Documentation improvements
- Example notebooks
- Tutorial videos
- Integration with other tools

Low Priority
~~~~~~~~~~~~

- Code cleanup
- Refactoring
- Style improvements

Reporting Bugs
--------------

Report bugs via GitHub Issues:

1. Check existing issues first
2. Use issue template
3. Include:
   - Python version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages/logs

Bug Report Template
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   **Description**
   Clear description of the bug

   **To Reproduce**
   1. Step 1
   2. Step 2
   3. ...

   **Expected Behavior**
   What should happen

   **Actual Behavior**
   What actually happened

   **Environment**
   - Python version:
   - OS:
   - Pipeline version:

   **Logs**
   ```
   Relevant log output
   ```

Feature Requests
----------------

Suggest features via GitHub Issues:

1. Describe the feature
2. Explain use case
3. Provide examples

Community Guidelines
--------------------

- Be respectful and professional
- Provide constructive feedback
- Help other contributors
- Follow code of conduct

Getting Help
------------

- GitHub Issues: Bug reports and features
- Discussions: Questions and general discussion
- Email: maintainer@example.com

License
-------

By contributing, you agree that your contributions will be
licensed under the MIT License.

Acknowledgments
---------------

Contributors are acknowledged in:

- README.md contributors section
- CHANGELOG.md for their contributions
- Git commit history
