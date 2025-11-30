"""
Simplified Post-Docking Analysis Pipeline for GNINA.

Focuses on:
- 3-folder input structure (sdf_folder, log_folder, receptors_folder)
- Generate all_scores.csv from logs
- Create complex PDB files (receptor + ligand)
- Comparative benchmarking using PDB code matching + pairlist
- RMSD analysis
- Simplified visualizations (no PandaMap, no plugins)
"""
from pathlib import Path
from typing import Optional, Dict, List
import pandas as pd
import logging

from .generate_scores_csv import generate_all_scores_csv
from .pose_extractor import extract_best_poses_from_gnina
from .pdb_code_matcher import (
    extract_pdb_code,
    find_comparative_reference,
    load_pairlist as load_pairlist_df
)
from .simplified_input_handler import (
    find_sdf_files,
    find_log_files,
    find_receptor_files,
    load_pairlist,
    match_poses_to_receptors
)
from .publication_pandamap import run_publication_pandamap_analysis
from .binding_affinity_analyzer import analyze_binding_affinities
from .hierarchical_analyzer import HierarchicalDockingAnalyzer, run_hierarchical_analysis
from .py3dmol_visualizer import (
    visualize_all_complexes,
    visualize_ligands_by_protein
)
from .prolif_interaction_maps import create_interaction_maps_for_all_complexes
from .enhanced_rmsd_analyzer import (
    calculate_rmsd_matrix_from_pdbs,
    analyze_pose_clustering_enhanced,
    analyze_conformational_diversity_enhanced,
    create_rmsd_visualizations_enhanced
)


class SimplifiedPostDockingPipeline:
    """
    Simplified post-docking analysis pipeline for GNINA.
    
    Input Structure:
    - sdf_folder: Docking poses (SDF files)
    - log_folder: Docking logs (can be same as sdf_folder)
    - receptors_folder: Receptor PDBQT files
    - pairlist_file: Optional pairlist.csv for matching
    """
    
    def __init__(
        self,
        sdf_folder: str,
        log_folder: str,
        receptors_folder: str,
        output_dir: str,
        pairlist_file: Optional[str] = None
    ):
        """
        Initialize simplified pipeline.
        
        Parameters
        ----------
        sdf_folder : str
            Folder containing SDF pose files
        log_folder : str
            Folder containing log files (can be same as sdf_folder)
        receptors_folder : str
            Folder containing receptor PDBQT files
        output_dir : str
            Output directory for results
        pairlist_file : str, optional
            Path to pairlist.csv
        """
        self.sdf_folder = Path(sdf_folder)
        self.log_folder = Path(log_folder)
        self.receptors_folder = Path(receptors_folder)
        self.output_dir = Path(output_dir)
        self.pairlist_file = Path(pairlist_file) if pairlist_file else None
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        log_file = self.output_dir / "simplified_pipeline.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Results storage
        self.results = {}
        self.complexes = []
        self.scores_df = None
        
    def run(self) -> bool:
        """
        Run the simplified pipeline.
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        self.logger.info("🚀 Starting Simplified Post-Docking Analysis Pipeline")
        self.logger.info(f"📂 SDF folder: {self.sdf_folder}")
        self.logger.info(f"📂 Log folder: {self.log_folder}")
        self.logger.info(f"📂 Receptors folder: {self.receptors_folder}")
        self.logger.info(f"📂 Output directory: {self.output_dir}")
        
        try:
            # Step 1: Find input files
            if not self._find_input_files():
                return False
            
            # Step 2: Generate all_scores.csv
            if not self._generate_scores_csv():
                return False
            
            # Step 3: Match poses to receptors
            if not self._match_poses_to_receptors():
                return False
            
            # Step 4: Create complex PDB files
            if not self._create_complexes():
                return False
            
            # Step 5: Binding affinity analysis with comparative benchmarking
            if not self._analyze_binding_affinity():
                return False
            
            # Step 6: RMSD analysis
            if not self._analyze_rmsd():
                return False
            
            # Step 7: Extract and organize poses
            if not self._extract_poses():
                return False
            
            # Step 8: Generate reports
            if not self._generate_reports():
                return False
            
            # Step 9: Generate simplified visualizations
            if not self._generate_visualizations():
                return False
            
            # Step 10: Generate publication-quality PandaMap analysis
            self._generate_pandamap_analysis()  # Don't fail if PandaMap unavailable
            
            # Step 11: Generate py3Dmol 3D visualizations
            self._generate_py3dmol_visualizations()  # Don't fail if py3Dmol unavailable
            
            # Step 12: Generate ProLIF 2D interaction maps
            self._generate_prolif_interaction_maps()  # Don't fail if ProLIF unavailable
            
            self.logger.info("✅ Simplified pipeline completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
            return False
    
    def _find_input_files(self) -> bool:
        """Find and validate input files."""
        self.logger.info("🔍 Finding input files...")
        
        self.sdf_files = find_sdf_files(self.sdf_folder)
        self.log_files = find_log_files(self.log_folder)
        self.receptor_files = find_receptor_files(self.receptors_folder)
        
        self.logger.info(f"  Found {len(self.sdf_files)} SDF files")
        self.logger.info(f"  Found {len(self.log_files)} log files")
        self.logger.info(f"  Found {len(self.receptor_files)} receptor files")
        
        if not self.log_files:
            self.logger.error("❌ No log files found!")
            return False
        
        if not self.receptor_files:
            self.logger.warning("⚠️  No receptor files found!")
        
        return True
    
    def _generate_scores_csv(self) -> bool:
        """Generate all_scores.csv from log files."""
        self.logger.info("📊 Generating all_scores.csv...")
        
        scores_csv = self.output_dir / "all_scores.csv"
        
        # Use log_folder as gnina_out_dir for generate_all_scores_csv
        success = generate_all_scores_csv(
            self.log_folder,
            scores_csv,
            self.pairlist_file
        )
        
        if success and scores_csv.exists():
            self.scores_df = pd.read_csv(scores_csv)
            self.logger.info(f"✅ Generated all_scores.csv with {len(self.scores_df)} scores")
            return True
        else:
            self.logger.error("❌ Failed to generate all_scores.csv")
            return False
    
    def _match_poses_to_receptors(self) -> bool:
        """Match SDF poses to receptors using pairlist or filename patterns."""
        self.logger.info("🔗 Matching poses to receptors...")
        
        pairlist_df = load_pairlist(self.pairlist_file)
        
        self.complexes = match_poses_to_receptors(
            self.sdf_files,
            self.receptor_files,
            pairlist_df
        )
        
        self.logger.info(f"✅ Matched {len(self.complexes)} complexes")
        return len(self.complexes) > 0
    
    def _create_complexes(self) -> bool:
        """Create complex PDB files (receptor + ligand)."""
        self.logger.info("🧬 Creating complex PDB files...")
        
        complexes_dir = self.output_dir / "complexes"
        complexes_dir.mkdir(exist_ok=True)
        
        written = 0
        for complex_info in self.complexes:
            receptor_file = complex_info.get('receptor_file')
            pose_file = complex_info.get('pose_file')
            complex_name = complex_info.get('complex_name', 'unknown')
            
            if not receptor_file or not pose_file:
                self.logger.warning(f"  ⚠️  Missing files for {complex_name}")
                continue
            
            # Create complex PDB using pose_extractor logic
            try:
                output_pdb = complexes_dir / f"{complex_name}.pdb"
                
                # Use create_complex_pdb helper if available, otherwise use OpenBabel
                from openbabel import pybel
                
                # Read receptor PDBQT
                receptor_lines = []
                if Path(receptor_file).exists():
                    try:
                        receptor_mol = next(pybel.readfile("pdbqt", str(receptor_file)))
                        receptor_pdb = receptor_mol.write("pdb")
                        for line in receptor_pdb.split('\n'):
                            if line.startswith('ATOM'):
                                line = line.ljust(80)
                                new_line = f"ATOM  {line[6:21]}A{line[22:]}"
                                receptor_lines.append(new_line)
                    except Exception as e:
                        self.logger.warning(f"  ⚠️  Could not read receptor {receptor_file}: {e}")
                        continue
                
                # Read ligand SDF
                ligand_lines = []
                try:
                    ligand_mol = next(pybel.readfile("sdf", str(pose_file)))
                    ligand_pdb = ligand_mol.write("pdb")
                    for line in ligand_pdb.split('\n'):
                        if line.startswith('ATOM') or line.startswith('HETATM'):
                            line = line.ljust(80)
                            new_line = f"HETATM{line[6:21]}B{line[22:]}"
                            new_line = new_line[:17] + "UNK" + new_line[20:]
                            ligand_lines.append(new_line)
                except Exception as e:
                    self.logger.warning(f"  ⚠️  Could not read ligand {pose_file}: {e}")
                    continue
                
                # Combine receptor and ligand
                all_lines = receptor_lines + ligand_lines + ["END"]
                
                with open(output_pdb, 'w') as f:
                    f.write('\n'.join(all_lines))
                
                written += 1
                self.logger.debug(f"  ✅ Created complex: {complex_name}")
                
            except ImportError:
                self.logger.error("  ❌ OpenBabel not available for complex creation")
                return False
            except Exception as e:
                self.logger.warning(f"  ⚠️  Error creating complex {complex_name}: {e}")
                continue
        
        self.logger.info(f"✅ Created {written} complex PDB files")
        return written > 0
    
    def _analyze_binding_affinity(self) -> bool:
        """
        Analyze binding affinities using hierarchical analysis.
        
        Hierarchy:
        1. Best pose per ligand-protein pair
        2. Best ligand per protein
        3. Cross-protein comparison (same ligands)
        4. Comparative (redocking) analysis
        """
        self.logger.info("📈 Analyzing binding affinities (hierarchical)...")
        
        if self.scores_df is None or self.scores_df.empty:
            self.logger.error("❌ No scores data available")
            return False
        
        if not self.pairlist_file or not self.pairlist_file.exists():
            self.logger.warning("⚠️  No pairlist.csv - falling back to basic analysis")
            return self._analyze_binding_affinity_basic()
        
        try:
            # Use hierarchical analyzer with pairlist mapping
            scores_csv = self.output_dir / "all_scores.csv"
            analysis_dir = self.output_dir / "analysis"
            analysis_dir.mkdir(exist_ok=True)
            
            # Run hierarchical analysis
            analyzer = HierarchicalDockingAnalyzer(
                str(scores_csv),
                str(self.pairlist_file),
                str(analysis_dir)
            )
            
            hierarchical_results = analyzer.analyze_all()
            analyzer.create_visualizations()
            report = analyzer.generate_report()
            
            # Print report
            print("\n" + report)
            
            # Store results
            self.results['hierarchical_analysis'] = hierarchical_results
            self.results['proteins'] = analyzer.proteins
            self.results['ligands'] = analyzer.ligands
            
            # Also organize best poses by affinity
            self._organize_poses_by_affinity(hierarchical_results['best_poses'])
            
            self.logger.info("✅ Hierarchical analysis completed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in hierarchical analysis: {e}", exc_info=True)
            return False
    
    def _analyze_binding_affinity_basic(self) -> bool:
        """Basic binding affinity analysis without pairlist."""
        try:
            scores_csv = self.output_dir / "all_scores.csv"
            
            analysis_results = analyze_binding_affinities(
                str(scores_csv),
                comparative_benchmark="*",
                top_count=20
            )
            
            # Save results
            reports_dir = self.output_dir / "reports"
            reports_dir.mkdir(exist_ok=True)
            
            analysis_results['best_poses'].to_csv(
                reports_dir / "best_poses.csv", index=False
            )
            analysis_results['summary_stats'].to_csv(
                reports_dir / "summary_stats.csv", index=False
            )
            
            self.results['affinity_analysis'] = analysis_results
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in basic analysis: {e}", exc_info=True)
            return False
    
    def _organize_poses_by_affinity(self, best_poses_df: pd.DataFrame):
        """Organize best poses by binding affinity strength."""
        best_poses_dir = self.output_dir / "best_poses"
        best_poses_dir.mkdir(exist_ok=True)
        
        strong_binders_dir = best_poses_dir / "strong_binders"
        moderate_binders_dir = best_poses_dir / "moderate_binders"
        weak_binders_dir = best_poses_dir / "weak_binders"
        
        for dir_path in [strong_binders_dir, moderate_binders_dir, weak_binders_dir]:
            dir_path.mkdir(exist_ok=True)
        
        import shutil
        
        # Strong: < -8.0, Moderate: -6.0 to -8.0, Weak: > -6.0
        strong_threshold = -8.0
        moderate_threshold = -6.0
        
        for _, row in best_poses_df.iterrows():
            tag = row.get('tag', '')
            affinity = row.get('vina_affinity', 0)
            
            # Try to find complex file
            complex_file = self.output_dir / "complexes" / f"{tag}.pdb"
            if not complex_file.exists():
                continue
            
            if affinity <= strong_threshold:
                target_dir = strong_binders_dir
            elif affinity <= moderate_threshold:
                target_dir = moderate_binders_dir
            else:
                target_dir = weak_binders_dir
            
            try:
                shutil.copy2(complex_file, target_dir / complex_file.name)
            except Exception:
                pass
        
        self.logger.info(f"✅ Organized poses by affinity")
    
    def _analyze_rmsd(self) -> bool:
        """Perform RMSD analysis with pose clustering and conformational diversity."""
        self.logger.info("📐 Analyzing RMSD with clustering and diversity...")
        
        if self.scores_df is None or self.scores_df.empty:
            self.logger.warning("⚠️  No scores data for RMSD analysis")
            return False
        
        try:
            rmsd_dir = self.output_dir / "rmsd_analysis"
            rmsd_dir.mkdir(exist_ok=True)
            
            # Get best poses (one per complex)
            best_poses_df = self.scores_df.loc[
                self.scores_df.groupby('tag')['vina_affinity'].idxmin()
            ].copy()
            
            # Find corresponding PDB files
            complexes_dir = self.output_dir / "complexes"
            pdb_files = []
            valid_tags = []
            
            for tag in best_poses_df['tag']:
                pdb_file = complexes_dir / f"{tag}.pdb"
                if pdb_file.exists():
                    pdb_files.append(pdb_file)
                    valid_tags.append(tag)
                else:
                    self.logger.debug(f"  ⚠️  PDB file not found for {tag}")
            
            if len(pdb_files) < 2:
                self.logger.warning("⚠️  Need at least 2 PDB files for RMSD analysis")
                return False
            
            # Filter poses data to valid tags
            valid_poses = best_poses_df[best_poses_df['tag'].isin(valid_tags)].copy()
            valid_poses = valid_poses.reset_index(drop=True)
            
            self.logger.info(f"  Calculating RMSD matrix for {len(pdb_files)} complexes...")
            
            # Calculate RMSD matrix from PDB files
            rmsd_matrix, filenames = calculate_rmsd_matrix_from_pdbs(
                pdb_files,
                ligand_only=True,
                max_pairs=500  # Limit for performance
            )
            
            # Save RMSD matrix
            rmsd_df = pd.DataFrame(rmsd_matrix, index=filenames, columns=filenames)
            rmsd_df.to_csv(rmsd_dir / "rmsd_matrix.csv")
            
            # Perform pose clustering
            self.logger.info("  Performing pose clustering...")
            clustering_results = analyze_pose_clustering_enhanced(
                valid_poses,
                rmsd_matrix,
                pdb_files,
                method='kmeans',
                n_clusters=min(5, len(valid_poses) // 2)  # Adaptive cluster count
            )
            
            # Save clustering results
            clustering_results['poses_with_clusters'].to_csv(
                rmsd_dir / "poses_with_clusters.csv", index=False
            )
            clustering_results['cluster_summary'].to_csv(
                rmsd_dir / "cluster_summary.csv", index=False
            )
            clustering_results['cluster_centroids'].to_csv(
                rmsd_dir / "cluster_centroids.csv", index=False
            )
            
            # Analyze conformational diversity
            self.logger.info("  Analyzing conformational diversity...")
            diversity_results = analyze_conformational_diversity_enhanced(
                valid_poses,
                rmsd_matrix
            )
            
            # Save diversity results
            diversity_results['diversity_metrics'].to_csv(
                rmsd_dir / "diversity_metrics.csv", index=False
            )
            
            diversity_stats = pd.DataFrame([diversity_results['overall_stats']])
            diversity_stats.to_csv(rmsd_dir / "diversity_overall_stats.csv", index=False)
            
            # Create visualizations
            viz_dir = rmsd_dir / "visualizations"
            viz_dir.mkdir(exist_ok=True)
            
            self.logger.info("  Creating RMSD visualizations...")
            viz_files = create_rmsd_visualizations_enhanced(
                clustering_results,
                diversity_results,
                viz_dir,
                dpi=300
            )
            
            self.results['rmsd_analysis'] = {
                'clustering': clustering_results,
                'diversity': diversity_results,
                'rmsd_matrix': rmsd_matrix
            }
            
            self.logger.info(f"✅ RMSD analysis completed")
            if len(clustering_results['cluster_summary']) > 0:
                self.logger.info(f"   Clusters found: {len(clustering_results['cluster_summary'])}")
            if 'overall_stats' in diversity_results and 'avg_pairwise_rmsd' in diversity_results['overall_stats']:
                self.logger.info(f"   Average pairwise RMSD: {diversity_results['overall_stats']['avg_pairwise_rmsd']:.2f} Å")
            
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️  RMSD analysis error: {e}", exc_info=True)
            # Don't fail the pipeline if RMSD fails
            return True
    
    def _extract_poses(self) -> bool:
        """Extract best poses and create complexes."""
        self.logger.info("📦 Extracting best poses...")
        
        # Complexes are already created in _create_complexes()
        # This step is mainly for organization and validation
        
        complexes_dir = self.output_dir / "complexes"
        if not complexes_dir.exists():
            self.logger.warning("⚠️  Complexes directory not found, creating...")
            complexes_dir.mkdir(exist_ok=True)
        
        complex_files = list(complexes_dir.glob("*.pdb"))
        self.logger.info(f"✅ Found {len(complex_files)} complex files")
        
        return len(complex_files) > 0
    
    def _generate_reports(self) -> bool:
        """Generate analysis reports."""
        self.logger.info("📄 Generating reports...")
        
        reports_dir = self.output_dir / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        if self.scores_df is not None:
            # Best poses
            best_poses = self.scores_df.loc[
                self.scores_df.groupby('tag')['vina_affinity'].idxmin()
            ].sort_values('vina_affinity')
            
            best_poses.to_csv(reports_dir / "best_poses.csv", index=False)
            
            # Summary stats
            summary = self.scores_df.groupby('tag').agg({
                'vina_affinity': ['min', 'max', 'mean', 'std']
            }).round(3)
            summary.columns = ['_'.join(col).strip() for col in summary.columns]
            summary.to_csv(reports_dir / "summary_stats.csv")
            
            self.logger.info("✅ Reports generated")
            return True
        
        return False
    
    def _generate_visualizations(self) -> bool:
        """Generate enhanced visualizations with 2D plots and heatmaps."""
        self.logger.info("📊 Generating enhanced visualizations...")
        
        viz_dir = self.output_dir / "visualizations"
        viz_dir.mkdir(exist_ok=True)
        
        if self.scores_df is None or self.scores_df.empty:
            self.logger.warning("⚠️  No scores data for visualizations")
            return False
        
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Set publication style
            plt.style.use('default')
            sns.set_palette("husl")
            
            # 1. Affinity distribution histogram
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(self.scores_df['vina_affinity'], bins=30, alpha=0.7, edgecolor='black', color='skyblue')
            mean_aff = self.scores_df['vina_affinity'].mean()
            median_aff = self.scores_df['vina_affinity'].median()
            ax.axvline(mean_aff, color='red', linestyle='--', 
                      label=f'Mean: {mean_aff:.2f}')
            ax.axvline(median_aff, color='green', linestyle='--',
                      label=f'Median: {median_aff:.2f}')
            ax.set_xlabel('Vina Affinity (kcal/mol)', fontsize=12)
            ax.set_ylabel('Frequency', fontsize=12)
            ax.set_title('Distribution of Binding Affinities', fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(viz_dir / "affinity_distribution.png", dpi=300, bbox_inches='tight')
            plt.close()
            
            # 2. Top performers bar chart
            if 'affinity_analysis' in self.results:
                best_poses = self.results['affinity_analysis']['best_poses']
                top_10 = best_poses.head(10)
                
                fig, ax = plt.subplots(figsize=(12, 6))
                bars = ax.barh(range(len(top_10)), top_10['vina_affinity'].values, 
                               color='lightcoral', edgecolor='black')
                ax.set_yticks(range(len(top_10)))
                ax.set_yticklabels(top_10['tag'].values, fontsize=10)
                ax.set_xlabel('Vina Affinity (kcal/mol)', fontsize=12)
                ax.set_title('Top 10 Binding Affinities', fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.3, axis='x')
                plt.tight_layout()
                plt.savefig(viz_dir / "top_performers.png", dpi=300, bbox_inches='tight')
                plt.close()
            
            # 3. Affinity heatmap (if multiple proteins/ligands)
            if 'affinity_analysis' in self.results:
                best_poses = self.results['affinity_analysis']['best_poses']
                
                # Try to extract protein and ligand names
                if 'protein' in best_poses.columns and 'ligand' in best_poses.columns:
                    # Create pivot table for heatmap
                    pivot_data = best_poses.pivot_table(
                        values='vina_affinity',
                        index='protein',
                        columns='ligand',
                        aggfunc='min'
                    )
                    
                    if len(pivot_data) > 1 and len(pivot_data.columns) > 1:
                        fig, ax = plt.subplots(figsize=(max(12, len(pivot_data.columns) * 0.8),
                                                       max(8, len(pivot_data) * 0.6)))
                        sns.heatmap(pivot_data, annot=True, fmt='.2f', cmap='viridis_r',
                                   cbar_kws={'label': 'Binding Affinity (kcal/mol)'},
                                   ax=ax, linewidths=0.5)
                        ax.set_title('Binding Affinity Heatmap (Protein × Ligand)', 
                                   fontsize=14, fontweight='bold')
                        ax.set_xlabel('Ligand', fontsize=12)
                        ax.set_ylabel('Protein', fontsize=12)
                        plt.tight_layout()
                        plt.savefig(viz_dir / "affinity_heatmap.png", dpi=300, bbox_inches='tight')
                        plt.close()
            
            # 4. Binding affinity by protein (if protein column exists)
            if 'affinity_analysis' in self.results:
                best_poses = self.results['affinity_analysis']['best_poses']
                if 'protein' in best_poses.columns:
                    fig, ax = plt.subplots(figsize=(12, 6))
                    protein_affinities = best_poses.groupby('protein')['vina_affinity'].min().sort_values()
                    bars = ax.bar(range(len(protein_affinities)), protein_affinities.values,
                                 color='lightblue', edgecolor='black')
                    ax.set_xticks(range(len(protein_affinities)))
                    ax.set_xticklabels(protein_affinities.index, rotation=45, ha='right')
                    ax.set_ylabel('Best Binding Affinity (kcal/mol)', fontsize=12)
                    ax.set_title('Best Binding Affinity by Protein', fontsize=14, fontweight='bold')
                    ax.grid(True, alpha=0.3, axis='y')
                    plt.tight_layout()
                    plt.savefig(viz_dir / "affinity_by_protein.png", dpi=300, bbox_inches='tight')
                    plt.close()
            
            self.logger.info("✅ Enhanced visualizations generated")
            return True
            
        except ImportError:
            self.logger.warning("⚠️  Matplotlib/Seaborn not available for visualizations")
            return False
        except Exception as e:
            self.logger.warning(f"⚠️  Error generating visualizations: {e}", exc_info=True)
            return False
    
    def _generate_py3dmol_visualizations(self) -> bool:
        """Generate py3Dmol 3D visualizations for complexes."""
        self.logger.info("🌐 Generating py3Dmol 3D visualizations...")
        
        complexes_dir = self.output_dir / "complexes"
        if not complexes_dir.exists() or not list(complexes_dir.glob("*.pdb")):
            self.logger.warning("⚠️  No complexes found for py3Dmol visualization")
            return False
        
        viz_3d_dir = self.output_dir / "3d_visualizations"
        viz_3d_dir.mkdir(exist_ok=True)
        
        try:
            # Visualize individual complexes
            individual_dir = viz_3d_dir / "individual_complexes"
            created_individual = visualize_all_complexes(
                complexes_dir,
                individual_dir,
                width=800,
                height=600
            )
            
            self.logger.info(f"  ✅ Created {len(created_individual)} individual 3D visualizations")
            
            # Visualize aggregated ligands by protein
            if 'affinity_analysis' in self.results:
                aggregated_dir = viz_3d_dir / "aggregated_by_protein"
                created_aggregated = visualize_ligands_by_protein(
                    complexes_dir,
                    self.receptors_folder,
                    self.results['affinity_analysis']['best_poses'],
                    aggregated_dir,
                    width=1000,
                    height=800
                )
                
                self.logger.info(f"  ✅ Created {len(created_aggregated)} aggregated visualizations")
                self.results['py3dmol_visualizations'] = {
                    'individual': created_individual,
                    'aggregated': created_aggregated
                }
            
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️  py3Dmol visualization error: {e}")
            return False
    
    def _generate_prolif_interaction_maps(self) -> bool:
        """Generate ProLIF 2D interaction maps for complexes."""
        self.logger.info("📊 Generating ProLIF 2D interaction maps...")
        
        complexes_dir = self.output_dir / "complexes"
        if not complexes_dir.exists() or not list(complexes_dir.glob("*.pdb")):
            self.logger.warning("⚠️  No complexes found for ProLIF interaction maps")
            return False
        
        interaction_maps_dir = self.output_dir / "interaction_maps"
        interaction_maps_dir.mkdir(exist_ok=True)
        
        try:
            created_maps = create_interaction_maps_for_all_complexes(
                complexes_dir,
                interaction_maps_dir,
                ligand_resname="UNK",
                dpi=300
            )
            
            self.logger.info(f"  ✅ Created {len(created_maps)} interaction maps")
            self.results['prolif_interaction_maps'] = created_maps
            
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️  ProLIF interaction map error: {e}")
            return False
    
    def _generate_pandamap_analysis(self) -> bool:
        """Generate publication-quality PandaMap interaction analysis."""
        self.logger.info("🐼 Generating publication-quality PandaMap analysis...")
        
        complexes_dir = self.output_dir / "complexes"
        if not complexes_dir.exists() or not list(complexes_dir.glob("*.pdb")):
            self.logger.warning("⚠️  No complexes found for PandaMap analysis")
            return False
        
        pandamap_dir = self.output_dir / "pandamap_analysis"
        pandamap_dir.mkdir(exist_ok=True)
        
        try:
            summary = run_publication_pandamap_analysis(
                complexes_dir=complexes_dir,
                output_dir=pandamap_dir,
                ligand_name="UNK",
                conda_env="pandamap",
                max_complexes=20  # Limit for performance
            )
            
            if summary:
                self.logger.info(f"✅ PandaMap analysis completed")
                self.logger.info(f"   📊 Generated {summary.get('generated_2d_maps', 0)} 2D maps")
                self.logger.info(f"   🌐 Generated {summary.get('generated_3d_visualizations', 0)} 3D visualizations")
                self.results['pandamap_summary'] = summary
                return True
            else:
                self.logger.warning("⚠️  PandaMap analysis returned no results")
                return False
                
        except Exception as e:
            self.logger.warning(f"⚠️  PandaMap analysis error: {e}")
            # Don't fail the pipeline if PandaMap is not available
            return True

