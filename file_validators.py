#!/usr/bin/env python3
"""
File Validation Module
======================

Comprehensive validation for molecular structure file formats.
Checks file integrity, format compliance, and basic structural validity.
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class FileValidationError(Exception):
    """Exception raised when file validation fails."""
    pass


class FileValidator:
    """
    Validates molecular structure files for format compliance and integrity.
    """

    # File format signatures (magic numbers/headers)
    FORMAT_SIGNATURES = {
        'pdb': [
            b'HEADER',
            b'ATOM  ',
            b'HETATM',
            b'CRYST1',
            b'MODEL '
        ],
        'pdbqt': [
            b'ATOM  ',
            b'HETATM',
            b'ROOT',
            b'TORSDOF'
        ],
        'sdf': [
            b'V2000',
            b'V3000',
            b'$$$$'
        ],
        'mol2': [
            b'@<TRIPOS>MOLECULE',
            b'@<TRIPOS>ATOM'
        ]
    }

    # Minimum file sizes (bytes) - prevents empty/corrupted files
    MIN_FILE_SIZES = {
        'pdb': 100,
        'pdbqt': 100,
        'sdf': 50,
        'mol2': 50
    }

    @staticmethod
    def validate_file_exists(file_path: str) -> Path:
        """
        Validate that file exists and is readable.

        Args:
            file_path: Path to file

        Returns:
            Path object if valid

        Raises:
            FileValidationError: If file doesn't exist or isn't readable
        """
        path = Path(file_path)

        if not path.exists():
            raise FileValidationError(f"File does not exist: {file_path}")

        if not path.is_file():
            raise FileValidationError(f"Path is not a file: {file_path}")

        if not os.access(path, os.R_OK):
            raise FileValidationError(f"File is not readable: {file_path}")

        return path

    @staticmethod
    def validate_file_size(file_path: Path, format_type: str) -> int:
        """
        Validate file size is above minimum threshold.

        Args:
            file_path: Path to file
            format_type: File format (pdb, pdbqt, sdf, mol2)

        Returns:
            File size in bytes

        Raises:
            FileValidationError: If file is too small
        """
        size = file_path.stat().st_size
        min_size = FileValidator.MIN_FILE_SIZES.get(format_type.lower(), 50)

        if size < min_size:
            raise FileValidationError(
                f"File too small ({size} bytes < {min_size} bytes minimum): {file_path}"
            )

        if size == 0:
            raise FileValidationError(f"File is empty: {file_path}")

        return size

    @staticmethod
    def validate_format_signature(file_path: Path, format_type: str) -> bool:
        """
        Validate file has expected format signature/magic numbers.

        Args:
            file_path: Path to file
            format_type: Expected file format

        Returns:
            True if valid signature found

        Raises:
            FileValidationError: If no valid signature found
        """
        format_type = format_type.lower()
        expected_signatures = FileValidator.FORMAT_SIGNATURES.get(format_type)

        if not expected_signatures:
            logger.warning(f"No signatures defined for format: {format_type}")
            return True

        try:
            with open(file_path, 'rb') as f:
                # Read first 10KB to check for signatures
                content = f.read(10240)

                for signature in expected_signatures:
                    if signature in content:
                        return True

                raise FileValidationError(
                    f"No valid {format_type.upper()} signature found in file: {file_path}\n"
                    f"Expected one of: {[sig.decode('utf-8', errors='ignore') for sig in expected_signatures]}"
                )
        except Exception as e:
            raise FileValidationError(f"Error reading file {file_path}: {e}")

    @staticmethod
    def validate_pdb_structure(file_path: Path) -> Dict:
        """
        Validate PDB file structure and extract basic information.

        Args:
            file_path: Path to PDB file

        Returns:
            Dictionary with validation results and file info

        Raises:
            FileValidationError: If PDB structure is invalid
        """
        info = {
            'has_atoms': False,
            'atom_count': 0,
            'has_hetatm': False,
            'hetatm_count': 0,
            'has_coordinates': False,
            'chain_ids': set(),
            'warnings': []
        }

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if line.startswith('ATOM  '):
                        info['has_atoms'] = True
                        info['atom_count'] += 1
                        # Check coordinate format (columns 31-54)
                        if len(line) >= 54:
                            try:
                                x = float(line[30:38].strip())
                                y = float(line[38:46].strip())
                                z = float(line[46:54].strip())
                                info['has_coordinates'] = True
                            except ValueError:
                                info['warnings'].append(
                                    f"Invalid coordinates at line {line_num}"
                                )
                        # Extract chain ID (column 22)
                        if len(line) >= 22:
                            chain = line[21].strip()
                            if chain:
                                info['chain_ids'].add(chain)

                    elif line.startswith('HETATM'):
                        info['has_hetatm'] = True
                        info['hetatm_count'] += 1
                        if len(line) >= 22:
                            chain = line[21].strip()
                            if chain:
                                info['chain_ids'].add(chain)

            # Validation checks
            if not info['has_atoms'] and not info['has_hetatm']:
                raise FileValidationError(
                    f"PDB file contains no ATOM or HETATM records: {file_path}"
                )

            if not info['has_coordinates']:
                raise FileValidationError(
                    f"PDB file contains no valid coordinates: {file_path}"
                )

            info['chain_ids'] = sorted(info['chain_ids'])
            logger.info(f"PDB validation passed: {info['atom_count']} atoms, "
                       f"{info['hetatm_count']} heteroatoms, "
                       f"chains: {info['chain_ids']}")

            return info

        except FileValidationError:
            raise
        except Exception as e:
            raise FileValidationError(f"Error validating PDB structure: {e}")

    @staticmethod
    def validate_pdbqt_structure(file_path: Path) -> Dict:
        """
        Validate PDBQT file structure (AutoDock format).

        Args:
            file_path: Path to PDBQT file

        Returns:
            Dictionary with validation results

        Raises:
            FileValidationError: If PDBQT structure is invalid
        """
        info = {
            'has_atoms': False,
            'atom_count': 0,
            'has_charges': False,
            'has_atom_types': False,
            'model_count': 0,
            'warnings': []
        }

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                in_model = False
                for line in f:
                    if line.startswith('MODEL'):
                        info['model_count'] += 1
                        in_model = True
                    elif line.startswith('ENDMDL'):
                        in_model = False
                    elif line.startswith('ATOM  ') or line.startswith('HETATM'):
                        info['has_atoms'] = True
                        info['atom_count'] += 1

                        # PDBQT format: charge in column 71-76, atom type in 78-79
                        if len(line) >= 76:
                            try:
                                charge = float(line[70:76].strip())
                                info['has_charges'] = True
                            except ValueError:
                                pass

                        if len(line) >= 79:
                            atom_type = line[77:79].strip()
                            if atom_type:
                                info['has_atom_types'] = True

            if not info['has_atoms']:
                raise FileValidationError(
                    f"PDBQT file contains no ATOM records: {file_path}"
                )

            if not info['has_charges']:
                info['warnings'].append("PDBQT file missing charge information")

            if not info['has_atom_types']:
                info['warnings'].append("PDBQT file missing atom type information")

            logger.info(f"PDBQT validation passed: {info['atom_count']} atoms, "
                       f"{info['model_count']} models")

            return info

        except FileValidationError:
            raise
        except Exception as e:
            raise FileValidationError(f"Error validating PDBQT structure: {e}")

    @staticmethod
    def validate_sdf_structure(file_path: Path) -> Dict:
        """
        Validate SDF file structure.

        Args:
            file_path: Path to SDF file

        Returns:
            Dictionary with validation results

        Raises:
            FileValidationError: If SDF structure is invalid
        """
        info = {
            'molecule_count': 0,
            'has_atoms': False,
            'has_bonds': False,
            'warnings': []
        }

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

                # Count molecules (delimited by $$$$)
                info['molecule_count'] = content.count('$$$$')

                # Check for V2000 or V3000 format
                if 'V2000' in content or 'V3000' in content:
                    info['has_atoms'] = True
                else:
                    raise FileValidationError(
                        f"SDF file missing V2000/V3000 format marker: {file_path}"
                    )

                # Basic structure check - should have counts line
                lines = content.split('\n')
                if len(lines) < 4:
                    raise FileValidationError(
                        f"SDF file too short (< 4 lines): {file_path}"
                    )

            if info['molecule_count'] == 0:
                info['warnings'].append("SDF file may not be properly terminated (no $$$$)")

            logger.info(f"SDF validation passed: {info['molecule_count']} molecules")

            return info

        except FileValidationError:
            raise
        except Exception as e:
            raise FileValidationError(f"Error validating SDF structure: {e}")

    @staticmethod
    def compute_checksum(file_path: Path, algorithm: str = 'md5') -> str:
        """
        Compute checksum of file for integrity verification.

        Args:
            file_path: Path to file
            algorithm: Hash algorithm ('md5', 'sha256')

        Returns:
            Hexadecimal checksum string
        """
        if algorithm == 'md5':
            hasher = hashlib.md5()
        elif algorithm == 'sha256':
            hasher = hashlib.sha256()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)

        return hasher.hexdigest()

    @staticmethod
    def validate_file(file_path: str, format_type: str,
                     check_structure: bool = True,
                     compute_hash: bool = False) -> Dict:
        """
        Comprehensive file validation.

        Args:
            file_path: Path to file
            format_type: File format (pdb, pdbqt, sdf, mol2)
            check_structure: Whether to perform deep structure validation
            compute_hash: Whether to compute file checksum

        Returns:
            Dictionary with validation results

        Raises:
            FileValidationError: If validation fails
        """
        result = {
            'valid': False,
            'file_path': file_path,
            'format': format_type,
            'size': 0,
            'checksum': None,
            'structure_info': None,
            'errors': [],
            'warnings': []
        }

        try:
            # Step 1: Check existence and readability
            path = FileValidator.validate_file_exists(file_path)

            # Step 2: Check file size
            result['size'] = FileValidator.validate_file_size(path, format_type)

            # Step 3: Check format signature
            FileValidator.validate_format_signature(path, format_type)

            # Step 4: Deep structure validation if requested
            if check_structure:
                if format_type.lower() == 'pdb':
                    result['structure_info'] = FileValidator.validate_pdb_structure(path)
                    result['warnings'].extend(result['structure_info'].get('warnings', []))
                elif format_type.lower() == 'pdbqt':
                    result['structure_info'] = FileValidator.validate_pdbqt_structure(path)
                    result['warnings'].extend(result['structure_info'].get('warnings', []))
                elif format_type.lower() == 'sdf':
                    result['structure_info'] = FileValidator.validate_sdf_structure(path)
                    result['warnings'].extend(result['structure_info'].get('warnings', []))

            # Step 5: Compute checksum if requested
            if compute_hash:
                result['checksum'] = FileValidator.compute_checksum(path)

            result['valid'] = True
            logger.info(f"File validation passed: {file_path}")

        except FileValidationError as e:
            result['errors'].append(str(e))
            logger.error(f"File validation failed: {e}")
            raise
        except Exception as e:
            result['errors'].append(f"Unexpected error: {e}")
            logger.error(f"Unexpected validation error: {e}")
            raise FileValidationError(f"Validation failed: {e}")

        return result


def validate_batch_files(file_list: List[str], format_type: str,
                        fail_fast: bool = False) -> Tuple[List[Dict], List[Dict]]:
    """
    Validate multiple files in batch.

    Args:
        file_list: List of file paths
        format_type: Expected file format
        fail_fast: Stop on first failure

    Returns:
        Tuple of (valid_files, invalid_files) with validation results
    """
    valid_files = []
    invalid_files = []

    for file_path in file_list:
        try:
            result = FileValidator.validate_file(file_path, format_type)
            valid_files.append(result)
        except FileValidationError as e:
            invalid_files.append({
                'file_path': file_path,
                'error': str(e)
            })
            if fail_fast:
                raise

    logger.info(f"Batch validation: {len(valid_files)} valid, "
               f"{len(invalid_files)} invalid")

    return valid_files, invalid_files


if __name__ == "__main__":
    # Example usage
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 3:
        print("Usage: python file_validators.py <file_path> <format>")
        print("Example: python file_validators.py structure.pdb pdb")
        sys.exit(1)

    file_path = sys.argv[1]
    format_type = sys.argv[2]

    try:
        result = FileValidator.validate_file(file_path, format_type,
                                            check_structure=True,
                                            compute_hash=True)
        print(f"✓ Validation passed for {file_path}")
        print(f"  Size: {result['size']} bytes")
        print(f"  Checksum: {result['checksum']}")
        if result['structure_info']:
            print(f"  Structure info: {result['structure_info']}")
        if result['warnings']:
            print(f"  Warnings: {result['warnings']}")
    except FileValidationError as e:
        print(f"❌ Validation failed: {e}")
        sys.exit(1)
