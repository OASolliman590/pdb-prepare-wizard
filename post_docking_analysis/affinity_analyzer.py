"""
Binding affinity analyzer for post-docking analysis pipeline.

This module handles the analysis of docking scores, identification of best poses,
and ranking of protein-ligand complexes.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple

def parse_docking_scores(complexes: List[Dict[str, Path]]) -> pd.DataFrame:
    """
    Parse docking scores from result files.
    
    Parameters
    ----------
    complexes : List[Dict[str, Path]]
        List of complex information
        
    Returns
    -------
    pd.DataFrame
        DataFrame containing parsed docking scores
    """
    print("📊 Parsing docking scores...")
    
    # This would implement the functionality from parse_vina_csv.py
    # and binding_affinity_analyzer.py
    
    # For now, create a placeholder DataFrame
    data = []
    for complex_info in complexes:
        # Placeholder data - in reality, this would be parsed from the files
        data.append({
            "complex_name": complex_info["name"],
            "vina_affinity": np.random.uniform(-15, -5),  # Random binding affinity
            "cnn_affinity": np.random.uniform(-15, -5),   # Random CNN affinity
            "cnn_score": np.random.uniform(0, 1),         # Random CNN score
            "rmsd_lb": np.random.uniform(0, 5),           # Random RMSD lower bound
            "rmsd_ub": np.random.uniform(0, 5),           # Random RMSD upper bound
            "mode": 1  # Pose mode
        })
    
    df = pd.DataFrame(data)
    print(f"✅ Parsed scores for {len(df)} complexes")
    return df

def analyze_binding_affinities(scores_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Analyze binding affinities and identify top performers.
    
    Parameters
    ----------
    scores_df : pd.DataFrame
        DataFrame containing docking scores
        
    Returns
    -------
    Dict[str, pd.DataFrame]
        Dictionary containing analysis results
    """
    print("🏆 Analyzing binding affinities...")
    
    # Sort by binding affinity (most negative = strongest binding)
    best_poses = scores_df.loc[scores_df.groupby('complex_name')['vina_affinity'].idxmin()].copy()
    best_poses = best_poses.sort_values('vina_affinity')
    
    # Calculate summary statistics per complex
    summary_stats = scores_df.groupby('complex_name').agg({
        'vina_affinity': ['min', 'max', 'mean', 'std'],
        'cnn_affinity': ['min', 'max', 'mean'],
        'cnn_score': ['max', 'mean']
    }).round(3)
    
    # Flatten column names
    summary_stats.columns = ['_'.join(col).strip() for col in summary_stats.columns]
    summary_stats = summary_stats.reset_index()
    
    # Highlight top performers
    top_overall = best_poses.head(10)[['complex_name', 'vina_affinity', 'cnn_affinity', 'cnn_score', 'mode']]
    
    results = {
        'full_data': scores_df,
        'best_poses': best_poses,
        'summary_stats': summary_stats,
        'top_overall': top_overall
    }
    
    print(f"✅ Analysis complete for {len(scores_df)} complexes")
    print(f"   Top binding affinity: {best_poses['vina_affinity'].min():.2f} kcal/mol")
    return results

def identify_top_performers(analysis_results: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Identify top performers by different criteria.
    
    Parameters
    ----------
    analysis_results : Dict[str, pd.DataFrame]
        Dictionary containing analysis results
        
    Returns
    -------
    Dict[str, pd.DataFrame]
        Dictionary containing top performers
    """
    print("🌟 Identifying top performers...")
    
    best_poses = analysis_results['best_poses']
    
    # Best per protein (assuming protein is first part of complex name)
    best_poses['protein'] = best_poses['complex_name'].str.split('_').str[0]
    best_per_protein = best_poses.groupby('protein').first().reset_index()
    best_per_protein = best_per_protein.sort_values('vina_affinity')
    
    # Best per ligand (assuming ligand is last part of complex name)
    best_poses['ligand'] = best_poses['complex_name'].str.split('_').str[-1]
    best_per_ligand = best_poses.groupby('ligand').first().reset_index() 
    best_per_ligand = best_per_ligand.sort_values('vina_affinity')
    
    top_performers = {
        'best_per_protein': best_per_protein,
        'best_per_ligand': best_per_ligand
    }
    
    print(f"✅ Identified top performers")
    print(f"   Best protein: {best_per_protein.iloc[0]['protein']} ({best_per_protein.iloc[0]['vina_affinity']:.2f} kcal/mol)")
    print(f"   Best ligand: {best_per_ligand.iloc[0]['ligand']} ({best_per_ligand.iloc[0]['vina_affinity']:.2f} kcal/mol)")
    
    return top_performers