"""
Correlation analysis module for post-docking analysis pipeline.

This module handles correlation analysis between different scoring functions,
particularly Vina vs CNN scores, and other comparative analyses.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import pearsonr, spearmanr
import warnings
warnings.filterwarnings('ignore')

def analyze_vina_cnn_correlation(scores_df: pd.DataFrame) -> Dict:
    """
    Analyze correlation between Vina and CNN scores.
    
    Parameters
    ----------
    scores_df : pd.DataFrame
        DataFrame containing Vina and CNN scores
        
    Returns
    -------
    Dict
        Dictionary containing correlation analysis results
    """
    print("📊 Analyzing Vina vs CNN correlation...")
    
    # Check if CNN scores are available
    if 'cnn_affinity' not in scores_df.columns or 'cnn_score' not in scores_df.columns:
        print("⚠️ CNN scores not available - skipping correlation analysis")
        return {'error': 'CNN scores not available'}
    
    # Remove rows with missing values
    valid_data = scores_df.dropna(subset=['vina_affinity', 'cnn_affinity', 'cnn_score'])
    
    if len(valid_data) == 0:
        print("⚠️ No valid data for correlation analysis")
        return {'error': 'No valid data'}
    
    # Calculate correlations
    vina_affinity = valid_data['vina_affinity']
    cnn_affinity = valid_data['cnn_affinity']
    cnn_score = valid_data['cnn_score']
    
    # Pearson correlations
    pearson_vina_cnn_affinity, pearson_p_vina_cnn = pearsonr(vina_affinity, cnn_affinity)
    pearson_vina_cnn_score, pearson_p_vina_score = pearsonr(vina_affinity, cnn_score)
    pearson_cnn_affinity_score, pearson_p_cnn_score = pearsonr(cnn_affinity, cnn_score)
    
    # Spearman correlations
    spearman_vina_cnn_affinity, spearman_p_vina_cnn = spearmanr(vina_affinity, cnn_affinity)
    spearman_vina_cnn_score, spearman_p_vina_score = spearmanr(vina_affinity, cnn_score)
    spearman_cnn_affinity_score, spearman_p_cnn_score = spearmanr(cnn_affinity, cnn_score)
    
    # Create correlation matrix
    correlation_data = valid_data[['vina_affinity', 'cnn_affinity', 'cnn_score']].corr()
    
    # Statistical significance
    n_samples = len(valid_data)
    
    correlation_results = {
        'n_samples': n_samples,
        'pearson_correlations': {
            'vina_cnn_affinity': {
                'correlation': pearson_vina_cnn_affinity,
                'p_value': pearson_p_vina_cnn,
                'significant': pearson_p_vina_cnn < 0.05
            },
            'vina_cnn_score': {
                'correlation': pearson_vina_cnn_score,
                'p_value': pearson_p_vina_score,
                'significant': pearson_p_vina_score < 0.05
            },
            'cnn_affinity_score': {
                'correlation': pearson_cnn_affinity_score,
                'p_value': pearson_p_cnn_score,
                'significant': pearson_p_cnn_score < 0.05
            }
        },
        'spearman_correlations': {
            'vina_cnn_affinity': {
                'correlation': spearman_vina_cnn_affinity,
                'p_value': spearman_p_vina_cnn,
                'significant': spearman_p_vina_cnn < 0.05
            },
            'vina_cnn_score': {
                'correlation': spearman_vina_cnn_score,
                'p_value': spearman_p_vina_score,
                'significant': spearman_p_vina_score < 0.05
            },
            'cnn_affinity_score': {
                'correlation': spearman_cnn_affinity_score,
                'p_value': spearman_p_cnn_score,
                'significant': spearman_p_cnn_score < 0.05
            }
        },
        'correlation_matrix': correlation_data,
        'valid_data': valid_data
    }
    
    print(f"✅ Correlation analysis completed for {n_samples} samples")
    print(f"   Vina-CNN Affinity Pearson r: {pearson_vina_cnn_affinity:.3f} (p={pearson_p_vina_cnn:.3f})")
    print(f"   Vina-CNN Score Pearson r: {pearson_vina_cnn_score:.3f} (p={pearson_p_vina_score:.3f})")
    
    return correlation_results

def analyze_score_distributions(scores_df: pd.DataFrame) -> Dict:
    """
    Analyze distributions of different scoring functions.
    
    Parameters
    ----------
    scores_df : pd.DataFrame
        DataFrame containing scoring data
        
    Returns
    -------
    Dict
        Dictionary containing distribution analysis results
    """
    print("📈 Analyzing score distributions...")
    
    # Calculate descriptive statistics
    score_columns = ['vina_affinity']
    if 'cnn_affinity' in scores_df.columns:
        score_columns.append('cnn_affinity')
    if 'cnn_score' in scores_df.columns:
        score_columns.append('cnn_score')
    
    distribution_stats = {}
    for col in score_columns:
        if col in scores_df.columns:
            data = scores_df[col].dropna()
            distribution_stats[col] = {
                'mean': data.mean(),
                'std': data.std(),
                'min': data.min(),
                'max': data.max(),
                'median': data.median(),
                'q25': data.quantile(0.25),
                'q75': data.quantile(0.75),
                'skewness': stats.skew(data),
                'kurtosis': stats.kurtosis(data),
                'n_samples': len(data)
            }
    
    # Normality tests
    normality_tests = {}
    for col in score_columns:
        if col in scores_df.columns:
            data = scores_df[col].dropna()
            if len(data) >= 3:  # Minimum sample size for Shapiro-Wilk
                try:
                    shapiro_stat, shapiro_p = stats.shapiro(data)
                    normality_tests[col] = {
                        'shapiro_wilk': {
                            'statistic': shapiro_stat,
                            'p_value': shapiro_p,
                            'normal': shapiro_p > 0.05
                        }
                    }
                except:
                    normality_tests[col] = {'error': 'Could not perform normality test'}
    
    distribution_results = {
        'descriptive_stats': distribution_stats,
        'normality_tests': normality_tests
    }
    
    print("✅ Score distribution analysis completed")
    return distribution_results

def analyze_score_agreement(scores_df: pd.DataFrame, threshold: float = 0.1) -> Dict:
    """
    Analyze agreement between different scoring functions.
    
    Parameters
    ----------
    scores_df : pd.DataFrame
        DataFrame containing scoring data
    threshold : float
        Threshold for considering scores in agreement
        
    Returns
    -------
    Dict
        Dictionary containing agreement analysis results
    """
    print("🤝 Analyzing score agreement...")
    
    if 'cnn_affinity' not in scores_df.columns:
        print("⚠️ CNN scores not available - skipping agreement analysis")
        return {'error': 'CNN scores not available'}
    
    # Normalize scores to 0-1 range for comparison
    vina_norm = (scores_df['vina_affinity'] - scores_df['vina_affinity'].min()) / \
                (scores_df['vina_affinity'].max() - scores_df['vina_affinity'].min())
    cnn_norm = (scores_df['cnn_affinity'] - scores_df['cnn_affinity'].min()) / \
               (scores_df['cnn_affinity'].max() - scores_df['cnn_affinity'].min())
    
    # Calculate agreement
    score_diff = np.abs(vina_norm - cnn_norm)
    agreement_mask = score_diff <= threshold
    
    agreement_results = {
        'threshold': threshold,
        'total_comparisons': len(scores_df),
        'agreements': np.sum(agreement_mask),
        'disagreements': np.sum(~agreement_mask),
        'agreement_percentage': (np.sum(agreement_mask) / len(scores_df)) * 100,
        'mean_score_difference': np.mean(score_diff),
        'std_score_difference': np.std(score_diff),
        'agreement_details': {
            'vina_norm': vina_norm,
            'cnn_norm': cnn_norm,
            'score_differences': score_diff,
            'agreement_mask': agreement_mask
        }
    }
    
    print(f"✅ Score agreement analysis completed")
    print(f"   Agreement rate: {agreement_results['agreement_percentage']:.1f}%")
    print(f"   Mean score difference: {agreement_results['mean_score_difference']:.3f}")
    
    return agreement_results

def create_correlation_visualizations(correlation_results: Dict, distribution_results: Dict,
                                    agreement_results: Dict, output_dir: Path) -> List[Path]:
    """
    Create visualizations for correlation analysis.
    
    Parameters
    ----------
    correlation_results : Dict
        Results from correlation analysis
    distribution_results : Dict
        Results from distribution analysis
    agreement_results : Dict
        Results from agreement analysis
    output_dir : Path
        Output directory for visualizations
        
    Returns
    -------
    List[Path]
        List of created visualization files
    """
    print("📊 Creating correlation visualizations...")
    
    output_dir.mkdir(exist_ok=True)
    created_files = []
    
    if 'error' in correlation_results:
        print("⚠️ Skipping correlation visualizations due to missing data")
        return created_files
    
    valid_data = correlation_results['valid_data']
    
    # 1. Correlation matrix heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    correlation_matrix = correlation_results['correlation_matrix']
    
    mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
    sns.heatmap(correlation_matrix, mask=mask, annot=True, cmap='coolwarm', center=0,
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8}, ax=ax)
    ax.set_title('Correlation Matrix: Vina vs CNN Scores', fontsize=16, fontweight='bold')
    
    plt.tight_layout()
    heatmap_file = output_dir / 'correlation_matrix.png'
    plt.savefig(heatmap_file, dpi=300, bbox_inches='tight')
    plt.close()
    created_files.append(heatmap_file)
    
    # 2. Scatter plots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Score Correlations and Distributions', fontsize=16, fontweight='bold')
    
    # Vina vs CNN Affinity
    ax1 = axes[0, 0]
    ax1.scatter(valid_data['vina_affinity'], valid_data['cnn_affinity'], alpha=0.6)
    ax1.set_xlabel('Vina Affinity (kcal/mol)')
    ax1.set_ylabel('CNN Affinity')
    ax1.set_title('Vina vs CNN Affinity')
    
    # Add correlation info
    pearson_r = correlation_results['pearson_correlations']['vina_cnn_affinity']['correlation']
    pearson_p = correlation_results['pearson_correlations']['vina_cnn_affinity']['p_value']
    ax1.text(0.05, 0.95, f'Pearson r = {pearson_r:.3f}\np = {pearson_p:.3f}', 
             transform=ax1.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    ax1.grid(True, alpha=0.3)
    
    # Vina vs CNN Score
    ax2 = axes[0, 1]
    ax2.scatter(valid_data['vina_affinity'], valid_data['cnn_score'], alpha=0.6, color='orange')
    ax2.set_xlabel('Vina Affinity (kcal/mol)')
    ax2.set_ylabel('CNN Score')
    ax2.set_title('Vina vs CNN Score')
    
    # Add correlation info
    pearson_r = correlation_results['pearson_correlations']['vina_cnn_score']['correlation']
    pearson_p = correlation_results['pearson_correlations']['vina_cnn_score']['p_value']
    ax2.text(0.05, 0.95, f'Pearson r = {pearson_r:.3f}\np = {pearson_p:.3f}', 
             transform=ax2.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    ax2.grid(True, alpha=0.3)
    
    # Score distributions
    ax3 = axes[1, 0]
    ax3.hist(valid_data['vina_affinity'], bins=20, alpha=0.7, color='blue', label='Vina', density=True)
    if 'cnn_affinity' in valid_data.columns:
        ax3.hist(valid_data['cnn_affinity'], bins=20, alpha=0.7, color='red', label='CNN', density=True)
    ax3.set_xlabel('Affinity')
    ax3.set_ylabel('Density')
    ax3.set_title('Score Distributions')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Agreement analysis
    ax4 = axes[1, 1]
    if 'error' not in agreement_results:
        score_diffs = agreement_results['agreement_details']['score_differences']
        ax4.hist(score_diffs, bins=20, alpha=0.7, color='green', edgecolor='black')
        ax4.axvline(agreement_results['threshold'], color='red', linestyle='--', 
                   label=f'Threshold: {agreement_results["threshold"]}')
        ax4.set_xlabel('Normalized Score Difference')
        ax4.set_ylabel('Frequency')
        ax4.set_title('Score Agreement Analysis')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    scatter_file = output_dir / 'correlation_scatter_plots.png'
    plt.savefig(scatter_file, dpi=300, bbox_inches='tight')
    plt.close()
    created_files.append(scatter_file)
    
    # 3. Summary statistics plot
    if distribution_results and 'descriptive_stats' in distribution_results:
        fig, ax = plt.subplots(figsize=(12, 8))
        
        stats_data = distribution_results['descriptive_stats']
        score_types = list(stats_data.keys())
        means = [stats_data[score]['mean'] for score in score_types]
        stds = [stats_data[score]['std'] for score in score_types]
        
        x_pos = np.arange(len(score_types))
        bars = ax.bar(x_pos, means, yerr=stds, capsize=5, alpha=0.7)
        ax.set_xlabel('Score Type')
        ax.set_ylabel('Value')
        ax.set_title('Score Statistics Summary')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(score_types, rotation=45)
        ax.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for i, (mean, std) in enumerate(zip(means, stds)):
            ax.text(i, mean + std + 0.1, f'{mean:.2f}±{std:.2f}', 
                   ha='center', va='bottom')
        
        plt.tight_layout()
        stats_file = output_dir / 'score_statistics.png'
        plt.savefig(stats_file, dpi=300, bbox_inches='tight')
        plt.close()
        created_files.append(stats_file)
    
    print(f"✅ Created {len(created_files)} correlation visualizations")
    return created_files

