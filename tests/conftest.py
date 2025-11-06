"""
Pytest configuration and shared fixtures.
"""
import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture(scope="session")
def test_data_dir():
    """Provide path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def tmp_output_dir():
    """Create a temporary output directory for tests."""
    tmpdir = tempfile.mkdtemp(prefix="pdb_wizard_test_")
    yield Path(tmpdir)
    # Cleanup
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def sample_pdb_content():
    """Provide sample PDB file content."""
    return """HEADER    TEST PROTEIN
TITLE     TEST STRUCTURE FOR UNIT TESTING
COMPND    MOL_ID: 1;
COMPND   2 MOLECULE: TEST PROTEIN;
COMPND   3 CHAIN: A;
REMARK   1 CREATED FOR TESTING PURPOSES
ATOM      1  N   MET A   1      20.154  29.699   5.276  1.00 49.05           N
ATOM      2  CA  MET A   1      19.123  28.934   4.580  1.00 49.05           C
ATOM      3  C   MET A   1      19.444  28.849   3.092  1.00 48.96           C
ATOM      4  O   MET A   1      20.529  28.403   2.704  1.00 48.90           O
ATOM      5  CB  MET A   1      18.885  27.532   5.155  1.00 49.12           C
HETATM  100  C1  LIG A 200      10.000  10.000  10.000  1.00 30.00           C
HETATM  101  C2  LIG A 200      11.000  10.000  10.000  1.00 30.00           C
HETATM  102  O1  LIG A 200      10.500  11.000  10.000  1.00 30.00           O
END
"""


@pytest.fixture
def sample_pdbqt_content():
    """Provide sample PDBQT file content."""
    return """MODEL 1
REMARK VINA RESULT:    -9.5      0.000      0.000
ROOT
ATOM      1  C   UNK     1       0.000   0.000   0.000  0.00  0.00    +0.150 C
ATOM      2  C   UNK     1       1.400   0.000   0.000  0.00  0.00    +0.050 C
ATOM      3  C   UNK     1       2.100   1.200   0.000  0.00  0.00    +0.050 C
ENDROOT
TORSDOF 2
ENDMDL
MODEL 2
REMARK VINA RESULT:    -8.8      1.500      2.200
ROOT
ATOM      1  C   UNK     1       0.100   0.100   0.100  0.00  0.00    +0.150 C
ATOM      2  C   UNK     1       1.500   0.100   0.100  0.00  0.00    +0.050 C
ATOM      3  C   UNK     1       2.200   1.300   0.100  0.00  0.00    +0.050 C
ENDROOT
TORSDOF 2
ENDMDL
"""


@pytest.fixture
def sample_sdf_content():
    """Provide sample SDF file content."""
    return """Test Ligand
  ChemDraw

  3  2  0  0  0  0  0  0  0  0999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.4000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    2.1000    1.2000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0
  2  3  1  0
M  END
$$$$
"""


@pytest.fixture
def mock_config():
    """Provide mock configuration for testing."""
    return {
        'random_seed': 42,
        'numpy_seed': 42,
        'sklearn_seed': 42,
        'output_dir': './test_output',
        'generate_visualizations': False,  # Skip viz in tests
        'enable_plip': False,  # Skip PLIP in tests
    }
