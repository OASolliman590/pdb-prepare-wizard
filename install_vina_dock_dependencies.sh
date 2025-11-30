#!/usr/bin/env bash
# Install additional dependencies for vina_dock conda environment
# Based on Jupyter_Dock requirements

set -euo pipefail

echo "=========================================="
echo "Installing dependencies for vina_dock"
echo "=========================================="
echo ""

# Activate vina_dock environment
echo "📦 Activating vina_dock environment..."
conda activate vina_dock

# Install py3Dmol for 3D visualization
echo ""
echo "🌐 Installing py3Dmol for 3D visualization..."
conda install -c conda-forge py3dmol -y

# Install RDKit and Cython (required for ProLIF)
echo ""
echo "🧪 Installing RDKit and Cython (required for ProLIF)..."
conda install -c conda-forge rdkit cython -y

# Install ProLIF from GitHub
echo ""
echo "📊 Installing ProLIF for 2D interaction maps..."
pip install git+https://github.com/chemosim-lab/ProLIF.git

# Verify installations
echo ""
echo "✅ Verifying installations..."
python -c "import py3Dmol; print('✓ py3Dmol installed')" || echo "✗ py3Dmol failed"
python -c "from prolif import ProLIF; print('✓ ProLIF installed')" || echo "✗ ProLIF failed"
python -c "from rdkit import Chem; print('✓ RDKit installed')" || echo "✗ RDKit failed"

echo ""
echo "=========================================="
echo "✅ Installation complete!"
echo "=========================================="
echo ""
echo "Dependencies installed:"
echo "  - py3Dmol (3D visualization)"
echo "  - ProLIF (2D interaction maps)"
echo "  - RDKit (required for ProLIF)"
echo "  - Cython (required for ProLIF)"

