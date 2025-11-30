"""
Enhanced RMSD Analysis with actual structure-based calculations.

Calculates RMSD from PDB structures, performs pose clustering,
and analyzes conformational diversity.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from sklearn.cluster import KMeans, DBSCAN
import matplotlib.pyplot as plt
import seaborn as sns
import logging

try:
    from Bio.PDB import PDBParser, Superimposer
    from Bio import pairwise2
    BIOPYTHON_AVAILABLE = True
except ImportError:
    BIOPYTHON_AVAILABLE = False

logger = logging.getLogger(__name__)


def calculate_rmsd_between_structures(pdb_file1: Path, pdb_file2: Path, ligand_only: bool = True) -> float:
    """
    Calculate RMSD between two PDB structures.
    
    Parameters
    ----------
    pdb_file1 : Path
        Path to first PDB file
    pdb_file2 : Path
        Path to second PDB file
    ligand_only : bool
        If True, calculate RMSD only for ligand atoms (HETATM)
        
    Returns
    -------
    float
        RMSD value in Angstroms, or np.nan if calculation fails
    """
    if not BIOPYTHON_AVAILABLE:
        logger.warning("BioPython not available, using fallback RMSD calculation")
        return _calculate_rmsd_simple(pdb_file1, pdb_file2, ligand_only)
    
    try:
        parser = PDBParser(QUIET=True)
        
        # Parse structures
        structure1 = parser.get_structure('struct1', str(pdb_file1))
        structure2 = parser.get_structure('struct2', str(pdb_file2))
        
        # Extract coordinates
        coords1 = []
        coords2 = []
        
        for model in structure1:
            for chain in model:
                for residue in chain:
                    for atom in residue:
                        if ligand_only:
                            if residue.id[0] != ' ' or atom.name.startswith('H'):
                                continue
                        if atom.name.startswith('H'):
                            continue
                        coords1.append(atom.coord)
        
        for model in structure2:
            for chain in model:
                for residue in chain:
                    for atom in residue:
                        if ligand_only:
                            if residue.id[0] != ' ' or atom.name.startswith('H'):
                                continue
                        if atom.name.startswith('H'):
                            continue
                        coords2.append(atom.coord)
        
        if len(coords1) != len(coords2) or len(coords1) == 0:
            return np.nan
        
        coords1 = np.array(coords1)
        coords2 = np.array(coords2)
        
        # Align structures
        superimposer = Superimposer()
        superimposer.set_atoms(coords1, coords2)
        superimposer.apply(coords2)
        
        # Calculate RMSD
        rmsd = np.sqrt(np.mean(np.sum((coords1 - coords2) ** 2, axis=1)))
        
        return rmsd
        
    except Exception as e:
        logger.warning(f"Error calculating RMSD between {pdb_file1.name} and {pdb_file2.name}: {e}")
        return _calculate_rmsd_simple(pdb_file1, pdb_file2, ligand_only)


def _calculate_rmsd_simple(pdb_file1: Path, pdb_file2: Path, ligand_only: bool = True) -> float:
    """
    Simple RMSD calculation without BioPython.
    
    Parameters
    ----------
    pdb_file1 : Path
        Path to first PDB file
    pdb_file2 : Path
        Path to second PDB file
    ligand_only : bool
        If True, calculate RMSD only for ligand atoms
        
    Returns
    -------
    float
        RMSD value in Angstroms
    """
    try:
        coords1 = []
        coords2 = []
        
        # Read first structure
        with open(pdb_file1, 'r') as f:
            for line in f:
                if ligand_only:
                    if line.startswith('HETATM'):
                        parts = line.split()
                        if len(parts) >= 6:
                            try:
                                x, y, z = float(parts[5]), float(parts[6]), float(parts[7])
                                coords1.append([x, y, z])
                            except (ValueError, IndexError):
                                continue
                else:
                    if line.startswith(('ATOM', 'HETATM')):
                        parts = line.split()
                        if len(parts) >= 6:
                            try:
                                x, y, z = float(parts[5]), float(parts[6]), float(parts[7])
                                coords1.append([x, y, z])
                            except (ValueError, IndexError):
                                continue
        
        # Read second structure
        with open(pdb_file2, 'r') as f:
            for line in f:
                if ligand_only:
                    if line.startswith('HETATM'):
                        parts = line.split()
                        if len(parts) >= 6:
                            try:
                                x, y, z = float(parts[5]), float(parts[6]), float(parts[7])
                                coords2.append([x, y, z])
                            except (ValueError, IndexError):
                                continue
                else:
                    if line.startswith(('ATOM', 'HETATM')):
                        parts = line.split()
                        if len(parts) >= 6:
                            try:
                                x, y, z = float(parts[5]), float(parts[6]), float(parts[7])
                                coords2.append([x, y, z])
                            except (ValueError, IndexError):
                                continue
        
        if len(coords1) != len(coords2) or len(coords1) == 0:
            return np.nan
        
        coords1 = np.array(coords1)
        coords2 = np.array(coords2)
        
        # Center structures
        coords1 -= coords1.mean(axis=0)
        coords2 -= coords2.mean(axis=0)
        
        # Calculate RMSD
        rmsd = np.sqrt(np.mean(np.sum((coords1 - coords2) ** 2, axis=1)))
        
        return rmsd
        
    except Exception as e:
        logger.warning(f"Error in simple RMSD calculation: {e}")
        return np.nan


def calculate_rmsd_matrix_from_pdbs(
    pdb_files: List[Path],
    ligand_only: bool = True,
    max_pairs: Optional[int] = None
) -> Tuple[np.ndarray, List[str]]:
    """
    Calculate RMSD matrix from PDB files.
    
    Parameters
    ----------
    pdb_files : List[Path]
        List of PDB file paths
    ligand_only : bool
        Calculate RMSD only for ligand atoms
    max_pairs : int, optional
        Maximum number of pairs to calculate (for performance)
        
    Returns
    -------
    Tuple[np.ndarray, List[str]]
        RMSD matrix and list of filenames
    """
    logger.info(f"📏 Calculating RMSD matrix from {len(pdb_files)} PDB files...")
    
    n = len(pdb_files)
    rmsd_matrix = np.zeros((n, n))
    filenames = [f.stem for f in pdb_files]
    
    total_pairs = n * (n - 1) // 2
    calculated = 0
    
    for i in range(n):
        for j in range(i + 1, n):
            if max_pairs and calculated >= max_pairs:
                # Fill remaining with NaN
                rmsd_matrix[i, j] = np.nan
                rmsd_matrix[j, i] = np.nan
                continue
            
            rmsd = calculate_rmsd_between_structures(
                pdb_files[i],
                pdb_files[j],
                ligand_only=ligand_only
            )
            
            rmsd_matrix[i, j] = rmsd
            rmsd_matrix[j, i] = rmsd
            
            calculated += 1
            
            if calculated % 10 == 0:
                logger.debug(f"  Calculated {calculated}/{total_pairs} pairs...")
    
    logger.info(f"✅ RMSD matrix calculated ({calculated} pairs)")
    return rmsd_matrix, filenames


def analyze_pose_clustering_enhanced(
    poses_data: pd.DataFrame,
    rmsd_matrix: np.ndarray,
    pdb_files: List[Path],
    method: str = 'kmeans',
    n_clusters: int = 3,
    eps: float = 2.0,
    min_samples: int = 2
) -> Dict:
    """
    Enhanced pose clustering analysis with actual RMSD data.
    
    Parameters
    ----------
    poses_data : pd.DataFrame
        DataFrame containing pose metadata
    rmsd_matrix : np.ndarray
        RMSD matrix between poses
    pdb_files : List[Path]
        List of PDB file paths
    method : str
        Clustering method ('kmeans' or 'dbscan')
    n_clusters : int
        Number of clusters for K-means
    eps : float
        Epsilon parameter for DBSCAN
    min_samples : int
        Minimum samples for DBSCAN
        
    Returns
    -------
    Dict
        Dictionary containing clustering results
    """
    logger.info(f"🔍 Analyzing pose clustering using {method}...")
    
    # Remove NaN values for clustering
    valid_mask = ~np.isnan(rmsd_matrix).any(axis=1)
    valid_indices = np.where(valid_mask)[0]
    
    if len(valid_indices) < n_clusters:
        logger.warning(f"⚠️  Not enough valid poses for {n_clusters} clusters")
        n_clusters = max(1, len(valid_indices) // 2)  # At least 1, or half of available
    
    if n_clusters == 0 or len(valid_indices) == 0:
        logger.warning("⚠️  No valid poses for clustering")
        return {
            'poses_with_clusters': poses_data.copy(),
            'cluster_summary': pd.DataFrame(),
            'cluster_centroids': pd.DataFrame(),
            'rmsd_matrix': rmsd_matrix,
            'cluster_labels': np.array([]),
            'valid_indices': np.array([])
        }
    
    valid_rmsd = rmsd_matrix[np.ix_(valid_indices, valid_indices)]
    valid_poses = poses_data.iloc[valid_indices].copy()
    
    # Perform clustering
    if method == 'kmeans':
        clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = clusterer.fit_predict(valid_rmsd)
    elif method == 'dbscan':
        clusterer = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
        cluster_labels = clusterer.fit_predict(valid_rmsd)
    else:
        raise ValueError(f"Unknown clustering method: {method}")
    
    # Add cluster labels to poses data
    valid_poses['cluster'] = cluster_labels
    
    # Analyze clusters
    cluster_summary = []
    cluster_centroids = []
    
    for cluster_id in sorted(set(cluster_labels)):
        if cluster_id == -1:  # Skip noise points in DBSCAN
            continue
        
        cluster_poses = valid_poses[valid_poses['cluster'] == cluster_id]
        
        if len(cluster_poses) == 0:
            continue
        
        # Cluster statistics
        cluster_summary.append({
            'cluster': cluster_id,
            'size': len(cluster_poses),
            'avg_affinity': cluster_poses['vina_affinity'].mean() if 'vina_affinity' in cluster_poses.columns else np.nan,
            'min_affinity': cluster_poses['vina_affinity'].min() if 'vina_affinity' in cluster_poses.columns else np.nan,
            'max_affinity': cluster_poses['vina_affinity'].max() if 'vina_affinity' in cluster_poses.columns else np.nan,
            'avg_rmsd': valid_rmsd[cluster_poses.index][:, cluster_poses.index].mean() if len(cluster_poses) > 1 else 0.0
        })
        
        # Find centroid (pose with lowest average RMSD to others in cluster)
        if len(cluster_poses) > 1:
            cluster_indices = cluster_poses.index
            cluster_rmsd = valid_rmsd[np.ix_(cluster_indices, cluster_indices)]
            avg_rmsd_per_pose = cluster_rmsd.mean(axis=1)
            centroid_idx = cluster_indices[np.argmin(avg_rmsd_per_pose)]
        else:
            centroid_idx = cluster_poses.index[0]
        
        cluster_centroids.append({
            'cluster': cluster_id,
            'centroid_pose': valid_poses.loc[centroid_idx, 'tag'] if 'tag' in valid_poses.columns else f"pose_{centroid_idx}",
            'centroid_affinity': valid_poses.loc[centroid_idx, 'vina_affinity'] if 'vina_affinity' in valid_poses.columns else np.nan,
            'cluster_size': len(cluster_poses),
            'avg_affinity': cluster_poses['vina_affinity'].mean() if 'vina_affinity' in cluster_poses.columns else np.nan
        })
    
    cluster_summary_df = pd.DataFrame(cluster_summary)
    cluster_centroids_df = pd.DataFrame(cluster_centroids)
    
    logger.info(f"✅ Pose clustering completed")
    logger.info(f"   Found {len(cluster_summary_df)} clusters")
    if len(cluster_centroids_df) > 0:
        logger.info(f"   Best cluster affinity: {cluster_centroids_df['avg_affinity'].min():.2f} kcal/mol")
    
    return {
        'poses_with_clusters': valid_poses,
        'cluster_summary': cluster_summary_df,
        'cluster_centroids': cluster_centroids_df,
        'rmsd_matrix': valid_rmsd,
        'cluster_labels': cluster_labels,
        'valid_indices': valid_indices
    }


def analyze_conformational_diversity_enhanced(
    poses_data: pd.DataFrame,
    rmsd_matrix: np.ndarray
) -> Dict:
    """
    Enhanced conformational diversity analysis.
    
    Parameters
    ----------
    poses_data : pd.DataFrame
        DataFrame containing pose metadata
    rmsd_matrix : np.ndarray
        RMSD matrix between poses
        
    Returns
    -------
    Dict
        Dictionary containing diversity analysis results
    """
    logger.info("🌊 Analyzing conformational diversity...")
    
    # Remove NaN values
    valid_mask = ~np.isnan(rmsd_matrix).any(axis=1)
    valid_indices = np.where(valid_mask)[0]
    valid_rmsd = rmsd_matrix[np.ix_(valid_indices, valid_indices)]
    valid_poses = poses_data.iloc[valid_indices].copy()
    
    # Calculate diversity metrics for each pose
    diversity_metrics = []
    
    for i, (idx, pose) in enumerate(valid_poses.iterrows()):
        # Calculate average RMSD to all other poses
        other_rmsds = np.concatenate([valid_rmsd[i, :i], valid_rmsd[i, i+1:]])
        other_rmsds = other_rmsds[~np.isnan(other_rmsds)]
        
        if len(other_rmsds) == 0:
            continue
        
        diversity_metrics.append({
            'tag': pose.get('tag', f'pose_{idx}'),
            'vina_affinity': pose.get('vina_affinity', np.nan),
            'avg_rmsd_to_others': np.mean(other_rmsds),
            'max_rmsd_to_others': np.max(other_rmsds),
            'min_rmsd_to_others': np.min(other_rmsds),
            'rmsd_std': np.std(other_rmsds),
            'median_rmsd': np.median(other_rmsds)
        })
    
    diversity_df = pd.DataFrame(diversity_metrics)
    
    # Overall diversity statistics
    upper_triangle = valid_rmsd[np.triu_indices_from(valid_rmsd, k=1)]
    upper_triangle = upper_triangle[~np.isnan(upper_triangle)]
    
    overall_stats = {
        'total_poses': len(valid_poses),
        'avg_pairwise_rmsd': np.mean(upper_triangle),
        'max_pairwise_rmsd': np.max(upper_triangle),
        'min_pairwise_rmsd': np.min(upper_triangle),
        'rmsd_std': np.std(upper_triangle),
        'median_pairwise_rmsd': np.median(upper_triangle)
    }
    
    # Identify most diverse poses
    if len(diversity_df) > 0:
        most_diverse = diversity_df.nlargest(5, 'avg_rmsd_to_others')
        least_diverse = diversity_df.nsmallest(5, 'avg_rmsd_to_others')
    else:
        most_diverse = pd.DataFrame()
        least_diverse = pd.DataFrame()
    
    logger.info(f"✅ Conformational diversity analysis completed")
    logger.info(f"   Average pairwise RMSD: {overall_stats['avg_pairwise_rmsd']:.2f} Å")
    if len(most_diverse) > 0:
        logger.info(f"   Most diverse pose: {most_diverse.iloc[0]['tag']} ({most_diverse.iloc[0]['avg_rmsd_to_others']:.2f} Å)")
    
    return {
        'diversity_metrics': diversity_df,
        'overall_stats': overall_stats,
        'most_diverse_poses': most_diverse,
        'least_diverse_poses': least_diverse,
        'rmsd_matrix': valid_rmsd
    }


def create_rmsd_visualizations_enhanced(
    clustering_results: Dict,
    diversity_results: Dict,
    output_dir: Path,
    dpi: int = 300
) -> List[Path]:
    """
    Create enhanced RMSD visualizations with heatmaps and 2D plots.
    
    Parameters
    ----------
    clustering_results : Dict
        Results from pose clustering analysis
    diversity_results : Dict
        Results from diversity analysis
    output_dir : Path
        Output directory for visualizations
    dpi : int
        DPI for image output
        
    Returns
    -------
    List[Path]
        List of created visualization files
    """
    logger.info("📊 Creating enhanced RMSD visualizations...")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    created_files = []
    
    rmsd_matrix = clustering_results['rmsd_matrix']
    poses_data = clustering_results['poses_with_clusters']
    
    # 1. RMSD Heatmap (similarity matrix)
    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(rmsd_matrix, cmap='viridis', aspect='auto', interpolation='nearest')
    ax.set_title('RMSD Similarity Matrix', fontsize=16, fontweight='bold')
    ax.set_xlabel('Pose Index', fontsize=12)
    ax.set_ylabel('Pose Index', fontsize=12)
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('RMSD (Å)', fontsize=12)
    plt.tight_layout()
    
    heatmap_file = output_dir / 'rmsd_heatmap.png'
    plt.savefig(heatmap_file, dpi=dpi, bbox_inches='tight')
    plt.close()
    created_files.append(heatmap_file)
    
    # 2. Cluster analysis plot
    if len(poses_data) > 0 and 'cluster' in poses_data.columns:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Binding affinity vs cluster
        unique_clusters = sorted([c for c in poses_data['cluster'].unique() if c != -1])
        colors = plt.cm.Set3(np.linspace(0, 1, len(unique_clusters)))
        
        for i, cluster in enumerate(unique_clusters):
            cluster_data = poses_data[poses_data['cluster'] == cluster]
            if 'vina_affinity' in cluster_data.columns:
                ax1.scatter([cluster] * len(cluster_data), cluster_data['vina_affinity'],
                           c=[colors[i]], label=f'Cluster {cluster}', alpha=0.7, s=50)
        
        ax1.set_xlabel('Cluster', fontsize=12)
        ax1.set_ylabel('Binding Affinity (kcal/mol)', fontsize=12)
        ax1.set_title('Binding Affinity by Cluster', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Cluster size distribution
        cluster_sizes = poses_data['cluster'].value_counts().sort_index()
        cluster_sizes = cluster_sizes[cluster_sizes.index != -1]
        if len(cluster_sizes) > 0:
            ax2.bar(cluster_sizes.index, cluster_sizes.values, color=colors[:len(cluster_sizes)])
            ax2.set_xlabel('Cluster', fontsize=12)
            ax2.set_ylabel('Number of Poses', fontsize=12)
            ax2.set_title('Cluster Size Distribution', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        cluster_file = output_dir / 'cluster_analysis.png'
        plt.savefig(cluster_file, dpi=dpi, bbox_inches='tight')
        plt.close()
        created_files.append(cluster_file)
    
    # 3. Diversity analysis plot
    if len(diversity_results['diversity_metrics']) > 0:
        diversity_df = diversity_results['diversity_metrics']
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Binding affinity vs diversity
        if 'vina_affinity' in diversity_df.columns and 'avg_rmsd_to_others' in diversity_df.columns:
            scatter = ax1.scatter(diversity_df['avg_rmsd_to_others'], diversity_df['vina_affinity'],
                                 alpha=0.7, c=diversity_df['vina_affinity'], cmap='viridis', s=50)
            ax1.set_xlabel('Average RMSD to Other Poses (Å)', fontsize=12)
            ax1.set_ylabel('Binding Affinity (kcal/mol)', fontsize=12)
            ax1.set_title('Binding Affinity vs Conformational Diversity', fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            plt.colorbar(scatter, ax=ax1, label='Affinity (kcal/mol)')
        
        # RMSD distribution
        if 'avg_rmsd_to_others' in diversity_df.columns:
            ax2.hist(diversity_df['avg_rmsd_to_others'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            mean_rmsd = diversity_df['avg_rmsd_to_others'].mean()
            ax2.axvline(mean_rmsd, color='red', linestyle='--',
                       label=f'Mean: {mean_rmsd:.2f} Å')
            ax2.set_xlabel('Average RMSD to Other Poses (Å)', fontsize=12)
            ax2.set_ylabel('Frequency', fontsize=12)
            ax2.set_title('Distribution of Conformational Diversity', fontsize=14, fontweight='bold')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        diversity_file = output_dir / 'diversity_analysis.png'
        plt.savefig(diversity_file, dpi=dpi, bbox_inches='tight')
        plt.close()
        created_files.append(diversity_file)
    
    logger.info(f"✅ Created {len(created_files)} RMSD visualizations")
    return created_files

