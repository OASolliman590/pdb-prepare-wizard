"""
Visualization module for post-docking analysis pipeline.

This module handles the generation of charts and graphs from analysis results.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def generate_binding_affinity_plot(analysis_results: Dict[str, pd.DataFrame], output_dir: Path):
    """
    Generate a plot of binding affinities.
    
    Parameters
    ----------
    analysis_results : Dict[str, pd.DataFrame]
        Dictionary containing analysis results
    output_dir : Path
        Output directory for plots
    """
    print("📊 Generating binding affinity plot...")
    
    # Create output directory
    viz_dir = output_dir / "visualizations"
    viz_dir.mkdir(exist_ok=True)
    
    # Get best poses data
    best_poses = analysis_results['best_poses']
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot binding affinities
    sns.histplot(best_poses['vina_affinity'], kde=True, ax=ax)
    ax.set_xlabel('Binding Affinity (kcal/mol)')
    ax.set_ylabel('Frequency')
    ax.set_title('Distribution of Binding Affinities')
    
    # Save plot
    plot_file = viz_dir / "binding_affinity_distribution.png"
    plt.tight_layout()
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Binding affinity plot saved to: {plot_file}")

def generate_top_performers_plot(analysis_results: Dict[str, pd.DataFrame], output_dir: Path):
    """
    Generate a plot of top performers.
    
    Parameters
    ----------
    analysis_results : Dict[str, pd.DataFrame]
        Dictionary containing analysis results
    output_dir : Path
        Output directory for plots
    """
    print("📊 Generating top performers plot...")
    
    # Create output directory
    viz_dir = output_dir / "visualizations"
    viz_dir.mkdir(exist_ok=True)
    
    # Get top overall performers
    top_overall = analysis_results['top_overall']
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot top performers
    sns.barplot(data=top_overall, x='vina_affinity', y='complex_name', ax=ax)
    ax.set_xlabel('Binding Affinity (kcal/mol)')
    ax.set_ylabel('Complex')
    ax.set_title('Top Performing Complexes')
    
    # Save plot
    plot_file = viz_dir / "top_performers.png"
    plt.tight_layout()
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Top performers plot saved to: {plot_file}")

def generate_comparison_plot(analysis_results: Dict[str, pd.DataFrame], output_dir: Path):
    """
    Generate a comparison plot of Vina vs CNN scores.
    
    Parameters
    ----------
    analysis_results : Dict[str, pd.DataFrame]
        Dictionary containing analysis results
    output_dir : Path
        Output directory for plots
    """
    print("📊 Generating comparison plot...")
    
    # Create output directory
    viz_dir = output_dir / "visualizations"
    viz_dir.mkdir(exist_ok=True)
    
    # Get best poses data
    best_poses = analysis_results['best_poses']
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot comparison
    sns.scatterplot(data=best_poses, x='vina_affinity', y='cnn_affinity', ax=ax)
    ax.set_xlabel('Vina Affinity (kcal/mol)')
    ax.set_ylabel('CNN Affinity (kcal/mol)')
    ax.set_title('Vina vs CNN Affinity Comparison')
    
    # Add diagonal line for reference
    min_val = min(best_poses['vina_affinity'].min(), best_poses['cnn_affinity'].min())
    max_val = max(best_poses['vina_affinity'].max(), best_poses['cnn_affinity'].max())
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.5)
    
    # Save plot
    plot_file = viz_dir / "vina_cnn_comparison.png"
    plt.tight_layout()
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Comparison plot saved to: {plot_file}")

def generate_all_visualizations(analysis_results: Dict[str, pd.DataFrame], output_dir: Path):
    """
    Generate all visualizations.
    
    Parameters
    ----------
    analysis_results : Dict[str, pd.DataFrame]
        Dictionary containing analysis results
    output_dir : Path
        Output directory for plots
    """
    print("📊 Generating all visualizations...")
    
    generate_binding_affinity_plot(analysis_results, output_dir)
    generate_top_performers_plot(analysis_results, output_dir)
    generate_comparison_plot(analysis_results, output_dir)
    
    print("✅ All visualizations generated successfully!")