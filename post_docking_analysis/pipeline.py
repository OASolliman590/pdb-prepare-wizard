"""
Main pipeline module for post-docking analysis.
"""
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add the docking_analysis directory to the path so we can import its scripts
docking_analysis_path = Path(__file__).parent.parent / "docking_analysis"
sys.path.insert(0, str(docking_analysis_path))

from .config import *
from .input_handler import find_docking_files, validate_complex_files
from .docking_parser import parse_all_docking_results

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
        if ANALYZE_BINDING_AFFINITY:
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
        with open(summary_file, 'w') as f:
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
        fig, ax = plt.subplots(figsize=(12, 8))
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
        fig, ax = plt.subplots(figsize=(12, 8))
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
        
        # Check if Open Babel is available
        try:
            from openbabel import pybel
        except ImportError:
            print("⚠️  Open Babel not available - PDB extraction skipped")
            return True
        
        # Create output directory
        poses_dir = self.output_dir / "best_poses_pdb"
        poses_dir.mkdir(exist_ok=True)
        
        best_poses = self.results['best_poses']
        extracted_count = 0
        
        for _, row in best_poses.iterrows():
            complex_name = row['complex_name']
            pose_number = int(row['pose'])
            
            # Find the complex info
            complex_info = None
            for comp in self.complexes:
                if comp['name'] == complex_name:
                    complex_info = comp
                    break
            
            if not complex_info:
                print(f"⚠️  Complex info not found for {complex_name}")
                continue
                
            try:
                # Extract PDB from PDBQT
                pdb_content = self._extract_pose_from_pdbqt(
                    complex_info['docking_result'], 
                    pose_number,
                    complex_info.get('receptor'),
                    complex_name
                )
                
                if pdb_content:
                    # Save PDB file
                    pdb_file = poses_dir / f"{complex_name}_pose{pose_number}.pdb"
                    with open(pdb_file, 'w') as f:
                        f.write(pdb_content)
                    extracted_count += 1
                    print(f"✅ Extracted {complex_name} pose {pose_number}")
                else:
                    print(f"⚠️  Failed to extract {complex_name} pose {pose_number}")
                    
            except Exception as e:
                print(f"❌ Error extracting {complex_name} pose {pose_number}: {e}")
        
        print(f"✅ Extracted {extracted_count} best poses as PDB files to: {poses_dir}")
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