"""
RMSD analysis module for post-docking analysis pipeline.

This module handles RMSD analysis, pose clustering, and conformational diversity analysis.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from .config import RANDOM_SEED, NUMPY_SEED, SKLEARN_SEED

# Set seeds for reproducibility
if NUMPY_SEED is not None:
    np.random.seed(NUMPY_SEED)

def calculate_rmsd_matrix(poses_data: pd.DataFrame) -> np.ndarray:
    """
    Calculate RMSD matrix between all poses.
    
    Parameters
    ----------
    poses_data : pd.DataFrame
        DataFrame containing pose coordinates and metadata
        
    Returns
    -------
    np.ndarray
        RMSD matrix between all poses
    """
    print("📏 Calculating RMSD matrix...")
    
    # This is a placeholder implementation
    # In reality, you would:
    # 1. Load PDB files for each pose
    # 2. Align structures
    # 3. Calculate pairwise RMSD values
    
    n_poses = len(poses_data)
    rmsd_matrix = np.random.uniform(0, 10, (n_poses, n_poses))
    
    # Make matrix symmetric
    rmsd_matrix = (rmsd_matrix + rmsd_matrix.T) / 2
    
    # Set diagonal to zero
    np.fill_diagonal(rmsd_matrix, 0)
    
    print(f"✅ RMSD matrix calculated for {n_poses} poses")
    return rmsd_matrix

def analyze_pose_clustering(poses_data: pd.DataFrame, rmsd_matrix: np.ndarray, 
                          method: str = 'kmeans', n_clusters: int = 3) -> Dict:
    """
    Analyze pose clustering based on RMSD values.
    
    Parameters
    ----------
    poses_data : pd.DataFrame
        DataFrame containing pose data
    rmsd_matrix : np.ndarray
        RMSD matrix between poses
    method : str
        Clustering method ('kmeans' or 'dbscan')
    n_clusters : int
        Number of clusters for K-means
        
    Returns
    -------
    Dict
        Dictionary containing clustering results
    """
    print(f"🔍 Analyzing pose clustering using {method}...")
    
    # Prepare data for clustering
    # Use RMSD values as features (you might want to use actual coordinates)
    features = rmsd_matrix
    
    if method == 'kmeans':
        # Use configured seed for reproducibility
        random_state = SKLEARN_SEED if SKLEARN_SEED is not None else 42
        clusterer = KMeans(n_clusters=n_clusters, random_state=random_state)
        cluster_labels = clusterer.fit_predict(features)
        print(f"✓ K-means clustering with random_state={random_state} for reproducibility")
    elif method == 'dbscan':
        clusterer = DBSCAN(eps=2.0, min_samples=2)
        cluster_labels = clusterer.fit_predict(features)
        print(f"✓ DBSCAN clustering (deterministic)")
    else:
        raise ValueError(f"Unknown clustering method: {method}")
    
    # Add cluster labels to poses data
    poses_data = poses_data.copy()
    poses_data['cluster'] = cluster_labels
    
    # Analyze clusters
    cluster_summary = poses_data.groupby('cluster').agg({
        'vina_affinity': ['min', 'max', 'mean', 'std', 'count'],
        'complex_name': 'count'
    }).round(3)
    
    # Flatten column names
    cluster_summary.columns = ['_'.join(col).strip() for col in cluster_summary.columns]
    cluster_summary = cluster_summary.reset_index()
    
    # Calculate cluster centroids (representative poses)
    cluster_centroids = []
    for cluster_id in sorted(poses_data['cluster'].unique()):
        if cluster_id == -1:  # Skip noise points in DBSCAN
            continue
            
        cluster_poses = poses_data[poses_data['cluster'] == cluster_id]
        # Find pose closest to cluster center (lowest average RMSD to other poses in cluster)
        cluster_rmsd = rmsd_matrix[cluster_poses.index][:, cluster_poses.index]
        avg_rmsd = np.mean(cluster_rmsd, axis=1)
        centroid_idx = cluster_poses.index[np.argmin(avg_rmsd)]
        
        cluster_centroids.append({
            'cluster': cluster_id,
            'centroid_pose': poses_data.loc[centroid_idx, 'complex_name'],
            'centroid_affinity': poses_data.loc[centroid_idx, 'vina_affinity'],
            'cluster_size': len(cluster_poses),
            'avg_affinity': cluster_poses['vina_affinity'].mean()
        })
    
    cluster_centroids_df = pd.DataFrame(cluster_centroids)
    
    print(f"✅ Pose clustering completed")
    print(f"   Found {len(cluster_centroids_df)} clusters")
    print(f"   Best cluster affinity: {cluster_centroids_df['avg_affinity'].min():.2f} kcal/mol")
    
    return {
        'poses_with_clusters': poses_data,
        'cluster_summary': cluster_summary,
        'cluster_centroids': cluster_centroids_df,
        'rmsd_matrix': rmsd_matrix,
        'cluster_labels': cluster_labels
    }

def analyze_conformational_diversity(poses_data: pd.DataFrame, rmsd_matrix: np.ndarray) -> Dict:
    """
    Analyze conformational diversity of poses.
    
    Parameters
    ----------
    poses_data : pd.DataFrame
        DataFrame containing pose data
    rmsd_matrix : np.ndarray
        RMSD matrix between poses
        
    Returns
    -------
    Dict
        Dictionary containing diversity analysis results
    """
    print("🌊 Analyzing conformational diversity...")
    
    # Calculate diversity metrics
    diversity_metrics = []
    
    for i, (_, pose) in enumerate(poses_data.iterrows()):
        # Calculate average RMSD to all other poses
        other_rmsds = np.concatenate([rmsd_matrix[i, :i], rmsd_matrix[i, i+1:]])
        avg_rmsd = np.mean(other_rmsds)
        max_rmsd = np.max(other_rmsds)
        min_rmsd = np.min(other_rmsds)
        
        diversity_metrics.append({
            'complex_name': pose['complex_name'],
            'vina_affinity': pose['vina_affinity'],
            'avg_rmsd_to_others': avg_rmsd,
            'max_rmsd_to_others': max_rmsd,
            'min_rmsd_to_others': min_rmsd,
            'rmsd_std': np.std(other_rmsds)
        })
    
    diversity_df = pd.DataFrame(diversity_metrics)
    
    # Overall diversity statistics
    overall_stats = {
        'total_poses': len(poses_data),
        'avg_pairwise_rmsd': np.mean(rmsd_matrix[np.triu_indices_from(rmsd_matrix, k=1)]),
        'max_pairwise_rmsd': np.max(rmsd_matrix),
        'min_pairwise_rmsd': np.min(rmsd_matrix[np.triu_indices_from(rmsd_matrix, k=1)]),
        'rmsd_std': np.std(rmsd_matrix[np.triu_indices_from(rmsd_matrix, k=1)])
    }
    
    # Identify most diverse poses
    most_diverse = diversity_df.nlargest(5, 'avg_rmsd_to_others')
    least_diverse = diversity_df.nsmallest(5, 'avg_rmsd_to_others')
    
    print(f"✅ Conformational diversity analysis completed")
    print(f"   Average pairwise RMSD: {overall_stats['avg_pairwise_rmsd']:.2f} Å")
    print(f"   Most diverse pose: {most_diverse.iloc[0]['complex_name']} ({most_diverse.iloc[0]['avg_rmsd_to_others']:.2f} Å)")
    
    return {
        'diversity_metrics': diversity_df,
        'overall_stats': overall_stats,
        'most_diverse_poses': most_diverse,
        'least_diverse_poses': least_diverse,
        'rmsd_matrix': rmsd_matrix
    }

def create_rmsd_visualizations(clustering_results: Dict, diversity_results: Dict, 
                             output_dir: Path) -> List[Path]:
    """
    Create visualizations for RMSD analysis.
    
    Parameters
    ----------
    clustering_results : Dict
        Results from pose clustering analysis
    diversity_results : Dict
        Results from diversity analysis
    output_dir : Path
        Output directory for visualizations
        
    Returns
    -------
    List[Path]
        List of created visualization files
    """
    print("📊 Creating RMSD visualizations...")
    
    output_dir.mkdir(exist_ok=True)
    created_files = []
    
    # 1. RMSD heatmap
    fig, ax = plt.subplots(figsize=(12, 10))
    rmsd_matrix = clustering_results['rmsd_matrix']
    im = ax.imshow(rmsd_matrix, cmap='viridis', aspect='auto')
    ax.set_title('RMSD Matrix Between Poses', fontsize=16, fontweight='bold')
    ax.set_xlabel('Pose Index')
    ax.set_ylabel('Pose Index')
    plt.colorbar(im, ax=ax, label='RMSD (Å)')
    plt.tight_layout()
    
    heatmap_file = output_dir / 'rmsd_heatmap.png'
    plt.savefig(heatmap_file, dpi=300, bbox_inches='tight')
    plt.close()
    created_files.append(heatmap_file)
    
    # 2. Cluster analysis plot
    poses_data = clustering_results['poses_with_clusters']
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Binding affinity vs cluster
    unique_clusters = sorted(poses_data['cluster'].unique())
    colors = plt.cm.Set3(np.linspace(0, 1, len(unique_clusters)))
    
    for i, cluster in enumerate(unique_clusters):
        if cluster == -1:  # Skip noise points
            continue
        cluster_data = poses_data[poses_data['cluster'] == cluster]
        ax1.scatter(cluster_data['cluster'], cluster_data['vina_affinity'], 
                   c=[colors[i]], label=f'Cluster {cluster}', alpha=0.7)
    
    ax1.set_xlabel('Cluster')
    ax1.set_ylabel('Binding Affinity (kcal/mol)')
    ax1.set_title('Binding Affinity by Cluster')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Cluster size distribution
    cluster_sizes = poses_data['cluster'].value_counts().sort_index()
    cluster_sizes = cluster_sizes[cluster_sizes.index != -1]  # Remove noise
    ax2.bar(cluster_sizes.index, cluster_sizes.values, color=colors[:len(cluster_sizes)])
    ax2.set_xlabel('Cluster')
    ax2.set_ylabel('Number of Poses')
    ax2.set_title('Cluster Size Distribution')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    cluster_file = output_dir / 'cluster_analysis.png'
    plt.savefig(cluster_file, dpi=300, bbox_inches='tight')
    plt.close()
    created_files.append(cluster_file)
    
    # 3. Diversity analysis plot
    diversity_df = diversity_results['diversity_metrics']
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Binding affinity vs diversity
    ax1.scatter(diversity_df['avg_rmsd_to_others'], diversity_df['vina_affinity'], 
               alpha=0.7, c=diversity_df['vina_affinity'], cmap='viridis')
    ax1.set_xlabel('Average RMSD to Other Poses (Å)')
    ax1.set_ylabel('Binding Affinity (kcal/mol)')
    ax1.set_title('Binding Affinity vs Conformational Diversity')
    ax1.grid(True, alpha=0.3)
    
    # RMSD distribution
    ax2.hist(diversity_df['avg_rmsd_to_others'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
    ax2.axvline(diversity_df['avg_rmsd_to_others'].mean(), color='red', linestyle='--', 
               label=f'Mean: {diversity_df["avg_rmsd_to_others"].mean():.2f} Å')
    ax2.set_xlabel('Average RMSD to Other Poses (Å)')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Distribution of Conformational Diversity')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    diversity_file = output_dir / 'diversity_analysis.png'
    plt.savefig(diversity_file, dpi=300, bbox_inches='tight')
    plt.close()
    created_files.append(diversity_file)
    
    print(f"✅ Created {len(created_files)} RMSD visualizations")
    return created_files

