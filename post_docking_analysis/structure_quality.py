"""
Structure quality assessment module for post-docking analysis pipeline.

This module handles structure quality assessment including Ramachandran plots,
clash detection, and other quality metrics.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns

def calculate_ramachandran_angles(pdb_file: Path) -> Dict[str, np.ndarray]:
    """
    Calculate Ramachandran angles (phi and psi) from PDB file.
    
    Parameters
    ----------
    pdb_file : Path
        Path to PDB file
        
    Returns
    -------
    Dict[str, np.ndarray]
        Dictionary containing phi and psi angles
    """
    print(f"📐 Calculating Ramachandran angles for {pdb_file.name}...")
    
    # This is a placeholder implementation
    # In reality, you would:
    # 1. Parse PDB file to extract atom coordinates
    # 2. Calculate phi and psi angles for each residue
    # 3. Handle missing atoms and chain breaks
    
    # Mock data for demonstration
    n_residues = 100
    phi_angles = np.random.uniform(-180, 180, n_residues)
    psi_angles = np.random.uniform(-180, 180, n_residues)
    
    # Apply some realistic constraints (most residues in allowed regions)
    allowed_mask = np.random.random(n_residues) > 0.1  # 90% in allowed regions
    phi_angles[allowed_mask] = np.random.uniform(-60, -30, np.sum(allowed_mask))
    psi_angles[allowed_mask] = np.random.uniform(-30, 30, np.sum(allowed_mask))
    
    print(f"✅ Calculated Ramachandran angles for {n_residues} residues")
    
    return {
        'phi': phi_angles,
        'psi': psi_angles,
        'residue_names': [f'RES_{i}' for i in range(n_residues)]
    }

def detect_structure_clashes(pdb_file: Path, clash_cutoff: float = 2.0) -> Dict:
    """
    Detect structure clashes (overlapping atoms).
    
    Parameters
    ----------
    pdb_file : Path
        Path to PDB file
    clash_cutoff : float
        Distance cutoff for clash detection (Å)
        
    Returns
    -------
    Dict
        Dictionary containing clash detection results
    """
    print(f"⚠️ Detecting structure clashes in {pdb_file.name}...")
    
    # This is a placeholder implementation
    # In reality, you would:
    # 1. Parse PDB file to extract atom coordinates
    # 2. Calculate pairwise distances between all atoms
    # 3. Identify clashes based on van der Waals radii
    
    # Mock data for demonstration
    n_atoms = 500
    clashes = []
    
    # Generate some random clashes
    n_clashes = np.random.poisson(5)  # Average 5 clashes
    for _ in range(n_clashes):
        atom1 = np.random.randint(0, n_atoms)
        atom2 = np.random.randint(0, n_atoms)
        if atom1 != atom2:
            distance = np.random.uniform(1.0, clash_cutoff)
            clashes.append({
                'atom1': f'ATOM_{atom1}',
                'atom2': f'ATOM_{atom2}',
                'distance': distance,
                'severity': 'severe' if distance < 1.5 else 'moderate'
            })
    
    clash_summary = {
        'total_clashes': len(clashes),
        'severe_clashes': len([c for c in clashes if c['severity'] == 'severe']),
        'moderate_clashes': len([c for c in clashes if c['severity'] == 'moderate']),
        'clash_details': clashes
    }
    
    print(f"✅ Clash detection completed: {clash_summary['total_clashes']} clashes found")
    
    return clash_summary

def assess_structure_quality(pdb_file: Path) -> Dict:
    """
    Comprehensive structure quality assessment.
    
    Parameters
    ----------
    pdb_file : Path
        Path to PDB file
        
    Returns
    -------
    Dict
        Dictionary containing quality assessment results
    """
    print(f"🔍 Assessing structure quality for {pdb_file.name}...")
    
    # Calculate Ramachandran angles
    ramachandran_data = calculate_ramachandran_angles(pdb_file)
    
    # Detect clashes
    clash_data = detect_structure_clashes(pdb_file)
    
    # Calculate quality metrics
    phi_angles = ramachandran_data['phi']
    psi_angles = ramachandran_data['psi']
    
    # Ramachandran quality assessment
    ramachandran_quality = assess_ramachandran_quality(phi_angles, psi_angles)
    
    # Overall quality score
    quality_score = calculate_quality_score(ramachandran_quality, clash_data)
    
    quality_assessment = {
        'pdb_file': str(pdb_file),
        'ramachandran_data': ramachandran_data,
        'ramachandran_quality': ramachandran_quality,
        'clash_data': clash_data,
        'quality_score': quality_score,
        'overall_quality': 'High' if quality_score > 0.8 else 'Medium' if quality_score > 0.6 else 'Low'
    }
    
    print(f"✅ Structure quality assessment completed")
    print(f"   Quality score: {quality_score:.2f} ({quality_assessment['overall_quality']})")
    
    return quality_assessment

def assess_ramachandran_quality(phi_angles: np.ndarray, psi_angles: np.ndarray) -> Dict:
    """
    Assess Ramachandran plot quality.
    
    Parameters
    ----------
    phi_angles : np.ndarray
        Phi angles
    psi_angles : np.ndarray
        Psi angles
        
    Returns
    -------
    Dict
        Dictionary containing Ramachandran quality metrics
    """
    # Define Ramachandran regions (simplified)
    # In reality, you would use more sophisticated region definitions
    
    n_residues = len(phi_angles)
    
    # Count residues in different regions
    allowed_count = 0
    generously_allowed_count = 0
    disallowed_count = 0
    
    for phi, psi in zip(phi_angles, psi_angles):
        # Simplified region definitions
        if (-60 <= phi <= -30 and -30 <= psi <= 30) or \
           (60 <= phi <= 120 and -60 <= psi <= 0):
            allowed_count += 1
        elif (-180 <= phi <= 180 and -180 <= psi <= 180):
            generously_allowed_count += 1
        else:
            disallowed_count += 1
    
    ramachandran_quality = {
        'total_residues': n_residues,
        'allowed_residues': allowed_count,
        'generously_allowed_residues': generously_allowed_count,
        'disallowed_residues': disallowed_count,
        'allowed_percentage': (allowed_count / n_residues) * 100,
        'generously_allowed_percentage': (generously_allowed_count / n_residues) * 100,
        'disallowed_percentage': (disallowed_count / n_residues) * 100
    }
    
    return ramachandran_quality

def calculate_quality_score(ramachandran_quality: Dict, clash_data: Dict) -> float:
    """
    Calculate overall structure quality score.
    
    Parameters
    ----------
    ramachandran_quality : Dict
        Ramachandran quality metrics
    clash_data : Dict
        Clash detection results
        
    Returns
    -------
    float
        Overall quality score (0-1)
    """
    # Ramachandran score (0-1)
    ramachandran_score = ramachandran_quality['allowed_percentage'] / 100.0
    
    # Clash score (0-1, lower is better)
    total_clashes = clash_data['total_clashes']
    clash_score = max(0, 1 - (total_clashes / 10.0))  # Penalty for clashes
    
    # Weighted combination
    overall_score = 0.7 * ramachandran_score + 0.3 * clash_score
    
    return min(1.0, max(0.0, overall_score))

def create_quality_visualizations(quality_results: List[Dict], output_dir: Path) -> List[Path]:
    """
    Create visualizations for structure quality assessment.
    
    Parameters
    ----------
    quality_results : List[Dict]
        List of quality assessment results
    output_dir : Path
        Output directory for visualizations
        
    Returns
    -------
    List[Path]
        List of created visualization files
    """
    print("📊 Creating structure quality visualizations...")
    
    output_dir.mkdir(exist_ok=True)
    created_files = []
    
    # 1. Ramachandran plots
    n_structures = len(quality_results)
    fig, axes = plt.subplots(2, (n_structures + 1) // 2, figsize=(5 * ((n_structures + 1) // 2), 10))
    if n_structures == 1:
        axes = [axes]
    elif n_structures <= 2:
        axes = axes.flatten()
    else:
        axes = axes.flatten()
    
    for i, quality_data in enumerate(quality_results):
        if i >= len(axes):
            break
            
        phi_angles = quality_data['ramachandran_data']['phi']
        psi_angles = quality_data['ramachandran_data']['psi']
        
        # Create Ramachandran plot
        ax = axes[i]
        ax.scatter(phi_angles, psi_angles, alpha=0.6, s=20)
        ax.set_xlabel('Phi (degrees)')
        ax.set_ylabel('Psi (degrees)')
        ax.set_title(f"Ramachandran Plot - {Path(quality_data['pdb_file']).stem}")
        ax.set_xlim(-180, 180)
        ax.set_ylim(-180, 180)
        ax.grid(True, alpha=0.3)
        
        # Add quality information
        quality_score = quality_data['quality_score']
        ax.text(0.02, 0.98, f'Quality Score: {quality_score:.2f}', 
                transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Hide unused subplots
    for i in range(n_structures, len(axes)):
        axes[i].set_visible(False)
    
    plt.tight_layout()
    ramachandran_file = output_dir / 'ramachandran_plots.png'
    plt.savefig(ramachandran_file, dpi=300, bbox_inches='tight')
    plt.close()
    created_files.append(ramachandran_file)
    
    # 2. Quality score comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Quality scores
    structure_names = [Path(q['pdb_file']).stem for q in quality_results]
    quality_scores = [q['quality_score'] for q in quality_results]
    
    bars = ax1.bar(range(len(structure_names)), quality_scores, 
                   color=['green' if s > 0.8 else 'orange' if s > 0.6 else 'red' for s in quality_scores])
    ax1.set_xlabel('Structure')
    ax1.set_ylabel('Quality Score')
    ax1.set_title('Structure Quality Scores')
    ax1.set_xticks(range(len(structure_names)))
    ax1.set_xticklabels(structure_names, rotation=45, ha='right')
    ax1.set_ylim(0, 1)
    ax1.grid(True, alpha=0.3)
    
    # Add quality thresholds
    ax1.axhline(y=0.8, color='green', linestyle='--', alpha=0.7, label='High Quality')
    ax1.axhline(y=0.6, color='orange', linestyle='--', alpha=0.7, label='Medium Quality')
    ax1.legend()
    
    # Clash summary
    clash_counts = [q['clash_data']['total_clashes'] for q in quality_results]
    ax2.bar(range(len(structure_names)), clash_counts, color='red', alpha=0.7)
    ax2.set_xlabel('Structure')
    ax2.set_ylabel('Number of Clashes')
    ax2.set_title('Structure Clashes')
    ax2.set_xticks(range(len(structure_names)))
    ax2.set_xticklabels(structure_names, rotation=45, ha='right')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    quality_file = output_dir / 'quality_comparison.png'
    plt.savefig(quality_file, dpi=300, bbox_inches='tight')
    plt.close()
    created_files.append(quality_file)
    
    print(f"✅ Created {len(created_files)} quality visualizations")
    return created_files

