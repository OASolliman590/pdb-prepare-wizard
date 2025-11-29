#!/usr/bin/env python3
"""
binding_affinity_analyzer.py
============================
Analyzes GNINA docking results to find:
• Best binding affinity for each protein-ligand complex
• Overall top performers across all complexes
• Summary statistics and visualizations
• Comparative benchmarking against specified targets

Reads: all_scores.csv (from post_gnina.py output)
Outputs: 
• best_affinities.csv (top pose per complex)
• affinity_summary.csv (statistics per complex)
• binding_affinity_plot.png (visualization)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import re
import argparse
import yaml

def parse_complex_info(tag):
    """Extract protein, binding site, and ligand from filename tag."""
    # Example: "PBP1_Catalytic_Amoxacillin" -> protein=PBP1, site=Catalytic, ligand=Amoxacillin
    parts = tag.split('_')
    if len(parts) >= 3:
        protein = parts[0]
        site = parts[1] 
        ligand = '_'.join(parts[2:])  # Handle multi-word ligands
    elif len(parts) == 2:
        protein = parts[0]
        site = "Unknown"
        ligand = parts[1]
    else:
        protein = tag
        site = "Unknown"
        ligand = "Unknown"
    
    return protein, site, ligand

def analyze_binding_affinities(csv_file, comparative_benchmark="*", top_count=10):
    """Analyze binding affinities and find best poses per complex with comparative benchmarking."""
    print("📊 Loading docking results...")
    df = pd.read_csv(csv_file)
    
    # Filter by comparative benchmark if specified
    if comparative_benchmark != "*":
        # Filter complexes that match the benchmark
        benchmark_filter = df['tag'].str.contains(comparative_benchmark, case=False, na=False)
        df = df[benchmark_filter]
        print(f"🔍 Filtering by benchmark '{comparative_benchmark}': {len(df)} complexes")
    
    # Parse complex information
    print("🔍 Parsing complex information...")
    df[['protein', 'binding_site', 'ligand']] = df['tag'].apply(
        lambda x: pd.Series(parse_complex_info(x))
    )
    
    # Create complex identifier
    df['complex'] = df['protein'] + '_' + df['binding_site'] + '_' + df['ligand']
    
    print(f"✓ Loaded {len(df)} poses from {df['tag'].nunique()} complexes")
    print(f"✓ Found {df['protein'].nunique()} unique proteins")
    print(f"✓ Found {df['ligand'].nunique()} unique ligands")
    
    # Find best pose for each complex (most negative = strongest binding)
    print("\n🏆 Finding best poses per complex...")
    best_poses = df.loc[df.groupby('tag')['vina_affinity'].idxmin()].copy()
    best_poses = best_poses.sort_values('vina_affinity')
    
    # Calculate summary statistics per complex
    print("📈 Calculating summary statistics...")
    summary_stats = df.groupby('tag').agg({
        'vina_affinity': ['min', 'max', 'mean', 'std', 'count'],
        'cnn_affinity': ['min', 'max', 'mean'],
        'cnn_score': ['max', 'mean']  # Higher CNN score is better
    }).round(3)
    
    # Flatten column names
    summary_stats.columns = ['_'.join(col).strip() for col in summary_stats.columns]
    summary_stats = summary_stats.reset_index()
    
    # Add complex info to summary
    summary_stats[['protein', 'binding_site', 'ligand']] = summary_stats['tag'].apply(
        lambda x: pd.Series(parse_complex_info(x))
    )
    
    # Highlight top performers
    print("\n🌟 Identifying top performers...")
    
    # Top N overall binding affinities (configurable)
    top_overall = best_poses.head(top_count)[['tag', 'protein', 'ligand', 'vina_affinity', 'cnn_affinity', 'cnn_score', 'mode']]
    
    # Best per protein
    best_per_protein = best_poses.groupby('protein').first().reset_index()
    best_per_protein = best_per_protein.sort_values('vina_affinity')
    
    # Best per ligand
    best_per_ligand = best_poses.groupby('ligand').first().reset_index() 
    best_per_ligand = best_per_ligand.sort_values('vina_affinity')
    
    return {
        'full_data': df,
        'best_poses': best_poses,
        'summary_stats': summary_stats,
        'top_overall': top_overall,
        'best_per_protein': best_per_protein,
        'best_per_ligand': best_per_ligand
    }

def create_visualizations(results, output_dir, dpi=300):
    """Create visualizations of binding affinity results."""
    print("\n📊 Creating visualizations...")
    
    df = results['full_data']
    best_poses = results['best_poses']
    
    # Set style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('GNINA Docking Results Analysis', fontsize=16, fontweight='bold')
    
    # 1. Distribution of binding affinities
    axes[0,0].hist(df['vina_affinity'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    axes[0,0].axvline(df['vina_affinity'].mean(), color='red', linestyle='--', 
                     label=f'Mean: {df["vina_affinity"].mean():.2f}')
    axes[0,0].set_xlabel('Vina Affinity (kcal/mol)')
    axes[0,0].set_ylabel('Frequency')
    axes[0,0].set_title('Distribution of Binding Affinities')
    axes[0,0].legend()
    axes[0,0].grid(True, alpha=0.3)
    
    # 2. Best affinity per protein
    protein_best = best_poses.groupby('protein')['vina_affinity'].min().sort_values()
    bars = axes[0,1].bar(range(len(protein_best)), protein_best.values, color='lightcoral')
    axes[0,1].set_xlabel('Protein')
    axes[0,1].set_ylabel('Best Vina Affinity (kcal/mol)')
    axes[0,1].set_title('Best Binding Affinity per Protein')
    axes[0,1].set_xticks(range(len(protein_best)))
    axes[0,1].set_xticklabels(protein_best.index, rotation=45, ha='right')
    axes[0,1].grid(True, alpha=0.3)
    
    # Highlight best protein
    best_idx = np.argmin(protein_best.values)
    bars[best_idx].set_color('darkred')
    
    # 3. CNN vs Vina affinity correlation
    scatter = axes[1,0].scatter(df['vina_affinity'], df['cnn_affinity'], 
                               alpha=0.6, c=df['cnn_score'], cmap='viridis')
    axes[1,0].set_xlabel('Vina Affinity (kcal/mol)')
    axes[1,0].set_ylabel('CNN Affinity')
    axes[1,0].set_title('CNN vs Vina Affinity (colored by CNN score)')
    plt.colorbar(scatter, ax=axes[1,0], label='CNN Score')
    axes[1,0].grid(True, alpha=0.3)
    
    # 4. Top 15 complexes
    top_15 = best_poses.head(15)
    y_pos = np.arange(len(top_15))
    bars = axes[1,1].barh(y_pos, top_15['vina_affinity'].values, color='mediumseagreen')
    axes[1,1].set_yticks(y_pos)
    axes[1,1].set_yticklabels([f"{row['protein']}_{row['ligand']}" for _, row in top_15.iterrows()], 
                             fontsize=8)
    axes[1,1].set_xlabel('Vina Affinity (kcal/mol)')
    axes[1,1].set_title('Top 15 Protein-Ligand Complexes')
    axes[1,1].grid(True, alpha=0.3)
    
    # Highlight best complex
    bars[0].set_color('darkgreen')
    
    plt.tight_layout()
    
    # Save plot
    plot_file = output_dir / 'binding_affinity_analysis.png'
    plt.savefig(plot_file, dpi=dpi, bbox_inches='tight')
    print(f"✓ Visualization saved: {plot_file}")
    
    return plot_file

def print_summary(results):
    """Print summary of results to console."""
    best_poses = results['best_poses']
    summary_stats = results['summary_stats']
    top_overall = results['top_overall']
    
    print("\n" + "="*60)
    print("🏆 BINDING AFFINITY ANALYSIS SUMMARY")
    print("="*60)
    
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"• Total poses analyzed: {len(results['full_data'])}")
    print(f"• Number of complexes: {len(best_poses)}")
    print(f"• Best overall affinity: {best_poses['vina_affinity'].min():.2f} kcal/mol")
    print(f"• Worst overall affinity: {best_poses['vina_affinity'].max():.2f} kcal/mol")
    print(f"• Average best affinity: {best_poses['vina_affinity'].mean():.2f} kcal/mol")
    
    print(f"\n🥇 TOP 5 PROTEIN-LIGAND COMPLEXES:")
    for i, (_, row) in enumerate(top_overall.head(5).iterrows(), 1):
        print(f"{i}. {row['protein']} + {row['ligand']}: {row['vina_affinity']:.2f} kcal/mol (mode {row['mode']})")
    
    print(f"\n🧬 BEST PERFORMANCE BY PROTEIN:")
    for _, row in results['best_per_protein'].head(5).iterrows():
        print(f"• {row['protein']}: {row['vina_affinity']:.2f} kcal/mol with {row['ligand']}")
    
    print(f"\n💊 BEST PERFORMANCE BY LIGAND:")
    for _, row in results['best_per_ligand'].head(5).iterrows():
        print(f"• {row['ligand']}: {row['vina_affinity']:.2f} kcal/mol with {row['protein']}")

def save_results(results, output_dir):
    """Save analysis results to CSV files."""
    print(f"\n💾 Saving results to {output_dir}...")
    
    # Best poses per complex
    best_file = output_dir / 'best_affinities.csv'
    results['best_poses'].to_csv(best_file, index=False)
    print(f"✓ Best poses saved: {best_file}")
    
    # Summary statistics
    summary_file = output_dir / 'affinity_summary.csv'
    results['summary_stats'].to_csv(summary_file, index=False)
    print(f"✓ Summary statistics saved: {summary_file}")
    
    # Top performers
    top_file = output_dir / 'top_performers.csv'
    results['top_overall'].to_csv(top_file, index=False)
    print(f"✓ Top performers saved: {top_file}")
    
    # Best per protein
    protein_file = output_dir / 'best_per_protein.csv'
    results['best_per_protein'].to_csv(protein_file, index=False)
    print(f"✓ Best per protein saved: {protein_file}")
    
    # Best per ligand
    ligand_file = output_dir / 'best_per_ligand.csv'
    results['best_per_ligand'].to_csv(ligand_file, index=False)
    print(f"✓ Best per ligand saved: {ligand_file}")

def load_config(config_file):
    """Load configuration from YAML file."""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def main():
    """Main analysis function."""
    parser = argparse.ArgumentParser(description="Binding Affinity Analyzer for GNINA Docking Results")
    parser.add_argument("-i", "--input", default="all_scores.csv", help="Input CSV file with docking scores")
    parser.add_argument("-o", "--output", default="binding_analysis", help="Output directory for results")
    parser.add_argument("-c", "--config", help="Configuration file (YAML)")
    parser.add_argument("-b", "--benchmark", default="*", help="Comparative benchmark target (default: *)")
    parser.add_argument("-n", "--top-count", type=int, default=10, help="Number of top performers to report")
    parser.add_argument("--dpi", type=int, default=300, help="DPI for output images")
    
    args = parser.parse_args()
    
    # Load configuration if provided
    config = {}
    if args.config:
        try:
            config = load_config(args.config)
            print(f"✅ Configuration loaded from: {args.config}")
        except Exception as e:
            print(f"⚠️  Error loading configuration: {e}")
    
    # Override with command line arguments
    input_file = Path(args.input)
    output_dir = Path(args.output)
    comparative_benchmark = config.get("analysis", {}).get("comparative_benchmark", args.benchmark)
    top_count = config.get("binding_affinity", {}).get("top_performers_count", args.top_count)
    dpi = config.get("visualization", {}).get("dpi", args.dpi)
    
    output_dir.mkdir(exist_ok=True)
    
    if not input_file.exists():
        print(f"❌ Error: {input_file} not found!")
        print("Run post_gnina.py first to generate the scores CSV.")
        return
    
    try:
        # Analyze data
        results = analyze_binding_affinities(input_file, comparative_benchmark, top_count)
        
        # Print summary
        print_summary(results)
        
        # Save results
        save_results(results, output_dir)
        
        # Create visualizations
        create_visualizations(results, output_dir, dpi)
        
        print(f"\n✅ Analysis complete! Results saved in '{output_dir}' directory")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        raise

if __name__ == "__main__":
    main()