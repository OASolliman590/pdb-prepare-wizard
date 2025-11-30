"""
Hierarchical Docking Analysis Module.

Respects the data structure:
- Multiple proteins
- Each protein docked to multiple ligands (with categories: Series, Lapi, Comparative)
- Each ligand-protein pair has multiple poses (typically 10)

Analysis hierarchy:
1. Best pose per ligand-protein pair
2. Best ligand per protein
3. Cross-protein comparison (same ligands across different proteins)
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)


def load_pairlist(pairlist_file: str) -> pd.DataFrame:
    """Load pairlist.csv and extract protein/ligand names."""
    df = pd.read_csv(pairlist_file)
    
    # Extract protein name from receptor (e.g., "Caspas3_3H0E_cleaned.pdbqt" -> "Caspas3")
    df['protein'] = df['receptor'].apply(lambda x: x.split('_')[0])
    
    # Extract ligand name (remove .pdbqt extension)
    df['ligand_name'] = df['ligand'].apply(lambda x: x.replace('.pdbqt', ''))
    
    # Create unique tag (matches log filename pattern)
    df['tag'] = df['receptor'] + '_' + df['site_id'] + '_' + df['ligand']
    
    return df


def parse_scores_with_pairlist(scores_csv: str, pairlist_file: str) -> pd.DataFrame:
    """
    Parse all_scores.csv and enrich with pairlist mapping.
    
    Returns DataFrame with columns:
    - tag: original tag from log
    - protein: protein name (e.g., Caspas3, AXL, VEGFR2)
    - site_id: ligand category (Series, Lapi, Compartive)
    - ligand: ligand name (e.g., 1S1, Lapatinib)
    - pose: pose number (1-10)
    - vina_affinity, cnn_affinity, cnn_score
    """
    # Load scores
    scores_df = pd.read_csv(scores_csv)
    
    # Load pairlist
    pairlist_df = load_pairlist(pairlist_file)
    
    # Create mapping from tag to protein/site_id/ligand
    tag_mapping = {}
    for _, row in pairlist_df.iterrows():
        # The tag in scores matches: receptor_site_id_ligand (without .log)
        tag_pattern = f"{row['receptor']}_{row['site_id']}_{row['ligand']}"
        tag_mapping[tag_pattern] = {
            'protein': row['protein'],
            'site_id': row['site_id'],
            'ligand': row['ligand_name'],
            'receptor': row['receptor']
        }
    
    # Map each score to its protein/ligand
    def map_tag(tag):
        # Try exact match first
        if tag in tag_mapping:
            return tag_mapping[tag]
        
        # Try without .log extension
        tag_clean = tag.replace('.log', '')
        if tag_clean in tag_mapping:
            return tag_mapping[tag_clean]
        
        # Try to find partial match
        for pattern, mapping in tag_mapping.items():
            if pattern in tag or tag in pattern:
                return mapping
        
        # Fallback: parse from filename
        parts = tag.replace('.log', '').replace('.pdbqt', '').split('_')
        return {
            'protein': parts[0] if parts else 'Unknown',
            'site_id': 'Unknown',
            'ligand': parts[-1] if parts else 'Unknown',
            'receptor': 'Unknown'
        }
    
    # Apply mapping
    mapping_results = scores_df['tag'].apply(map_tag)
    scores_df['protein'] = mapping_results.apply(lambda x: x['protein'])
    scores_df['site_id'] = mapping_results.apply(lambda x: x['site_id'])
    scores_df['ligand'] = mapping_results.apply(lambda x: x['ligand'])
    scores_df['receptor'] = mapping_results.apply(lambda x: x['receptor'])
    
    # Rename mode to pose for clarity
    if 'mode' in scores_df.columns:
        scores_df['pose'] = scores_df['mode']
    
    return scores_df


class HierarchicalDockingAnalyzer:
    """
    Hierarchical analysis of docking results.
    
    Structure:
    - Proteins (targets)
      - Ligand categories (Series, Lapi, Comparative)
        - Ligands
          - Poses (typically 10 per ligand-protein pair)
    """
    
    def __init__(self, scores_csv: str, pairlist_file: str, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load and enrich data
        logger.info("📊 Loading docking results with pairlist mapping...")
        self.df = parse_scores_with_pairlist(scores_csv, pairlist_file)
        
        # Summary
        self.proteins = sorted(self.df['protein'].unique())
        self.ligands = sorted(self.df['ligand'].unique())
        self.site_ids = sorted(self.df['site_id'].unique())
        
        logger.info(f"✅ Loaded {len(self.df)} poses")
        logger.info(f"   Proteins: {len(self.proteins)} ({', '.join(self.proteins)})")
        logger.info(f"   Ligands: {len(self.ligands)}")
        logger.info(f"   Categories: {', '.join(self.site_ids)}")
    
    def analyze_all(self) -> Dict:
        """Run complete hierarchical analysis."""
        results = {}
        
        # Level 1: Best pose per ligand-protein pair
        results['best_poses'] = self._analyze_best_poses()
        
        # Level 2: Best ligand per protein
        results['best_ligands_per_protein'] = self._analyze_best_ligands_per_protein()
        
        # Level 3: Cross-protein comparison
        results['cross_protein'] = self._analyze_cross_protein()
        
        # Level 4: Comparative analysis (redocking)
        results['comparative'] = self._analyze_comparative()
        
        # Save all results
        self._save_results(results)
        
        return results
    
    def _analyze_best_poses(self) -> pd.DataFrame:
        """Find best pose for each ligand-protein pair."""
        logger.info("\n🎯 Level 1: Best Pose per Ligand-Protein Pair")
        
        # Group by protein + ligand, find best (most negative) vina_affinity
        best_poses = self.df.loc[
            self.df.groupby(['protein', 'ligand'])['vina_affinity'].idxmin()
        ].copy()
        
        best_poses = best_poses.sort_values(['protein', 'vina_affinity'])
        
        logger.info(f"   Found {len(best_poses)} unique protein-ligand pairs")
        
        return best_poses
    
    def _analyze_best_ligands_per_protein(self) -> Dict[str, pd.DataFrame]:
        """For each protein, rank ligands by best binding affinity."""
        logger.info("\n🏆 Level 2: Best Ligands per Protein")
        
        results = {}
        
        for protein in self.proteins:
            protein_data = self.df[self.df['protein'] == protein].copy()
            
            # Get best pose per ligand for this protein
            best_per_ligand = protein_data.loc[
                protein_data.groupby('ligand')['vina_affinity'].idxmin()
            ].copy()
            
            best_per_ligand = best_per_ligand.sort_values('vina_affinity')
            results[protein] = best_per_ligand
            
            # Log top 3
            top3 = best_per_ligand.head(3)
            logger.info(f"   {protein}:")
            for _, row in top3.iterrows():
                logger.info(f"      {row['ligand']}: {row['vina_affinity']:.2f} kcal/mol")
        
        return results
    
    def _analyze_cross_protein(self) -> pd.DataFrame:
        """Compare same ligands across different proteins."""
        logger.info("\n🔄 Level 3: Cross-Protein Comparison")
        
        # Only use Series ligands (common across all proteins)
        series_data = self.df[self.df['site_id'] == 'Series'].copy()
        
        if series_data.empty:
            logger.warning("   No Series ligands found for cross-protein comparison")
            return pd.DataFrame()
        
        # Get best pose per protein-ligand pair
        best_poses = series_data.loc[
            series_data.groupby(['protein', 'ligand'])['vina_affinity'].idxmin()
        ]
        
        # Pivot to create protein × ligand matrix
        pivot = best_poses.pivot_table(
            index='ligand',
            columns='protein',
            values='vina_affinity',
            aggfunc='first'
        )
        
        # Calculate mean affinity per ligand across all proteins
        pivot['mean_affinity'] = pivot.mean(axis=1)
        pivot['std_affinity'] = pivot.std(axis=1)
        pivot = pivot.sort_values('mean_affinity')
        
        logger.info(f"   Created {pivot.shape[0]} × {pivot.shape[1]-2} affinity matrix")
        
        # Best overall ligands (across all proteins)
        logger.info("   Top ligands across all proteins:")
        for ligand in pivot.head(5).index:
            mean = pivot.loc[ligand, 'mean_affinity']
            logger.info(f"      {ligand}: {mean:.2f} kcal/mol (mean)")
        
        return pivot
    
    def _analyze_comparative(self) -> pd.DataFrame:
        """Analyze comparative/redocking results."""
        logger.info("\n📊 Level 4: Comparative (Redocking) Analysis")
        
        # Get Comparative ligands
        comp_data = self.df[self.df['site_id'] == 'Compartive'].copy()
        
        if comp_data.empty:
            logger.warning("   No Comparative ligands found")
            return pd.DataFrame()
        
        # Best pose per comparative ligand
        best_comp = comp_data.loc[
            comp_data.groupby(['protein', 'ligand'])['vina_affinity'].idxmin()
        ]
        
        best_comp = best_comp.sort_values('vina_affinity')
        
        logger.info(f"   Found {len(best_comp)} comparative (redocking) results:")
        for _, row in best_comp.iterrows():
            logger.info(f"      {row['protein']}: {row['ligand']} = {row['vina_affinity']:.2f} kcal/mol")
        
        return best_comp
    
    def _save_results(self, results: Dict):
        """Save all analysis results."""
        logger.info("\n💾 Saving results...")
        
        # Save best poses
        results['best_poses'].to_csv(
            self.output_dir / 'best_poses_per_pair.csv', index=False
        )
        
        # Save best ligands per protein
        for protein, df in results['best_ligands_per_protein'].items():
            df.to_csv(
                self.output_dir / f'best_ligands_{protein}.csv', index=False
            )
        
        # Save cross-protein matrix
        if not results['cross_protein'].empty:
            results['cross_protein'].to_csv(
                self.output_dir / 'cross_protein_affinity_matrix.csv'
            )
        
        # Save comparative
        if not results['comparative'].empty:
            results['comparative'].to_csv(
                self.output_dir / 'comparative_redocking.csv', index=False
            )
        
        logger.info(f"   Results saved to {self.output_dir}")
    
    def create_visualizations(self):
        """Create hierarchical visualizations."""
        logger.info("\n📊 Creating visualizations...")
        
        viz_dir = self.output_dir / 'visualizations'
        viz_dir.mkdir(exist_ok=True)
        
        # Set style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # 1. Affinity distribution per protein
        self._plot_affinity_by_protein(viz_dir)
        
        # 2. Heatmap: Protein × Ligand affinity matrix
        self._plot_affinity_heatmap(viz_dir)
        
        # 3. Best ligand per protein bar chart
        self._plot_best_ligand_per_protein(viz_dir)
        
        # 4. Cross-protein comparison for common ligands
        self._plot_cross_protein_comparison(viz_dir)
        
        # 5. Comparative (redocking) results
        self._plot_comparative_results(viz_dir)
        
        logger.info(f"   Visualizations saved to {viz_dir}")
    
    def _plot_affinity_by_protein(self, viz_dir: Path):
        """Box plot of affinities by protein."""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Only best poses per ligand
        best_poses = self.df.loc[
            self.df.groupby(['protein', 'ligand'])['vina_affinity'].idxmin()
        ]
        
        sns.boxplot(data=best_poses, x='protein', y='vina_affinity', ax=ax)
        ax.set_xlabel('Protein Target')
        ax.set_ylabel('Vina Affinity (kcal/mol)')
        ax.set_title('Binding Affinity Distribution by Protein')
        ax.axhline(y=-7.0, color='r', linestyle='--', alpha=0.5, label='Strong binding (-7)')
        ax.legend()
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(viz_dir / 'affinity_by_protein.png', dpi=300)
        plt.close()
    
    def _plot_affinity_heatmap(self, viz_dir: Path):
        """Heatmap of protein × ligand affinities."""
        # Only Series ligands for consistency
        series_data = self.df[self.df['site_id'] == 'Series'].copy()
        
        if series_data.empty:
            return
        
        # Best pose per pair
        best_poses = series_data.loc[
            series_data.groupby(['protein', 'ligand'])['vina_affinity'].idxmin()
        ]
        
        # Create pivot
        pivot = best_poses.pivot_table(
            index='ligand',
            columns='protein',
            values='vina_affinity',
            aggfunc='first'
        )
        
        # Sort by mean affinity
        pivot['mean'] = pivot.mean(axis=1)
        pivot = pivot.sort_values('mean')
        pivot = pivot.drop('mean', axis=1)
        
        fig, ax = plt.subplots(figsize=(10, 12))
        sns.heatmap(
            pivot, 
            annot=True, 
            fmt='.1f',
            cmap='RdYlGn_r',  # Red=bad, Green=good (more negative)
            center=-6,
            ax=ax,
            cbar_kws={'label': 'Vina Affinity (kcal/mol)'}
        )
        ax.set_title('Binding Affinity Matrix: Ligands × Proteins')
        ax.set_xlabel('Protein')
        ax.set_ylabel('Ligand')
        plt.tight_layout()
        plt.savefig(viz_dir / 'affinity_heatmap.png', dpi=300)
        plt.close()
    
    def _plot_best_ligand_per_protein(self, viz_dir: Path):
        """Bar chart showing best ligand for each protein."""
        best_per_protein = []
        
        for protein in self.proteins:
            protein_data = self.df[self.df['protein'] == protein]
            best_idx = protein_data['vina_affinity'].idxmin()
            best_row = protein_data.loc[best_idx]
            best_per_protein.append({
                'protein': protein,
                'ligand': best_row['ligand'],
                'affinity': best_row['vina_affinity']
            })
        
        best_df = pd.DataFrame(best_per_protein)
        best_df = best_df.sort_values('affinity')
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(best_df['protein'], best_df['affinity'], color=sns.color_palette("husl", len(best_df)))
        
        # Add ligand names as labels
        for i, (idx, row) in enumerate(best_df.iterrows()):
            ax.text(row['affinity'] + 0.1, i, row['ligand'], va='center', fontsize=9)
        
        ax.set_xlabel('Vina Affinity (kcal/mol)')
        ax.set_title('Best Ligand per Protein Target')
        ax.axvline(x=-7.0, color='r', linestyle='--', alpha=0.5, label='Strong binding')
        plt.tight_layout()
        plt.savefig(viz_dir / 'best_ligand_per_protein.png', dpi=300)
        plt.close()
    
    def _plot_cross_protein_comparison(self, viz_dir: Path):
        """Line plot comparing same ligands across proteins."""
        series_data = self.df[self.df['site_id'] == 'Series'].copy()
        
        if series_data.empty:
            return
        
        # Best pose per pair
        best_poses = series_data.loc[
            series_data.groupby(['protein', 'ligand'])['vina_affinity'].idxmin()
        ]
        
        # Get top 5 ligands (by mean affinity)
        ligand_means = best_poses.groupby('ligand')['vina_affinity'].mean().sort_values()
        top_ligands = ligand_means.head(5).index.tolist()
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for ligand in top_ligands:
            ligand_data = best_poses[best_poses['ligand'] == ligand]
            ligand_data = ligand_data.sort_values('protein')
            ax.plot(ligand_data['protein'], ligand_data['vina_affinity'], 
                   marker='o', linewidth=2, markersize=8, label=ligand)
        
        ax.set_xlabel('Protein Target')
        ax.set_ylabel('Vina Affinity (kcal/mol)')
        ax.set_title('Top 5 Ligands: Cross-Protein Comparison')
        ax.legend(title='Ligand', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.axhline(y=-7.0, color='r', linestyle='--', alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(viz_dir / 'cross_protein_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_comparative_results(self, viz_dir: Path):
        """Bar chart of comparative/redocking results."""
        comp_data = self.df[self.df['site_id'] == 'Compartive'].copy()
        
        if comp_data.empty:
            return
        
        # Best pose per comparative
        best_comp = comp_data.loc[
            comp_data.groupby(['protein', 'ligand'])['vina_affinity'].idxmin()
        ]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x_labels = best_comp['protein'] + '\n(' + best_comp['ligand'].str[:15] + ')'
        bars = ax.bar(range(len(best_comp)), best_comp['vina_affinity'], 
                     color=sns.color_palette("husl", len(best_comp)))
        
        ax.set_xticks(range(len(best_comp)))
        ax.set_xticklabels(x_labels, rotation=45, ha='right', fontsize=8)
        ax.set_ylabel('Vina Affinity (kcal/mol)')
        ax.set_title('Comparative (Redocking) Results')
        ax.axhline(y=-7.0, color='r', linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.savefig(viz_dir / 'comparative_redocking.png', dpi=300)
        plt.close()
    
    def generate_report(self) -> str:
        """Generate a summary report."""
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("HIERARCHICAL DOCKING ANALYSIS REPORT")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        # Overview
        report_lines.append("📊 DATA OVERVIEW")
        report_lines.append("-" * 40)
        report_lines.append(f"Total poses: {len(self.df)}")
        report_lines.append(f"Proteins: {len(self.proteins)}")
        report_lines.append(f"Ligands: {len(self.ligands)}")
        report_lines.append(f"Categories: {', '.join(self.site_ids)}")
        report_lines.append("")
        
        # Best ligand per protein
        report_lines.append("🏆 BEST LIGAND PER PROTEIN")
        report_lines.append("-" * 40)
        for protein in self.proteins:
            protein_data = self.df[self.df['protein'] == protein]
            best_idx = protein_data['vina_affinity'].idxmin()
            best_row = protein_data.loc[best_idx]
            report_lines.append(
                f"{protein:15} → {best_row['ligand']:15} ({best_row['vina_affinity']:.2f} kcal/mol)"
            )
        report_lines.append("")
        
        # Cross-protein top performers
        series_data = self.df[self.df['site_id'] == 'Series']
        if not series_data.empty:
            report_lines.append("🌟 TOP LIGANDS (across all proteins)")
            report_lines.append("-" * 40)
            best_poses = series_data.loc[
                series_data.groupby(['protein', 'ligand'])['vina_affinity'].idxmin()
            ]
            ligand_means = best_poses.groupby('ligand')['vina_affinity'].mean().sort_values()
            for ligand in ligand_means.head(5).index:
                mean = ligand_means[ligand]
                report_lines.append(f"{ligand:15} → mean: {mean:.2f} kcal/mol")
            report_lines.append("")
        
        # Comparative results
        comp_data = self.df[self.df['site_id'] == 'Compartive']
        if not comp_data.empty:
            report_lines.append("📊 COMPARATIVE (REDOCKING) RESULTS")
            report_lines.append("-" * 40)
            best_comp = comp_data.loc[
                comp_data.groupby(['protein', 'ligand'])['vina_affinity'].idxmin()
            ]
            for _, row in best_comp.iterrows():
                report_lines.append(
                    f"{row['protein']:15} : {row['ligand'][:20]:20} = {row['vina_affinity']:.2f} kcal/mol"
                )
        
        report_lines.append("")
        report_lines.append("=" * 60)
        
        report_text = "\n".join(report_lines)
        
        # Save report
        with open(self.output_dir / 'analysis_report.txt', 'w') as f:
            f.write(report_text)
        
        return report_text


def run_hierarchical_analysis(
    scores_csv: str,
    pairlist_file: str,
    output_dir: str
) -> Dict:
    """
    Run complete hierarchical docking analysis.
    
    Parameters
    ----------
    scores_csv : str
        Path to all_scores.csv
    pairlist_file : str
        Path to pairlist.csv
    output_dir : str
        Output directory for results
        
    Returns
    -------
    dict
        Analysis results
    """
    analyzer = HierarchicalDockingAnalyzer(scores_csv, pairlist_file, output_dir)
    results = analyzer.analyze_all()
    analyzer.create_visualizations()
    report = analyzer.generate_report()
    
    print("\n" + report)
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python hierarchical_analyzer.py <scores.csv> <pairlist.csv> <output_dir>")
        sys.exit(1)
    
    run_hierarchical_analysis(sys.argv[1], sys.argv[2], sys.argv[3])

