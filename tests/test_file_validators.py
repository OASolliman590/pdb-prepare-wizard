"""
Unit tests for file validation utilities.
"""
import pytest
from pathlib import Path
import tempfile
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_validators import FileValidator, FileValidationError


class TestPDBValidation:
    """Test PDB file validation."""

    @pytest.fixture
    def valid_pdb_file(self, tmp_path):
        """Create a valid minimal PDB file."""
        pdb_content = """HEADER    TEST STRUCTURE
ATOM      1  N   MET A   1      20.154  29.699   5.276  1.00 49.05           N
ATOM      2  CA  MET A   1      19.123  28.934   4.580  1.00 49.05           C
HETATM  100  C   LIG A 200      10.000  10.000  10.000  1.00 30.00           C
END
"""
        pdb_file = tmp_path / "test.pdb"
        pdb_file.write_text(pdb_content)
        return pdb_file

    @pytest.fixture
    def invalid_pdb_file(self, tmp_path):
        """Create an invalid PDB file."""
        pdb_file = tmp_path / "invalid.pdb"
        pdb_file.write_text("This is not a PDB file")
        return pdb_file

    @pytest.fixture
    def empty_file(self, tmp_path):
        """Create an empty file."""
        empty_file = tmp_path / "empty.pdb"
        empty_file.touch()
        return empty_file

    def test_validate_valid_pdb(self, valid_pdb_file):
        """Test validation of valid PDB file."""
        result = FileValidator.validate_file(valid_pdb_file, 'pdb')
        assert result['valid'] is True
        assert result['structure_info'] is not None
        assert result['structure_info']['has_atoms'] is True
        assert result['structure_info']['has_hetatm'] is True

    def test_validate_invalid_pdb(self, invalid_pdb_file):
        """Test rejection of invalid PDB file."""
        with pytest.raises(FileValidationError):
            FileValidator.validate_file(invalid_pdb_file, 'pdb')

    def test_validate_empty_file(self, empty_file):
        """Test rejection of empty file."""
        with pytest.raises(FileValidationError):
            FileValidator.validate_file(empty_file, 'pdb')

    def test_validate_nonexistent_file(self):
        """Test rejection of nonexistent file."""
        with pytest.raises(FileValidationError):
            FileValidator.validate_file("/nonexistent/file.pdb", 'pdb')

    def test_pdb_structure_validation(self, valid_pdb_file):
        """Test detailed PDB structure validation."""
        info = FileValidator.validate_pdb_structure(valid_pdb_file)
        assert info['has_atoms'] is True
        assert info['has_hetatm'] is True
        assert info['atom_count'] > 0
        assert info['hetatm_count'] > 0
        assert len(info['chain_ids']) > 0


class TestPDBQTValidation:
    """Test PDBQT file validation."""

    @pytest.fixture
    def valid_pdbqt_file(self, tmp_path):
        """Create a valid minimal PDBQT file."""
        pdbqt_content = """MODEL 1
REMARK VINA RESULT:    -9.5      0.000      0.000
ROOT
ATOM      1  C   UNK     1       0.000   0.000   0.000  0.00  0.00    +0.000 C
ENDROOT
TORSDOF 0
ENDMDL
"""
        pdbqt_file = tmp_path / "test.pdbqt"
        pdbqt_file.write_text(pdbqt_content)
        return pdbqt_file

    def test_validate_valid_pdbqt(self, valid_pdbqt_file):
        """Test validation of valid PDBQT file."""
        result = FileValidator.validate_file(valid_pdbqt_file, 'pdbqt')
        assert result['valid'] is True

    def test_pdbqt_structure_validation(self, valid_pdbqt_file):
        """Test detailed PDBQT structure validation."""
        info = FileValidator.validate_pdbqt_structure(valid_pdbqt_file)
        assert info['has_atoms'] is True
        assert info['model_count'] == 1


class TestSDFValidation:
    """Test SDF file validation."""

    @pytest.fixture
    def valid_sdf_file(self, tmp_path):
        """Create a valid minimal SDF file."""
        sdf_content = """Test Molecule

  0  0  0  0  0  0  0  0  0  0999 V2000
M  END
$$$$
"""
        sdf_file = tmp_path / "test.sdf"
        sdf_file.write_text(sdf_content)
        return sdf_file

    def test_validate_valid_sdf(self, valid_sdf_file):
        """Test validation of valid SDF file."""
        result = FileValidator.validate_file(valid_sdf_file, 'sdf')
        assert result['valid'] is True


class TestChecksumComputation:
    """Test file checksum computation."""

    def test_compute_md5_checksum(self, tmp_path):
        """Test MD5 checksum computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        checksum = FileValidator.compute_checksum(test_file, 'md5')
        assert len(checksum) == 32  # MD5 is 32 hex characters
        assert checksum.isalnum()

    def test_compute_sha256_checksum(self, tmp_path):
        """Test SHA256 checksum computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        checksum = FileValidator.compute_checksum(test_file, 'sha256')
        assert len(checksum) == 64  # SHA256 is 64 hex characters
        assert checksum.isalnum()

    def test_checksum_consistency(self, tmp_path):
        """Test that same content gives same checksum."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        checksum1 = FileValidator.compute_checksum(test_file, 'md5')
        checksum2 = FileValidator.compute_checksum(test_file, 'md5')
        assert checksum1 == checksum2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
