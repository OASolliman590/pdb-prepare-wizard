# Test Suite

Comprehensive test suite for PDB Prepare Wizard.

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html
```

### Run specific test categories
```bash
# Security tests only
pytest -m security

# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Run specific test file
```bash
pytest tests/test_security.py -v
```

## Test Structure

- `test_security.py` - Security validation tests
- `test_file_validators.py` - File validation tests
- `conftest.py` - Shared fixtures and configuration

## Test Data

Test fixtures are provided in `conftest.py`:
- `sample_pdb_content` - Minimal valid PDB file
- `sample_pdbqt_content` - Minimal valid PDBQT file
- `sample_sdf_content` - Minimal valid SDF file
- `tmp_output_dir` - Temporary directory for test outputs

## Adding New Tests

1. Create test file: `tests/test_<module>.py`
2. Import the module to test
3. Create test class: `class Test<Feature>`
4. Add test methods: `def test_<scenario>(self)`
5. Use fixtures from `conftest.py`
6. Add appropriate markers (`@pytest.mark.unit`, etc.)

## Coverage Goals

- Minimum coverage: 80%
- Critical modules: 90%+
- Security functions: 100%
