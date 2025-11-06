"""
Unit tests for security utilities.
"""
import pytest
from pathlib import Path
import tempfile
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_utils import SecurityValidator, SecurityError


class TestPDBIDValidation:
    """Test PDB ID validation."""

    def test_valid_pdb_ids(self):
        """Test that valid PDB IDs pass validation."""
        valid_ids = ["1ABC", "7CMD", "6WX4", "5T3M"]
        for pdb_id in valid_ids:
            result = SecurityValidator.validate_pdb_id(pdb_id)
            assert result == pdb_id.upper()

    def test_invalid_pdb_ids(self):
        """Test that invalid PDB IDs are rejected."""
        invalid_ids = [
            "ABC",  # Too short
            "12ABC",  # Too long
            "ABC!",  # Invalid character
            "AB-C",  # Dash
            "../AB",  # Path traversal
            "AB; rm",  # Command injection
        ]
        for pdb_id in invalid_ids:
            with pytest.raises(SecurityError):
                SecurityValidator.validate_pdb_id(pdb_id)

    def test_empty_pdb_id(self):
        """Test that empty PDB ID is rejected."""
        with pytest.raises(SecurityError):
            SecurityValidator.validate_pdb_id("")


class TestFilenameValidation:
    """Test filename sanitization."""

    def test_safe_filenames(self):
        """Test that safe filenames pass validation."""
        safe_names = ["test.pdb", "ligand_1.sdf", "structure-2024.pdbqt"]
        for filename in safe_names:
            result = SecurityValidator.sanitize_filename(filename)
            assert len(result) > 0

    def test_dangerous_filenames(self):
        """Test that dangerous filenames are rejected."""
        dangerous_names = [
            "../../../etc/passwd",
            "test; rm -rf /",
            "file$(cat /etc/passwd)",
            "file|malicious",
            "file`whoami`",
        ]
        for filename in dangerous_names:
            with pytest.raises(SecurityError):
                SecurityValidator.sanitize_filename(filename)

    def test_filename_length_limit(self):
        """Test that overly long filenames are rejected."""
        long_name = "a" * 300 + ".pdb"
        with pytest.raises(SecurityError):
            SecurityValidator.sanitize_filename(long_name)


class TestPathValidation:
    """Test path validation."""

    def test_valid_path_within_base(self):
        """Test that paths within base directory are accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.pdb"
            test_file.touch()

            result = SecurityValidator.validate_path(test_file, base_dir=tmpdir)
            assert result.exists()

    def test_path_traversal_rejection(self):
        """Test that path traversal is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            traversal_path = Path(tmpdir) / ".." / ".." / "etc" / "passwd"

            with pytest.raises(SecurityError):
                SecurityValidator.validate_path(traversal_path, base_dir=tmpdir)

    def test_nonexistent_path_with_must_exist(self):
        """Test that nonexistent paths fail when must_exist=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "nonexistent.pdb"

            with pytest.raises(SecurityError):
                SecurityValidator.validate_path(nonexistent, must_exist=True)


class TestCommandSanitization:
    """Test command argument sanitization."""

    def test_safe_command_args(self):
        """Test that safe command arguments pass validation."""
        safe_args = ["obabel", "input.pdb", "-O", "output.sdf", "-h"]
        result = SecurityValidator.sanitize_command_args(safe_args)
        assert len(result) == len(safe_args)

    def test_dangerous_command_args(self):
        """Test that dangerous command arguments are rejected."""
        dangerous_args = [
            ["plip", "-f", "structure.pdb; rm -rf /"],
            ["cmd", "$(cat /etc/passwd)"],
            ["tool", "`whoami`"],
            ["prog", "|malicious"],
        ]
        for args in dangerous_args:
            with pytest.raises(SecurityError):
                SecurityValidator.sanitize_command_args(args)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
