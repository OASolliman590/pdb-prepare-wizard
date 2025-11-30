# Visualization Guide - py3Dmol and ProLIF

This guide explains how to use the 3D visualization (py3Dmol) and 2D interaction maps (ProLIF) features, inspired by [Jupyter_Dock](https://github.com/AngelRuizMoreno/Jupyter_Dock).

## Installation

### Install Dependencies

Run the installation script:

```bash
./install_vina_dock_dependencies.sh
```

Or manually:

```bash
conda activate vina_dock
conda install -c conda-forge py3dmol rdkit cython -y
pip install git+https://github.com/chemosim-lab/ProLIF.git
```

## Features

### 1. 3D Visualization with py3Dmol

Creates interactive HTML visualizations of protein-ligand complexes.

#### Individual Complex Visualization
- Each best pose/complex gets its own interactive 3D visualization
- Shows protein (cartoon) and ligand (stick)
- Interactive: rotate, zoom, pan
- Output: HTML files in `3d_visualizations/individual_complexes/`

#### Aggregated Visualization by Protein
- All ligands docked to the same protein in one figure
- Each ligand has a different color
- Includes legend
- Output: HTML files in `3d_visualizations/aggregated_by_protein/`

### 2. 2D Interaction Maps with ProLIF

Creates 2D interaction network diagrams showing:
- Hydrogen bonds
- Hydrophobic interactions
- π-π stacking
- Salt bridges
- Other interactions

#### Features
- One interaction map per best pose/complex
- Publication-quality (300 DPI)
- Shows all interaction types
- Output: PNG files in `interaction_maps/`

## Usage

The visualizations are automatically generated when running the simplified pipeline:

```bash
python -m post_docking_analysis.simplified_cli \
  --sdf-folder /path/to/sdf \
  --log-folder /path/to/logs \
  --receptors-folder /path/to/receptors \
  --output /path/to/output \
  --pairlist /path/to/pairlist.csv
```

## Output Structure

```
output/
├── 3d_visualizations/
│   ├── individual_complexes/
│   │   ├── complex1_3d.html
│   │   ├── complex2_3d.html
│   │   └── ...
│   └── aggregated_by_protein/
│       ├── VEGFR2_all_ligands_3d.html
│       ├── MMP9_all_ligands_3d.html
│       └── ...
└── interaction_maps/
    ├── complex1_interaction_map.png
    ├── complex2_interaction_map.png
    └── ...
```

## Viewing Results

### 3D Visualizations (HTML)
- Open HTML files in any web browser
- Interactive: click and drag to rotate, scroll to zoom
- Works offline (all data embedded)

### 2D Interaction Maps (PNG)
- Open PNG files in any image viewer
- Publication-ready (300 DPI)
- Can be included directly in papers/presentations

## Customization

### py3Dmol Styling

You can customize protein and ligand styles by modifying the code in `py3dmol_visualizer.py`:

```python
# Protein style options
style_protein = {
    'cartoon': {'color': 'spectrum'},  # or 'rainbow', 'spectrum', etc.
    'stick': {'radius': 0.3}  # optional
}

# Ligand style options
style_ligand = {
    'stick': {'colorscheme': 'greenCarbon'},  # or 'cyanCarbon', etc.
    'sphere': {'radius': 0.5}  # optional
}
```

### ProLIF Interaction Maps

The interaction maps are automatically generated with ProLIF's default settings. To customize:

1. Modify `prolif_interaction_maps.py`
2. Adjust figure size: `figsize=(12, 8)`
3. Adjust DPI: `dpi=300`
4. Change ligand residue name: `ligand_resname="UNK"`

## Troubleshooting

### py3Dmol not working
- Verify installation: `python -c "import py3Dmol; print(py3Dmol.__version__)"`
- Check browser compatibility (modern browsers required)
- Ensure PDB files are valid

### ProLIF not working
- Verify RDKit: `python -c "from rdkit import Chem; print('OK')"`
- Verify ProLIF: `python -c "from prolif import ProLIF; print('OK')"`
- Check that ligand residue name matches PDB file (default: "UNK")
- Ensure PDB files contain both protein and ligand

### Missing ligands in aggregated view
- Check that receptor PDB files exist (not just PDBQT)
- Verify protein names match between scores and receptor files
- Check that complexes directory contains PDB files

## References

- **Jupyter_Dock**: https://github.com/AngelRuizMoreno/Jupyter_Dock
- **py3Dmol**: https://github.com/3dmol/3Dmol.js
- **ProLIF**: https://github.com/chemosim-lab/ProLIF

