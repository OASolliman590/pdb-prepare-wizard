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

# Advanced Analysis Features
ENABLE_PROTEIN_LIGAND_BREAKDOWN = True
ENABLE_RMSD_ANALYSIS = True
ENABLE_STRUCTURE_QUALITY = True
ENABLE_CORRELATION_ANALYSIS = True
ENABLE_PYMOL_VISUALIZATIONS = True

# RMSD Analysis Settings
RMSD_CLUSTERING_METHOD = "kmeans"  # "kmeans" or "dbscan"
RMSD_N_CLUSTERS = 3
RMSD_CUTOFF = 2.0  # Å

# Structure Quality Settings
QUALITY_CLASH_CUTOFF = 2.0  # Å
QUALITY_RAMACHANDRAN_THRESHOLD = 0.8

# PyMOL Visualization Settings
PYMOL_HIGHLIGHT_RESIDUES = [212, 213, 214]  # Residues to highlight
PYMOL_INTERACTION_CUTOFF = 4.0  # Å
PYMOL_DPI = 600

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