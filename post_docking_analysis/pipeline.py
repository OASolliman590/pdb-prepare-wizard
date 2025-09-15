"""
Main pipeline module for post-docking analysis.
"""
import sys
from pathlib import Path
import pandas as pd

# Add the docking_analysis directory to the path so we can import its scripts
docking_analysis_path = Path(__file__).parent.parent / "docking_analysis"
sys.path.insert(0, str(docking_analysis_path))

from .config import INPUT_DIR, OUTPUT_DIR, GENERATE_VISUALIZATIONS, OUTPUT_PDB
from .input_handler import find_docking_files, validate_complex_files
from .docking_parser import parse_all_docking_results
from .affinity_analyzer import analyze_protein_ligand_breakdown
from .rmsd_analyzer import calculate_rmsd_matrix, analyze_pose_clustering, analyze_conformational_diversity, create_rmsd_visualizations
from .structure_quality import assess_structure_quality, create_quality_visualizations
from .correlation_analyzer import analyze_vina_cnn_correlation, analyze_score_distributions, analyze_score_agreement, create_correlation_visualizations
from .pymol_visualizer import PyMOLVisualizer, create_comparative_analysis
from .pymol_generate import render_pymol_scene

class PostDockingAnalysisPipeline:
    """
    Main pipeline for post-docking analysis.
    
    This pipeline handles the complete analysis of molecular docking results,
    from parsing output files to generating comprehensive reports.
    """
    
    def __init__(self, input_dir="", output_dir=""):
        """
        Initialize the pipeline.
        
        Parameters
        ----------
        input_dir : str
            Path to the directory containing docking results
        output_dir : str
            Path to the directory where results will be saved
        """
        self.input_dir = Path(input_dir).resolve() if input_dir else Path(INPUT_DIR).resolve()
        self.output_dir = Path(output_dir).resolve() if output_dir else Path(OUTPUT_DIR).resolve()
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize results storage
        self.results = {}
        self.complexes = []
        self.docking_results = {}
        
    def validate_input(self):
        """
        Validate the input directory and files.
        
        Returns
        -------
        bool
            True if input is valid, False otherwise
        """
        if not self.input_dir.exists():
            print(f"❌ Input directory does not exist: {self.input_dir}")
            return False
            
        if not self.input_dir.is_dir():
            print(f"❌ Input path is not a directory: {self.input_dir}")
            return False
            
        return True
        
    def run_pipeline(self):
        """
        Run the complete post-docking analysis pipeline.
        """
        print("🚀 Starting Post-Docking Analysis Pipeline")
        print(f"📂 Input directory: {self.input_dir.absolute()}")
        print(f"📂 Output directory: {self.output_dir.absolute()}")
        print()
        
        # Validate input
        if not self.validate_input():
            return False
        
        # Fast-path: GNINA results already aggregated to CSV
        gnina_scores = self.input_dir / "gnina_out" / "all_scores.csv"
        if gnina_scores.exists():
            print("⚡ Detected GNINA scores CSV. Using streamlined analysis path.")
            if not self._analyze_from_gnina_scores(gnina_scores):
                return False
            # Reports
            if not self.generate_reports():
                return False
            # Visualizations
            if GENERATE_VISUALIZATIONS:
                if not self.generate_visualizations():
                    return False
            # Best poses extraction (supports GNINA SDFs)
            if OUTPUT_PDB:
                if not self.extract_best_poses_pdb():
                    return False
            print("✅ Post-Docking Analysis (GNINA fast-path) completed successfully!")
            return True
            
        # Step 1: Find docking files
        print("🔍 Finding docking files...")
        self.complexes = find_docking_files(self.input_dir)
        print(f"✅ Found {len(self.complexes)} complexes")
        
        # Validate complexes
        self.complexes = validate_complex_files(self.complexes)
        print(f"✅ Validated {len(self.complexes)} complexes")
        
        if len(self.complexes) == 0:
            print("❌ No valid complexes found. Check input directory structure.")
            return False
            
        # Print details about found complexes
        for i, complex_info in enumerate(self.complexes, 1):
            print(f"  {i}. {complex_info['name']}")
            for key, value in complex_info.items():
                if key != 'name' and key != 'directory':
                    print(f"     {key}: {value}")
        
        # Step 2: Parse docking results
        if not self.parse_docking_results():
            return False
            
        # Step 3: Analyze binding affinities
        if not self.analyze_binding_affinities():
            return False
                
        # Step 4: Generate reports
        if not self.generate_reports():
            return False
            
        # Step 5: Generate visualizations
        if GENERATE_VISUALIZATIONS:
            if not self.generate_visualizations():
                return False
                
        # Step 6: Extract best poses as PDB files
        if OUTPUT_PDB:
            if not self.extract_best_poses_pdb():
                return False
        
        # Step 7: Analyze protein vs ligand breakdown
        if not self.analyze_protein_ligand_breakdown():
            return False
            
        # Step 8: Perform RMSD analysis and clustering
        if not self.analyze_rmsd_and_clustering():
            return False
            
        # Step 9: Assess structure quality
        if not self.assess_structure_quality():
            return False
            
        # Step 10: Analyze score correlations
        if not self.analyze_correlations():
            return False
            
        # Step 11: Create PyMOL visualizations
        if not self.create_pymol_visualizations():
            return False
                
        print("✅ Post-Docking Analysis Pipeline completed successfully!")
        return True
        
    def parse_docking_results(self):
        """
        Parse docking result files and extract scores.
        
        Returns
        -------
        bool
            True if parsing successful, False otherwise
        """
        print("🔍 Parsing docking results...")
        
        # Parse all docking results
        self.docking_results = parse_all_docking_results(self.complexes)
        
        if not self.docking_results:
            print("❌ No docking results parsed successfully")
            return False
            
        print(f"✅ Parsed docking results for {len(self.docking_results)} complexes")
        return True
        
    def analyze_binding_affinities(self):
        """
        Analyze binding affinities and identify top performers.
        
        Returns
        -------
        bool
            True if analysis successful, False otherwise
        """
        print("📊 Analyzing binding affinities...")
        
        # Create a comprehensive DataFrame with all results
        all_data = []
        for complex_name, df in self.docking_results.items():
            for _, row in df.iterrows():
                all_data.append({
                    'complex_name': complex_name,
                    'pose': row['pose'],
                    'vina_affinity': row['vina_affinity'],
                    'rmsd_lb': row['rmsd_lb'],
                    'rmsd_ub': row['rmsd_ub']
                })
        
        if not all_data:
            print("❌ No data to analyze")
            return False
            
        full_df = pd.DataFrame(all_data)
        
        # Find best pose for each complex (most negative = strongest binding)
        best_poses = full_df.loc[full_df.groupby('complex_name')['vina_affinity'].idxmin()].copy()
        best_poses = best_poses.sort_values('vina_affinity')
        
        # Calculate summary statistics per complex
        summary_stats = full_df.groupby('complex_name').agg({
            'vina_affinity': ['min', 'max', 'mean', 'std'],
        }).round(3)
        
        # Flatten column names
        summary_stats.columns = ['_'.join(col).strip() for col in summary_stats.columns]
        summary_stats = summary_stats.reset_index()
        
        # Highlight top performers
        top_overall = best_poses.head(10)[['complex_name', 'vina_affinity', 'pose']]
        
        self.results = {
            'full_data': full_df,
            'best_poses': best_poses,
            'summary_stats': summary_stats,
            'top_overall': top_overall
        }
        
        print(f"✅ Binding affinities analyzed for {len(full_df)} poses across {len(best_poses)} complexes")
        print(f"   Best binding affinity: {best_poses['vina_affinity'].min():.2f} kcal/mol")
        return True
        
    def generate_reports(self):
        """
        Generate summary reports in various formats.
        
        Returns
        -------
        bool
            True if report generation successful, False otherwise
        """
        print("📝 Generating summary reports...")
        
        # Create output directory
        reports_dir = self.output_dir / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        # Generate individual CSV files for each result type
        for name, df in self.results.items():
            if isinstance(df, pd.DataFrame):
                csv_file = reports_dir / f"{name}.csv"
                df.to_csv(csv_file, index=False)
                print(f"✅ {name} report saved to: {csv_file}")
        
        # Generate Excel report
        try:
            import openpyxl
            excel_file = reports_dir / "docking_analysis_results.xlsx"
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                for name, df in self.results.items():
                    if isinstance(df, pd.DataFrame):
                        # Limit sheet name to 31 characters (Excel limit)
                        sheet_name = name[:31]
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"✅ Excel report saved to: {excel_file}")
        except ImportError:
            print("⚠️  openpyxl not available - Excel report generation skipped")
        
        # Generate summary report
        best_poses = self.results['best_poses']
        summary_lines = [
            "Post-Docking Analysis Summary Report",
            "==================================",
            "",
            f"Total complexes analyzed: {len(best_poses)}",
            f"Average binding affinity: {best_poses['vina_affinity'].mean():.2f} kcal/mol",
            f"Best binding affinity: {best_poses['vina_affinity'].min():.2f} kcal/mol",
            f"Worst binding affinity: {best_poses['vina_affinity'].max():.2f} kcal/mol",
            "",
            "Top 5 Performers:",
        ]
        
        # Add top 5 performers
        top_5 = best_poses.head(5)
        for idx, (_, row) in enumerate(top_5.iterrows(), 1):
            summary_lines.append(
                f"  {idx}. {row['complex_name']}: {row['vina_affinity']:.2f} kcal/mol (Pose {row['pose']})"
            )
        
        # Save summary report
        summary_file = reports_dir / "summary_report.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary_lines))
        print(f"✅ Summary report saved to: {summary_file}")
        
        print("✅ Summary reports generated successfully!")
        return True
        
    def generate_visualizations(self):
        """
        Generate visualizations of the results.
        
        Returns
        -------
        bool
            True if visualization generation successful, False otherwise
        """
        print("📊 Generating visualizations...")
        
        # Check if matplotlib is available
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
        except ImportError:
            print("⚠️  matplotlib/seaborn not available - visualization generation skipped")
            return True
        
        # Create output directory
        viz_dir = self.output_dir / "visualizations"
        viz_dir.mkdir(exist_ok=True)
        
        # Get best poses data
        best_poses = self.results['best_poses']
        
        # Create binding affinity distribution plot
        _fig, ax = plt.subplots(figsize=(12, 8))
        sns.histplot(best_poses['vina_affinity'], kde=True, ax=ax)
        ax.set_xlabel('Binding Affinity (kcal/mol)')
        ax.set_ylabel('Frequency')
        ax.set_title('Distribution of Binding Affinities')
        plot_file = viz_dir / "binding_affinity_distribution.png"
        plt.tight_layout()
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Binding affinity plot saved to: {plot_file}")
        
        # Create top performers plot
        _fig2, ax = plt.subplots(figsize=(12, 8))
        top_10 = best_poses.head(10)
        sns.barplot(data=top_10, x='vina_affinity', y='complex_name', ax=ax)
        ax.set_xlabel('Binding Affinity (kcal/mol)')
        ax.set_ylabel('Complex')
        ax.set_title('Top 10 Performing Complexes')
        plot_file = viz_dir / "top_performers.png"
        plt.tight_layout()
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Top performers plot saved to: {plot_file}")
        
        print("✅ Visualizations generated successfully!")
        return True
        
    def extract_best_poses_pdb(self):
        """
        Extract best poses as PDB files by combining receptor and ligand coordinates.
        
        Returns
        -------
        bool
            True if extraction successful, False otherwise
        """
        print("🔬 Extracting best poses as PDB files...")
        
        # Prefer GNINA SDF-based extraction when a gnina_out folder exists
        try:
            from .pose_extractor import extract_best_poses_from_gnina
            gnina_dir = self.input_dir / "gnina_out"
            if gnina_dir.exists():
                written = extract_best_poses_from_gnina(self.input_dir, self.output_dir)
                if written > 0:
                    return True
                else:
                    print("⚠️  GNINA-based extraction wrote 0 files; falling back to PDBQT extraction")
        except Exception as e:
            print(f"⚠️  GNINA-based extraction unavailable: {e}")
        
        # Fallback: extract from Vina PDBQT outputs if available
        try:
            from openbabel import pybel  # noqa: F401
        except ImportError:
            print("⚠️  Open Babel not available - PDB extraction skipped")
            return True
        
        poses_dir = self.output_dir / "best_poses_pdb"
        poses_dir.mkdir(exist_ok=True)
        
        best_poses = self.results['best_poses']
        extracted_count = 0
        
        for _, row in best_poses.iterrows():
            complex_name = row['complex_name']
            pose_number = int(row['pose'])
            
            complex_info = None
            for comp in self.complexes:
                if comp['name'] == complex_name:
                    complex_info = comp
                    break
            
            if not complex_info:
                print(f"⚠️  Complex info not found for {complex_name}")
                continue
                
            try:
                pdb_content = self._extract_pose_from_pdbqt(
                    complex_info['docking_result'], 
                    pose_number,
                    complex_info.get('receptor'),
                    complex_name
                )
                
                if pdb_content:
                    pdb_file = poses_dir / f"{complex_name}_pose{pose_number}.pdb"
                    with open(pdb_file, 'w', encoding='utf-8') as f:
                        f.write(pdb_content)
                    extracted_count += 1
                    print(f"✅ Extracted {complex_name} pose {pose_number}")
                else:
                    print(f"⚠️  Failed to extract {complex_name} pose {pose_number}")
                    
            except Exception as e:
                print(f"❌ Error extracting {complex_name} pose {pose_number}: {e}")
        
        print(f"✅ Extracted {extracted_count} best poses as PDB files to: {poses_dir}")
        
        # Optional: auto-render PyMOL PNGs for each extracted pose if PyMOL is available
        try:
            rendered_dir = self.output_dir / "pymol_renders"
            for pdb_file in poses_dir.glob("*.pdb"):
                render_pymol_scene(pdb_file, rendered_dir, pdb_file.stem)
        except Exception as e:
            print(f"⚠️  Skipping PyMOL auto-render: {e}")
        return True
        
    def _extract_pose_from_pdbqt(self, pdbqt_file, pose_number, receptor_file, complex_name):
        """
        Extract a specific pose from PDBQT file and combine with receptor.
        
        Parameters
        ----------
        pdbqt_file : Path
            Path to PDBQT file
        pose_number : int
            Pose number to extract (1-based)
        receptor_file : Path
            Path to receptor PDBQT file
        complex_name : str
            Name of the complex
            
        Returns
        -------
        str
            PDB content as string, or None if failed
        """
        try:
            from openbabel import pybel
            
            # Read the PDBQT file and extract the specific pose
            poses = list(pybel.readfile("pdbqt", str(pdbqt_file)))
            
            if pose_number > len(poses):
                print(f"⚠️  Pose {pose_number} not found in {pdbqt_file}")
                return None
                
            ligand_pose = poses[pose_number - 1]  # Convert to 0-based index
            
            # Convert ligand to PDB format
            ligand_pdb = ligand_pose.write("pdb")
            ligand_lines = []
            for line in ligand_pdb.split('\n'):
                if line.startswith('ATOM') or line.startswith('HETATM'):
                    # Fix the line format and assign chain B
                    line = line.ljust(80)
                    new_line = f"HETATM{line[6:21]}B{line[22:]}"
                    new_line = new_line[:17] + "UNK" + new_line[20:]
                    ligand_lines.append(new_line)
            
            # Read receptor if available
            receptor_lines = []
            if receptor_file and receptor_file.exists():
                try:
                    receptor_mol = next(pybel.readfile("pdbqt", str(receptor_file)))
                    receptor_pdb = receptor_mol.write("pdb")
                    for line in receptor_pdb.split('\n'):
                        if line.startswith('ATOM'):
                            # Fix the line format and assign chain A
                            line = line.ljust(80)
                            new_line = f"ATOM  {line[6:21]}A{line[22:]}"
                            receptor_lines.append(new_line)
                except Exception as e:
                    print(f"⚠️  Could not read receptor {receptor_file}: {e}")
            
            # Combine receptor and ligand
            all_lines = receptor_lines + ligand_lines + ["END"]
            return '\n'.join(all_lines)
            
        except Exception as e:
            print(f"❌ Error extracting pose from PDBQT: {e}")
            return None
    
    def analyze_protein_ligand_breakdown(self):
        """
        Analyze best performance by protein and by ligand.
        
        Returns
        -------
        bool
            True if analysis successful, False otherwise
        """
        print("🧬 Analyzing protein vs ligand breakdown...")
        
        if not hasattr(self, 'results') or 'best_poses' not in self.results:
            print("❌ No results available for protein-ligand breakdown")
            return False
        
        try:
            # Perform protein-ligand breakdown analysis
            breakdown_results = analyze_protein_ligand_breakdown(self.results['best_poses'])
            
            # Store results
            if not hasattr(self, 'results'):
                self.results = {}
            self.results['protein_ligand_breakdown'] = breakdown_results
            
            # Save breakdown reports
            breakdown_dir = self.output_dir / "reports"
            breakdown_dir.mkdir(exist_ok=True)
            
            breakdown_results['best_per_protein'].to_csv(
                breakdown_dir / "best_per_protein.csv", index=False
            )
            breakdown_results['best_per_ligand'].to_csv(
                breakdown_dir / "best_per_ligand.csv", index=False
            )
            breakdown_results['protein_summary'].to_csv(
                breakdown_dir / "protein_summary.csv", index=False
            )
            breakdown_results['ligand_summary'].to_csv(
                breakdown_dir / "ligand_summary.csv", index=False
            )
            
            print("✅ Protein vs ligand breakdown completed")
            return True
            
        except Exception as e:
            print(f"❌ Error in protein-ligand breakdown: {e}")
            return False
    
    def analyze_rmsd_and_clustering(self):
        """
        Perform RMSD analysis and pose clustering.
        
        Returns
        -------
        bool
            True if analysis successful, False otherwise
        """
        print("📏 Analyzing RMSD and pose clustering...")
        
        if not hasattr(self, 'results') or 'full_data' not in self.results:
            print("❌ No results available for RMSD analysis")
            return False
        
        try:
            # Calculate RMSD matrix (placeholder implementation)
            rmsd_matrix = calculate_rmsd_matrix(self.results['full_data'])
            
            # Perform pose clustering
            clustering_results = analyze_pose_clustering(
                self.results['full_data'], rmsd_matrix, method='kmeans', n_clusters=3
            )
            
            # Analyze conformational diversity
            diversity_results = analyze_conformational_diversity(
                self.results['full_data'], rmsd_matrix
            )
            
            # Store results
            if not hasattr(self, 'results'):
                self.results = {}
            self.results['rmsd_analysis'] = {
                'clustering': clustering_results,
                'diversity': diversity_results,
                'rmsd_matrix': rmsd_matrix
            }
            
            # Create RMSD visualizations
            viz_dir = self.output_dir / "visualizations"
            viz_dir.mkdir(exist_ok=True)
            create_rmsd_visualizations(
                clustering_results, diversity_results, viz_dir
            )
            
            # Save RMSD reports
            reports_dir = self.output_dir / "reports"
            reports_dir.mkdir(exist_ok=True)
            
            clustering_results['poses_with_clusters'].to_csv(
                reports_dir / "poses_with_clusters.csv", index=False
            )
            clustering_results['cluster_summary'].to_csv(
                reports_dir / "cluster_summary.csv", index=False
            )
            clustering_results['cluster_centroids'].to_csv(
                reports_dir / "cluster_centroids.csv", index=False
            )
            diversity_results['diversity_metrics'].to_csv(
                reports_dir / "diversity_metrics.csv", index=False
            )
            
            print("✅ RMSD analysis and clustering completed")
            return True
            
        except Exception as e:
            print(f"❌ Error in RMSD analysis: {e}")
            return False
    
    def assess_structure_quality(self):
        """
        Assess structure quality of best poses.
        
        Returns
        -------
        bool
            True if analysis successful, False otherwise
        """
        print("🔍 Assessing structure quality...")
        
        if not hasattr(self, 'results') or 'best_poses' not in self.results:
            print("❌ No results available for structure quality assessment")
            return False
        
        try:
            # Get best poses PDB files
            poses_dir = self.output_dir / "best_poses_pdb"
            if not poses_dir.exists():
                print("⚠️ Best poses PDB files not found - skipping quality assessment")
                return True
            
            quality_results = []
            pdb_files = list(poses_dir.glob("*.pdb"))
            
            for pdb_file in pdb_files:
                quality_assessment = assess_structure_quality(pdb_file)
                quality_results.append(quality_assessment)
            
            # Store results
            if not hasattr(self, 'results'):
                self.results = {}
            self.results['structure_quality'] = quality_results
            
            # Create quality visualizations
            viz_dir = self.output_dir / "visualizations"
            viz_dir.mkdir(exist_ok=True)
            create_quality_visualizations(quality_results, viz_dir)
            
            # Save quality reports
            reports_dir = self.output_dir / "reports"
            reports_dir.mkdir(exist_ok=True)
            
            quality_summary = []
            for result in quality_results:
                quality_summary.append({
                    'pdb_file': Path(result['pdb_file']).name,
                    'quality_score': result['quality_score'],
                    'overall_quality': result['overall_quality'],
                    'total_clashes': result['clash_data']['total_clashes'],
                    'allowed_residues_pct': result['ramachandran_quality']['allowed_percentage']
                })
            
            quality_df = pd.DataFrame(quality_summary)
            quality_df.to_csv(reports_dir / "structure_quality_summary.csv", index=False)
            
            print("✅ Structure quality assessment completed")
            return True
            
        except Exception as e:
            print(f"❌ Error in structure quality assessment: {e}")
            return False
    
    def analyze_correlations(self):
        """
        Analyze correlations between different scoring functions.
        
        Returns
        -------
        bool
            True if analysis successful, False otherwise
        """
        print("📊 Analyzing score correlations...")
        
        if not hasattr(self, 'results') or 'full_data' not in self.results:
            print("❌ No results available for correlation analysis")
            return False
        
        try:
            # Analyze Vina-CNN correlations
            correlation_results = analyze_vina_cnn_correlation(self.results['full_data'])
            
            # Analyze score distributions
            distribution_results = analyze_score_distributions(self.results['full_data'])
            
            # Analyze score agreement
            agreement_results = analyze_score_agreement(self.results['full_data'])
            
            # Store results
            if not hasattr(self, 'results'):
                self.results = {}
            self.results['correlation_analysis'] = {
                'correlations': correlation_results,
                'distributions': distribution_results,
                'agreement': agreement_results
            }
            
            # Create correlation visualizations
            viz_dir = self.output_dir / "visualizations"
            viz_dir.mkdir(exist_ok=True)
            create_correlation_visualizations(
                correlation_results, distribution_results, agreement_results, viz_dir
            )
            
            # Save correlation reports
            reports_dir = self.output_dir / "reports"
            reports_dir.mkdir(exist_ok=True)
            
            if 'error' not in correlation_results:
                correlation_summary = {
                    'n_samples': correlation_results['n_samples'],
                    'vina_cnn_affinity_pearson': correlation_results['pearson_correlations']['vina_cnn_affinity']['correlation'],
                    'vina_cnn_affinity_p_value': correlation_results['pearson_correlations']['vina_cnn_affinity']['p_value'],
                    'vina_cnn_score_pearson': correlation_results['pearson_correlations']['vina_cnn_score']['correlation'],
                    'vina_cnn_score_p_value': correlation_results['pearson_correlations']['vina_cnn_score']['p_value']
                }
                
                correlation_df = pd.DataFrame([correlation_summary])
                correlation_df.to_csv(reports_dir / "correlation_summary.csv", index=False)
            
            print("✅ Correlation analysis completed")
            return True
            
        except Exception as e:
            print(f"❌ Error in correlation analysis: {e}")
            return False
    
    def create_pymol_visualizations(self):
        """
        Create 3D visualizations using PyMOL.
        
        Returns
        -------
        bool
            True if analysis successful, False otherwise
        """
        print("🎬 Creating PyMOL visualizations...")
        
        try:
            # Create PyMOL visualizer
            pymol_dir = self.output_dir / "pymol_visualizations"
            visualizer = PyMOLVisualizer(pymol_dir)
            
            # Get best poses PDB files
            poses_dir = self.output_dir / "best_poses_pdb"
            if poses_dir.exists():
                pdb_files = list(poses_dir.glob("*.pdb"))
                
                if len(pdb_files) >= 2:
                    # Create comparative analysis between first two poses
                    reference_pdb = pdb_files[0]
                    novel_pdb = pdb_files[1]
                    
                    comparative_results = create_comparative_analysis(
                        reference_pdb, novel_pdb, pymol_dir, highlight_residues=[212, 213, 214]
                    )
                    
                    # Create best poses gallery
                    gallery_session = visualizer.create_best_poses_gallery(
                        pdb_files[:5], "best_poses_gallery"  # Limit to first 5 poses
                    )
                    
                    # Store results
                    if not hasattr(self, 'results'):
                        self.results = {}
                    self.results['pymol_visualizations'] = {
                        'comparative_analysis': comparative_results,
                        'gallery_session': gallery_session,
                        'output_directory': pymol_dir
                    }
                    
                    print("✅ PyMOL visualizations created")
                    return True
                else:
                    print("⚠️ Need at least 2 PDB files for comparative analysis")
                    return True
            else:
                print("⚠️ Best poses PDB files not found - skipping PyMOL visualizations")
                return True
                
        except Exception as e:
            print(f"❌ Error creating PyMOL visualizations: {e}")
            return False

    def _analyze_from_gnina_scores(self, scores_csv: Path):
        """
        Streamlined analysis when GNINA all_scores.csv is available.
        Populates self.results with full_data, best_poses, summary_stats, top_overall.
        """
        try:
            print("🔍 Loading GNINA scores CSV...")
            df = pd.read_csv(scores_csv)
            if df.empty:
                print("❌ GNINA scores CSV is empty")
                return False
            # Normalize columns
            required = {'tag', 'mode', 'vina_affinity'}
            if not required.issubset(set(df.columns)):
                print("❌ GNINA scores CSV missing required columns")
                return False
            df['complex_name'] = df['tag']
            df['pose'] = df['mode']
            full_df = df[['complex_name', 'pose', 'vina_affinity']].copy()
            # Best poses per tag
            best_poses = df.loc[df.groupby('tag')['vina_affinity'].idxmin()].copy()
            best_poses = best_poses.sort_values('vina_affinity')
            best_poses.rename(columns={'tag': 'complex_name', 'mode': 'pose'}, inplace=True)
            best_poses = best_poses[['complex_name', 'pose', 'vina_affinity']]
            # Summary
            summary_stats = full_df.groupby('complex_name').agg({
                'vina_affinity': ['min', 'max', 'mean', 'std']
            }).round(3)
            summary_stats.columns = ['_'.join(col).strip() for col in summary_stats.columns]
            summary_stats = summary_stats.reset_index()
            # Top
            top_overall = best_poses.head(10)[['complex_name', 'vina_affinity', 'pose']]
            self.results = {
                'full_data': full_df,
                'best_poses': best_poses,
                'summary_stats': summary_stats,
                'top_overall': top_overall
            }
            print(f"✅ GNINA scores loaded: {len(full_df)} poses, {len(best_poses)} complexes")
            return True
        except Exception as e:
            print(f"❌ Error reading GNINA scores: {e}")
            return False


def main():
    """
    Main function to run the pipeline from command line.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Post-Docking Analysis Pipeline")
    parser.add_argument("-i", "--input", help="Input directory containing docking results")
    parser.add_argument("-o", "--output", help="Output directory for results")
    parser.add_argument("--config", help="Configuration file path")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = PostDockingAnalysisPipeline(
        input_dir=args.input or "",
        output_dir=args.output or ""
    )
    
    # Run pipeline
    success = pipeline.run_pipeline()
    
    if success:
        print("\n🎉 Pipeline completed successfully!")
        print(f"📁 Results saved to: {pipeline.output_dir}")
    else:
        print("\n❌ Pipeline failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()