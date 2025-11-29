"""
Enhanced visualization module for post-docking analysis pipeline.

This module handles the generation of charts, graphs, and 3D visualizations
from analysis results, with a focus on best poses only for improved performance
and clarity.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List
import warnings
warnings.filterwarnings("ignore")

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def generate_binding_affinity_plot(analysis_results: Dict[str, pd.DataFrame], 
                                 output_dir: Path, 
                                 dpi: int = 300) -> Path:
    """
    Generate a plot of binding affinities for best poses only.
    
    Parameters
    ----------
    analysis_results : Dict[str, pd.DataFrame]
        Dictionary containing analysis results
    output_dir : Path
        Output directory for plots
    dpi : int
        DPI for image output
        
    Returns
    -------
    Path
        Path to the created plot file
    """
    print("📊 Generating binding affinity plot for best poses...")
    
    # Create output directory
    viz_dir = output_dir / "visualizations"
    viz_dir.mkdir(exist_ok=True)
    
    # Get best poses data (focus only on best poses for clarity)
    best_poses = analysis_results['best_poses']
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot binding affinities
    sns.histplot(best_poses['vina_affinity'], kde=True, ax=ax, color='skyblue')
    ax.set_xlabel('Binding Affinity (kcal/mol)', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Distribution of Best Binding Affinities', fontsize=14, fontweight='bold')
    
    # Add statistics
    mean_affinity = best_poses['vina_affinity'].mean()
    ax.axvline(mean_affinity, color='red', linestyle='--', 
               label=f'Mean: {mean_affinity:.2f} kcal/mol')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Save plot
    plot_file = viz_dir / "binding_affinity_distribution.png"
    plt.tight_layout()
    plt.savefig(plot_file, dpi=dpi, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Binding affinity plot saved to: {plot_file}")
    return plot_file

def generate_top_performers_plot(analysis_results: Dict[str, pd.DataFrame], 
                               output_dir: Path,
                               top_count: int = 10,
                               dpi: int = 300) -> Path:
    """
    Generate a plot of top performers (best poses only).
    
    Parameters
    ----------
    analysis_results : Dict[str, pd.DataFrame]
        Dictionary containing analysis results
    output_dir : Path
        Output directory for plots
    top_count : int
        Number of top performers to show
    dpi : int
        DPI for image output
        
    Returns
    -------
    Path
        Path to the created plot file
    """
    print("📊 Generating top performers plot...")
    
    # Create output directory
    viz_dir = output_dir / "visualizations"
    viz_dir.mkdir(exist_ok=True)
    
    # Get top overall performers (best poses only)
    top_overall = analysis_results['top_overall'].head(top_count)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot top performers
    y_pos = np.arange(len(top_overall))
    bars = ax.barh(y_pos, top_overall['vina_affinity'].values, color='mediumseagreen')
    ax.set_yticks(y_pos)
    
    # Extract protein and ligand from complex_name if columns don't exist
    if 'protein' in top_overall.columns and 'ligand' in top_overall.columns:
        labels = [f"{row['protein']}_{row['ligand']}" for _, row in top_overall.iterrows()]
    else:
        # Extract from complex_name
        labels = []
        for _, row in top_overall.iterrows():
            complex_name = row['complex_name']
            if '_' in complex_name:
                parts = complex_name.split('_')
                if len(parts) >= 3:
                    protein = f"{parts[0]}_{parts[1]}"  # e.g., 4TRO_INHA
                    ligand = '_'.join(parts[3:])  # e.g., ML1H
                else:
                    protein = parts[0]
                    ligand = '_'.join(parts[1:])
            else:
                protein = complex_name
                ligand = "Unknown"
            labels.append(f"{protein}_{ligand}")
    
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel('Binding Affinity (kcal/mol)', fontsize=12)
    ax.set_ylabel('Complex', fontsize=12)
    ax.set_title(f'Top {top_count} Performing Complexes (Best Poses)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Highlight best complex
    bars[0].set_color('darkgreen')
    
    # Add value labels
    for i, (bar, value) in enumerate(zip(bars, top_overall['vina_affinity'].values)):
        ax.text(value + 0.1, i, f'{value:.2f}', 
                va='center', ha='left', fontsize=9)
    
    plt.tight_layout()
    
    # Save plot
    plot_file = viz_dir / f"top_{top_count}_performers.png"
    plt.savefig(plot_file, dpi=dpi, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Top performers plot saved to: {plot_file}")
    return plot_file

def generate_comparison_plot(analysis_results: Dict[str, pd.DataFrame], 
                           output_dir: Path,
                           dpi: int = 300) -> Path:
    """
    Generate a comparison plot of Vina vs CNN scores for best poses.
    
    Parameters
    ----------
    analysis_results : Dict[str, pd.DataFrame]
        Dictionary containing analysis results
    output_dir : Path
        Output directory for plots
    dpi : int
        DPI for image output
        
    Returns
    -------
    Path
        Path to the created plot file
    """
    print("📊 Generating Vina vs CNN comparison plot...")
    
    # Create output directory
    viz_dir = output_dir / "visualizations"
    viz_dir.mkdir(exist_ok=True)
    
    # Get best poses data (focus only on best poses for clarity)
    best_poses = analysis_results['best_poses']
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot comparison with color based on CNN score
    scatter = ax.scatter(best_poses['vina_affinity'], best_poses['cnn_affinity'], 
                        alpha=0.7, c=best_poses['cnn_score'], cmap='viridis', s=60)
    ax.set_xlabel('Vina Affinity (kcal/mol)', fontsize=12)
    ax.set_ylabel('CNN Affinity (kcal/mol)', fontsize=12)
    ax.set_title('Vina vs CNN Affinity for Best Poses\n(colored by CNN Score)', 
                fontsize=14, fontweight='bold')
    
    # Add diagonal line for reference
    min_val = min(best_poses['vina_affinity'].min(), best_poses['cnn_affinity'].min())
    max_val = max(best_poses['vina_affinity'].max(), best_poses['cnn_affinity'].max())
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.5, linewidth=1)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('CNN Score', fontsize=12)
    
    ax.grid(True, alpha=0.3)
    
    # Save plot
    plot_file = viz_dir / "vina_cnn_comparison.png"
    plt.tight_layout()
    plt.savefig(plot_file, dpi=dpi, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Comparison plot saved to: {plot_file}")
    return plot_file

def generate_protein_ligand_heatmap(analysis_results: Dict[str, pd.DataFrame], 
                                  output_dir: Path,
                                  dpi: int = 300) -> Path:
    """
    Generate a heatmap showing best affinities by protein and ligand.
    
    Parameters
    ----------
    analysis_results : Dict[str, pd.DataFrame]
        Dictionary containing analysis results
    output_dir : Path
        Output directory for plots
    dpi : int
        DPI for image output
        
    Returns
    -------
    Path
        Path to the created plot file
    """
    print("📊 Generating protein-ligand heatmap...")
    
    # Create output directory
    viz_dir = output_dir / "visualizations"
    viz_dir.mkdir(exist_ok=True)
    
    # Get best poses data
    best_poses = analysis_results['best_poses'].copy()
    
    # Add protein and ligand columns if they don't exist
    if 'protein' not in best_poses.columns or 'ligand' not in best_poses.columns:
        def parse_complex_name(complex_name):
            if '_' in complex_name:
                parts = complex_name.split('_')
                if len(parts) >= 3:
                    protein = f"{parts[0]}_{parts[1]}"  # e.g., 4TRO_INHA
                    ligand = '_'.join(parts[3:])  # e.g., ML1H
                else:
                    protein = parts[0]
                    ligand = '_'.join(parts[1:])
            else:
                protein = complex_name
                ligand = "Unknown"
            return protein, ligand
        
        parsed_info = best_poses['complex_name'].apply(parse_complex_name)
        best_poses['protein'] = [info[0] for info in parsed_info]
        best_poses['ligand'] = [info[1] for info in parsed_info]
    
    # Create pivot table for heatmap
    pivot_data = best_poses.pivot_table(values='vina_affinity', 
                                       index='protein', 
                                       columns='ligand', 
                                       aggfunc='min')
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Generate heatmap
    sns.heatmap(pivot_data, annot=True, fmt='.2f', cmap='coolwarm_r', 
                cbar_kws={'label': 'Binding Affinity (kcal/mol)'}, ax=ax)
    ax.set_title('Best Binding Affinities by Protein and Ligand', 
                fontsize=14, fontweight='bold')
    ax.set_xlabel('Ligand', fontsize=12)
    ax.set_ylabel('Protein', fontsize=12)
    
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    plt.tight_layout()
    
    # Save plot
    plot_file = viz_dir / "protein_ligand_heatmap.png"
    plt.savefig(plot_file, dpi=dpi, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Protein-ligand heatmap saved to: {plot_file}")
    return plot_file

def generate_per_protein_visualizations(analysis_results: Dict[str, pd.DataFrame], 
                                      output_dir: Path,
                                      dpi: int = 300):
    """
    Generate individual visualizations for each protein.
    
    Parameters
    ----------
    analysis_results : Dict[str, pd.DataFrame]
        Dictionary containing analysis results
    output_dir : Path
        Output directory for plots
    dpi : int
        DPI for image output
        
    Returns
    -------
    List[Path]
        List of created plot files
    """
    import matplotlib.pyplot as plt
    import numpy as np
    
    print("📊 Generating per-protein visualizations...")
    
    # Create output directory
    viz_dir = output_dir / "visualizations"
    viz_dir.mkdir(exist_ok=True)
    
    plot_files = []
    
    # Get best poses data
    best_poses = analysis_results['best_poses'].copy()
    
    # Add protein column if it doesn't exist
    if 'protein' not in best_poses.columns:
        def extract_protein(complex_name):
            if '_' in complex_name:
                parts = complex_name.split('_')
                if len(parts) >= 2:
                    return f"{parts[0]}_{parts[1]}"  # e.g., 4TRO_INHA
                else:
                    return parts[0]
            return complex_name
        
        best_poses['protein'] = best_poses['complex_name'].apply(extract_protein)
    
    # Get unique proteins
    proteins = best_poses['protein'].unique()
    
    for protein in proteins:
        protein_data = best_poses[best_poses['protein'] == protein]
        
        if len(protein_data) > 0:
            # Create protein-specific binding affinity plot
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Sort by affinity
            protein_data_sorted = protein_data.sort_values('vina_affinity')
            
            # Create bar plot
            y_pos = np.arange(len(protein_data_sorted))
            bars = ax.barh(y_pos, protein_data_sorted['vina_affinity'].values, 
                          color='steelblue', alpha=0.7)
            
            # Customize plot
            ax.set_yticks(y_pos)
            ax.set_yticklabels([row['complex_name'].split('_')[-1] for _, row in protein_data_sorted.iterrows()], 
                              fontsize=9)
            ax.set_xlabel('Binding Affinity (kcal/mol)', fontsize=12)
            ax.set_ylabel('Ligand', fontsize=12)
            ax.set_title(f'Binding Affinities for {protein}', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for i, (_, row) in enumerate(protein_data_sorted.iterrows()):
                ax.text(row['vina_affinity'] - 0.1, i, f"{row['vina_affinity']:.2f}", 
                       va='center', ha='right', fontsize=8)
            
            # Save plot
            plot_file = viz_dir / f"{protein}_binding_affinities.png"
            plt.savefig(plot_file, dpi=dpi, bbox_inches='tight')
            plt.close()
            
            plot_files.append(plot_file)
            print(f"✅ {protein} visualization saved to: {plot_file}")
    
    return plot_files

def generate_all_visualizations(analysis_results: Dict[str, pd.DataFrame], 
                              output_dir: Path,
                              config: dict = None):
    """
    Generate all visualizations focused on best poses only.
    
    Parameters
    ----------
    analysis_results : Dict[str, pd.DataFrame]
        Dictionary containing analysis results
    output_dir : Path
        Output directory for plots
    config : dict, optional
        Configuration dictionary
    """
    print("📊 Generating all visualizations (best poses only)...")
    
    # Use configuration or defaults
    if config is None:
        config = {}
    
    dpi = config.get("visualization", {}).get("dpi", 300)
    top_count = config.get("binding_affinity", {}).get("top_performers_count", 10)
    
    # Generate individual plots
    plot_files = []
    
    try:
        plot_files.append(generate_binding_affinity_plot(analysis_results, output_dir, dpi))
    except Exception as e:
        print(f"⚠️  Error generating binding affinity plot: {e}")
    
    try:
        plot_files.append(generate_top_performers_plot(analysis_results, output_dir, top_count, dpi))
    except Exception as e:
        print(f"⚠️  Error generating top performers plot: {e}")
    
    try:
        plot_files.append(generate_comparison_plot(analysis_results, output_dir, dpi))
    except Exception as e:
        print(f"⚠️  Error generating comparison plot: {e}")
    
    try:
        plot_files.append(generate_protein_ligand_heatmap(analysis_results, output_dir, dpi))
    except Exception as e:
        print(f"⚠️  Error generating protein-ligand heatmap: {e}")
    
    # Generate per-protein visualizations
    try:
        per_protein_plots = generate_per_protein_visualizations(analysis_results, output_dir, dpi)
        plot_files.extend(per_protein_plots)
    except Exception as e:
        print(f"⚠️  Error generating per-protein visualizations: {e}")
    
    print(f"✅ Generated {len(plot_files)} visualizations successfully!")
    return plot_files