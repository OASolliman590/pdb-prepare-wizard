# Configuration for Post-Docking Analysis Pipeline

# Input/Output Directories
# Use absolute paths or paths relative to the execution directory
INPUT_DIR = ""
OUTPUT_DIR = "./post_docking_results"

# Structure Processing
SPLIT_COMPLEXES = True
EXTRACT_APO_PROTEINS = True
EXTRACT_LIGANDS = True

# Analysis Parameters
ANALYZE_BINDING_AFFINITY = True
GENERATE_VISUALIZATIONS = True
CREATE_SUMMARY_REPORTS = True

# File Format Options
OUTPUT_CSV = True
OUTPUT_EXCEL = True
OUTPUT_PDB = True
OUTPUT_MOL2 = True

# Advanced Options
FIX_CHAINS = False
RUN_ADDITIONAL_DOCKING = False

# Scoring Function Options
USE_VINA_SCORE = True
USE_CNN_SCORE = True  # Requires GNINA

# Directory Structure Options
# SINGLE_FOLDER: All docking results in one directory
# MULTI_FOLDER: Docking results in subdirectories by complex
DIRECTORY_STRUCTURE = "SINGLE_FOLDER"

# For MULTI_FOLDER structure, specify patterns
RECEPTOR_PATTERN = "*receptor*.pdb"
LIGAND_PATTERN = "*ligand*.sdf"
DOCKING_RESULT_PATTERN = "*out*.pdbqt"