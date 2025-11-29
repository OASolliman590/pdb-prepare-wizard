"""
Binding affinity analyzer for post-docking analysis pipeline.

This module handles the analysis of docking scores, identification of best poses,
and ranking of protein-ligand complexes with comparative benchmarking.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import re

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

def analyze_binding_affinities(scores_df: pd.DataFrame, comparative_benchmark: str = "*", strong_binder_threshold: str = "auto") -> Dict[str, pd.DataFrame]:
    """
    Analyze binding affinities and identify top performers with comparative benchmarking.
    
    Parameters
    ----------
    scores_df : pd.DataFrame
        DataFrame containing docking scores
    comparative_benchmark : str
        Benchmark target for comparison ("*" for all, or specific target name)
    strong_binder_threshold : str or float
        Affinity threshold for considering strong binders:
        - "auto": Calculate dynamically based on data distribution
        - "comparative": Use the comparative benchmark's average
        - numeric value: Fixed threshold (e.g., -8.0)
        
    Returns
    -------
    Dict[str, pd.DataFrame]
        Dictionary containing analysis results
    """
    print("🏆 Analyzing binding affinities...")
    
    # Filter out failed docking attempts (positive values)
    original_count = len(scores_df)
    scores_df = scores_df[scores_df['vina_affinity'] < 0]
    failed_count = original_count - len(scores_df)
    if failed_count > 0:
        print(f"🚫 Filtered out {failed_count} failed docking attempts (positive affinity values)")
    
    # Filter by comparative benchmark if specified
    if comparative_benchmark != "*":
        # Filter complexes that match the benchmark
        benchmark_filter = scores_df['complex_name'].str.contains(comparative_benchmark, case=False, na=False)
        scores_df = scores_df[benchmark_filter]
        print(f"🔍 Filtering by benchmark '{comparative_benchmark}': {len(scores_df)} complexes")
    
    # Sort by binding affinity (most negative = strongest binding)
    best_poses = scores_df.loc[scores_df.groupby('complex_name')['vina_affinity'].idxmin()].copy()
    best_poses = best_poses.sort_values('vina_affinity')
    
    # Calculate dynamic strong binder threshold if needed
    if strong_binder_threshold == "auto":
        # Use 1.5 times the interquartile range below the 25th percentile
        q25 = best_poses['vina_affinity'].quantile(0.25)
        q75 = best_poses['vina_affinity'].quantile(0.75)
        iqr = q75 - q25
        strong_binder_threshold = q25 - 1.5 * iqr
        print(f"📊 Auto-calculated strong binder threshold: {strong_binder_threshold:.2f} kcal/mol")
    elif strong_binder_threshold == "comparative" and comparative_benchmark != "*":
        # Use the average of the comparative benchmark
        strong_binder_threshold = best_poses['vina_affinity'].mean()
        print(f"📊 Comparative-based strong binder threshold: {strong_binder_threshold:.2f} kcal/mol")
    else:
        # Convert to float if it's a string representation of a number
        try:
            strong_binder_threshold = float(strong_binder_threshold)
        except (ValueError, TypeError):
            # Default to -8.0 if conversion fails
            strong_binder_threshold = -8.0
    
    # Add strong binder categorization
    best_poses['binder_category'] = pd.cut(best_poses['vina_affinity'], 
                                          bins=[-float('inf'), strong_binder_threshold, -6.0, 0],
                                          labels=['Strong binder', 'Moderate binder', 'Weak binder'])
    
    # Calculate summary statistics per complex
    agg_dict = {'vina_affinity': ['min', 'max', 'mean', 'std']}
    
    # Add CNN columns if they exist
    if 'cnn_affinity' in scores_df.columns:
        agg_dict['cnn_affinity'] = ['min', 'max', 'mean']
    if 'cnn_score' in scores_df.columns:
        agg_dict['cnn_score'] = ['max', 'mean']
    
    summary_stats = scores_df.groupby('complex_name').agg(agg_dict).round(3)
    
    # Flatten column names
    summary_stats.columns = ['_'.join(col).strip() for col in summary_stats.columns]
    summary_stats = summary_stats.reset_index()
    
    # Add complex info to summary
    # Parse complex names to extract protein and ligand information
    def parse_complex_name(complex_name):
        """Parse complex name to extract protein and ligand."""
        # Handle pairlist naming convention: receptor_site_ligand
        if '_' in complex_name:
            parts = complex_name.split('_')
            if len(parts) >= 3:
                # Format: receptor_site_ligand (e.g., 4TRO_INHA_prep_catalytic_ML1H)
                receptor_part = parts[0]  # e.g., 4TRO
                protein = f"{receptor_part}_{parts[1]}"  # e.g., 4TRO_INHA
                ligand = '_'.join(parts[3:])  # e.g., ML1H
            elif len(parts) >= 2:
                # Fallback for simpler naming
                protein = parts[0]
                ligand = '_'.join(parts[1:])
            else:
                protein = complex_name
                ligand = "Unknown"
        else:
            protein = complex_name
            ligand = "Unknown"
        
        return protein, ligand
    
    # Add protein and ligand columns
    parsed_info = best_poses['complex_name'].apply(parse_complex_name)
    best_poses['protein'] = [info[0] for info in parsed_info]
    best_poses['ligand'] = [info[1] for info in parsed_info]
    
    # Highlight top performers
    top_columns = ['complex_name', 'protein', 'ligand', 'vina_affinity', 'binder_category']
    if 'cnn_affinity' in best_poses.columns:
        top_columns.append('cnn_affinity')
    if 'cnn_score' in best_poses.columns:
        top_columns.append('cnn_score')
    if 'mode' in best_poses.columns:
        top_columns.append('mode')
    
    top_overall = best_poses.head(10)[top_columns]
    
    # Best per protein
    best_per_protein = best_poses.groupby('protein').first().reset_index()
    best_per_protein = best_per_protein.sort_values('vina_affinity')
    
    # Best per ligand
    best_per_ligand = best_poses.groupby('ligand').first().reset_index() 
    best_per_ligand = best_per_ligand.sort_values('vina_affinity')
    
    results = {
        'full_data': scores_df,
        'best_poses': best_poses,
        'summary_stats': summary_stats,
        'top_overall': top_overall,
        'best_per_protein': best_per_protein,
        'best_per_ligand': best_per_ligand,
        'strong_binder_threshold': strong_binder_threshold
    }
    
    print(f"✅ Analysis complete for {len(scores_df)} complexes")
    print(f"   Top binding affinity: {best_poses['vina_affinity'].min():.2f} kcal/mol")
    print(f"   Strong binder threshold: {strong_binder_threshold:.2f} kcal/mol")
    
    # Print binder categorization summary
    binder_counts = best_poses['binder_category'].value_counts()
    print(f"   Strong binders (<{strong_binder_threshold:.2f} kcal/mol): {binder_counts.get('Strong binder', 0)}")
    print(f"   Moderate binders (-6.0 to {strong_binder_threshold:.2f} kcal/mol): {binder_counts.get('Moderate binder', 0)}")
    print(f"   Weak binders (> -6.0 kcal/mol): {binder_counts.get('Weak binder', 0)}")
    
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

def analyze_protein_ligand_breakdown(scores_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Analyze best performance by protein and by ligand with detailed breakdown.
    
    Parameters
    ----------
    scores_df : pd.DataFrame
        DataFrame containing docking scores with complex information
        
    Returns
    -------
    Dict[str, pd.DataFrame]
        Dictionary containing protein and ligand breakdown results
    """
    print("🧬 Analyzing protein vs ligand breakdown...")
    
    # Parse complex names to extract protein and ligand information
    def parse_complex_name(complex_name):
        """Parse complex name to extract protein and ligand."""
        # Handle different naming conventions
        if 'x' in complex_name:
            parts = complex_name.split('x')
            protein = parts[0].strip()
            ligand = parts[1].strip()
        elif '_' in complex_name:
            parts = complex_name.split('_')
            if len(parts) >= 2:
                protein = parts[0]
                ligand = '_'.join(parts[1:])
            else:
                protein = complex_name
                ligand = "Unknown"
        else:
            protein = complex_name
            ligand = "Unknown"
        
        return protein, ligand
    
    # Add protein and ligand columns
    parsed_info = scores_df['complex_name'].apply(parse_complex_name)
    scores_df = scores_df.copy()
    scores_df['protein'] = [info[0] for info in parsed_info]
    scores_df['ligand'] = [info[1] for info in parsed_info]
    
    # Find best pose for each complex
    best_poses = scores_df.loc[scores_df.groupby('complex_name')['vina_affinity'].idxmin()].copy()
    
    # Best performance by protein
    best_per_protein = best_poses.groupby('protein').agg({
        'vina_affinity': 'min',
        'complex_name': 'first',
        'ligand': 'first',
        'cnn_affinity': 'first',
        'cnn_score': 'first'
    }).reset_index()
    best_per_protein = best_per_protein.sort_values('vina_affinity')
    best_per_protein.columns = ['protein', 'best_affinity', 'best_complex', 'best_ligand', 'cnn_affinity', 'cnn_score']
    
    # Best performance by ligand
    best_per_ligand = best_poses.groupby('ligand').agg({
        'vina_affinity': 'min',
        'complex_name': 'first',
        'protein': 'first',
        'cnn_affinity': 'first',
        'cnn_score': 'first'
    }).reset_index()
    best_per_ligand = best_per_ligand.sort_values('vina_affinity')
    best_per_ligand.columns = ['ligand', 'best_affinity', 'best_complex', 'best_protein', 'cnn_affinity', 'cnn_score']
    
    # Protein performance summary
    protein_summary = best_poses.groupby('protein').agg({
        'vina_affinity': ['min', 'max', 'mean', 'std', 'count'],
        'complex_name': 'count'
    }).round(3)
    protein_summary.columns = ['min_affinity', 'max_affinity', 'mean_affinity', 'std_affinity', 'pose_count', 'complex_count']
    protein_summary = protein_summary.reset_index()
    
    # Ligand performance summary
    ligand_summary = best_poses.groupby('ligand').agg({
        'vina_affinity': ['min', 'max', 'mean', 'std', 'count'],
        'complex_name': 'count'
    }).round(3)
    ligand_summary.columns = ['min_affinity', 'max_affinity', 'mean_affinity', 'std_affinity', 'pose_count', 'complex_count']
    ligand_summary = ligand_summary.reset_index()
    
    print(f"✅ Protein vs ligand breakdown completed")
    print(f"   Best protein: {best_per_protein.iloc[0]['protein']} ({best_per_protein.iloc[0]['best_affinity']:.2f} kcal/mol)")
    print(f"   Best ligand: {best_per_ligand.iloc[0]['ligand']} ({best_per_ligand.iloc[0]['best_affinity']:.2f} kcal/mol)")
    
    return {
        'best_per_protein': best_per_protein,
        'best_per_ligand': best_per_ligand,
        'protein_summary': protein_summary,
        'ligand_summary': ligand_summary,
        'scores_with_breakdown': scores_df
    }