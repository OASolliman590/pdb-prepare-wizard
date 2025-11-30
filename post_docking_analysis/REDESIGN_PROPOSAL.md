# Post-Docking Analysis Pipeline - Simplified Redesign

## 🎯 Core Requirements

### 1. Simplified Input Structure
```
Input:
├── sdf_folder/          # Docking poses (SDF files)
│   ├── complex1_top.sdf
│   ├── complex2_top.sdf
│   └── ...
├── log_folder/          # Docking logs (can be same as sdf_folder)
│   ├── complex1_log
│   ├── complex2_log
│   └── ...
└── receptors_folder/    # Receptor PDBQT files
    ├── VEGFR2_4AG8_cleaned.pdbqt
    ├── MMP9_4WZV_cleaned.pdbqt
    └── ...
```

### 2. Core Functionality

#### A. Generate all_scores.csv
- Parse log files (GNINA/Vina)
- Extract scores (vina_affinity, cnn_score if GNINA)
- Create unified CSV with columns: `tag`, `mode`, `vina_affinity`, `cnn_score` (optional)

#### B. Create Complex PDB Files
- For each pose: receptor + ligand → complex PDB
- Match receptor to pose using pairlist.csv or filename matching
- Output: `output/complexes/complex1.pdb`, `complex2.pdb`, etc.

#### C. Binding Affinity Analysis
- **Top performers**: Rank by affinity
- **Comparative benchmarking**: 
  - Extract PDB code from receptor filename: `VEGFR2_4AG8_cleaned.pdbqt` → `4AG8`
  - Extract PDB code from ligand filename: `4AG8_ligand_AXI_A_2000.pdbqt` → `4AG8`
  - Match if PDB codes match → use as comparative reference
  - Site ID marked in output name (e.g., `catalytic`, `allosteric`)
- **Dynamic threshold**: "auto" mode calculates from data
- **Categorization**: Strong/Moderate/Weak binders
- **Breakdown**: By protein, by ligand

#### D. RMSD Analysis
- Pose clustering (K-means/DBSCAN)
- Conformational diversity
- Pose similarity matrices

#### E. Pose Extraction & Organization
- Extract best poses as PDB complexes ✓
- Organize by affinity categories ✓
- Support PDB format (primary), SDF/MOL2 optional

#### F. Visualizations (Simplified)
- Remove PandaMap (doesn't work)
- Basic 2D plots: affinity distributions, heatmaps
- Simple PyMOL sessions (optional, configurable)
- Make visualization parameters easily adjustable

#### G. Pairlist Integration
- Use pairlist.csv for receptor-ligand mapping ✓
- Eliminates filename pattern matching errors ✓

### 3. Remove
- ❌ Plugin system (not needed)
- ❌ PandaMap integration (doesn't work)
- ❌ Complex visualization customization (too complicated)

## 📋 Proposed Workflow

```
1. Input Detection
   ├── Find SDF files (poses)
   ├── Find log files (scores)
   └── Find receptor PDBQT files

2. Generate all_scores.csv
   ├── Parse GNINA logs → extract scores
   ├── Parse Vina logs → extract scores
   └── Create unified CSV

3. Match Receptors to Poses
   ├── Use pairlist.csv if available
   └── Fallback: filename pattern matching

4. Create Complex PDB Files
   ├── For each pose: receptor + ligand → complex
   └── Save to output/complexes/

5. Binding Affinity Analysis
   ├── Load all_scores.csv
   ├── Identify comparative references (PDB code matching)
   ├── Calculate thresholds
   ├── Categorize binders
   └── Generate breakdowns

6. RMSD Analysis
   ├── Extract poses
   ├── Calculate RMSD matrix
   ├── Cluster poses
   └── Analyze diversity

7. Generate Reports
   ├── CSV reports
   ├── Summary text
   └── Basic visualizations

8. Organize Output
   ├── Best poses by affinity
   ├── Strong/Moderate/Weak binders
   └── Complex PDB files
```

## 🔧 Simplified Configuration

```yaml
# Input/Output
paths:
  sdf_folder: ""           # Folder with SDF pose files
  log_folder: ""          # Folder with log files (can be same as sdf_folder)
  receptors_folder: ""    # Folder with receptor PDBQT files
  output_dir: "./post_docking_results"
  pairlist_file: ""       # Optional: pairlist.csv path

# Analysis
analysis:
  generate_all_scores: true
  create_complexes: true
  binding_affinity: true
  rmsd_analysis: true
  extract_poses: true
  generate_reports: true
  generate_visualizations: true

# Binding Affinity
binding_affinity:
  strong_binder_threshold: "auto"  # "auto", "comparative", or numeric
  top_performers_count: 10
  analyze_by_protein: true
  analyze_by_ligand: true
  comparative_matching: "pdb_code"  # Match by PDB code in filenames

# RMSD
rmsd:
  clustering_method: "kmeans"  # "kmeans" or "dbscan"
  kmeans_clusters: 3
  dbscan_epsilon: 2.0
  dbscan_min_samples: 2

# Pose Extraction
pose_extraction:
  extract_all_poses: false
  best_pose_criteria: "affinity"
  output_formats: [pdb]  # Primary format

# Visualizations (Simplified)
visualization:
  generate_2d_plots: true
  generate_pymol: false  # Optional, disabled by default
  dpi: 300
  plot_types: ["affinity_distribution", "heatmap", "top_performers"]
```

## 🎨 Comparative Benchmarking Logic

```python
def identify_comparative_reference(receptor_file, ligand_files):
    """
    Identify comparative reference ligand by matching PDB codes.
    
    Example:
    - Receptor: VEGFR2_4AG8_cleaned.pdbqt → PDB code: 4AG8
    - Ligand: 4AG8_ligand_AXI_A_2000.pdbqt → PDB code: 4AG8
    - Match! Use this ligand as comparative reference
    
    Site ID extraction:
    - If pairlist.csv has site_id column, use that
    - Otherwise, extract from filename pattern
    """
    receptor_pdb_code = extract_pdb_code(receptor_file)
    
    for ligand_file in ligand_files:
        ligand_pdb_code = extract_pdb_code(ligand_file)
        if receptor_pdb_code == ligand_pdb_code:
            site_id = extract_site_id(ligand_file)  # From pairlist or filename
            return {
                'ligand_file': ligand_file,
                'pdb_code': ligand_pdb_code,
                'site_id': site_id
            }
    
    return None
```

## 📊 Output Structure

```
post_docking_results/
├── all_scores.csv                    # Generated scores CSV
├── complexes/                        # Receptor+ligand complexes
│   ├── complex1.pdb
│   ├── complex2.pdb
│   └── ...
├── best_poses/                      # Best poses organized
│   ├── strong_binders/
│   ├── moderate_binders/
│   └── weak_binders/
├── reports/                         # Analysis reports
│   ├── binding_affinity_summary.csv
│   ├── top_performers.csv
│   ├── by_protein.csv
│   ├── by_ligand.csv
│   └── summary.txt
├── rmsd_analysis/                    # RMSD results
│   ├── rmsd_matrix.csv
│   ├── clusters.csv
│   └── diversity_analysis.csv
└── visualizations/                  # Simple plots
    ├── affinity_distribution.png
    ├── top_performers.png
    └── heatmap.png
```

## ✅ Implementation Checklist

- [ ] Simplify input structure (sdf_folder, log_folder, receptors_folder)
- [ ] Generate all_scores.csv from logs
- [ ] Create complex PDB files (receptor + ligand)
- [ ] Implement PDB code-based comparative matching
- [ ] Simplify binding affinity analysis
- [ ] Keep RMSD analysis as-is
- [ ] Remove PandaMap integration
- [ ] Remove plugin system
- [ ] Simplify visualizations (basic plots only)
- [ ] Make visualization parameters easily configurable
- [ ] Update CLI to match new structure
- [ ] Update documentation

